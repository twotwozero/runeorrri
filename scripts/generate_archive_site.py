#!/usr/bin/env python3
import re
import shutil
from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ISSUES_DIR = ROOT / "issues"
SITE_DIR = ROOT / "site"
SITE_ISSUES_DIR = SITE_DIR / "issues"
SITE_ASSETS_DIR = SITE_DIR / "assets"


@dataclass
class Story:
    index: int
    title: str
    region: str = ""
    category: str = ""
    summary: str = ""
    why: str = ""
    source: str = ""
    url: str = ""


@dataclass
class Issue:
    date: str
    number: str
    title: str
    intro: str
    stories: list[Story]
    hero: str = ""
    lineup: str = ""
    checkpoints: str = ""
    card_album: str = ""


def issue_number_from_title(title):
    match = re.search(r"브리핑\s+(\d+)", title)
    return match.group(1).zfill(2) if match else "01"


def parse_source(value):
    match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", value)
    if not match:
        return value.strip(), ""
    return match.group(1).strip(), match.group(2).strip()


def parse_newsletter(path):
    text = path.read_text(encoding="utf-8")
    date_text = path.name.split("-running-newsletter.md", 1)[0]
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else f"오늘의 러닝 브리핑 - {date_text}"
    number = issue_number_from_title(title)

    intro_start = text.find("\n\n")
    first_story = re.search(r"^##\s+\d+\.", text, re.MULTILINE)
    intro = ""
    if intro_start != -1 and first_story:
        intro = text[intro_start:first_story.start()].strip()
        intro = re.sub(r"^발행일:.*$", "", intro, flags=re.MULTILINE)
        intro = re.sub(r"^구성:.*$", "", intro, flags=re.MULTILINE).strip()

    stories = []
    story_matches = list(re.finditer(r"^##\s+(\d+)\.\s+(.+)$", text, re.MULTILINE))
    for pos, match in enumerate(story_matches):
        start = match.end()
        end = story_matches[pos + 1].start() if pos + 1 < len(story_matches) else len(text)
        block = text[start:end]
        story = Story(index=int(match.group(1)), title=match.group(2).strip())
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("- 구분:"):
                value = line.split(":", 1)[1].strip()
                if "/" in value:
                    story.region, story.category = [part.strip() for part in value.split("/", 1)]
                else:
                    story.region = value
            elif line.startswith("- 요약:"):
                story.summary = line.split(":", 1)[1].strip()
            elif line.startswith("- 러너에게 중요한 이유:"):
                story.why = line.split(":", 1)[1].strip()
            elif line.startswith("- 원문:"):
                story.source, story.url = parse_source(line.split(":", 1)[1].strip())
        stories.append(story)

    issue = Issue(date=date_text, number=number, title=title, intro=intro, stories=stories)
    attach_assets(issue)
    return issue


def copy_if_exists(src, dst):
    if not src.exists():
        return ""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return str(dst.relative_to(SITE_DIR))


def attach_assets(issue):
    art_dir = ISSUES_DIR / f"{issue.date}-art"
    asset_dir = SITE_ASSETS_DIR / issue.date
    issue.hero = copy_if_exists(art_dir / "hero.png", asset_dir / "hero.png")
    issue.lineup = copy_if_exists(art_dir / "lineup.png", asset_dir / "lineup.png")
    issue.checkpoints = copy_if_exists(art_dir / "checkpoints.png", asset_dir / "checkpoints.png")

    album = ISSUES_DIR / f"{issue.date}-running-cardnews-album.html"
    if album.exists():
        issue.card_album = copy_if_exists(album, SITE_ISSUES_DIR / f"{issue.date}-cardnews-album.html")


