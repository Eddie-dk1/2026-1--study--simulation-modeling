#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def make_cover(title: str, subtitle: str, width: int = 1920, height: int = 1080) -> Image.Image:
    img = Image.new("RGB", (width, height), (243, 248, 255))
    d = ImageDraw.Draw(img)
    h1 = load_font(72)
    h2 = load_font(42)
    body = load_font(34)

    d.rectangle((0, 0, width, 170), fill=(20, 52, 100))
    d.text((60, 48), title, fill="white", font=h1)
    d.text((60, 235), subtitle, fill=(26, 46, 78), font=h2)

    lines = [
        "Студент: Гашимов Кенан Мухтар оглы",
        "Группа: НКНбд-01-23",
        "Студенческий билет: 1032235820",
        "Дисциплина: Имитационное моделирование",
    ]
    y = 360
    for line in lines:
        d.text((90, y), line, fill=(32, 52, 84), font=body)
        y += 56

    d.rounded_rectangle((70, 700, width - 70, 980), radius=24, fill=(255, 255, 255), outline=(80, 110, 150), width=3)
    d.text((110, 760), "PDF сформирован из визуальных материалов ЛР4 для гарантированного отображения изображений.", fill=(38, 58, 92), font=body)
    return img


def layout_page(image_path: Path, idx: int, total: int, width: int = 1920, height: int = 1080) -> Image.Image:
    page = Image.new("RGB", (width, height), (248, 251, 255))
    d = ImageDraw.Draw(page)
    title = load_font(42)
    text = load_font(28)

    d.rectangle((0, 0, width, 120), fill=(23, 58, 112))
    d.text((40, 34), f"ЛР4 · Иллюстрация {idx}/{total}", fill="white", font=title)

    d.rounded_rectangle((50, 160, width - 50, height - 120), radius=20, fill=(255, 255, 255), outline=(92, 124, 170), width=3)
    d.text((90, 190), f"Файл: {image_path.name}", fill=(35, 56, 92), font=text)

    img = Image.open(image_path).convert("RGB")
    max_w, max_h = width - 180, height - 360
    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    x = (width - img.width) // 2
    y = 270
    page.paste(img, (x, y))

    d.text((90, height - 90), "Источник: labs/lab04/(report|presentation)/image", fill=(56, 74, 105), font=text)
    return page


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    src = Path(args.source_dir)
    files = sorted(src.glob("*.png"))
    if args.limit > 0:
        files = files[: args.limit]
    if not files:
        raise SystemExit(f"no png files in {src}")

    pages = [make_cover(args.title, args.subtitle)]
    total = len(files)
    for i, path in enumerate(files, start=1):
        pages.append(layout_page(path, i, total))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Use palette mode to avoid dependency on JPEG encoder in this environment.
    p_pages = [pg.convert("P", palette=Image.Palette.ADAPTIVE, colors=256) for pg in pages]
    p_pages[0].save(out, save_all=True, append_images=p_pages[1:], resolution=150)


if __name__ == "__main__":
    main()
