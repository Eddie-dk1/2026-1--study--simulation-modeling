from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PAGE = (1240, 1754)
MARGIN = 90
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"


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
        draw.text((MARGIN, y), title, fill="black", font=title_font)
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
    draw.text((MARGIN, MARGIN), caption or path.name, fill="black", font=caption_font)
    with Image.open(path) as source:
        source = source.convert("RGB")
        max_w = PAGE[0] - 2 * MARGIN
        max_h = PAGE[1] - 3 * MARGIN
        source.thumbnail((max_w, max_h))
        x = (PAGE[0] - source.width) // 2
        y = MARGIN + 70
        img.paste(source, (x, y))
    draw.text((MARGIN, PAGE[1] - MARGIN + 15), str(path), fill="gray", font=body_font)
    pages.append(img)


def build_pdf(source: Path, output: Path) -> None:
    pages: list[Image.Image] = []
    current_title = ""
    buffer: list[str] = []
    in_yaml = False

    for raw in source.read_text(encoding="utf-8").splitlines():
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
