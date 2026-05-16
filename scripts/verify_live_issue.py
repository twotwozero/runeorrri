#!/usr/bin/env python3
import argparse
import csv
import urllib.error
import urllib.request
from pathlib import Path

from utils import issue_number_from_id, load_dotenv, required_env


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "candidates_archive.csv"


def resolve_issue_id(value):
    with ARCHIVE.open(newline="", encoding="utf-8") as f:
        ids = sorted({row["issue_id"] for row in csv.DictReader(f) if row.get("issue_id")})
    if not ids:
        raise SystemExit("No issue_id values found in candidates_archive.csv")
    if value == "latest":
        return ids[-1]
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-id", default="latest")
    args = parser.parse_args()
    issue_id = resolve_issue_id(args.issue_id)
    number = issue_number_from_id(issue_id, default="")
    if not number:
        raise SystemExit(f"Cannot resolve issue number from issue id: {issue_id}")
    load_dotenv(ROOT)
    base_url = required_env("RUNEORRRI_SITE_BASE_URL").rstrip("/")
    url = f"{base_url}/{number}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "runeorrri-live-check/1.0"},
        method="HEAD",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status >= 400:
                raise SystemExit(f"Live check failed: {url} returned {response.status}")
    except urllib.error.HTTPError as error:
        raise SystemExit(f"Live check failed: {url} returned {error.code}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Live check failed: {url} ({error.reason})") from error

    print(f"Live issue verified: {url}")


if __name__ == "__main__":
    main()
