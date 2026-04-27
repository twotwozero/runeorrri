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
    card_copy = row["card_copy"].strip()

    return (
        f"## {index}. {title}\n\n"
        f"- 구분: {region} / {category}\n"
        f"- 요약: {summary}\n"
        f"- 러너에게 중요한 이유: {why}\n"
        f"- 원문: [{source}]({url})\n"
        f"- 카드 한 줄: {card_copy}\n"
    )


def format_instagram_card(index, row):
    return (
        f"### 카드 {index}\n\n"
        f"{row['title'].strip()}\n\n"
        f"{row['card_copy'].strip()}\n\n"
        f"{row['why_it_matters'].strip()}\n"
    )


def build_issue(rows):
    today = issue_date()
    number = issue_number()
    newsletter_items = "\n".join(
        format_newsletter_item(index, row) for index, row in enumerate(rows, start=1)
    )
    korea_count = sum(1 for row in rows if row["region"].strip().lower() == "korea")
    global_count = len(rows) - korea_count

    return f"""# 오늘의 러닝 브리핑 {number} - {today}

발행일: {today}
구성: 국내 {korea_count}개 / 해외 {global_count}개

러너리가 국내 러닝 소식 {korea_count}개와 해외 소식 {global_count}개를 골랐습니다. 바쁜 러너가 빠르게 훑고, 필요한 링크만 바로 열어볼 수 있게 정리했습니다.

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
