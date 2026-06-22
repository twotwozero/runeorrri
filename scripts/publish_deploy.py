#!/usr/bin/env python3
import argparse
import subprocess
import sys


def run(command):
    return subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Generate, build, deploy, and verify a newsletter issue."
    )
    parser.add_argument("--issue-id", default="latest", help="Issue id to publish, or latest.")
    args = parser.parse_args()

    try:
        run(["python3", "scripts/run_newsletter_pipeline.py", "--issue-id", args.issue_id])
        run(["npm", "run", "build"])
        run(["npm", "run", "deploy"])
        run(["npm", "run", "verify:live", "--", "--issue-id", args.issue_id])
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error


if __name__ == "__main__":
    sys.exit(main())
