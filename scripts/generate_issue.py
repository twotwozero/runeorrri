#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

from utils import category_label, clean_text, is_selected, issue_date_from_id
from utils import issue_number_from_id, korean_today, story_sort_key


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "candidates_archive.csv"
ISSUES_DIR = ROOT / "issues"


def resolve_issue_id(value):
    with ARCHIVE.open(newline="", encoding="utf-8") as f:
        ids = sorted({row["issue_id"] for row in csv.DictReader(f) if row.get("issue_id")})
    if not ids:
        raise SystemExit("No issue_id values found in candidates_archive.csv")
    if value == "latest":
        return ids[-1]
    return value


def read_selected_candidates(issue_id):
    with ARCHIVE.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    issue_rows = [row for row in rows if row.get("issue_id") == issue_id]
    if not issue_rows:
        raise SystemExit(f"No candidates found for issue_id: {issue_id}")
    selected = sorted(
        [row for row in issue_rows if is_selected(row.get("selected", ""))],
        key=story_sort_key,
    )
    if len(selected) != 5:
        raise SystemExit(f"Expected exactly 5 selected candidates for {issue_id}, found {len(selected)}.")
    return selected


def issue_date(issue_id):
    return issue_date_from_id(issue_id) or korean_today()


def issue_number(issue_id):
    return issue_number_from_id(issue_id)


def topic_particle(text):
    for char in reversed(text.strip()):
        if "가" <= char <= "힣":
            return "은" if (ord(char) - ord("가")) % 28 else "는"
        if char.isalnum():
            return "은"
    return "는"


def format_newsletter_item(index, row):
    title = clean_text(row["title"].strip())
    summary = clean_text(row["summary"].strip())
    why = clean_text(row["why_it_matters"].strip())
    url = row["url"].strip()
    source = clean_text(row["source"].strip())
    region = "국내" if row["region"].strip().lower() == "korea" else "해외"
    category = category_label(row["category"])
    one_liner = clean_text(row["one_liner"].strip())

    return (
        f"## {index}. {title}\n\n"
        f"- 구분: {region} / {category}\n"
        f"- 요약: {summary}\n"
        f"- 러너에게 중요한 이유: {why}\n"
        f"- 원문: [{source}]({url})\n"
        f"- 한 줄 관점: {one_liner}\n"
    )


