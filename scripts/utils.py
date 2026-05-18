#!/usr/bin/env python3
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")


def clean_text(value):
    return str(value).replace("\u00b7", ", ")


def is_selected(value):
    return str(value).strip().lower() in {"yes", "y", "true", "1", "selected"}


def issue_date_from_id(issue_id):
    match = re.match(r"(\d{4}-\d{2}-\d{2})-", issue_id or "")
    return match.group(1) if match else ""


def issue_number_from_id(issue_id, default="01"):
    if not issue_id:
        return default
    suffix = str(issue_id).rsplit("-", 1)[-1]
    return suffix.zfill(2) if suffix.isdigit() else default


def korean_today():
    return datetime.now(KST).date().isoformat()


def category_label(value):
    labels = {
        "event": "이벤트",
        "race": "레이스",
        "news": "뉴스",
        "gear": "장비",
        "elite": "엘리트",
        "training": "훈련",
        "safety": "안전",
    }
    category = str(value).strip().lower()
    return labels.get(category, str(value).strip())


def story_sort_key(row):
    region_order = {"korea": 0, "global": 1}
    category_order = {"event": 0, "gear": 1, "elite": 2, "news": 3, "training": 4, "safety": 5}
    return (
        region_order.get(row.get("region", "").strip().lower(), 9),
        category_order.get(row.get("category", "").strip().lower(), 9),
    )


def load_dotenv(root):
    env_file = Path(root) / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value
