#!/usr/bin/env python3
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT_ISSUE = ROOT / "data" / "current_issue_id.txt"


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
        raise SystemExit(f"Missing current issue file: {CURRENT_ISSUE}")
    issue_id = CURRENT_ISSUE.read_text(encoding="utf-8").strip()
    suffix = issue_id.rsplit("-", 1)[-1]
    if not re.fullmatch(r"\d+", suffix):
        raise SystemExit(f"Cannot resolve issue number from current issue id: {issue_id}")
    return suffix.zfill(2)


def main():
    load_dotenv()
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