def build_issue_focus(rows, has_trail, has_gear, has_training):
    domestic_events = [row for row in rows if row["region"].strip().lower() == "korea"]
    global_items = [row for row in rows if row["region"].strip().lower() != "korea"]
    text = " ".join(
        " ".join(
            [
                row.get("title", ""),
                row.get("summary", ""),
                row.get("why_it_matters", ""),
                row.get("one_liner", ""),
            ]
        )
        for row in rows
    )
    has_deadline = "마감" in text or "접수" in text
    has_cancellation = "취소" in text

    if domestic_events and global_items and has_cancellation:
        return (
            "이번 호는 '어디에 신청할까'보다 '무엇을 먼저 확인할까'에 가깝습니다. "
            "마감이 가까운 대회는 일정과 이동 동선을 바로 정해야 하고, 취소 표기가 엇갈리는 이벤트는 공식 공지와 환불 안내를 먼저 확인해야 합니다. "
            "해외 소식은 신발과 훈련 빈도를 내 시즌 계획에 맞춰 다시 나누는 참고 자료로 읽으면 좋습니다."
        )
    if has_trail and has_gear:
        return (
            "이번 호는 6월 레이스를 한 줄 캘린더로 보지 않고 준비 방식별로 나눠 보는 호입니다. "
            "도로 대회는 접수 마감과 이동 동선이 먼저이고, 트레일 일정은 노면과 전날 준비 시간이 핵심입니다. "
            "장비 소식은 새 제품 이름보다 내 훈련화가 맡을 역할을 정하는 데 쓰면 좋습니다."
        )
    if has_training and domestic_events:
        return (
            "이번 호는 대회 캘린더와 훈련 계획을 따로 보지 않는 데 초점을 맞췄습니다. "
            "참가 후보를 고를 때는 마감일과 출발 시간만 볼 게 아니라, 그 일정을 무리 없이 준비할 수 있는 주간 훈련 구조까지 같이 봐야 합니다."
        )
    if domestic_events and global_items and has_deadline:
        return (
            "이번 호는 이번 주 안에 결정해야 할 국내 일정과 해외 러닝 흐름을 함께 묶었습니다. "
            "국내 소식은 접수 마감, 출발 시간, 현장 동선을 확인하는 데 쓰고, 해외 소식은 훈련과 장비 선택의 기준을 점검하는 데 쓰면 좋습니다."
        )
    if domestic_events and global_items:
        return (
            "이번 호는 국내 참가형 소식과 해외 흐름형 소식을 나눠 읽으면 좋습니다. "
            "하나는 일정표와 현장 준비에 바로 반영할 정보이고, 다른 하나는 다음 훈련과 장비 선택에 참고할 배경입니다."
        )
    if domestic_events:
        return (
            "이번 호의 중심은 국내 레이스 캘린더를 실제 참가 기준으로 정리하는 일입니다. "
            "날짜만 보지 말고 접수 상태, 이동 동선, 출발 시간, 더위 대비까지 같이 확인하세요."
        )
    if "gear" in {row["category"].strip().lower() for row in rows}:
        return (
            "이번 호는 해외 장비 흐름을 국내 러너의 구매 판단으로 번역해 보는 호입니다. "
            "새 제품 이름보다 내 훈련에서 필요한 역할, 내구성, 가격 대비 활용 빈도를 먼저 보세요."
        )
    return (
        "이번 호는 해외 러닝 흐름을 국내 러너의 훈련, 장비, 참가 선택과 연결해 보는 일에 초점을 맞췄습니다. "
        "기록이나 제품명 자체보다 내 다음 선택에 어떤 영향을 줄지 기준을 세워 읽으면 좋습니다."
    )


