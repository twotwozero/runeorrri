#!/usr/bin/env python3
import argparse
import csv
import os
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "candidates_archive.csv"
TODAY = date.today().isoformat()


def run(command):
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def can_import_pillow(python_bin):
    return subprocess.run(
        [python_bin, "-c", "import PIL"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def python_with_pillow():
    if can_import_pillow(sys.executable):
        return sys.executable

    candidates = [
        os.environ.get("RUNNERI_PYTHON"),
        "/Users/heehyeong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists() and can_import_pillow(candidate):
            return candidate

    venv_dir = ROOT / ".venv"
    python_bin = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python_bin.exists():
        run([sys.executable, "-m", "venv", str(venv_dir)])
    run([str(python_bin), "-m", "pip", "install", "Pillow"])
    return str(python_bin)


def archive_rows():
    if not ARCHIVE.exists():
        raise SystemExit(f"Missing candidate archive: {ARCHIVE}")
    with ARCHIVE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def resolve_issue_id(value):
    rows = archive_rows()
    issue_ids = sorted({row["issue_id"] for row in rows if row.get("issue_id")})
    if value == "latest":
        if not issue_ids:
            raise SystemExit("No issue_id values found in candidates_archive.csv")
        return issue_ids[-1]
    if value == "today":
        todays = sorted({row["issue_id"] for row in rows if row.get("issue_date") == TODAY})
        if not todays:
            raise SystemExit(
                f"No candidates for today's issue_date ({TODAY}). "
                "Add reviewed rows to data/candidates_archive.csv first."
            )
        return todays[-1]
    return value


def main():
    parser = argparse.ArgumentParser(description="Build and optionally send one runeorrri newsletter issue.")
    parser.add_argument(
        "--issue-id",
        default="today",
        help="Issue id to build from candidates_archive.csv, or one of: today, latest.",
    )
    parser.add_argument("--send-email", action="store_true", help="Send the newsletter via SMTP after generation.")
    parser.add_argument("--no-email", action="store_true", help="Generate files only. This is the default.")
    args = parser.parse_args()

    issue_id = resolve_issue_id(args.issue_id)
    run([sys.executable, "scripts/validate_candidate_pool.py", issue_id, "--mode", "publish"])

    run([sys.executable, "scripts/generate_issue.py", "--issue-id", issue_id])
    art_python = python_with_pillow()
    run([art_python, "scripts/generate_newsletter_art.py", "--issue-id", issue_id])
    run([sys.executable, "scripts/generate_web_data.py"])

    if args.send_email and not args.no_email:
        run([sys.executable, "scripts/send_issue_email.py", "--recipients", "test", "--issue-id", issue_id])
    else:
        print("Email skipped. Pass --send-email to send via SMTP.")


if __name__ == "__main__":
    main()
