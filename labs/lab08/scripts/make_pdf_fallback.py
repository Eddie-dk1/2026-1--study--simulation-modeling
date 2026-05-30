from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PAGE = (1240, 1754)
MARGIN = 90
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
ACCENT = (25, 76, 121)
MUTED = (88, 96, 105)


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def clean_line(line: str) -> str:
    line = re.sub(r"\{#[^}]+\}", "", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    line = line.replace("`", "")
    return line.strip()


def image_path(line: str, base: Path) -> Path | None:
    match = re.search(r"!\[[^\]]*\]\(([^)]+)\)", line)
    if not match:
        return None
    return (base / match.group(1)).resolve()


def add_text_page(pages: list[Image.Image], title: str, lines: list[str]) -> None:
    img = Image.new("RGB", PAGE, "white")
    draw = ImageDraw.Draw(img)
    title_font = font(34)
    body_font = font(24)
    y = MARGIN
    if title:
        draw.rectangle((0, 0, PAGE[0], 24), fill=ACCENT)
        draw.text((MARGIN, y), title, fill=ACCENT, font=title_font)
        draw.line((MARGIN, y + 46, PAGE[0] - MARGIN, y + 46), fill=(220, 226, 232), width=2)
        y += 58
    for line in lines:
        for wrapped in textwrap.wrap(line, width=82):
            if y > PAGE[1] - MARGIN:
                pages.append(img)
                img = Image.new("RGB", PAGE, "white")
                draw = ImageDraw.Draw(img)
                y = MARGIN
            draw.text((MARGIN, y), wrapped, fill="black", font=body_font)
            y += 34
        y += 8
    pages.append(img)


def add_image_page(pages: list[Image.Image], path: Path, caption: str) -> None:
    if not path.is_file():
        return
    img = Image.new("RGB", PAGE, "white")
    draw = ImageDraw.Draw(img)
    caption_font = font(26)
    body_font = font(22)
    draw.rectangle((0, 0, PAGE[0], 24), fill=ACCENT)
    draw.text((MARGIN, MARGIN), caption or path.name, fill=ACCENT, font=caption_font)
    with Image.open(path) as source:
        source = source.convert("RGB")
        max_w = PAGE[0] - 2 * MARGIN
        max_h = PAGE[1] - 3 * MARGIN
        source.thumbnail((max_w, max_h))
        x = (PAGE[0] - source.width) // 2
        y = MARGIN + 70
        img.paste(source, (x, y))
    draw.text((MARGIN, PAGE[1] - MARGIN + 15), str(path), fill=MUTED, font=body_font)
    pages.append(img)


def parse_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    in_yaml = False
    author_next = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "---":
            in_yaml = not in_yaml
            continue
        if not in_yaml:
            continue
        if line.startswith("title:"):
            metadata["title"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("subtitle:"):
            metadata["subtitle"] = line.split(":", 1)[1].strip().strip('"')
        elif line == "author:":
            author_next = True
        elif author_next and line.startswith("name:"):
            metadata["author"] = line.split(":", 1)[1].strip().strip('"')
            author_next = False
    return metadata


def add_cover_page(pages: list[Image.Image], metadata: dict[str, str], kind: str) -> None:
    img = Image.new("RGB", PAGE, (248, 250, 252))
    draw = ImageDraw.Draw(img)
    title_font = font(48)
    subtitle_font = font(30)
    body_font = font(26)
    small_font = font(22)

    draw.rectangle((0, 0, PAGE[0], 180), fill=ACCENT)
    draw.rectangle((MARGIN, 260, PAGE[0] - MARGIN, 1180), fill="white", outline=(224, 229, 235), width=2)
    draw.text((MARGIN + 45, 315), metadata.get("title", "Лабораторная работа 8"), fill=ACCENT, font=title_font)
    draw.text((MARGIN + 45, 390), metadata.get("subtitle", ""), fill=(33, 37, 41), font=subtitle_font)
    draw.line((MARGIN + 45, 455, PAGE[0] - MARGIN - 45, 455), fill=(224, 229, 235), width=3)

    rows = [
        ("Тип документа", kind),
        ("Автор", "Гашимов Кенан Мухтар оглы"),
        ("Группа", "НКНбд-01-23"),
        ("Студенческий билет", "1032235820"),
        ("Дисциплина", "Имитационное моделирование"),
        ("Организация", "РУДН имени Патриса Лумумбы"),
        ("Город", "Москва"),
        ("Год", "2026"),
    ]
    y = 535
    for key, value in rows:
        draw.text((MARGIN + 45, y), key, fill=MUTED, font=small_font)
        draw.text((MARGIN + 360, y), value, fill=(20, 25, 31), font=body_font)
        y += 58

    draw.text((MARGIN, PAGE[1] - 130), "Дискретно-событийное имитационное моделирование SIR", fill=MUTED, font=small_font)
    pages.append(img)


def build_pdf(source: Path, output: Path) -> None:
    pages: list[Image.Image] = []
    current_title = ""
    buffer: list[str] = []
    in_yaml = False
    text = source.read_text(encoding="utf-8")
    kind = "Презентация" if "presentation" in str(source) else "Отчёт"
    add_cover_page(pages, parse_metadata(text), kind)

    for raw in text.splitlines():
        if raw.strip() == "---":
            in_yaml = not in_yaml
            continue
        if in_yaml:
            continue
        img = image_path(raw, source.parent)
        if img:
            if buffer:
                add_text_page(pages, current_title, buffer)
                buffer = []
            caption = re.search(r"!\[([^\]]*)\]", raw)
            add_image_page(pages, img, caption.group(1) if caption else "")
            continue
        line = clean_line(raw)
        if not line:
            continue
        if line.startswith("#"):
            if buffer:
                add_text_page(pages, current_title, buffer)
                buffer = []
            current_title = line.lstrip("#").strip()
        elif not line.startswith("|") and not line.startswith(":"):
            buffer.append(line.lstrip("- ").strip())

    if buffer or not pages:
        add_text_page(pages, current_title, buffer)

    output.parent.mkdir(parents=True, exist_ok=True)
    first, *rest = pages
    first.save(output, "PDF", save_all=True, append_images=rest)


if __name__ == "__main__":
    build_pdf(Path(sys.argv[1]), Path(sys.argv[2]))
