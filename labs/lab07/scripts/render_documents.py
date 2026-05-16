from __future__ import annotations

import csv
import base64
import html
import os
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


DATA = ROOT / "data"
PLOTS = ROOT / "plots"
REPORT = ROOT / "report"
PRESENTATION = ROOT / "presentation"


def read_one(name: str) -> dict[str, str]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return next(csv.DictReader(f))


def read_all(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(row: dict[str, str], key: str, digits: int = 3) -> str:
    return f"{float(row[key]):.{digits}f}"


def write_references() -> None:
    (REPORT / "references.bib").write_text(
        """@book{ross2014,
  author = {Ross, Sheldon M.},
  title = {Introduction to Probability Models},
  edition = {11},
  publisher = {Academic Press},
  year = {2014}
}

@book{kleinrock1975,
  author = {Kleinrock, Leonard},
  title = {Queueing Systems, Volume 1: Theory},
  publisher = {Wiley},
  year = {1975}
}

@article{bezanson2017,
  author = {Bezanson, Jeff and Edelman, Alan and Karpinski, Stefan and Shah, Viral B.},
  title = {Julia: A Fresh Approach to Numerical Computing},
  journal = {SIAM Review},
  volume = {59},
  number = {1},
  pages = {65--98},
  year = {2017}
}

@misc{literate2026,
  author = {{Literate.jl contributors}},
  title = {Literate.jl},
  year = {2026},
  url = {https://github.com/fredrikekre/Literate.jl}
}
""",
        encoding="utf-8",
    )


def make_report_markdown() -> str:
    mmc = read_one("mmc_summary.csv")
    ross = read_one("ross_base_metrics.csv")
    ross_run = read_one("ross_runs_summary.csv")
    params = read_all("ross_params_summary.csv")

    param_lines = [
        "| N | ремонтников | имитация, ч | аналитика, ч | загрузка | очередь |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in params:
        param_lines.append(
            f"| {row['N']} | {row['repairers']} | {num(row, 'mean_crash_time', 1)} | "
            f"{num(row, 'analytic_crash_time', 1)} | {num(row, 'mean_repairer_utilization')} | "
            f"{num(row, 'mean_repair_queue')} |"
        )

    return f"""---
title: "Имитационное моделирование"
subtitle: "Лабораторная работа №7. Дискретно-событийное моделирование"
author: "Гашимов Кенан Мухтар оглы, НКНбд-01-23"
date: "2026-05-16"
lang: "ru"
toc: true
numbersections: true
bibliography: references.bib
---

# Цель работы

Изучить дискретно-событийное моделирование на примере системы массового обслуживания `M/M/c` и модели Росса с резервом и ремонтом, перенести расчёты в структуру DrWatson, добавить графики, параметрические прогоны, литературный код и производные документы.

# Задание

1. Создать рабочий каталог для кода.
2. Установить необходимые Julia-пакеты.
3. Выполнить предложенный код и преобразовать его в литературный стиль.
4. Сгенерировать чистый код, Jupyter notebook и Quarto-документацию.
5. Для `M/M/c` добавить графики и сравнить с аналитическими характеристиками.
6. Для модели Росса добавить нескольких ремонтников, выполнить прогоны для разного количества машин, построить мониторинг ремонтника и очереди, сравнить с аналитическим решением.
7. Подготовить отчёт, презентацию и релизные файлы.

# Структура проекта

- `Project.toml`, `Manifest.toml` — Julia-окружение.
- `src/SimulationModelingLab07.jl` — функции имитации и аналитики.
- `scripts/mmc_literate.jl`, `scripts/ross_literate.jl`, `scripts/params_literate.jl` — литературный код.
- `generated/clean`, `generated/md`, `generated/notebooks`, `generated/qmd` — производные literate-артефакты.
- `data/` — CSV-таблицы с результатами.
- `plots/` — графики.
- `report/`, `presentation/`, `deliverables/` — итоговые материалы.

# Модель M/M/c

Модель `M/M/c` описывает очередь с пуассоновским входящим потоком, экспоненциальным временем обслуживания и `c` параллельными каналами [@kleinrock1975]. В базовом эксперименте использованы параметры `lambda = {mmc['lambda']}`, `mu = {mmc['mu']}`, `c = {mmc['c']}`, что даёт загрузку `rho = {num(mmc, 'rho')}`.

Аналитические значения рассчитаны по формуле Эрланга C: вероятность ожидания `Pwait = {num(mmc, 'p_wait')}`, среднее число заявок в очереди `Lq = {num(mmc, 'lq')}`, среднее ожидание `Wq = {num(mmc, 'wq')}`, среднее время в системе `W = {num(mmc, 'w')}`.

Имитация для `{mmc['customers']}` заявок дала вероятность ожидания `{num(mmc, 'observed_wait_probability')}`, `Wq = {num(mmc, 'observed_wq')}`, `W = {num(mmc, 'observed_w')}`, `Lq = {num(mmc, 'observed_lq')}`. Отличие связано с конечной длиной прогона и высокой загрузкой `rho = 0.9`, при которой дисперсия ожидания заметна.

![Динамика очереди M/M/c](../plots/mmc_trace.png)

![Параметрическое сравнение Wq](../plots/mmc_sweep_wq.png)

# Модель Росса

Модель Росса рассматривает `N` работающих машин, `S` резервных машин и ремонтное устройство [@ross2014]. После отказа работающей машины резерв немедленно занимает её место. Если резерв пуст, следующий отказ приводит к падению системы. После ремонта машина возвращается в резерв.

В реализации добавлена поддержка нескольких ремонтников. Состояние мониторинга содержит время события, число резервных машин, длину очереди ремонта, число занятых ремонтников и число исправных машин.

Базовый прогон: `N = {ross['N']}`, `S = {ross['S']}`, ремонтников `{ross['repairers']}`. Падение произошло на времени `{num(ross, 'crash_time', 1)}` ч. Загрузка ремонтника составила `{num(ross, 'repairer_utilization')}`, средняя длина очереди ремонта `{num(ross, 'average_repair_queue')}`.

Для серии прогонов при тех же параметрах среднее время до падения равно `{num(ross_run, 'mean_crash_time', 1)}` ч, аналитическое ожидание — `{num(ross_run, 'analytic_crash_time', 1)}` ч. Все 80 прогонов завершились падением, поэтому цензурирования в базовой серии нет.

![Мониторинг модели Росса](../plots/ross_trace.png)

# Аналитическое сравнение

Для модели Росса решалась система линейных уравнений для средних времен достижения поглощающего состояния. Состояние задаётся числом исправных машин `i = N, ..., N + S`. При отказе происходит переход `i -> i - 1` с интенсивностью `N / failure_mean`; при завершении ремонта — переход `i -> i + 1` с интенсивностью `min(R, N + S - i) / repair_mean`.

Параметрические результаты:

{chr(10).join(param_lines)}

![Время до падения](../plots/ross_crash_time.png)

![Мониторинг загрузки и очереди](../plots/ross_monitoring.png)

# Литературный код и notebook

Из каждого literate-файла сгенерированы:

- чистый Julia-код в `generated/clean`;
- Markdown-документация в `generated/md`;
- Jupyter notebook в `generated/notebooks`;
- Quarto-документация в `generated/qmd`.

Notebook-файлы выполнены через `scripts/execute_notebooks.py`: скрипт извлекает Julia-код из ячеек и запускает его в том же окружении проекта. Это фиксирует проверку исполняемости notebook без зависимости от установленного Jupyter/IJulia.

# Выводы

Модель `M/M/c` реализована как дискретно-событийная система с календарём событий. Полученные оценки согласуются с формулами Эрланга C, а параметрический прогон показывает резкий рост ожидания при приближении загрузки к единице.

Модель Росса реализована для одного и нескольких ремонтников. Увеличение числа ремонтников снижает загрузку каждого ремонтника и среднюю очередь ремонта, а аналитическое решение даёт ориентир для среднего времени до падения. При фиксированном резерве увеличение числа основных машин ускоряет падение системы, потому что суммарная интенсивность отказов растёт.

# Список литературы
"""


def make_presentation_markdown() -> str:
    mmc = read_one("mmc_summary.csv")
    ross = read_one("ross_runs_summary.csv")
    return f"""---
title: "Лабораторная работа №7"
subtitle: "Дискретно-событийное моделирование"
author: "Гашимов Кенан Мухтар оглы"
date: "2026-05-16"
---

# Цель

- реализовать модель `M/M/c`;
- реализовать модель Росса с резервом и ремонтом;
- добавить графики, мониторинг и аналитику;
- подготовить literate-артефакты, отчёт и презентацию.

---

# Структура

- `src/SimulationModelingLab07.jl`;
- `scripts/*_literate.jl`;
- `generated/clean`, `md`, `notebooks`, `qmd`;
- `data/`, `plots/`;
- `report/`, `presentation/`, `deliverables/`.

---

# M/M/c

- `lambda = {mmc['lambda']}`, `mu = {mmc['mu']}`, `c = {mmc['c']}`;
- загрузка `rho = {num(mmc, 'rho')}`;
- аналитическое `Wq = {num(mmc, 'wq')}`;
- имитационное `Wq = {num(mmc, 'observed_wq')}`.

![M/M/c](../plots/mmc_trace.png)

---

# Параметры M/M/c

![Параметрическое сравнение](../plots/mmc_sweep_wq.png)

---

# Модель Росса

- `N = {ross['N']}`, `S = {ross['S']}`;
- несколько ремонтников поддержаны параметром `repairers`;
- базовая серия: среднее время до падения `{num(ross, 'mean_crash_time', 1)}` ч;
- аналитика: `{num(ross, 'analytic_crash_time', 1)}` ч.

![Мониторинг](../plots/ross_trace.png)

---

# Параметрический прогон

![Время до падения](../plots/ross_crash_time.png)

---

# Очередь ремонта

![Загрузка и очередь](../plots/ross_monitoring.png)

---

# Итоги

- `M/M/c` согласуется с формулами Эрланга C;
- для Росса построено аналитическое решение;
- добавлены несколько ремонтников и прогоны по `N`;
- сформированы Markdown, DOCX, PDF, HTML, notebook и Quarto-артефакты.
"""


def draw_text_page(pdf: PdfPages, title: str, paragraphs: list[str]) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.08, 0.94, title, fontsize=17, weight="bold", va="top")
    y = 0.89
    for paragraph in paragraphs:
        for line in textwrap.wrap(paragraph, width=92):
            fig.text(0.08, y, line, fontsize=10.5, va="top")
            y -= 0.025
        y -= 0.018
        if y < 0.08:
            pdf.savefig(fig)
            plt.close(fig)
            fig = plt.figure(figsize=(8.27, 11.69))
            y = 0.94
    pdf.savefig(fig)
    plt.close(fig)


def draw_image_page(pdf: PdfPages, title: str, image: Path, caption: str) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.08, 0.94, title, fontsize=17, weight="bold", va="top")
    ax = fig.add_axes([0.08, 0.29, 0.84, 0.55])
    ax.imshow(plt.imread(image))
    ax.axis("off")
    y = 0.24
    for line in textwrap.wrap(caption, width=95):
        fig.text(0.08, y, line, fontsize=10.5, va="top")
        y -= 0.026
    pdf.savefig(fig)
    plt.close(fig)