def build_editorial_meta(rows, number, korea_count, global_count):
    main = rows[0]
    global_items = [row for row in rows if row["region"].strip().lower() != "korea"]
    global_title = clean_text(global_items[0]["title"].split("…", 1)[0] if global_items else rows[-1]["title"].split("…", 1)[0])
    main_title = clean_text(main["title"].split("…", 1)[0])
    main_subject = f"{main_title}{topic_particle(main_title)}"
    main_category = main["category"].strip().lower()
    titles = clean_text(" ".join(row["title"] for row in rows))
    categories = {row["category"].strip().lower() for row in rows}
    has_trail = any(
        keyword in titles for keyword in ["50K", "트레일", "Skyrace", "TNF"]
    )
    has_gear = "gear" in categories
    has_training = "training" in categories

    email_intro = (
        f"안녕하세요, 러너리입니다. {number}호는 국내 {korea_count}개, 해외 {global_count}개로 구성했습니다. "
        f"이번 호에서는 {main_title} 같은 접수 소식과 {global_title} 같은 해외 흐름을 함께 봅니다. "
        "바로 일정표에 올릴 정보와 다음 훈련, 장비 선택에 참고할 기준을 나눠 담았습니다."
    )
    issue_focus = build_issue_focus(rows, has_trail, has_gear, has_training)
    if main_category == "event":
        main_editorial = (
            f"{main_title} 소식을 이번 호의 첫머리에 둔 이유는 실제 참가 결정에 필요한 변수가 한 번에 걸려 있기 때문입니다. "
            "날짜와 모집 정보는 본문 요약에서 확인하고, 여기서는 선택 기준만 잡겠습니다. "
            "접수 시작 시간, 마감일, 선착순 여부를 한 표에 놓고 보면 핵심은 '갈 수 있나'보다 '마감 전에 확정할 수 있나'입니다. "
            "접수 전에는 계정 로그인, 결제수단, 교통편, 동반자 일정을 먼저 고정하세요."
        )
        if has_trail:
            mid_run_note = (
                "로드와 트레일 일정이 같이 있을 때는 출발일보다 전날 준비 시간을 먼저 보세요. "
                "장비검사, 숙박, 이동 시간을 빼고 나면 실제로 선택 가능한 대회가 줄어듭니다."
            )
        else:
            mid_run_note = (
                "대회 소식은 코스보다 마감일이 먼저입니다. 관심 있는 대회는 접수 마감일, 환불 가능일, 출발 시간을 캘린더에 넣어두세요."
            )
    elif main_category == "gear":
        main_editorial = (
            f"{main_subject} 새 제품 소식이지만 구매 판단은 광고 문구보다 용도에서 시작해야 합니다. "
            "본문 요약은 업데이트 내용을 정리하고, 에디토리얼에서는 구매 기준만 남깁니다. "
            "지금 신는 신발의 역할과 겹치는지, 레이스용인지 데일리용인지, 내 주간 거리에서 내구성이 충분한지를 먼저 비교하세요."
        )
        mid_run_note = "장비 소식은 출시일보다 내 훈련에서 맡길 역할이 더 중요합니다. 레이스용, 조깅용, 회복주용을 구분해서 보세요."
    else:
        main_editorial = (
            f"{main_subject} 러너가 당장 참가하거나 구매하는 정보는 아니어도 흐름을 읽는 데 의미가 있습니다. "
            "본문 요약은 사실 관계를 맡기고, 에디토리얼은 해석에 집중합니다. "
            "이 변화가 내 훈련 계획, 장비 선택, 다음 대회 결정 중 어디에 영향을 주는지만 분리해 보면 충분합니다."
        )
        mid_run_note = "해외 소식은 기록 자체보다 국내 러너의 훈련, 장비, 참가 선택에 어떤 영향을 주는지까지 같이 보면 더 유용합니다."
    if has_trail and has_gear:
        mid_run_note = (
            "로드와 트레일 일정이 같이 있을 때는 출발일보다 전날 준비 시간을 먼저 보세요. "
            "장비검사, 숙박, 이동 시간을 빼고 나면 실제로 선택 가능한 대회가 줄어듭니다."
        )
        perspective = (
            "이번 호는 6월 초중순 레이스를 같은 목록으로 보되 준비 난도를 다르게 읽으면 좋습니다. "
            "도로 대회는 접수와 이동을, 트레일 대회는 전날 체크인과 장비를, 장비 소식은 내 훈련화 역할을 기준으로 나눠 보세요."
        )
    elif "63RUN" in titles or "월드런" in titles:
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
            "국내 대회 후보는 접수창과 이동 동선으로 나누고, 해외 소식은 장비 역할과 피로 관리 기준으로 읽으면 좋습니다."
        )
    else:
        perspective = (
            "이번 호는 ‘지금 내가 무엇을 결정할 수 있나’를 기준으로 읽으면 좋습니다. 참가형 소식은 일정과 조건을 확인하고, "
            "흐름형 소식은 내 훈련, 장비, 대회 선택에 어떤 영향을 줄지 보는 식입니다."
        )
    return {
        "email_intro": clean_text(email_intro),
        "issue_focus": clean_text(issue_focus),
        "main_editorial": clean_text(main_editorial),
        "mid_run_note": clean_text(mid_run_note),
        "perspective": clean_text(perspective),
    }


def build_issue(rows, issue_id):
    today = issue_date(issue_id)
    number = issue_number(issue_id)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-id", default="latest")
    args = parser.parse_args()
    issue_id = resolve_issue_id(args.issue_id)
    rows = read_selected_candidates(issue_id)
    ISSUES_DIR.mkdir(exist_ok=True)
    output = ISSUES_DIR / f"{issue_date(issue_id)}-running-newsletter.md"
    output.write_text(build_issue(rows, issue_id), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
