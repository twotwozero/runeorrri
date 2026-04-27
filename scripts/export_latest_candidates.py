#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "candidates_archive.csv"
CANDIDATES = ROOT / "data" / "candidates.csv"
CURRENT_ISSUE = ROOT / "data" / "current_issue_id.txt"
ARCHIVE_FIELDS = [
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
    "published_at",
    "one_liner",
    "verification_status",
    "notes",
]
CANDIDATE_FIELDS = [field for field in ARCHIVE_FIELDS if field not in {"issue_id", "issue_date"}]


def read_archive():
    with ARCHIVE.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"No archived candidates found in {ARCHIVE}")
    return rows


def latest_issue_id(rows):
    return sorted({row["issue_id"] for row in rows})[-1]


REGION_ORDER = {"korea": 0, "global": 1}
CATEGORY_ORDER = {"event": 0, "gear": 1, "elite": 2, "news": 3}


def story_sort_key(row):
    return (
        REGION_ORDER.get(row.get("region", ""), 9),
        CATEGORY_ORDER.get(row.get("category", ""), 9),
    )


def main():
    rows = read_archive()
    issue_id = sys.argv[1] if len(sys.argv) > 1 else latest_issue_id(rows)
    latest = [row for row in rows if row["issue_id"] == issue_id]
    if not latest:
        raise SystemExit(f"No candidates found for issue_id: {issue_id}")
    selected = sorted([r for r in latest if r.get("selected") == "yes"], key=story_sort_key)
    not_selected = [r for r in latest if r.get("selected") != "yes"]
    sorted_latest = selected + not_selected
    with CANDIDATES.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        for row in sorted_latest:
            writer.writerow({field: row.get(field, "") for field in CANDIDATE_FIELDS})
    CURRENT_ISSUE.write_text(f"{issue_id}\n", encoding="utf-8")
    print(f"Exported {len(latest)} candidates from {issue_id} to {CANDIDATES}")


if __name__ == "__main__":
    main()