def page_head(title):
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      --ink: #111514;
      --paper: #F7F5F1;
      --cream: #fff7ec;
      --accent: #ff6b4a;
      --muted: #5d6561;
      --line: #ded8cf;
      --green: #49dcb1;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", Arial, sans-serif;
      letter-spacing: 0;
    }}
    a {{ color: inherit; text-decoration: none; }}
    .shell {{ width: min(1040px, calc(100% - 32px)); margin: 0 auto; }}
    .topbar {{ padding: 28px 0 18px; display: flex; justify-content: space-between; align-items: center; gap: 16px; }}
    .brand {{ font-size: 26px; font-weight: 950; }}
    .instagram {{ color: var(--accent); font-size: 14px; font-weight: 900; }}
    .hero {{ border: 3px solid var(--ink); background: var(--cream); padding: 14px; margin-bottom: 28px; }}
    .hero img, .issue-image {{ display: block; width: 100%; height: auto; border: 0; }}
    .archive-title {{ font-size: clamp(44px, 8vw, 88px); line-height: 1.05; margin: 44px 0 16px; font-weight: 950; }}
    .lead {{ max-width: 760px; color: #323332; font-size: 18px; line-height: 1.75; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; margin: 32px 0 56px; }}
    .card {{ background: #fffffb; border: 2px solid var(--ink); padding: 16px; border-radius: 0; }}
    .card:hover {{ outline: 5px solid rgba(255, 107, 74, .25); }}
    .thumb {{ margin: -6px -6px 14px; border: 1px solid var(--line); background: var(--cream); }}
    .meta {{ color: var(--accent); font-size: 13px; font-weight: 950; margin-bottom: 8px; }}
    .card h2 {{ font-size: 24px; line-height: 1.25; margin: 0 0 12px; }}
    .story-list {{ padding-left: 20px; margin: 0; color: #323332; font-size: 14px; line-height: 1.55; font-weight: 750; }}
    .section {{ padding: 28px 0; border-top: 1px solid var(--line); }}
    .section-title {{ color: var(--accent); font-size: 13px; font-weight: 950; margin-bottom: 10px; }}
    .story {{ padding: 22px 0; border-top: 1px solid var(--line); }}
    .story h2 {{ font-size: clamp(24px, 4vw, 36px); line-height: 1.25; margin: 6px 0 14px; }}
    .story p {{ color: #323332; font-size: 16px; line-height: 1.8; font-weight: 650; }}
    .comment {{ background: var(--ink); color: #f7f4ec; padding: 16px 18px; font-size: 15px; line-height: 1.75; font-weight: 750; }}
    .comment b {{ color: var(--green); }}
    .source {{ color: var(--muted); font-size: 13px; font-weight: 800; }}
    .source a {{ color: var(--accent); }}
    .footer {{ padding: 40px 0 56px; color: var(--muted); font-size: 13px; text-align: center; }}
    @media (max-width: 680px) {{
      .topbar {{ align-items: flex-start; flex-direction: column; }}
      .hero {{ padding: 8px; }}
    }}
  </style>
</head>
<body>
"""


def image_tag(src, alt, class_name="issue-image"):
    if not src:
        return ""
    return f'<img class="{class_name}" src="{escape(src)}" alt="{escape(alt)}">'


def index_card(issue):
    detail_href = f"issues/{issue.date}.html"
    top_stories = issue.stories[:3]
    story_items = "".join(f"<li>{escape(story.title)}</li>" for story in top_stories)
    thumb = image_tag(issue.hero, f"{issue.date} 러너리 브리핑", "issue-image") if issue.hero else ""
    return f"""
      <a class="card" href="{detail_href}">
        <div class="thumb">{thumb}</div>
        <div class="meta">{escape(issue.date)} · {len(issue.stories)} stories</div>
        <h2>오늘의 러닝 브리핑 {escape(issue.number)}</h2>
        <ol class="story-list">{story_items}</ol>
      </a>
    """


def render_index(issues):
    cards = "\n".join(index_card(issue) for issue in issues)
    return f"""{page_head("러너리 뉴스레터 아카이브")}
  <main class="shell">
    <header class="topbar">
      <a class="brand" href="index.html">@runeorrri</a>
      <a class="instagram" href="https://instagram.com/runeorrri">Instagram</a>
    </header>
    <h1 class="archive-title">러너리<br>뉴스레터 아카이브</h1>
    <p class="lead">메일로 보낸 오늘의 러닝 브리핑을 모아둔 곳입니다. 대회 접수, 커뮤니티형 러닝, 글로벌 로드러닝 흐름까지 다시 확인하기 좋게 정리합니다.</p>
    <section class="grid" aria-label="뉴스레터 목록">
      {cards}
    </section>
  </main>
  <footer class="footer">runeorrri · running briefing</footer>
</body>
</html>
"""


def render_lineup(issue):
    rows = []
    for story in issue.stories:
        rows.append(
            f"""<div class="story">
              <div class="section-title">{story.index:02d} · {escape(story.region)} / {escape(story.category)}</div>
              <h2>{escape(story.title)}</h2>
              <p>{escape(story.summary)}</p>
              <div class="comment"><b>러너리 코멘트</b><br>{escape(story.why)}</div>
              <p class="source">원문: <a href="{escape(story.url)}">{escape(story.source)}</a></p>
            </div>"""
        )
    return "\n".join(rows)


def render_issue(issue):
    prefix = "../"
    hero = image_tag(prefix + issue.hero, f"{issue.date} 러너리 브리핑") if issue.hero else ""
    lineup = image_tag(prefix + issue.lineup, "오늘의 라인업") if issue.lineup else ""
    checkpoints = image_tag(prefix + issue.checkpoints, "러너리 체크포인트") if issue.checkpoints else ""
    album_link = (
        f'<p class="source"><a href="{escape(Path(issue.card_album).name)}">카드뉴스 앨범 보기</a></p>'
        if issue.card_album
        else ""
    )
    return f"""{page_head(f"오늘의 러닝 브리핑 {issue.number} - {issue.date}")}
  <main class="shell">
    <header class="topbar">
      <a class="brand" href="../index.html">@runeorrri</a>
      <a class="instagram" href="https://instagram.com/runeorrri">Instagram</a>
    </header>
    <section class="hero">{hero}</section>
    <section class="section">
      <div class="section-title">INTRO</div>
      <p class="lead">{escape(issue.intro)}</p>
      {album_link}
    </section>
    <section class="section">
      <div class="section-title">TODAY'S LINEUP</div>
      {lineup}
    </section>
    <section class="section">
      <div class="section-title">RUNNERLY BRIEFS</div>
      {render_lineup(issue)}
    </section>
    <section class="section">
      <div class="section-title">CHECKPOINTS</div>
      {checkpoints}
    </section>
  </main>
  <footer class="footer">runeorrri · running briefing</footer>
</body>
</html>
"""


def build_archive_site():
    SITE_DIR.mkdir(exist_ok=True)
    SITE_ISSUES_DIR.mkdir(parents=True, exist_ok=True)
    SITE_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    newsletters = sorted(ISSUES_DIR.glob("*-running-newsletter.md"), reverse=True)
    issues = [parse_newsletter(path) for path in newsletters]
    for issue in issues:
        (SITE_ISSUES_DIR / f"{issue.date}.html").write_text(render_issue(issue), encoding="utf-8")
    (SITE_DIR / "index.html").write_text(render_index(issues), encoding="utf-8")
    return issues


def main():
    issues = build_archive_site()
    print(SITE_DIR / "index.html")
    for issue in issues:
        print(SITE_ISSUES_DIR / f"{issue.date}.html")


if __name__ == "__main__":
    main()