def render_report_pdf(markdown: str) -> None:
    with PdfPages(REPORT / "report.pdf") as pdf:
        draw_text_page(pdf, "Лабораторная работа №7", [
            "Дискретно-событийное моделирование. Гашимов Кенан Мухтар оглы, НКНбд-01-23.",
            "В отчёте представлены модели M/M/c и Росса, аналитическое сравнение, графики и описание literate-артефактов.",
        ])
        sections = markdown.split("\n# ")
        for section in sections[1:5]:
            title, _, body = section.partition("\n")
            paragraphs = [p.strip().replace("\n", " ") for p in body.split("\n\n") if p.strip() and not p.strip().startswith("!")]
            draw_text_page(pdf, title.strip(), paragraphs[:8])
        draw_image_page(pdf, "M/M/c: динамика", PLOTS / "mmc_trace.png", "Динамика числа заявок в системе и длины очереди.")
        draw_image_page(pdf, "M/M/c: параметрический прогон", PLOTS / "mmc_sweep_wq.png", "Сравнение аналитического и имитационного среднего ожидания.")
        draw_image_page(pdf, "Модель Росса: мониторинг", PLOTS / "ross_trace.png", "Изменение числа исправных машин, резерва, очереди ремонта и занятости ремонтника.")
        draw_image_page(pdf, "Модель Росса: время до падения", PLOTS / "ross_crash_time.png", "Имитационное и аналитическое время до падения для разных N и числа ремонтников.")
        draw_image_page(pdf, "Модель Росса: очередь", PLOTS / "ross_monitoring.png", "Загрузка ремонтников и средняя длина очереди ремонта.")


