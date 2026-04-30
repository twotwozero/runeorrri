#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "candidates_archive.csv"

ARCHIVE_FIELDS = [
    "issue_id",
    "issue_date",
    "selected",
    "region",
    "category",
    "title",
    "summary",
    "why_it_matters",
    "url",
    "source",
    "published_at",
    "one_liner",
    "verification_status",
    "notes",
]

CLAUDE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
MIN_SCORE = 65


class ArticleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_style = False
        self.capture = None
        self.title = ""
        self.meta = []
        self.paragraphs = []
        self._current = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style", "noscript"}:
            if tag == "script":
                self.in_script = True
            elif tag == "style":
                self.in_style = True
            return
        if tag == "title":
            self.capture = "title"
            self._current = []
        elif tag in {"p", "h1", "h2", "h3", "li"}:
            self.capture = "body"
            self._current = []
        elif tag == "meta":
            name = (attrs.get("name") or attrs.get("property") or "").lower()
            content = attrs.get("content", "")
            if name in {"description", "og:description", "twitter:description"} and content:
                self.meta.append(content)

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
        elif tag == "style":
            self.in_style = False
        elif tag == "title" and self.capture == "title":
            self.title = normalize_text(" ".join(self._current))
            self.capture = None
        elif tag in {"p", "h1", "h2", "h3", "li"} and self.capture == "body":
            text = normalize_text(" ".join(self._current))
            if len(text) >= 35:
                self.paragraphs.append(text)
            self.capture = None

    def handle_data(self, data):
        if self.in_script or self.in_style or not self.capture:
            return
        text = normalize_text(data)
        if text:
            self._current.append(text)


def normalize_text(value):
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


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


def load_editorial_guidelines():
    path = ROOT / "docs" / "editorial-guidelines.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_system_prompt():
    guidelines = load_editorial_guidelines()
    return f"""당신은 한국 러닝 뉴스레터 '러너리(runeorrri)'의 편집자입니다.

아래 편집 가이드를 반드시 따르세요:

{guidelines}

핵심 원칙:
- 확인되지 않은 날짜, 금액, 경로, 제품 스펙, 접수 정보는 절대 쓰지 않습니다.
- 번역투·홍보 문구·과장된 표현을 피합니다.
- 원문에서 충분한 정보를 얻을 수 없으면 keep=false로 표시합니다."""


def read_archive():
    if not ARCHIVE.exists():
        raise SystemExit(f"Missing archive: {ARCHIVE}")
    with ARCHIVE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_archive(rows):
    with ARCHIVE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ARCHIVE_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in ARCHIVE_FIELDS} for row in rows)


