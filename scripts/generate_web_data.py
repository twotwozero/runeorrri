#!/usr/bin/env python3
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ISSUES_DIR = ROOT / "issues"
WEB_DIR = ROOT / "web"
WEB_DATA = WEB_DIR / "src" / "data" / "issues.json"
WEB_ASSETS = WEB_DIR / "public" / "assets" / "issues"


def issue_number_from_title(title):
    match = re.search(r"브리핑\s+(\d+)", title)
    return match.group(1).zfill(2) if match else "01"


def parse_source(value):
    match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", value)
    if not match:
        return {"name": value.strip(), "url": ""}
    return {"name": match.group(1).strip(), "url": match.group(2).strip()}


def clean_intro(text, first_story_start):
    intro = text[:first_story_start].strip()
    intro = re.sub(r"^#\s+.+$", "", intro, flags=re.MULTILINE)
    intro = re.sub(r"^발행일:.*$", "", intro, flags=re.MULTILINE)
    intro = re.sub(r"^구성:.*$", "", intro, flags=re.MULTILINE)
    return intro.strip()


def parse_newsletter(path):
    text = path.read_text(encoding="utf-8")
    issue_date = path.name.split("-running-newsletter.md", 1)[0]
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else f"오늘의 러닝 브리핑 - {issue_date}"
    story_matches = list(re.finditer(r"^##\s+(\d+)\.\s+(.+)$", text, re.MULTILINE))
    intro = clean_intro(text, story_matches[0].start()) if story_matches else ""

    stories = []
    for pos, match in enumerate(story_matches):
        start = match.end()
        end = story_matches[pos + 1].start() if pos + 1 < len(story_matches) else len(text)
        block = text[start:end]
        story = {
            "index": int(match.group(1)),
            "title": match.group(2).strip(),
            "region": "",
            "category": "",
            "summary": "",
            "why": "",
            "source": {"name": "", "url": ""},
            "cardCopy": "",
        }
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("- 구분:"):
                value = line.split(":", 1)[1].strip()
                if "/" in value:
                    story["region"], story["category"] = [part.strip() for part in value.split("/", 1)]
                else:
                    story["region"] = value
            elif line.startswith("- 요약:"):
                story["summary"] = line.split(":", 1)[1].strip()
            elif line.startswith("- 러너에게 중요한 이유:"):
                story["why"] = line.split(":", 1)[1].strip()
            elif line.startswith("- 원문:"):
                story["source"] = parse_source(line.split(":", 1)[1].strip())
            elif line.startswith("- 카드 한 줄:"):
                story["cardCopy"] = line.split(":", 1)[1].strip()
        stories.append(story)

    return {
        "date": issue_date,
        "number": issue_number_from_title(title),
        "title": title,
        "intro": intro,
        "stories": stories,
        "assets": copy_issue_assets(issue_date),
    }


def copy_asset(src, dst, public_path):
    if not src.exists():
        return ""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return public_path


def copy_issue_assets(issue_date):
    art_dir = ISSUES_DIR / f"{issue_date}-art"
    asset_dir = WEB_ASSETS / issue_date
    return {
        "hero": copy_asset(
            art_dir / "hero.png",
            asset_dir / "hero.png",
            f"/assets/issues/{issue_date}/hero.png",
        ),
        "lineup": copy_asset(
            art_dir / "lineup.png",
            asset_dir / "lineup.png",
            f"/assets/issues/{issue_date}/lineup.png",
        ),
        "checkpoints": copy_asset(
            art_dir / "checkpoints.png",
            asset_dir / "checkpoints.png",
            f"/assets/issues/{issue_date}/checkpoints.png",
        ),
    }


def build_web_data():
    issue_files = sorted(ISSUES_DIR.glob("*-running-newsletter.md"), reverse=True)
    issues = [parse_newsletter(path) for path in issue_files]
    WEB_DATA.parent.mkdir(parents=True, exist_ok=True)
    WEB_DATA.write_text(
        json.dumps(issues, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return issues


def main():
    issues = build_web_data()
    print(WEB_DATA)
    for issue in issues:
        print(f"{issue['date']} -> /{issue['number']}")


if __name__ == "__main__":
    main()
