from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".pydeps"))

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


REPORT_DIR = ROOT / "report"
PRESENTATION_DIR = ROOT / "presentation"
PLOTS_DIR = ROOT / "plots"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
FONT_NAME = "ArialUnicode"

pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))


def draw_wrapped_text(c: canvas.Canvas, text: str, x: float, y: float, max_width: float, font_size: int, leading: float | None = None) -> float:
    c.setFont(FONT_NAME, font_size)
    leading = leading or font_size * 1.35
    for paragraph in text.split("\n"):
        lines = simpleSplit(paragraph, FONT_NAME, font_size, max_width)
        if not lines:
            y -= leading
            continue
        for line in lines:
            c.drawString(x, y, line)
            y -= leading
        y -= leading * 0.35
    return y


def draw_bullets(c: canvas.Canvas, items: list[str], x: float, y: float, max_width: float, font_size: int) -> float:
    for item in items:
        y = draw_wrapped_text(c, f"• {item}", x, y, max_width, font_size)
    return y


def fit_image(path: Path, max_width: float, max_height: float) -> tuple[ImageReader, float, float]:
    image = ImageReader(str(path))
    width, height = image.getSize()
    scale = min(max_width / width, max_height / height)
    return image, width * scale, height * scale


def render_report() -> None:
    c = canvas.Canvas(str(REPORT_DIR / "report.pdf"), pagesize=A4)
    width, height = A4

    def title_page():
        c.setFont(FONT_NAME, 24)
        c.drawCentredString(width / 2, height - 70 * mm, "Имитационное моделирование")
        c.setFont(FONT_NAME, 18)
        c.drawCentredString(width / 2, height - 85 * mm, "Лабораторная работа №5. Аппарат сетей Петри")
        c.setFont(FONT_NAME, 14)
        c.drawCentredString(width / 2, height - 120 * mm, "Гашимов Кенан Мухтар оглы")
        c.drawCentredString(width / 2, height - 130 * mm, "Российский университет дружбы народов")
        c.drawCentredString(width / 2, height - 145 * mm, "2026-04-18")
        c.showPage()

    def text_page(title: str, paragraphs=None, bullets=None):
        c.setFont(FONT_NAME, 18)
        c.drawString(20 * mm, height - 20 * mm, title)
        y = height - 32 * mm
        for paragraph in paragraphs or []:
            y = draw_wrapped_text(c, paragraph, 22 * mm, y, width - 44 * mm, 11)
            y -= 2 * mm
        if bullets:
            y = draw_bullets(c, bullets, 26 * mm, y, width - 52 * mm, 11)
        c.showPage()

    def image_page(title: str, image_path: Path, caption: str, bullets=None):
        c.setFont(FONT_NAME, 18)
        c.drawString(20 * mm, height - 20 * mm, title)
        image, img_w, img_h = fit_image(image_path, width - 40 * mm, 105 * mm)
        x = (width - img_w) / 2
        y_img = height - 30 * mm - img_h
        c.drawImage(image, x, y_img, width=img_w, height=img_h)
        y = y_img - 10 * mm
        y = draw_wrapped_text(c, caption, 22 * mm, y, width - 44 * mm, 11)
        if bullets:
            draw_bullets(c, bullets, 26 * mm, y, width - 52 * mm, 11)
        c.showPage()

    def two_image_page(title: str, top_path: Path, bottom_path: Path, top_caption: str, bottom_caption: str):
        c.setFont(FONT_NAME, 18)
        c.drawString(20 * mm, height - 20 * mm, title)
        top_img, top_w, top_h = fit_image(top_path, width - 40 * mm, 75 * mm)
        bot_img, bot_w, bot_h = fit_image(bottom_path, width - 40 * mm, 75 * mm)
        c.drawImage(top_img, (width - top_w) / 2, height - 32 * mm - top_h, width=top_w, height=top_h)
        y_mid = height - 36 * mm - top_h
        draw_wrapped_text(c, top_caption, 22 * mm, y_mid, width - 44 * mm, 10)
        c.drawImage(bot_img, (width - bot_w) / 2, 42 * mm, width=bot_w, height=bot_h)
        draw_wrapped_text(c, bottom_caption, 22 * mm, 34 * mm, width - 44 * mm, 10)
        c.showPage()

    title_page()
    text_page(
        "Цель и задание",
        paragraphs=[
            "Цель работы состоит в изучении сетей Петри на примере задачи обедающих философов, воспроизведении взаимной блокировки в классической постановке и устранении deadlock с помощью арбитра.",
        ],
        bullets=[
            "Реализовать классическую и модифицированную сеть Петри.",
            "Выполнить стохастическое и детерминированное моделирование.",
            "Сохранить CSV-таблицы, графики, GIF-анимацию и literate-артефакты.",
            "Провести параметрическое исследование по N, tmax и seed.",
        ],
    )
    text_page(
        "Теоретическое введение",
        paragraphs=[
            "Сеть Петри описывает дискретную систему через позиции, переходы, дуги и маркировку. В задаче обедающих философов позиции представляют состояния философов и свободные вилки, а переходы моделируют захват и освобождение ресурсов.",
            "В классической постановке каждый философ может взять левую вилку и застрять в ожидании правой. Это приводит к тупиковой маркировке, когда все философы находятся в состоянии Hungry. Позиция Arbiter ограничивает число одновременных попыток захвата ресурсов и устраняет deadlock.",
        ],
    )
    text_page(
        "Структура проекта",
        bullets=[
            "src/DiningPhilosophers.jl — описание сети Петри и методов моделирования.",
            "scripts/dining_philosophers.jl — базовый эксперимент.",
            "scripts/dining_philosophers_animation.jl — построение GIF-анимации.",
            "scripts/dining_philosophers_report.jl — сравнительный график состояний Eat_i.",
            "scripts/dining_philosophers_params.jl — параметрическое исследование.",
            "generated/ — clean, md, ipynb и qmd представления literate-скриптов.",
        ],
    )
    image_page(
        "Классическая сеть",
        PLOTS_DIR / "classic_simulation.png",
        "Базовый прогон для классической сети завершился тупиковой маркировкой.",
        bullets=["deadlock = true", "число состояний = 9", "final_hungry = 5", "final_eat = 0", "t_deadlock ≈ 2.27"],
    )
    image_page(
        "Сеть с арбитром",
        PLOTS_DIR / "arbiter_simulation.png",
        "Модифицированная сеть сохраняет активность на всём интервале времени.",
        bullets=["deadlock = false", "число состояний = 76", "final_hungry = 3", "final_eat = 1", "модель активна до t = 50.0"],
    )
    two_image_page(
        "Детерминированные траектории",
        PLOTS_DIR / "classic_deterministic.png",
        PLOTS_DIR / "arbiter_deterministic.png",
        "Классическая детерминированная модель",
        "Детерминированная модель с арбитром",
    )
    image_page(
        "Итоговый сравнительный график",
        PLOTS_DIR / "final_report.png",
        "Сравнение состояний Eat_i наглядно показывает различие между двумя постановками.",
        bullets=[
            "в классической сети все Eat_i быстро опускаются к нулю",
            "в сети с арбитром состояния Eat_i продолжают появляться до конца интервала",
        ],
    )
    image_page(
        "Параметрическое исследование",
        PLOTS_DIR / "dining_params.png",
        "Проверка по 54 сериям запусков подтверждает устойчивость результата.",
        bullets=[
            "classic: 27 deadlock из 27 запусков",
            "arbiter: 0 deadlock из 27 запусков",
            "для classic final_eat всегда равен 0",
            "для arbiter в конце часто сохраняется хотя бы один Eat_i",
        ],
    )
    text_page(
        "Выводы",
        paragraphs=[
            "В лабораторной работе реализована сеть Петри для задачи обедающих философов, выполнены стохастическое и детерминированное моделирование, получены CSV-таблицы, графики, анимация и literate-представления.",
            "Классическая сеть во всех проверенных сериях приходит к deadlock, тогда как введение арбитра устраняет тупиковую конфигурацию и сохраняет живость модели.",
        ],
    )
    c.save()