def fetch_article_text(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; runeorrri-newsletter-bot/1.0; +https://runeorrri.pages.dev)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=18) as response:
            content_type = response.headers.get_content_charset() or "utf-8"
            raw = response.read(900_000)
            final_url = response.geturl()
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return "", f"article_fetch_failed: {exc}"

    text = raw.decode(content_type, errors="replace")
    parser = ArticleTextParser()
    parser.feed(text)
    parts = []
    if parser.title:
        parts.append(parser.title)
    parts.extend(parser.meta[:2])
    parts.extend(parser.paragraphs[:18])
    article = normalize_text(" ".join(parts))
    if len(article) > 5500:
        article = article[:5500]
    return article, f"article_url: {final_url}; extracted_chars: {len(article)}"


def enrichment_schema():
    return {
        "type": "object",
        "properties": {
            "keep": {"type": "boolean"},
            "quality_score": {"type": "integer"},
            "category": {"type": "string", "enum": ["event", "gear", "elite", "news"]},
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "why_it_matters": {"type": "string"},
            "one_liner": {"type": "string"},
            "editor_note": {"type": "string"},
        },
        "required": [
            "keep",
            "quality_score",
            "category",
            "title",
            "summary",
            "why_it_matters",
            "one_liner",
            "editor_note",
        ],
    }


def build_prompt(row, article_text):
    return f"""다음 기사 후보를 러너리 뉴스레터 기준으로 평가하고 편집해 주세요.

후보 메타데이터:
- region: {row.get('region', '')}
- category: {row.get('category', '')}
- title: {row.get('title', '')}
- source: {row.get('source', '')}
- published_at: {row.get('published_at', '')}
- url: {row.get('url', '')}
- rss_notes: {row.get('notes', '')}

원문 추출 텍스트:
{article_text or '(원문 추출 실패 또는 정보 부족)'}"""


def claude_json(prompt, schema, retries=4):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "ANTHROPIC_API_KEY is required for newsletter enrichment. "
            "Set it as a GitHub Actions secret or in the .env file."
        )
    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": build_system_prompt(),
        "tools": [
            {
                "name": "enrich_candidate",
                "description": "러닝 뉴스 후보를 평가하고 뉴스레터용 콘텐츠를 생성합니다.",
                "input_schema": schema,
            }
        ],
        "tool_choice": {"type": "tool", "name": "enrich_candidate"},
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        CLAUDE_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload["content"][0]["input"]
        except urllib.error.HTTPError as e:
            if e.code == 529 and attempt < retries - 1:
                wait = 60 * (attempt + 1)
                print(f"  overloaded, waiting {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise


def quality_sort_key(row):
    try:
        score = int(row.get("_quality_score", "0"))
    except ValueError:
        score = 0
    region_bonus = 4 if row.get("region") == "korea" else 0
    category_bonus = 3 if row.get("category") in {"event", "gear"} else 0
    return score + region_bonus + category_bonus


def choose_selected(rows, count):
    keepers = [row for row in rows if row.get("_keep") == "yes" and quality_sort_key(row) >= MIN_SCORE]
    ranked = sorted(keepers, key=quality_sort_key, reverse=True)
    selected = []
    for target_region, limit in (("korea", 3), ("global", 2)):
        for row in ranked:
            if len([item for item in selected if item.get("region") == target_region]) >= limit:
                break
            if row.get("region") == target_region and row not in selected:
                selected.append(row)
    for row in ranked:
        if len(selected) >= count:
            break
        if row not in selected:
            selected.append(row)
    if len(selected) < count:
        raise SystemExit(f"Only {len(selected)} publishable candidates after enrichment; need {count}.")
    selected_ids = {id(row) for row in selected[:count]}
    for row in rows:
        row["selected"] = "yes" if id(row) in selected_ids else "no"


def enrich_row(row, index, total):
    article_text, extraction_note = fetch_article_text(row.get("url", ""))
    prompt = build_prompt(row, article_text)
    result = claude_json(prompt, enrichment_schema())
    row["_keep"] = "yes" if result["keep"] else "no"
    row["_quality_score"] = str(max(0, min(100, int(result["quality_score"]))))
    if result["keep"]:
        row["title"] = normalize_text(result["title"])[:90]
        row["category"] = result["category"]
        row["summary"] = normalize_text(result["summary"])
        row["why_it_matters"] = normalize_text(result["why_it_matters"])
        row["one_liner"] = normalize_text(result["one_liner"])[:44]
        row["verification_status"] = "reviewed"
    else:
        row["verification_status"] = "rejected"
    row["notes"] = (
        f"AI enriched. keep={row['_keep']}; score={row['_quality_score']}; "
        f"{extraction_note}; editor_note: {normalize_text(result['editor_note'])}"
    )
    print(f"[{index}/{total}] {row['_quality_score']} {row['_keep']} {row['source']} - {row['title']}", flush=True)
    time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="Fetch source pages and AI-edit collected newsletter candidates.")
    parser.add_argument("issue_id")
    parser.add_argument("--select", type=int, default=5)
    args = parser.parse_args()

    load_dotenv()

    rows = read_archive()
    issue_rows = [row for row in rows if row.get("issue_id") == args.issue_id]
    if not issue_rows:
        raise SystemExit(f"No rows found for issue_id: {args.issue_id}")

    to_enrich = [row for row in issue_rows if row.get("selected") == "yes"]
    if len(to_enrich) < args.select:
        raise SystemExit(f"Only {len(to_enrich)} pre-selected candidates; need {args.select}.")

    for index, row in enumerate(to_enrich, start=1):
        enrich_row(row, index, len(to_enrich))

    kept = [row for row in to_enrich if row.get("_keep") == "yes"]
    if len(kept) < args.select:
        raise SystemExit(f"Only {len(kept)} candidates passed AI review; need {args.select}.")

    for row in to_enrich:
        row.pop("_keep", None)
        row.pop("_quality_score", None)
    write_archive(rows)
    print(f"Enriched {len(to_enrich)} candidates for {args.issue_id}; {len(kept)} passed review.")


if __name__ == "__main__":
    main()
