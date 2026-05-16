from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DELIVERABLES = ROOT / "deliverables"


FILES = {
    ROOT / "report" / "report.md": "simulation-modeling--lab07--report.md",
    ROOT / "report" / "report.docx": "simulation-modeling--lab07--report.docx",
    ROOT / "report" / "report.pdf": "simulation-modeling--lab07--report.pdf",
    ROOT / "presentation" / "presentation.md": "simulation-modeling--lab07--presentation.md",
    ROOT / "presentation" / "presentation.html": "simulation-modeling--lab07--presentation.html",
    ROOT / "presentation" / "presentation.pdf": "simulation-modeling--lab07--presentation.pdf",
}


SOURCE_DIRS = ["src", "scripts", "generated", "data", "plots", "report", "presentation"]
SOURCE_FILES = ["Project.toml", "Manifest.toml", "README.md", "CHANGELOG.md", "check-list.md", "lab07.pdf"]


def copy_release_files() -> None:
    DELIVERABLES.mkdir(exist_ok=True)
    for src, name in FILES.items():
        shutil.copy2(src, DELIVERABLES / name)


def build_sources_zip() -> None:
    zip_path = DELIVERABLES / "simulation-modeling--lab07--sources.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for directory in SOURCE_DIRS:
            root_dir = ROOT / directory
            for path in root_dir.rglob("*"):
                if path.is_file() and "deliverables" not in path.parts:
                    zf.write(path, path.relative_to(ROOT))
        for name in SOURCE_FILES:
            path = ROOT / name
            if path.exists():
                zf.write(path, path.relative_to(ROOT))


def write_submission_template() -> None:
    (DELIVERABLES / "submission-response-template.md").write_text(
        """## Скринкасты

- [Rutube](TODO)
    - [Выполнение лабораторной работы](TODO)
    - [Подготовка отчёта](TODO)
    - [Подготовка презентации](TODO)
    - [Защита лабораторной работы](TODO)

- [VKvideo](TODO)
    - [Выполнение лабораторной работы](TODO)
    - [Подготовка отчёта](TODO)
    - [Подготовка презентации](TODO)
    - [Защита лабораторной работы](TODO)

## Репозитории

- [github](https://github.com/Eddie-dk1/2026-1--study--simulation-modeling)
    - [Релиз lab07](https://github.com/Eddie-dk1/2026-1--study--simulation-modeling/releases/tag/lab07)
- [gitverse](https://gitverse.ru/Kenan/2026-1--study--simulation-modeling)
    - [Релиз lab07](https://gitverse.ru/Kenan/2026-1--study--simulation-modeling/releases/tag/lab07)
""",
        encoding="utf-8",
    )


def write_release_notes() -> None:
    (DELIVERABLES / "release-notes-lab07.md").write_text(
        """# lab07

Лабораторная работа №7 по дискретно-событийному моделированию.

## Состав релиза

- отчёт: Markdown, DOCX, PDF;
- презентация: Markdown, HTML, PDF;
- архив исходных материалов Markdown, Julia-кода, CSV-таблиц и графиков;
- literate-производные: clean, md, ipynb, qmd.

## Проверка

- `scripts/mmc_literate.jl`;
- `scripts/ross_literate.jl`;
- `scripts/params_literate.jl`;
- `scripts/generate_literate.jl`;
- `scripts/execute_notebooks.py`;
- `scripts/render_documents.py`.
""",
        encoding="utf-8",
    )


def main() -> None:
    copy_release_files()
    build_sources_zip()
    write_submission_template()
    write_release_notes()
    print(f"Built deliverables in {DELIVERABLES}")


if __name__ == "__main__":
    main()
