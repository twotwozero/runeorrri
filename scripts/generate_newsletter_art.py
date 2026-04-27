#!/usr/bin/env python3
import csv
import re
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates.csv"
CURRENT_ISSUE = ROOT / "data" / "current_issue_id.txt"


def issue_date():
    if CURRENT_ISSUE.exists():
        issue_id = CURRENT_ISSUE.read_text(encoding="utf-8").strip()
        match = re.match(r"(\d{4}-\d{2}-\d{2})-", issue_id)
        if match:
            return match.group(1)
    return date.today().isoformat()


ISSUE_DATE = issue_date()
OUT_DIR = ROOT / "issues" / f"{ISSUE_DATE}-art"
FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
DUCK_ASSET = ROOT / "assets" / "runeorrri-duck-character-sheet-2026-04-25-selected.png"


def font(size, index=16):
    for path in FONT_CANDIDATES:
        if not Path(path).exists():
            continue
        try:
            return ImageFont.truetype(path, size=size, index=index)
        except OSError:
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default(size=size)


def selected_rows():
    with CANDIDATES.open(newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row.get("selected", "").strip().lower() == "yes"]


def wrap(draw, text, font_obj, max_width):
    lines = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font_obj)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_text(draw, xy, text, font_obj, fill, max_width, line_height=None, max_lines=None):
    x, y = xy
    lines = wrap(draw, text, font_obj, max_width)
    if max_lines:
        lines = lines[:max_lines]
    line_height = line_height or int(font_obj.size * 1.28)
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        y += line_height
    return y


