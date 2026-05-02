#!/usr/bin/env python3
import csv
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates.csv"
CURRENT_ISSUE = ROOT / "data" / "current_issue_id.txt"
ISSUES_DIR = ROOT / "issues"


def issue_date():
    if CURRENT_ISSUE.exists():
        issue_id = CURRENT_ISSUE.read_text(encoding="utf-8").strip()
        match = re.match(r"(\d{4}-\d{2}-\d{2})-", issue_id)
        if match:
            return match.group(1)
    return date.today().isoformat()


def is_selected(value: str) -> bool:
    return value.strip().lower() in {"yes", "y", "true", "1", "selected"}


def read_selected_candidates():
    with CANDIDATES.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    selected = [row for row in rows if is_selected(row.get("selected", ""))]
    if len(selected) != 5:
        raise SystemExit(
            f"Expected exactly 5 selected candidates in {CANDIDATES}, found {len(selected)}."
        )
    return selected


def issue_number():
    if not CURRENT_ISSUE.exists():
        return "01"
    issue_id = CURRENT_ISSUE.read_text(encoding="utf-8").strip()
    suffix = issue_id.rsplit("-", 1)[-1]
    return suffix.zfill(2) if suffix.isdigit() else "01"


def format_newsletter_item(index, row):
    title = row["title"].strip()
    summary = row["summary"].strip()
    why = row["why_it_matters"].strip()
    url = row["url"].strip()
    source = row["source"].strip()
    region = "국내" if row["region"].strip().lower() == "korea" else "해외"
    category = row["category"].strip()
    one_liner = row["one_liner"].strip()

    return (
        f"## {index}. {title}\n\n"
        f"- 구분: {region} / {category}\n"
        f"- 요약: {summary}\n"
        f"- 러너에게 중요한 이유: {why}\n"
        f"- 원문: [{source}]({url})\n"
        f"- 한 줄 관점: {one_liner}\n"
    )


def build_editorial_meta(rows, number, korea_count, global_count):
    main = rows[0]
    domestic_events = [row for row in rows if row["region"].strip().lower() == "korea"]
    global_items = [row for row in rows if row["region"].strip().lower() != "korea"]
    event_titles = "·".join(row["title"].split("…", 1)[0] for row in domestic_events[:3])
    global_title = global_items[0]["title"].split("…", 1)[0] if global_items else rows[-1]["title"].split("…", 1)[0]

    email_intro = (
        f"안녕하세요, 러너리입니다. {number}호는 국내 {korea_count}개, 해외 {global_count}개로 구성했습니다. "
        f"{main['title'].split('…', 1)[0]}부터 {global_title}까지, 지금 접수·일정표에 올려둘 만한 소식과 "
        "러닝 판이 어디로 움직이는지 보여주는 변화를 함께 담았습니다."
    )
    issue_focus = (
        "이번 호의 중심은 여름과 가을 레이스 캘린더를 미리 채우는 일입니다. "
        f"{event_titles}처럼 지역·이벤트 성격이 뚜렷한 대회가 이어지고, 해외에서는 마라톤을 독립된 세계선수권으로 키우려는 움직임이 나왔습니다."
    )
    main_editorial = (
        "IRON RUN은 단순한 10km 대회가 아니라 거리 설계부터 다릅니다. 3.8km, 7.87km, 15.38km처럼 낯선 숫자를 앞세워 "
        "완주 경험 자체를 이벤트화하고, 포항 영일대 해변이라는 장소성을 강하게 씁니다. 7월 초 대회라 기록 욕심보다 더위 적응, "
        "출발 전 수분 계획, 완주 후 회복 동선을 먼저 잡는 편이 현실적입니다."
    )
    mid_run_note = (
        "5월 초부터 6월 초까지는 접수 마감이 겹칩니다. 관심 있는 대회는 코스보다 먼저 접수 마감일, 환불 가능일, 출발 시간을 캘린더에 넣어두세요."
    )
    perspective = (
        "이번 호는 ‘어디를 뛸까’와 ‘러닝 시장이 어디로 가나’를 같이 보면 좋습니다. 국내 소식은 참가자의 실제 선택지를 넓히고, "
        "월드애슬레틱스 소식은 마라톤이 독립 콘텐츠로 커지는 흐름을 보여줍니다."
    )
    return {
        "email_intro": email_intro,
        "issue_focus": issue_focus,
        "main_editorial": main_editorial,
        "mid_run_note": mid_run_note,
        "perspective": perspective,
    }


def build_issue(rows):
    today = issue_date()
    number = issue_number()
    newsletter_items = "\n".join(
        format_newsletter_item(index, row) for index, row in enumerate(rows, start=1)
    )
    korea_count = sum(1 for row in rows if row["region"].strip().lower() == "korea")
    global_count = len(rows) - korea_count
    meta = build_editorial_meta(rows, number, korea_count, global_count)

    return f"""# 오늘의 러닝 브리핑 {number} - {today}

발행일: {today}
구성: 국내 {korea_count}개 / 해외 {global_count}개
이메일 인트로: {meta["email_intro"]}
이번 호 중심: {meta["issue_focus"]}
메인 에디토리얼: {meta["main_editorial"]}
미드런 노트: {meta["mid_run_note"]}
이번 호 관점: {meta["perspective"]}

{meta["email_intro"]}

{newsletter_items}
"""


def main():
    rows = read_selected_candidates()
    ISSUES_DIR.mkdir(exist_ok=True)
    output = ISSUES_DIR / f"{issue_date()}-running-newsletter.md"
    output.write_text(build_issue(rows), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
