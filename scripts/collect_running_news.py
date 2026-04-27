#!/usr/bin/env python3
import argparse
import csv
import hashlib
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERIES = ROOT / "data" / "collection_queries.csv"
ARCHIVE = ROOT / "data" / "candidates_archive.csv"
CURRENT_ISSUE = ROOT / "data" / "current_issue_id.txt"
ISSUES_DIR = ROOT / "issues"

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

KEYWORDS = {
    "event": ["접수", "모집", "대회", "마라톤", "run", "race", "registration", "event", "marathon"],
    "gear": ["러닝화", "신발", "장비", "슈즈", "shoe", "gear", "adizero", "nike", "asics", "launch"],
    "elite": ["세계기록", "선수", "world athletics", "record", "championships", "elite", "marathon"],
    "news": ["러닝", "러너", "마라톤", "running", "runner", "community", "trend"],
}

EXCLUDE_TERMS = [
    "예비후보",
    "교육감",
    "선거",
    "cheating",
    "caught",
    "fury",
    "death",
    "crime",
    "accident",
    "celebrity",
    "스타",
]

LOW_VALUE_SOURCES = [
    "msn",
    "mirror",
    "앳스타일",
]


def read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_archive(rows):
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with ARCHIVE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ARCHIVE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def next_issue_id(issue_date):
    issue_numbers = []
    for path in ISSUES_DIR.glob("*-running-newsletter.md"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^#\s+오늘의 러닝 브리핑\s+(\d+)", text, re.MULTILINE)
        if match:
            issue_numbers.append(int(match.group(1)))
    if not issue_numbers:
        return f"{issue_date}-01"
    number = max(issue_numbers) + 1
    return f"{issue_date}-{number:02d}"


def google_news_rss(query, language, country):
    encoded = urllib.parse.quote_plus(f"{query} when:3d")
    ceid = f"{country}:{language}"
    return f"https://news.google.com/rss/search?q={encoded}&hl={language}&gl={country}&ceid={ceid}"


def fetch(url, timeout=20):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "runeorrri-newsletter-bot/1.0 (+https://runeorrri.pages.dev)",
            "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def text_of(node, name):
    child = node.find(name)
    return unescape(child.text or "").strip() if child is not None else ""


def source_of(item):
    source = item.find("source")
    if source is not None and source.text:
        return unescape(source.text).strip()
    return ""


def parse_date(value):
    if not value:
        return ""
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, IndexError):
        return ""


def clean_title(title):
    title = re.sub(r"\s+", " ", unescape(title)).strip()
    # Google News often formats titles as "Headline - Publisher".
    return re.sub(r"\s+-\s+[^-]{2,80}$", "", title).strip() or title


