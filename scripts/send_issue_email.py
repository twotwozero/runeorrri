#!/usr/bin/env python3
import csv
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from pathlib import Path

from generate_web_data import build_web_data


ROOT = Path(__file__).resolve().parents[1]
TODAY = date.today().isoformat()
NEWSLETTER = ROOT / "issues" / f"{TODAY}-running-newsletter.md"
CARDS_DIR = ROOT / "issues" / f"{TODAY}-cards"
CARD_ALBUM = ROOT / "issues" / f"{TODAY}-running-cardnews-album.html"
CURRENT_ISSUE = ROOT / "data" / "current_issue_id.txt"
ART_DIR = ROOT / "issues" / f"{TODAY}-art"


def load_dotenv():
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def issue_number():
    if not CURRENT_ISSUE.exists():
        return "01"
    issue_id = CURRENT_ISSUE.read_text(encoding="utf-8").strip()
    suffix = issue_id.rsplit("-", 1)[-1]
    return suffix.zfill(2) if suffix.isdigit() else "01"


def card_images():
    if not CARDS_DIR.exists():
        return []
    preferred_cards = sorted(CARDS_DIR.glob("*.svg.png"))
    fallback_cards = sorted(
        png for png in CARDS_DIR.glob("*.png") if not png.name.endswith(".svg.png")
    )
    return preferred_cards or fallback_cards


def art_images():
    return {
        "hero": ART_DIR / "hero.png",
        "lineup": ART_DIR / "lineup.png",
        "checkpoints": ART_DIR / "checkpoints.png",
    }


def runneri_issue_url(base_url):
    return f"{base_url.rstrip('/')}/issues/{TODAY}"


def selected_rows():
    candidates = ROOT / "data" / "candidates.csv"
    with candidates.open(newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row.get("selected", "").strip().lower() == "yes"]


def region_label(row):
    return "국내" if row.get("region", "").strip().lower() == "korea" else "해외"


def category_label(row):
    labels = {
        "event": "대회/이벤트",
        "race": "레이스",
        "news": "뉴스",
        "gear": "장비",
        "elite": "엘리트",
    }
    return labels.get(row.get("category", "").strip().lower(), row.get("category", "소식"))


def line_up(rows):
    return "\n".join(
        f"""
        <tr>
          <td style="padding:0 0 10px 0;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;">
            <div style="font-size:13px;line-height:1.3;font-weight:900;color:#ff6b4a;">{index:02d} · {escape(region_label(row))} / {escape(category_label(row))}</div>
            <div style="margin-top:3px;font-size:16px;line-height:1.45;font-weight:850;color:#111514;">{escape(row['title'])}</div>
          </td>
        </tr>
        """
        for index, row in enumerate(rows, start=1)
    )


def brief_items(rows):
    return "\n".join(
        f"""
        <tr>
          <td style="padding:20px 0;border-top:1px solid #ded8cf;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;">
            <div style="font-size:13px;line-height:1.3;font-weight:900;color:#ff6b4a;">{index:02d} · {escape(region_label(row))} / {escape(category_label(row))}</div>
            <div style="margin-top:7px;font-size:21px;line-height:1.35;font-weight:900;color:#111514;">{escape(row['title'])}</div>
            <div style="margin-top:12px;font-size:15px;line-height:1.75;font-weight:650;color:#323332;">{escape(row['summary'])}</div>
            <div style="margin-top:12px;padding:13px 15px;background:#fff7ec;border-left:4px solid #ff6b4a;font-size:14px;line-height:1.65;font-weight:750;color:#323332;">
              <span style="color:#ff6b4a;font-weight:900;">러너리 코멘트</span><br>{escape(row['why_it_matters'])}
            </div>
            <div style="margin-top:10px;font-size:13px;line-height:1.5;color:#7b817d;">
              원문: <a href="{escape(row['url'])}" style="color:#ff6b4a;text-decoration:none;font-weight:800;">{escape(row['source'])}</a>
            </div>
          </td>
        </tr>
        """
        for index, row in enumerate(rows, start=2)
    )


