#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time


WORKFLOW = "send-newsletter.yml"


def run(command, *, capture=False):
    kwargs = {
        "check": True,
        "text": True,
    }
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    return subprocess.run(command, **kwargs)


def output(command):
    return run(command, capture=True).stdout.strip()


def ensure_clean_worktree():
    status = output(["git", "status", "--porcelain"])
    if status:
        raise SystemExit(
            "Refusing to publish with uncommitted changes. Commit and push first, then run publish again."
        )


def ensure_branch_pushed():
    branch = output(["git", "branch", "--show-current"])
    upstream = output(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    local_sha = output(["git", "rev-parse", "HEAD"])
    upstream_sha = output(["git", "rev-parse", upstream])
    if local_sha != upstream_sha:
        raise SystemExit(
            f"Refusing to publish because {branch} is not pushed to {upstream}. Run git push first."
        )


def latest_run_id_for_current_sha():
    branch = output(["git", "branch", "--show-current"])
    local_sha = output(["git", "rev-parse", "HEAD"])
    for _ in range(10):
        run_id = output([
            "gh",
            "run",
            "list",
            "--workflow",
            WORKFLOW,
            "--branch",
            branch,
            "--limit",
            "10",
            "--json",
            "databaseId,headSha",
            "--jq",
            f'.[] | select(.headSha == "{local_sha}") | .databaseId',
        ]).splitlines()
        if run_id:
            return run_id[0]
        time.sleep(2)
    raise SystemExit("Workflow was triggered, but its run id was not found. Check GitHub Actions.")


def trigger_workflow(issue_id, watch):
    run([
        "gh",
        "workflow",
        "run",
        WORKFLOW,
        "-f",
        "confirm_subscriber_send=true",
        "-f",
        f"issue_id={issue_id}",
    ])
    run_id = latest_run_id_for_current_sha()
    print(f"Triggered {WORKFLOW}: https://github.com/twotwozero/runeorrri/actions/runs/{run_id}")
    if watch:
        run(["gh", "run", "watch", run_id, "--exit-status"])


def main():
    parser = argparse.ArgumentParser(
        description="Publish the newsletter through GitHub Actions so D1 subscriber access uses repository secrets."
    )
    parser.add_argument("--issue-id", default="latest", help="Issue id to publish, or latest.")
    parser.add_argument(
        "--confirm-subscriber-send",
        action="store_true",
        help="Required to trigger the subscriber-send workflow.",
    )
    parser.add_argument("--no-watch", action="store_true", help="Trigger the workflow without waiting for completion.")
    args = parser.parse_args()

    if not args.confirm_subscriber_send:
        raise SystemExit("Refusing subscriber publish without --confirm-subscriber-send.")

    try:
        ensure_clean_worktree()
        ensure_branch_pushed()
        trigger_workflow(args.issue_id, watch=not args.no_watch)
    except subprocess.CalledProcessError as error:
        if error.stdout:
            sys.stderr.write(error.stdout)
        if error.stderr:
            sys.stderr.write(error.stderr)
        raise SystemExit(error.returncode)


if __name__ == "__main__":
    main()