def render_presentation_pdf(slides: str) -> None:
    parts = [part.strip() for part in slides.split("\n---\n") if part.strip()]
    with PdfPages(PRESENTATION / "presentation.pdf") as pdf:
        for part in parts:
            lines = [line for line in part.splitlines() if line.strip()]
            title = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), "ЛР7")
            image_line = next((line for line in lines if line.startswith("![")), "")
            bullets = [line[2:].strip() for line in lines if line.startswith("- ")]
            fig = plt.figure(figsize=(12.8, 7.2))
            fig.text(0.06, 0.90, title, fontsize=24, weight="bold", va="top")
            if image_line:
                path = image_line.split("(")[-1].split(")")[0].replace("../", "")
                ax = fig.add_axes([0.06, 0.12, 0.58, 0.68])
                ax.imshow(plt.imread(ROOT / path))
                ax.axis("off")
                x = 0.69
            else:
                x = 0.10
            y = 0.76
            for bullet in bullets:
                for line in textwrap.wrap("• " + bullet, width=42):
                    fig.text(x, y, line, fontsize=16, va="top")
                    y -= 0.06
                y -= 0.02
            pdf.savefig(fig)
            plt.close(fig)


def render_presentation_html(slides: str) -> None:
    parts = [part.strip() for part in slides.split("\n---\n") if part.strip()]
    body = []
    for part in parts:
        content = []
        for line in part.splitlines():
            if line.startswith("# "):
                content.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
            elif line.startswith("- "):
                content.append(f"<p class='bullet'>• {html.escape(line[2:].strip())}</p>")
            elif line.startswith("!["):
                path = line.split("(")[-1].split(")")[0]
                image_path = ROOT / path.replace("../", "")
                encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
                content.append(f"<img src='data:image/png;base64,{encoded}' alt='slide image'>")
            elif line.strip() and not line.startswith("---"):
                content.append(f"<p>{html.escape(line.strip())}</p>")
        body.append("<section>" + "\n".join(content) + "</section>")
    (PRESENTATION / "presentation.html").write_text(
        """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Лабораторная работа №7</title>
<style>
body { margin: 0; font-family: Arial, sans-serif; background: #f6f7f9; color: #1f2933; }
section { box-sizing: border-box; min-height: 100vh; padding: 6vh 7vw; border-bottom: 1px solid #d8dee8; }
h1 { font-size: 42px; margin: 0 0 28px; }
p { font-size: 24px; line-height: 1.35; max-width: 980px; }
.bullet { margin: 12px 0; }
img { max-width: 68vw; max-height: 62vh; display: block; margin-top: 24px; border: 1px solid #cad2df; background: white; }
</style>
</head>
<body>
""" + "\n".join(body) + "\n</body>\n</html>\n",
        encoding="utf-8",
    )


def run_pandoc() -> None:
    subprocess.run(["pandoc", "report.md", "-o", "report.docx"], cwd=REPORT, check=True)
    subprocess.run(["pandoc", "report.md", "-o", "report.html", "--standalone"], cwd=REPORT, check=True)


def main() -> None:
    REPORT.mkdir(exist_ok=True)
    PRESENTATION.mkdir(exist_ok=True)
    write_references()
    report_md = make_report_markdown()
    presentation_md = make_presentation_markdown()
    (REPORT / "report.md").write_text(report_md, encoding="utf-8")
    (PRESENTATION / "presentation.md").write_text(presentation_md, encoding="utf-8")
    render_report_pdf(report_md)
    render_presentation_pdf(presentation_md)
    render_presentation_html(presentation_md)
    run_pandoc()
    print("Rendered report and presentation")


if __name__ == "__main__":
    main()
