#!/usr/bin/env python3
import urllib.error
import urllib.request
from pathlib import Path

from utils import issue_number_from_id, load_dotenv, read_current_issue_id, required_env


ROOT = Path(__file__).resolve().parents[1]
CURRENT_ISSUE = ROOT / "data" / "current_issue_id.txt"


def issue_number():
    issue_id = read_current_issue_id(CURRENT_ISSUE)
    if not issue_id:
        raise SystemExit(f"Missing current issue file: {CURRENT_ISSUE}")
    number = issue_number_from_id(issue_id, default="")
    if not number:
        raise SystemExit(f"Cannot resolve issue number from current issue id: {issue_id}")
    return number


def main():
    load_dotenv(ROOT)
    base_url = required_env("RUNEORRRI_SITE_BASE_URL").rstrip("/")
    url = f"{base_url}/{issue_number()}"
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