def source_links(rows):
    return "\n".join(
        f"""
        <tr>
          <td style="padding:8px 0;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;font-size:13px;line-height:1.5;">
            <a href="{escape(row['url'])}" style="color:#f7f4ec;text-decoration:none;font-weight:800;">{escape(row['title'])}</a>
            <div style="color:#aab4af;margin-top:2px;">{escape(row['source'])} · {escape(row.get('published_at', ''))}</div>
          </td>
        </tr>
        """
        for row in rows
    )


def action_list(rows):
    event_count = sum(1 for row in rows if row.get("category", "").strip().lower() in {"event", "race"})
    gear_count = sum(1 for row in rows if row.get("category", "").strip().lower() == "gear")
    return f"""
      <li style="margin:0 0 8px 0;">접수·일정형 소식 {event_count}개는 마감일과 장소를 먼저 확인하세요.</li>
      <li style="margin:0 0 8px 0;">해외 소식은 당장 참가보다 러닝 시장의 방향을 읽는 용도로 보면 좋습니다.</li>
      <li style="margin:0;">장비 소식 {gear_count}개는 구매 추천이 아니라 기술 흐름 참고용으로 정리했습니다.</li>
    """


def html_email(image_cids, issue_url):
    number = issue_number()
    rows = selected_rows()
    main = rows[0] if rows else {}
    other_rows = rows[1:]
    hero_img = f'<a href="{escape(issue_url)}" style="text-decoration:none;border:0;display:block;"><img src="cid:{image_cids["hero"]}" width="600" alt="러너리 브리핑" style="width:100%;max-width:600px;height:auto;display:block;margin:0 auto;border:0;"></a>'
    lineup_img = f'<img src="cid:{image_cids["lineup"]}" width="600" alt="오늘의 라인업" style="width:100%;max-width:600px;height:auto;display:block;margin:0 auto;border:0;">'
    checkpoint_img = f'<img src="cid:{image_cids["checkpoints"]}" width="600" alt="러너리 체크포인트" style="width:100%;max-width:600px;height:auto;display:block;margin:0 auto;border:0;">'
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>[러너리] 오늘의 러닝 브리핑 {escape(number)} - {TODAY}</title>
</head>
<body style="-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;margin:0;padding:0;background:#F7F5F1;">
  <div style="display:none;max-height:0;overflow:hidden;font-size:0;line-height:0;color:#F7F5F1;">
    국내외 러닝 소식 5개를 카드뉴스로 정리했습니다.
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;background:#F7F5F1;">
    <tr>
      <td align="center" style="padding:24px 0;">
        <table role="presentation" width="630" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:630px;background:#F7F5F1;">
          <tr>
            <td style="padding:12px 20px 8px 20px;text-align:center;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;color:#111514;">
              <div style="font-size:26px;line-height:1.2;font-weight:900;letter-spacing:0;"><a href="{escape(issue_url)}" style="color:#111514;text-decoration:none;">@runeorrri</a></div>
              <div style="margin-top:12px;font-size:14px;line-height:1.5;font-weight:800;color:#ff6b4a;"><a href="{escape(issue_url)}" style="color:#ff6b4a;text-decoration:none;">오늘의 러닝 브리핑 {escape(number)}</a></div>
              <div style="margin-top:4px;font-size:12px;line-height:1.5;font-weight:700;color:#6f7773;">{TODAY}</div>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 15px 18px 15px;">
              <div style="height:1px;background:#111514;opacity:0.25;line-height:1px;font-size:1px;">&nbsp;</div>
            </td>
          </tr>
          <tr>
            <td style="padding:0 15px 24px 15px;text-align:center;font-size:0;">
              {hero_img}
            </td>
          </tr>
          <tr>
            <td style="padding:2px 24px 26px 24px;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;color:#323332;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="padding:0;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;color:#323332;">
                    <div style="font-size:16px;line-height:1.8;font-weight:700;">
                      안녕하세요, 러너리입니다. 오늘은 “이번 주말 뭘 확인해야 하지?”라는 질문에 답이 될 만한 러닝 소식을 골랐습니다.
                      단순히 기사 제목을 모은 게 아니라, 지금 러너가 어떤 행동을 하면 좋을지까지 이어지도록 정리했어요.
                    </div>
                    <div style="margin-top:14px;font-size:16px;line-height:1.8;font-weight:650;">
                      이번 호의 중심은 <b>참여형 러닝 이벤트의 확장</b>입니다. 대회가 더 이상 기록만 겨루는 장이 아니라,
                      커뮤니티를 만나고 브랜드 경험을 체험하고, 때로는 기부나 여행과 연결되는 콘텐츠가 되고 있습니다.
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 30px 24px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff;border:1px solid #e6dfd5;">
                <tr>
                  <td style="padding:20px 20px 10px 20px;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;">
                    <div style="font-size:13px;line-height:1.4;font-weight:900;color:#ff6b4a;">오늘의 라인업</div>
                  </td>
                </tr>
                <tr>
                  <td style="padding:0 20px 12px 20px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                      {line_up(rows)}
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 15px 28px 15px;text-align:center;font-size:0;">
              {lineup_img}
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 28px 24px;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;color:#323332;">
              <div style="font-size:13px;line-height:1.3;font-weight:900;color:#ff6b4a;">MAIN STORY</div>
              <div style="margin-top:8px;font-size:28px;line-height:1.25;font-weight:950;color:#111514;">{escape(main.get('title', ''))}</div>
              <div style="margin-top:16px;font-size:16px;line-height:1.8;font-weight:650;color:#323332;">{escape(main.get('summary', ''))}</div>
              <div style="margin-top:14px;font-size:16px;line-height:1.8;font-weight:650;color:#323332;">
                이 소식은 러닝 행사가 어떤 방향으로 바뀌는지 보여줍니다. 최근 러닝 이벤트는 완주 기록보다
                <b>누구와, 어떤 분위기에서, 어떤 이야기를 만들며 달리느냐</b>를 더 강하게 내세우고 있습니다.
                그래서 러너 입장에서는 참가비와 기념품만 보는 대신, 운영 동선·안전 관리·현장 프로그램까지 함께 보는 눈이 필요합니다.
              </div>
              <div style="margin-top:16px;padding:16px 18px;background:#111514;color:#f7f4ec;font-size:15px;line-height:1.75;font-weight:750;">
                <span style="display:block;color:#49dcb1;font-size:13px;font-weight:900;margin-bottom:6px;">러너리 코멘트</span>
                {escape(main.get('why_it_matters', ''))}
              </div>
              <div style="margin-top:12px;font-size:13px;line-height:1.5;color:#7b817d;">
                원문: <a href="{escape(main.get('url', ''))}" style="color:#ff6b4a;text-decoration:none;font-weight:800;">{escape(main.get('source', ''))}</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 26px 24px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fffffb;border:1px solid #ded8cf;">
                <tr>
                  <td style="padding:18px 20px 8px 20px;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;">
                    <div style="font-size:13px;line-height:1.4;font-weight:900;color:#ff6b4a;">MID-RUN NOTE</div>
                    <div style="margin-top:6px;font-size:15px;line-height:1.75;font-weight:700;color:#323332;">
                      참가형 소식은 흥미로운 콘셉트만 보지 말고, 접수 시간·현장 수령·이동 동선까지 같이 체크하면 훨씬 덜 허둥댑니다.
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 26px 24px;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f7f4ec;border-top:3px solid #111514;border-bottom:1px solid #ded8cf;">
                <tr>
                  <td style="padding:18px 0 18px 0;">
                    <div style="font-size:15px;line-height:1.7;font-weight:900;color:#111514;">이번 호를 읽는 관점</div>
                    <div style="margin-top:8px;font-size:15px;line-height:1.8;font-weight:650;color:#323332;">
                      오늘의 다섯 소식은 모두 “러닝이 혼자 하는 운동을 넘어 어떻게 사람을 모으는 콘텐츠가 되는가”와 연결됩니다.
                      접수 일정은 실용적으로 챙기되, 그 뒤에 있는 커뮤니티·브랜드·도시 경험의 변화를 함께 보면 더 잘 읽힙니다.
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 8px 24px;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;">
              <div style="font-size:13px;line-height:1.3;font-weight:900;color:#ff6b4a;">RUNNERLY BRIEFS</div>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 28px 24px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                {brief_items(other_rows)}
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 30px 24px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fff7ec;border:1px solid #f0d7c1;">
                <tr>
                  <td style="padding:18px 20px;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;color:#323332;">
                    <div style="font-size:16px;line-height:1.45;font-weight:900;color:#111514;">이번 호에서 바로 할 일</div>
                    <ul style="margin:12px 0 0 20px;padding:0;font-size:14px;line-height:1.65;font-weight:700;">
                      {action_list(rows)}
                    </ul>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 15px 30px 15px;text-align:center;font-size:0;">
              {checkpoint_img}
            </td>
          </tr>
          <tr>
            <td style="padding:6px 24px 30px 24px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#111514;">
                <tr>
                  <td style="padding:20px 22px;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;">
                    <div style="font-size:13px;line-height:1.4;font-weight:900;color:#49dcb1;">SOURCES</div>
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:8px;">
                      {source_links(rows)}
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 20px 28px 20px;text-align:center;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',Arial,sans-serif;color:#6f7773;">
              <div style="font-size:12px;line-height:1.7;">
                runeorrri · running briefing<br>
                이 메일은 발행 전 검수용 테스트 메일입니다.
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def main():
    load_dotenv()
    runneri_site_base_url = required_env("RUNNERI_SITE_BASE_URL")
    smtp_host = required_env("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = required_env("SMTP_USER")
    smtp_password = required_env("SMTP_PASSWORD")
    mail_from = os.environ.get("MAIL_FROM", smtp_user)
    mail_from_name = os.environ.get("MAIL_FROM_NAME", "runeorrri")
    mail_to = required_env("MAIL_TO")

    if not NEWSLETTER.exists():
        raise SystemExit(f"Newsletter not found: {NEWSLETTER}")

    build_web_data()
    issue_url = runneri_issue_url(runneri_site_base_url)

    msg = EmailMessage()
    running_emoji = "\U0001f3c3\U0001f3fb\u200d\u2640\ufe0f"
    msg["Subject"] = f"[러너리] {running_emoji} 오늘의 러닝 브리핑 {issue_number()} - {TODAY}"
    msg["From"] = formataddr((mail_from_name, mail_from))
    msg["To"] = mail_to
    msg.set_content(NEWSLETTER.read_text(encoding="utf-8"))

    art = art_images()
    missing_art = [path for path in art.values() if not path.exists()]
    if missing_art:
        raise SystemExit(f"Missing newsletter art files: {', '.join(str(path) for path in missing_art)}")
    image_cids = {key: f"runeorrri-{key}-{TODAY}" for key in art}
    msg.add_alternative(html_email(image_cids, issue_url), subtype="html")
    html_part = msg.get_payload()[-1]
    for key, png in art.items():
        html_part.add_related(
            png.read_bytes(),
            maintype="image",
            subtype="png",
            cid=f"<{image_cids[key]}>",
            filename=png.name,
            disposition="inline",
        )

    msg.add_attachment(
        NEWSLETTER.read_bytes(),
        maintype="text",
        subtype="markdown",
        filename=NEWSLETTER.name,
    )

    if CARD_ALBUM.exists():
        msg.add_attachment(
            CARD_ALBUM.read_bytes(),
            maintype="text",
            subtype="html",
            filename=CARD_ALBUM.name,
        )

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(msg)

    print(f"Sent newsletter to {mail_to}")


if __name__ == "__main__":
    main()
