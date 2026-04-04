#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    bold_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
    ]
    reg_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    paths = bold_paths if bold else reg_paths
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def strip_front_matter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return text
    return "\n".join(lines[end + 1 :])


def sanitize_line(line: str) -> str:
    s = line.strip()
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"<([^>]+)>", r"\1", s)
    s = re.sub(r"\$\$(.*?)\$\$", r"\1", s)
    s = re.sub(r"\$(.*?)\$", r"\1", s)
    return s


def extract_image_path(line: str) -> str | None:
    m = re.search(r"!\[\]\(([^)]+)\)", line)
    if not m:
        return None
    return m.group(1).strip()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    cur = words[0]
    for w in words[1:]:
        probe = f"{cur} {w}"
        box = draw.textbbox((0, 0), probe, font=font)
        if box[2] - box[0] <= max_w:
            cur = probe
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


class PdfBuilder:
    def __init__(self, title: str, subtitle: str, image_dir: Path) -> None:
        self.w = 1654
        self.h = 2339
        self.margin = 110
        self.pages: List[Image.Image] = []
        self.image_dir = image_dir

        self.font_title = load_font(54, bold=True)
        self.font_h1 = load_font(40, bold=True)
        self.font_h2 = load_font(33, bold=True)
        self.font_body = load_font(26, bold=False)
        self.font_small = load_font(21, bold=False)

        self._new_page(with_header=False)
        self._draw_cover(title, subtitle)
        self._new_page(with_header=True)

    def _new_page(self, with_header: bool) -> None:
        page = Image.new("RGB", (self.w, self.h), "white")
        d = ImageDraw.Draw(page)
        if with_header:
            d.rectangle((0, 0, self.w, 86), fill=(22, 60, 120))
            d.text((self.margin, 23), "Лабораторная работа 4: отчёт", fill="white", font=self.font_small)
            d.text((self.w - 320, 23), f"стр. {len(self.pages) + 1}", fill="white", font=self.font_small)
        self.pages.append(page)
        self.y = 150 if with_header else 120

    def _draw_cover(self, title: str, subtitle: str) -> None:
        page = self.pages[-1]
        d = ImageDraw.Draw(page)
        d.rectangle((0, 0, self.w, 260), fill=(22, 60, 120))
        d.text((self.margin, 82), title, fill="white", font=self.font_title)
        d.text((self.margin, 330), subtitle, fill=(25, 50, 95), font=self.font_h2)
        base_y = 520
        info = [
            "Студент: Гашимов Кенан Мухтар оглы",
            "Группа: НКНбд-01-23",
            "Студенческий билет: 1032235820",
            "Дисциплина: Имитационное моделирование",
        ]
        for line in info:
            d.text((self.margin, base_y), line, fill=(35, 55, 90), font=self.font_body)
            base_y += 68
        d.rounded_rectangle((self.margin, 930, self.w - self.margin, 1310), radius=24, outline=(70, 100, 150), width=3)
        d.text(
            (self.margin + 36, 1010),
            "Документ содержит текстовое описание цели, методики, хода экспериментов, результатов и выводов.",
            fill=(38, 59, 94),
            font=self.font_body,
        )

    def _ensure_space(self, needed: int) -> None:
        if self.y + needed > self.h - self.margin:
            self._new_page(with_header=True)

    def add_heading(self, text: str, level: int) -> None:
        text = sanitize_line(text)
        if not text:
            return
        font = self.font_h1 if level == 1 else self.font_h2
        gap_before = 34 if level == 1 else 24
        self._ensure_space(140)
        self.y += gap_before
        page = self.pages[-1]
        d = ImageDraw.Draw(page)
        lines = wrap_text(d, text, font, self.w - 2 * self.margin)
        for line in lines:
            d.text((self.margin, self.y), line, fill=(20, 50, 95), font=font)
            box = d.textbbox((self.margin, self.y), line, font=font)
            self.y = box[3] + 8
        self.y += 8

    def add_paragraph(self, text: str) -> None:
        text = sanitize_line(text)
        if not text:
            self.y += 12
            return
        self._ensure_space(80)
        page = self.pages[-1]
        d = ImageDraw.Draw(page)
        lines = wrap_text(d, text, self.font_body, self.w - 2 * self.margin)
        for line in lines:
            self._ensure_space(48)
            page = self.pages[-1]
            d = ImageDraw.Draw(page)
            d.text((self.margin, self.y), line, fill=(25, 30, 40), font=self.font_body)
            box = d.textbbox((self.margin, self.y), line, font=self.font_body)
            self.y = box[3] + 6
        self.y += 6

    def add_list_item(self, text: str) -> None:
        text = sanitize_line(text)
        if not text:
            return
        self.add_paragraph(f"- {text}")

    def add_image(self, rel_path: str) -> None:
        rel_path = rel_path.split("{", 1)[0].strip()
        src = Path(rel_path)
        if not src.is_absolute():
            src = self.image_dir / src.name
        if not src.exists():
            return

        img = Image.open(src).convert("RGB")
        max_w = self.w - 2 * self.margin
        max_h = 620
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        needed = img.height + 90
        self._ensure_space(needed)

        page = self.pages[-1]
        d = ImageDraw.Draw(page)
        x = (self.w - img.width) // 2
        page.paste(img, (x, self.y))
        self.y += img.height + 12
        d.text((self.margin, self.y), f"Иллюстрация: {src.name}", fill=(70, 70, 90), font=self.font_small)
        self.y += 34

    def finalize(self, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        p_pages = [pg.convert("P", palette=Image.Palette.ADAPTIVE, colors=256) for pg in self.pages]
        p_pages[0].save(out_path, save_all=True, append_images=p_pages[1:], resolution=150)


def parse_and_render(source_qmd: Path, image_dir: Path, output: Path, title: str, subtitle: str) -> None:
    text = source_qmd.read_text(encoding="utf-8")
    body = strip_front_matter(text)
    builder = PdfBuilder(title=title, subtitle=subtitle, image_dir=image_dir)

    for raw in body.splitlines():
        img = extract_image_path(raw)
        if img is not None:
            builder.add_image(img)
            continue

        line = raw.rstrip()
        s = line.strip()
        if not s:
            builder.add_paragraph("")
            continue

        if s.startswith("# "):
            builder.add_heading(s[2:].strip(), level=1)
        elif s.startswith("## "):
            builder.add_heading(s[3:].strip(), level=2)
        elif s.startswith("### "):
            builder.add_heading(s[4:].strip(), level=2)
        elif re.match(r"^\d+\.\s+", s):
            builder.add_list_item(re.sub(r"^\d+\.\s+", "", s))
        elif s.startswith("- "):
            builder.add_list_item(s[2:])
        elif s.startswith("|") and s.endswith("|"):
            if not re.match(r"^\|[-: ]+\|$", s.replace("---", "-")):
                row = " | ".join(part.strip() for part in s.strip("|").split("|"))
                builder.add_paragraph(row)
        else:
            builder.add_paragraph(s)

    builder.finalize(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-qmd", required=True)
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Отчёт ЛР4")
    parser.add_argument("--subtitle", default="Агентная реализация SIR-модели")
    args = parser.parse_args()

    parse_and_render(
        source_qmd=Path(args.source_qmd),
        image_dir=Path(args.image_dir),
        output=Path(args.output),
        title=args.title,
        subtitle=args.subtitle,
    )


if __name__ == "__main__":
    main()