def render_presentation() -> None:
    slidesize = (320 * mm, 180 * mm)
    c = canvas.Canvas(str(PRESENTATION_DIR / "presentation.pdf"), pagesize=slidesize)
    width, height = slidesize

    def slide_title(title: str):
        c.setFont(FONT_NAME, 22)
        c.drawString(15 * mm, height - 18 * mm, title)

    def title_slide():
        c.setFont(FONT_NAME, 26)
        c.drawCentredString(width / 2, height - 45 * mm, "Имитационное моделирование")
        c.setFont(FONT_NAME, 18)
        c.drawCentredString(width / 2, height - 58 * mm, "Лабораторная работа №5. Аппарат сетей Петри")
        c.setFont(FONT_NAME, 14)
        c.drawCentredString(width / 2, height - 90 * mm, "Гашимов Кенан Мухтар оглы")
        c.drawCentredString(width / 2, height - 100 * mm, "2026-04-18")
        c.showPage()

    def text_slide(title: str, bullets):
        slide_title(title)
        draw_bullets(c, bullets, 22 * mm, height - 35 * mm, width - 44 * mm, 13)
        c.showPage()

    def image_slide(title: str, image_path: Path, caption: str, bullets=None):
        slide_title(title)
        image, img_w, img_h = fit_image(image_path, 180 * mm, 110 * mm)
        c.drawImage(image, 12 * mm, 26 * mm, width=img_w, height=img_h)
        y = height - 35 * mm
        y = draw_wrapped_text(c, caption, 205 * mm, y, 95 * mm, 12)
        if bullets:
            draw_bullets(c, bullets, 210 * mm, y, 85 * mm, 12)
        c.showPage()

    title_slide()
    text_slide("Цель и задачи", [
        "изучить задачу обедающих философов в терминах сетей Петри",
        "воспроизвести deadlock в классической постановке",
        "устранить блокировку с помощью арбитра",
        "получить графики, таблицы, GIF и literate-артефакты",
    ])
    text_slide("Структура проекта", [
        "src/DiningPhilosophers.jl — модуль модели",
        "базовый сценарий, анимация, итоговый график, параметрический анализ",
        "generated/clean, generated/md, generated/notebooks, generated/qmd",
    ])
    image_slide("Классическая сеть", PLOTS_DIR / "classic_simulation.png", "Классическая сеть быстро приходит к тупиковой маркировке.", ["deadlock = true", "final_hungry = 5", "final_eat = 0"])
    image_slide("Сеть с арбитром", PLOTS_DIR / "arbiter_simulation.png", "Арбитр не позволяет всем философам одновременно захватить по одной вилке.", ["deadlock = false", "final_hungry = 3", "final_eat = 1"])
    image_slide("Сравнение состояний Eat_i", PLOTS_DIR / "final_report.png", "На итоговом графике видно, что активность в классической сети исчезает.", ["верхняя панель — classical", "нижняя панель — arbiter"])
    image_slide("Параметрическое исследование", PLOTS_DIR / "dining_params.png", "Результат устойчив для всех проверенных значений N, tmax и seed.", ["classic: 27/27 deadlock", "arbiter: 0/27 deadlock"])
    text_slide("Основные артефакты", [
        "data/dining_classic.csv",
        "data/dining_arbiter.csv",
        "data/dining_params.csv",
        "plots/philosophers_simulation.gif",
        "generated/clean, md, ipynb, qmd",
    ])
    text_slide("Выводы", [
        "сети Петри наглядно описывают конкуренцию за ресурсы",
        "классическая постановка приводит к deadlock",
        "арбитр устраняет тупиковую конфигурацию",
        "результат подтверждён базовым и параметрическим экспериментами",
    ])
    c.save()


def main() -> None:
    render_report()
    render_presentation()
    print(f"Saved {REPORT_DIR / 'report.pdf'}")
    print(f"Saved {PRESENTATION_DIR / 'presentation.pdf'}")


if __name__ == "__main__":
    main()
