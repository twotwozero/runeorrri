#!/usr/bin/env python3
import argparse
import subprocess
import sys


def run(command):
    return subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Verify the live newsletter issue, then send it to active subscribers."
    )
    parser.add_argument("--issue-id", default="latest", help="Issue id to send, or latest.")
    args = parser.parse_args()

    try:
        run(["python3", "scripts/verify_live_issue.py", "--issue-id", args.issue_id])
        run([
            "python3",
            "scripts/send_issue_email.py",
            "--recipients",
            "subscribers",
            "--confirm-subscriber-send",
            "--issue-id",
            args.issue_id,
        ])
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error


if __name__ == "__main__":
    sys.exit(main())
