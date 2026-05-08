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


def topic_particle(text):
    for char in reversed(text.strip()):
        if "가" <= char <= "힣":
            return "은" if (ord(char) - ord("가")) % 28 else "는"
        if char.isalnum():
            return "은"
    return "는"


def category_label(value):
    labels = {
        "event": "이벤트",
        "race": "레이스",
        "news": "뉴스",
        "gear": "장비",
        "elite": "엘리트",
        "training": "훈련",
    }
    category = value.strip().lower()
    return labels.get(category, value.strip())


def format_newsletter_item(index, row):
    title = row["title"].strip()
    summary = row["summary"].strip()
    why = row["why_it_matters"].strip()
    url = row["url"].strip()
    source = row["source"].strip()
    region = "국내" if row["region"].strip().lower() == "korea" else "해외"
    category = category_label(row["category"])
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
    main_title = main["title"].split("…", 1)[0]
    main_subject = f"{main_title}{topic_particle(main_title)}"
    main_category = main["category"].strip().lower()
    titles = " ".join(row["title"] for row in rows)
    categories = {row["category"].strip().lower() for row in rows}

    email_intro = (
        f"안녕하세요, 러너리입니다. {number}호는 국내 {korea_count}개, 해외 {global_count}개로 구성했습니다. "
        f"{main_title}부터 {global_title}까지, 지금 접수·일정표에 올려둘 만한 소식과 "
        "러닝 판이 어디로 움직이는지 보여주는 변화를 함께 담았습니다."
    )
    if domestic_events and global_items:
        issue_focus = (
            "이번 호의 중심은 국내 러너가 바로 확인할 수 있는 선택지와 해외 러닝 흐름을 함께 보는 일입니다. "
            f"{event_titles}처럼 참가 여부를 판단할 수 있는 소식과 {global_title} 같은 흐름형 소식을 함께 묶었습니다."
        )
    elif domestic_events:
        issue_focus = (
            "이번 호의 중심은 국내 레이스 캘린더를 정리하는 일입니다. "
            f"{event_titles}처럼 참가 여부를 판단할 수 있는 소식을 우선했습니다."
        )
    else:
        issue_focus = (
            "이번 호의 중심은 해외 러닝 흐름을 국내 러너의 훈련, 장비, 참가 선택과 연결해 보는 일입니다."
        )
    if main_category == "event":
        main_editorial = (
            f"{main_subject} 일정 정보만 보고 넘기기보다 대회 성격을 같이 봐야 합니다. "
            f"{main['summary'].strip()} "
            f"{main['why_it_matters'].strip()} 참가 여부를 정할 때는 접수 마감, 출발 시간, 이동 동선, 환불 조건을 먼저 확인하세요."
        )
        mid_run_note = (
            "대회 소식은 코스보다 마감일이 먼저입니다. 관심 있는 대회는 접수 마감일, 환불 가능일, 출발 시간을 캘린더에 넣어두세요."
        )
    elif main_category == "gear":
        main_editorial = (
            f"{main_subject} 새 제품 소식이지만 구매 판단은 광고 문구보다 용도에서 시작해야 합니다. "
            f"{main['summary'].strip()} {main['why_it_matters'].strip()} 지금 신는 신발의 역할과 겹치는지 먼저 비교하세요."
        )
        mid_run_note = "장비 소식은 출시일보다 내 훈련에서 맡길 역할이 더 중요합니다. 레이스용, 조깅용, 회복주용을 구분해서 보세요."
    else:
        main_editorial = (
            f"{main_subject} 러너가 당장 참가하거나 구매하는 정보는 아니어도 흐름을 읽는 데 의미가 있습니다. "
            f"{main['summary'].strip()} {main['why_it_matters'].strip()}"
        )
        mid_run_note = "해외 소식은 기록 자체보다 국내 러너의 훈련, 장비, 참가 선택에 어떤 영향을 주는지까지 같이 보면 더 유용합니다."
    if "63RUN" in titles or "월드런" in titles:
        mid_run_note = (
            "계단 오르기, 캐처카 방식, 여행형 레이스처럼 운영 방식이 제각각입니다. 거리보다 출발 방식과 현장 동선을 먼저 확인하세요."
        )
        perspective = (
            "이번 호는 러닝 이벤트가 얼마나 다양한 형태로 넓어지는지를 보여줍니다. 기록형 로드 레이스만 보지 말고, "
            "내가 원하는 자극이 체험, 기부, 여행, 기록 중 어디에 가까운지 기준을 세워보세요."
        )
    elif "KB 마라톤 카드" in titles or "Gel-Kayano" in titles:
        mid_run_note = (
            "참가권 이벤트와 장비 소식은 조건을 잘게 읽어야 합니다. 응모 조건, 당첨 안내일, 출시일, 가격처럼 "
            "실제로 행동을 바꾸는 숫자만 따로 적어두세요."
        )
        perspective = (
            "이번 호는 달릴 대회를 고르는 문제와 러닝 주변의 선택지를 함께 다룹니다. 접수권을 얻는 방법, 공식 양도 채널, "
            "안정화 러닝화 흐름처럼 레이스 밖의 결정도 러너의 시즌 계획에 영향을 줍니다."
        )
    elif "training" in categories:
        mid_run_note = (
            "접수 일정과 몸 관리가 같이 걸려 있습니다. 대회 캘린더를 채울 때 장거리주, 회복식, "
            "컨디션 저하 신호를 같은 주간 계획 안에 넣어두세요."
        )
        perspective = (
            "이번 호는 ‘어디에 신청할까’에서 한 걸음 더 나아가 ‘무사히 준비할 수 있을까’를 같이 묻습니다. "
            "국내 대회 후보는 일정표에 올리고, 해외 소식은 안전한 양도와 충분한 에너지 섭취라는 운영 원칙으로 읽으면 좋습니다."
        )
    else:
        perspective = (
            "이번 호는 ‘지금 내가 무엇을 결정할 수 있나’를 기준으로 읽으면 좋습니다. 참가형 소식은 일정과 조건을 확인하고, "
            "흐름형 소식은 내 훈련·장비·대회 선택에 어떤 영향을 줄지 보는 식입니다."
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