def infer_category(title, fallback):
    text = title.lower()
    scores = {}
    for category, words in KEYWORDS.items():
        scores[category] = sum(1 for word in words if word.lower() in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else fallback


def score_item(item):
    title = item["title"].lower()
    source = item["source"].lower()
    score = 0
    for words in KEYWORDS.values():
        score += sum(1 for word in words if word.lower() in title)
    if item["category"] in {"event", "gear"}:
        score += 2
    if item["region"] == "korea":
        score += 1
    if item["published_at"]:
        score += 1
    if any(source_name in source for source_name in LOW_VALUE_SOURCES):
        score -= 3
    return score


def is_excluded(item):
    text = f"{item.get('title', '')} {item.get('source', '')}".lower()
    return any(term.lower() in text for term in EXCLUDE_TERMS)


def summarize(item):
    return (
        f"{item['source']}에서 {item['published_at'] or '최근'}에 전한 러닝 관련 소식입니다. "
        f"제목은 “{item['title']}”이며, 원문에서 일정, 참가 조건, 제품 정보, 핵심 수치를 확인해야 합니다."
    )


def why_it_matters(item):
    if item["category"] == "event":
        return "참가 가능 여부, 접수 마감, 장소와 이동 동선을 빠르게 확인할 수 있는 소식입니다."
    if item["category"] == "gear":
        return "레이스데이 장비 선택과 러닝화 기술 흐름을 볼 때 참고할 만한 소식입니다."
    if item["category"] == "elite":
        return "엘리트 레이스 흐름이 기록, 페이스, 장비 트렌드에 어떻게 연결되는지 볼 수 있습니다."
    return "국내 러너가 러닝 문화와 시장 변화를 빠르게 훑는 데 도움이 되는 소식입니다."


def card_copy(item):
    title = item["title"]
    return title if len(title) <= 38 else f"{title[:37]}..."


def collect_from_query(row):
    url = google_news_rss(row["query"], row.get("language", "ko"), row.get("country", "KR"))
    data = fetch(url)
    root = ET.fromstring(data)
    items = []
    for rss_item in root.findall("./channel/item"):
        title = clean_title(text_of(rss_item, "title"))
        link = text_of(rss_item, "link")
        if not title or not link:
            continue
        category = infer_category(title, row.get("category", "news"))
        source = source_of(rss_item) or row.get("query", "Google News")
        published_at = parse_date(text_of(rss_item, "pubDate"))
        item = {
            "region": row.get("region", "korea"),
            "category": category,
            "title": title,
            "url": link,
            "source": source,
            "published_at": published_at,
            "query": row.get("query", ""),
        }
        items.append(item)
    return items


def dedupe_key(item):
    url = item.get("url", "").split("&ved=", 1)[0]
    title = re.sub(r"\W+", "", item.get("title", "").lower())
    return hashlib.sha1(f"{url}|{title}".encode("utf-8")).hexdigest()


def existing_keys():
    keys = set()
    for row in read_csv(ARCHIVE):
        keys.add(dedupe_key(row))
    return keys


def build_archive_row(issue_id, issue_date, item, selected):
    row = {
        "issue_id": issue_id,
        "issue_date": issue_date,
        "selected": "yes" if selected else "no",
        "region": item["region"],
        "category": item["category"],
        "title": item["title"],
        "summary": summarize(item),
        "why_it_matters": why_it_matters(item),
        "url": item["url"],
        "source": item["source"],
        "published_at": item["published_at"],
        "card_copy": card_copy(item),
        "verification_status": "auto_collected",
        "notes": f"Auto-collected from Google News query: {item['query']}. Review facts before manual publication.",
    }
    return {field: row.get(field, "") for field in ARCHIVE_FIELDS}


def selected_indexes(ranked, count):
    korea = [idx for idx, item in enumerate(ranked) if item["region"] == "korea"]
    global_items = [idx for idx, item in enumerate(ranked) if item["region"] == "global"]
    selected = korea[:3] + global_items[:2]
    for idx in range(len(ranked)):
        if len(selected) >= count:
            break
        if idx not in selected:
            selected.append(idx)
    return set(selected[:count])


def main():
    parser = argparse.ArgumentParser(description="Collect recent running news into candidates_archive.csv.")
    parser.add_argument("--issue-date", default=date.today().isoformat())
    parser.add_argument("--issue-id", default="")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--select", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    query_rows = read_csv(QUERIES)
    if not query_rows:
        raise SystemExit(f"No collection queries found: {QUERIES}")

    collected = []
    for row in query_rows:
        try:
            collected.extend(collect_from_query(row))
        except Exception as exc:
            print(f"warning: failed to collect query {row.get('query')}: {exc}", file=sys.stderr)

    seen = existing_keys()
    unique = []
    for item in collected:
        if is_excluded(item):
            continue
        key = dedupe_key(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    ranked = sorted(unique, key=score_item, reverse=True)[: args.limit]
    if len(ranked) < args.select:
        raise SystemExit(f"Collected only {len(ranked)} new candidates; need at least {args.select}.")

    issue_id = args.issue_id or next_issue_id(args.issue_date)
    selected = selected_indexes(ranked, args.select)
    new_rows = [build_archive_row(issue_id, args.issue_date, item, selected=index in selected) for index, item in enumerate(ranked)]

    if args.dry_run:
        print(f"Would collect {len(new_rows)} candidates for {issue_id}; selected {len(selected)}.")
        for row in new_rows:
            marker = "*" if row["selected"] == "yes" else "-"
            print(f"{marker} [{row['region']}/{row['category']}] {row['title']} ({row['source']})")
        return

    archive = read_csv(ARCHIVE)
    archive.extend(new_rows)
    write_archive(archive)
    CURRENT_ISSUE.write_text(f"{issue_id}\n", encoding="utf-8")
    print(f"Collected {len(new_rows)} candidates for {issue_id}; selected {args.select}.")


if __name__ == "__main__":
    main()
