#!/usr/bin/env python3
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECIPIENT = "lhh4682@naver.com"
INTERVAL_SECONDS = 60
SEND_COUNT = 3


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    run(["python3", "scripts/generate_issue.py"])
    run([
        "/Users/heehyeong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
        "scripts/generate_cardnews_png.py",
    ])
    run(["python3", "scripts/generate_cardnews_album.py"])
    run([
        "/Users/heehyeong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
        "scripts/generate_newsletter_art.py",
    ])

    for index in range(1, SEND_COUNT + 1):
        print(f"Sending test email {index}/{SEND_COUNT} to {RECIPIENT}")
        run(["python3", "scripts/send_issue_email.py"])
        if index < SEND_COUNT:
            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
