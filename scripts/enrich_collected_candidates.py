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
    "card_copy",
    "verification_status",
    "notes",
]

OPENAI_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.2-mini"
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


def openai_json(prompt, schema):
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY is required for automatic newsletter enrichment. "
            "Set it as a GitHub Actions secret before the 08:00 run."
        )
    model = os.environ.get("OPENAI_MODEL", "").strip() or DEFAULT_MODEL
    body = {
        "model": model,
        "instructions": (
            "You are a Korean running-newsletter editor. Produce accurate, concise Korean copy. "
            "Use only the provided source text and metadata. If the source is too thin, mark keep=false. "
            "Do not invent dates, fees, routes, product specs, or registration details."
        ),
        "input": prompt,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "candidate_enrichment",
                "strict": True,
                "schema": schema,
            }
        },
    }
    request = urllib.request.Request(
        OPENAI_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    output_text = payload.get("output_text")
    if not output_text:
        output_text = "".join(
            content.get("text", "")
            for item in payload.get("output", [])
            for content in item.get("content", [])
            if content.get("type") == "output_text"
        )
    return json.loads(output_text)


def enrichment_schema():
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "keep": {"type": "boolean"},
            "quality_score": {"type": "integer"},
            "category": {"type": "string", "enum": ["event", "gear", "elite", "news"]},
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "why_it_matters": {"type": "string"},
            "card_copy": {"type": "string"},
            "editor_note": {"type": "string"},
        },
        "required": [
            "keep",
            "quality_score",
            "category",
            "title",
            "summary",
            "why_it_matters",
            "card_copy",
            "editor_note",
        ],
    }


def build_prompt(row, article_text):
    return f"""
JSON으로만 응답하세요.

목표:
- 러너리 뉴스레터에 실을 후보인지 판단합니다.
- 한국 러너가 바로 이해할 수 있게 자연스러운 한국어로 다시 씁니다.
- 핵심 날짜, 접수 마감, 장소, 비용, 제품명, 기록, 주최 등 확인된 사실을 우선합니다.
- 단순 사건사고, 지역성이 너무 약한 기사, 맥락 없는 광고성 기사, 원문 정보가 부족한 기사는 keep=false로 둡니다.

출력 규칙:
- quality_score는 0~100.
- title은 뉴스레터 제목으로 42자 이내.
- summary는 2문장, 180~260자.
- why_it_matters는 1~2문장, 한국 러너 관점.
- card_copy는 32자 이내의 카드뉴스 문구.
- 확인되지 않은 정보는 쓰지 않습니다.

후보 메타데이터:
- region: {row.get('region', '')}
- category: {row.get('category', '')}
- title: {row.get('title', '')}
- source: {row.get('source', '')}
- published_at: {row.get('published_at', '')}
- url: {row.get('url', '')}
- rss_notes: {row.get('notes', '')}

원문 추출 텍스트:
{article_text or '(원문 추출 실패 또는 정보 부족)'}
""".strip()


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
    result = openai_json(prompt, enrichment_schema())
    row["_keep"] = "yes" if result["keep"] else "no"
    row["_quality_score"] = str(max(0, min(100, int(result["quality_score"]))))
    if result["keep"]:
        row["title"] = normalize_text(result["title"])[:90]
        row["category"] = result["category"]
        row["summary"] = normalize_text(result["summary"])
        row["why_it_matters"] = normalize_text(result["why_it_matters"])
        row["card_copy"] = normalize_text(result["card_copy"])[:44]
        row["verification_status"] = "reviewed"
    else:
        row["verification_status"] = "rejected"
    row["notes"] = (
        f"AI enriched. keep={row['_keep']}; score={row['_quality_score']}; "
        f"{extraction_note}; editor_note: {normalize_text(result['editor_note'])}"
    )
    print(f"[{index}/{total}] {row['_quality_score']} {row['_keep']} {row['source']} - {row['title']}", flush=True)
    time.sleep(0.2)


def main():
    parser = argparse.ArgumentParser(description="Fetch source pages and AI-edit collected newsletter candidates.")
    parser.add_argument("issue_id")
    parser.add_argument("--select", type=int, default=5)
    args = parser.parse_args()

    rows = read_archive()
    issue_rows = [row for row in rows if row.get("issue_id") == args.issue_id]
    if not issue_rows:
        raise SystemExit(f"No rows found for issue_id: {args.issue_id}")

    for index, row in enumerate(issue_rows, start=1):
        enrich_row(row, index, len(issue_rows))
    choose_selected(issue_rows, args.select)

    for row in issue_rows:
        row.pop("_keep", None)
        row.pop("_quality_score", None)
    write_archive(rows)
    selected = [row for row in issue_rows if row.get("selected") == "yes"]
    print(f"Enriched {len(issue_rows)} candidates for {args.issue_id}; selected {len(selected)}.")


if __name__ == "__main__":
    main()
