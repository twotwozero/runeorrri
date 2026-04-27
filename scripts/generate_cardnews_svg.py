#!/usr/bin/env python3
import csv
import html
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates.csv"
OUT_DIR = ROOT / "issues" / f"{date.today().isoformat()}-cards"

WIDTH = 1080
HEIGHT = 1350

PALETTE = [
    ("#103c3f", "#d7fff1", "#ff6b4a"),
    ("#2d1b4e", "#f4edff", "#49dcb1"),
    ("#0f2742", "#eaf3ff", "#ffbe3d"),
    ("#3a2618", "#fff3e0", "#1e9f8a"),
    ("#172114", "#ecffd9", "#ff6b4a"),
]


def selected_rows():
    with CANDIDATES.open(newline="", encoding="utf-8") as f:
        rows = [row for row in csv.DictReader(f) if row["selected"].strip().lower() == "yes"]
    if len(rows) != 5:
        raise SystemExit(f"Expected 5 selected rows, found {len(rows)}")
    return rows


def esc(value):
    return html.escape(value or "", quote=False)


def wrap(text, max_chars):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) <= max_chars:
            line = candidate
        else:
            if line:
                lines.append(line)
            if len(word) > max_chars:
                lines.extend(word[i : i + max_chars] for i in range(0, len(word), max_chars))
                line = ""
            else:
                line = word
    if line:
        lines.append(line)
    return lines


def text_block(text, x, y, size, color, weight=700, max_chars=20, line_gap=1.25, max_lines=None):
    lines = wrap(text, max_chars)
    if max_lines:
        lines = lines[:max_lines]
    tspans = []
    for idx, line in enumerate(lines):
        dy = "0" if idx == 0 else str(int(size * line_gap))
        tspans.append(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-weight="{weight}" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">'
        f"{''.join(tspans)}</text>"
    )


def svg_shell(content, bg):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{bg}"/>
  {content}
</svg>
"""


def cover(today):
    content = f"""
  <path d="M0 0 H1080 V550 C780 500 590 290 0 360 Z" fill="#d7fff1" opacity="0.74"/>
  <path d="M1080 1350 H0 V930 C320 960 570 1130 1080 990 Z" fill="#ff6b4a" opacity="0.24"/>
  <text x="86" y="120" fill="#111514" font-size="34" font-weight="900" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">@runeorrri</text>
  {text_block("러너리 오늘의 러닝 브리핑", 86, 410, 108, "#111514", 950, 8, 1.03)}
  {text_block("국내 3개, 해외 2개. 대회 접수부터 장비 트렌드까지 짧게 정리했습니다.", 86, 1010, 42, "#2d3431", 760, 22, 1.35)}
  <line x1="86" y1="1218" x2="994" y2="1218" stroke="#111514" stroke-width="4"/>
  <text x="86" y="1280" fill="#111514" font-size="32" font-weight="900" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">{today}</text>
  <text x="786" y="1280" fill="#111514" font-size="32" font-weight="900" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">CARD NEWS</text>
"""
    return svg_shell(content, "#f7f4ec")


def story(row, index):
    bg, soft, accent = PALETTE[index - 1]
    region = "국내" if row["region"] == "korea" else "해외"
    label = f"{region} / {row['category']}"
    summary = row["summary"]
    why = row["why_it_matters"]
    content = f"""
  <rect x="760" y="1030" width="470" height="470" fill="none" stroke="{accent}" stroke-width="68" transform="rotate(18 995 1265)" opacity="0.92"/>
  <text x="86" y="120" fill="{soft}" font-size="28" font-weight="900" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">@runeorrri · {index:02d}</text>
  <text x="760" y="120" fill="{soft}" font-size="28" font-weight="900" text-anchor="start" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">{esc(label)}</text>
  <text x="86" y="300" fill="{accent}" font-size="180" font-weight="950" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">{index}</text>
  {text_block(row["title"], 86, 470, 72, soft, 950, 13, 1.16, 4)}
  {text_block(summary, 86, 760, 35, soft, 680, 28, 1.45, 5)}
  <rect x="86" y="1010" width="908" height="220" fill="#ffffff" opacity="0.13" stroke="#ffffff" stroke-opacity="0.24" stroke-width="2"/>
  <text x="124" y="1070" fill="{accent}" font-size="30" font-weight="900" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">러너에게 왜 중요?</text>
  {text_block(why, 124, 1130, 31, soft, 800, 31, 1.36, 3)}
  <text x="86" y="1290" fill="{soft}" opacity="0.78" font-size="25" font-weight="650" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">{esc(row["source"])} · {esc(row["published_at"])}</text>
"""
    return svg_shell(content, bg)


def closing(rows):
    y = 465
    items = []
    for row in rows:
        items.append(text_block(row["title"], 86, y, 29, "#f7f4ec", 780, 31, 1.22, 2))
        items.append(f'<text x="86" y="{y + 78}" fill="#aab4af" font-size="23" font-weight="650" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">{esc(row["source"])}</text>')
        items.append(f'<line x1="86" y1="{y + 112}" x2="994" y2="{y + 112}" stroke="#f7f4ec" stroke-opacity="0.18" stroke-width="2"/>')
        y += 145

    content = f"""
  <text x="86" y="120" fill="#f7f4ec" font-size="34" font-weight="900" font-family="-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif">SOURCES</text>
  {text_block("읽고 저장할 소식만 골랐어요", 86, 290, 86, "#49dcb1", 950, 11, 1.08, 2)}
  {''.join(items)}
  {text_block("대회 일정, 장비 소식, 해외 러닝 트렌드를 한 번에 확인하세요.", 86, 1210, 40, "#f7f4ec", 820, 24, 1.32, 2)}
"""
    return svg_shell(content, "#111514")


def convert_with_qlmanage(svg_path):
    qlmanage = "/usr/bin/qlmanage"
    if not Path(qlmanage).exists():
        return
    subprocess.run(
        [qlmanage, "-t", "-s", "1080", "-o", str(svg_path.parent), str(svg_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def main():
    rows = selected_rows()
    today = date.today().isoformat()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pages = [("00-cover", cover(today))]
    pages.extend((f"{i:02d}-story", story(row, i)) for i, row in enumerate(rows, 1))
    pages.append(("06-closing", closing(rows)))

    for name, markup in pages:
        svg_path = OUT_DIR / f"{name}.svg"
        svg_path.write_text(markup, encoding="utf-8")
        convert_with_qlmanage(svg_path)
        print(svg_path)


if __name__ == "__main__":
    main()