def save(img, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    img.save(path, "PNG")
    print(path)


def duck_crop(box, width):
    duck = Image.open(DUCK_ASSET).convert("L").crop(box)
    ratio = width / duck.width
    duck = duck.resize((width, int(duck.height * ratio)), Image.Resampling.LANCZOS)
    alpha = duck.point(lambda p: max(0, min(255, (245 - p) * 4)))
    line = Image.new("RGBA", duck.size, "#111514")
    line.putalpha(alpha)
    return line


def duck_cell(col, row, width, inset=0):
    duck = Image.open(DUCK_ASSET)
    cell_w = duck.width / 4
    cell_h = duck.height / 3
    return duck_crop(
        (
            int(col * cell_w + inset),
            int(row * cell_h + inset),
            int((col + 1) * cell_w - inset),
            int((row + 1) * cell_h - inset),
        ),
        width,
    )


def spot_duck(name, box, width=360):
    img = Image.new("RGBA", (420, 300), (0, 0, 0, 0))
    duck = duck_crop(box, width)
    img.paste(duck, ((420 - duck.width) // 2, (300 - duck.height) // 2), duck)
    save(img, name)


def hero(rows):
    img = Image.new("RGB", (1200, 720), "#fff7ec")
    draw = ImageDraw.Draw(img)
    draw.rectangle((18, 18, 1182, 702), outline="#111514", width=3)
    draw.rectangle((34, 34, 1166, 686), outline="#ff6b4a", width=8)
    if DUCK_ASSET.exists():
        duck_asset = Image.open(DUCK_ASSET)
        cell_h = duck_asset.height / 3
        duck = duck_crop((0, 0, 370, int(cell_h)), 400)
        img.paste(duck, (690, 145), duck)
    draw.text((72, 70), "@runeorrri", font=font(34), fill="#111514")
    draw_text(draw, (72, 205), "오늘의 러닝 브리핑", font(88), "#111514", 620, 92, 2)
    draw_text(
        draw,
        (72, 425),
        "대회 접수, 커뮤니티형 러닝, 글로벌 로드러닝 흐름까지 러너가 오늘 확인하면 좋은 것만 골랐습니다.",
        font(34, 6),
        "#323332",
        610,
        48,
        3,
    )
    draw.text((72, 630), f"{ISSUE_DATE} · {len(rows)} stories", font=font(28), fill="#111514")
    save(img, "hero.png")


def lineup(rows):
    img = Image.new("RGB", (1200, 760), "#111514")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 1200, 120), fill="#103c3f")
    draw.text((70, 52), "TODAY'S LINEUP", font=font(34), fill="#49dcb1")
    y = 165
    colors = ["#ff6b4a", "#49dcb1", "#ffbe3d", "#d7fff1", "#ffd2bf"]
    for idx, row in enumerate(rows, start=1):
        color = colors[(idx - 1) % len(colors)]
        draw.rounded_rectangle((70, y, 1130, y + 90), radius=0, outline="#38413d", width=2)
        draw.text((95, y + 24), f"{idx:02d}", font=font(34), fill=color)
        draw_text(draw, (170, y + 20), row["title"], font(30, 6), "#f7f4ec", 850, 38, 2)
        y += 108
    save(img, "lineup.png")


def action(rows):
    img = Image.new("RGB", (1200, 620), "#fff7ec")
    draw = ImageDraw.Draw(img)
    draw.rectangle((18, 18, 1182, 602), outline="#111514", width=3)
    draw.rectangle((34, 34, 1166, 586), outline="#ff6b4a", width=8)
    draw.line((835, 72, 835, 548), fill="#111514", width=3)
    draw.line((845, 78, 845, 540), fill="#111514", width=1)

    draw.text((72, 64), "러너리 체크포인트", font=font(50), fill="#111514")
    draw.text((75, 128), "오늘 읽은 소식, 이렇게만 챙기기", font=font(24, 6), fill="#4c4c47")

    tape = [(736, 58), (826, 46), (842, 90), (750, 103)]
    draw.polygon(tape, fill="#49dcb1", outline="#111514")
    draw.text((758, 63), "memo", font=font(20), fill="#111514")

    bullets = [
        ("접수형", "마감일과 장소를 먼저 확인하세요."),
        ("참여형", "기록보다 운영 방식과 안전 동선을 봅니다."),
        ("해외 소식", "당장 참가보다 시장의 방향을 읽는 힌트로 봅니다."),
    ]
    y = 184
    for idx, (label, body) in enumerate(bullets, start=1):
        row_height = 108 if idx == 3 else 92
        top = y + sum(108 if i == 3 else 92 for i in range(1, idx)) + (idx - 1) * 24
        bottom = top + row_height
        draw.rounded_rectangle((70, top, 782, bottom), radius=8, fill="#fffffb", outline="#111514", width=2)
        draw.rectangle((70, top, 123, bottom), fill="#111514")
        draw.text((86, top + (row_height - 38) // 2), f"{idx}", font=font(30), fill="#fff7ec")
        draw.rounded_rectangle(
            (142, top + (row_height - 38) // 2, 252, top + (row_height - 38) // 2 + 38),
            radius=8,
            fill="#ff6b4a",
            outline="#111514",
            width=2,
        )
        draw.text((163, top + (row_height - 19) // 2), label, font=font(19, 6), fill="#111514")

        body_font = font(26, 6)
        line_height = 35
        lines = wrap(draw, body, body_font, 485)[:2]
        text_y = top + (row_height - len(lines) * line_height) // 2
        for line in lines:
            draw.text((275, text_y), line, font=body_font, fill="#323332")
            text_y += line_height

    if DUCK_ASSET.exists():
        duck = duck_cell(2, 1, 250, inset=26)
        img.paste(duck, (890, 165), duck)
    save(img, "checkpoints.png")


def spots():
    if not DUCK_ASSET.exists():
        return
    img = Image.new("RGBA", (420, 300), (0, 0, 0, 0))
    duck = duck_cell(0, 0, 310)
    img.paste(duck, ((420 - duck.width) // 2, (300 - duck.height) // 2), duck)
    save(img, "duck-pace.png")

    img = Image.new("RGBA", (420, 300), (0, 0, 0, 0))
    duck = duck_cell(3, 0, 330)
    img.paste(duck, ((420 - duck.width) // 2, (300 - duck.height) // 2), duck)
    save(img, "duck-water.png")

    img = Image.new("RGBA", (420, 300), (0, 0, 0, 0))
    duck = duck_cell(0, 1, 340)
    img.paste(duck, ((420 - duck.width) // 2, (300 - duck.height) // 2), duck)
    save(img, "duck-peek.png")


def main():
    rows = selected_rows()
    hero(rows)
    lineup(rows)
    action(rows)
    spots()


if __name__ == "__main__":
    main()
