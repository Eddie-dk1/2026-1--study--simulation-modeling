#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAB_DIR="$ROOT_DIR/labs/lab04"
OUT_DIR="$LAB_DIR/release"
TMP_DIR="$ROOT_DIR/.tmp"

mkdir -p "$OUT_DIR" "$TMP_DIR"

REPORT_MD="$LAB_DIR/report/simulation-modeling--lab04--report.qmd"
PRES_MD="$LAB_DIR/presentation/simulation-modeling--lab04--presentation.qmd"
REPORT_DIR="$LAB_DIR/report"
PRES_DIR="$LAB_DIR/presentation"

REPORT_DOCX="$OUT_DIR/simulation-modeling--lab04--report.docx"
REPORT_PDF="$OUT_DIR/simulation-modeling--lab04--report.pdf"
PRES_HTML="$OUT_DIR/simulation-modeling--lab04--presentation.html"
PRES_PDF="$OUT_DIR/simulation-modeling--lab04--presentation.pdf"
SRC_ZIP="$OUT_DIR/simulation-modeling--lab04--sources.zip"

pandoc -f markdown "$REPORT_MD" --resource-path="$REPORT_DIR:$REPORT_DIR/image:$REPORT_DIR/_resources" -o "$REPORT_DOCX"

# Text-first PDF report generated from report.qmd with embedded illustrations.
python3 "$ROOT_DIR/tools/make_report_pdf.py" \
  --source-qmd "$REPORT_MD" \
  --image-dir "$REPORT_DIR/image" \
  --output "$REPORT_PDF" \
  --title "Отчёт ЛР4" \
  --subtitle "Агентная SIR-модель: постановка, эксперименты, результаты"

pandoc -f markdown "$PRES_MD" \
  --resource-path="$PRES_DIR:$PRES_DIR/image:$PRES_DIR/_resources" \
  -s \
  --embed-resources \
  --standalone \
  -o "$PRES_HTML"
python3 "$ROOT_DIR/tools/make_visual_pdf.py" \
  --title "Презентация ЛР4" \
  --subtitle "Ключевые слайды и визуализации экспериментов" \
  --source-dir "$PRES_DIR/image" \
  --output "$PRES_PDF" \
  --limit 14

zip -r "$SRC_ZIP" \
  labs/lab04/sources \
  labs/lab04/report/simulation-modeling--lab04--report.qmd \
  labs/lab04/presentation/simulation-modeling--lab04--presentation.qmd \
  check-list.md > /dev/null

rm -f "$TMP_DIR/report-lab4.txt" "$TMP_DIR/presentation-lab4.txt"

echo "Build completed. Artifacts in: $OUT_DIR"
ls -lh "$OUT_DIR"
