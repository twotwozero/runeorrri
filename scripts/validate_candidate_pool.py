#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "candidates_archive.csv"
CURRENT_ISSUE = ROOT / "data" / "current_issue_id.txt"

REQUIRED_FIELDS = [
    "issue_id",
    "issue_date",
    "selected",
    "region",
    "category",
    "title",
    "summary",
    "why_it_matters",
    "url",
    "source",
    "one_liner",
    "verification_status",
]

GENERIC_TOKENS = {
    "2026",
    "마라톤",
    "러닝",
    "대회",
    "개최",
    "접수",
    "공식",
    "모집",
    "선착순",
    "서울",
    "국내",
    "해외",
    "월",
    "일까지",
    "까지",
}


def read_archive():
    with ARCHIVE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def resolve_issue_id(value, rows):
    if value == "current":
        return CURRENT_ISSUE.read_text(encoding="utf-8").strip()
    if value == "latest":
        return sorted({row["issue_id"] for row in rows if row.get("issue_id")})[-1]
    return value


def is_selected(row):
    return row.get("selected", "").strip().lower() in {"yes", "y", "true", "1", "selected"}


def normalize(text):
    return re.sub(r"[^0-9a-z가-힣]+", "", text.lower())


def tokens(text):
    parts = re.split(r"[^0-9a-zA-Z가-힣]+", text.lower())
    return {part for part in parts if len(part) >= 2 and part not in GENERIC_TOKENS}


def validate_required(rows, errors):
    for index, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if not row.get(field, "").strip():
                errors.append(f"row {index}: missing {field}")
        status = row.get("verification_status", "").strip().lower()
        if status != "reviewed":
            errors.append(f"row {index}: verification_status must be reviewed, got {status or '(empty)'}")


def validate_pool_size(rows, expected, errors):
    if expected is not None and len(rows) != expected:
        errors.append(f"expected exactly {expected} candidates, found {len(rows)}")


def validate_selection(rows, selected_count, errors):
    if selected_count is None:
        return
    selected = [row for row in rows if is_selected(row)]
    if len(selected) != selected_count:
        errors.append(f"expected exactly {selected_count} selected candidates, found {len(selected)}")


def validate_internal_duplicates(rows, errors):
    seen_urls = {}
    seen_titles = {}
    for index, row in enumerate(rows, start=1):
        url = row.get("url", "").strip()
        title_key = normalize(row.get("title", ""))
        if url in seen_urls:
            errors.append(f"row {index}: duplicate URL with row {seen_urls[url]}: {url}")
        seen_urls[url] = index
        if title_key in seen_titles:
            errors.append(f"row {index}: duplicate title with row {seen_titles[title_key]}: {row.get('title')}")
        seen_titles[title_key] = index


def validate_archive_overlap(issue_id, current_rows, archive_rows, errors):
    published = [
        row
        for row in archive_rows
        if row.get("issue_id") != issue_id and is_selected(row)
    ]
    for index, row in enumerate(current_rows, start=1):
        current_title = row.get("title", "")
        current_key = normalize(current_title)
        current_tokens = tokens(current_title)
        current_url = row.get("url", "").strip()
        for previous in published:
            previous_title = previous.get("title", "")
            previous_key = normalize(previous_title)
            previous_tokens = tokens(previous_title)
            if current_url and current_url == previous.get("url", "").strip():
                errors.append(
                    f"row {index}: URL already published in {previous.get('issue_id')}: {current_url}"
                )
                continue
            if current_key and previous_key and (current_key == previous_key or current_key in previous_key or previous_key in current_key):
                errors.append(
                    f"row {index}: title overlaps with {previous.get('issue_id')}: {previous_title}"
                )
                continue
            shared = current_tokens & previous_tokens
            strong_shared = {token for token in shared if len(token) >= 3}
            if len(strong_shared) >= 2:
                errors.append(
                    f"row {index}: possible topic overlap with {previous.get('issue_id')} "
                    f"({', '.join(sorted(strong_shared))}): {previous_title}"
                )


def main():
    parser = argparse.ArgumentParser(description="Validate newsletter candidate pool and overlap rules.")
    parser.add_argument("issue_id", nargs="?", default="current")
    parser.add_argument(
        "--mode",
        choices=["collect", "publish"],
        default="publish",
        help="collect validates a 10-item reviewed pool; publish validates the approved 5 selected rows.",
    )
    parser.add_argument("--pool-size", type=int, default=None)
    args = parser.parse_args()

    archive_rows = read_archive()
    issue_id = resolve_issue_id(args.issue_id, archive_rows)
    current_rows = [row for row in archive_rows if row.get("issue_id") == issue_id]
    if not current_rows:
        raise SystemExit(f"No candidates found for issue_id: {issue_id}")

    errors = []
    expected_pool_size = args.pool_size
    selected_count = 5
    rows_to_check_for_overlap = [row for row in current_rows if is_selected(row)]
    if args.mode == "collect":
        expected_pool_size = 10 if expected_pool_size is None else expected_pool_size
        selected_count = None
        rows_to_check_for_overlap = current_rows

    validate_pool_size(current_rows, expected_pool_size, errors)
    validate_required(current_rows, errors)
    validate_selection(current_rows, selected_count, errors)
    validate_internal_duplicates(current_rows, errors)
    validate_archive_overlap(issue_id, rows_to_check_for_overlap, archive_rows, errors)

    if errors:
        detail = "\n".join(f"- {error}" for error in errors)
        raise SystemExit(f"Candidate pool validation failed for {issue_id}:\n{detail}")

    selected = sum(1 for row in current_rows if is_selected(row))
    print(f"Validated {len(current_rows)} candidates for {issue_id} ({selected} selected).")


if __name__ == "__main__":
    main()
