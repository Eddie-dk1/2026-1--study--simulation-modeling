# Лабораторная работа 7

Дискретно-событийное моделирование:

- модель массового обслуживания `M/M/c`;
- модель Росса с резервом, ремонтом и несколькими ремонтниками;
- аналитическое сравнение, мониторинг очередей и загрузки ремонтников;
- literate-исходники, чистый Julia-код, notebook и Quarto-документация;
- отчёт и презентация в требуемых форматах.

## Воспроизведение

```bash
JULIA_DEPOT_PATH="$PWD/.julia_depot:$HOME/.julia" julia --project=. -e 'import Pkg; Pkg.instantiate()'
JULIA_DEPOT_PATH="$PWD/.julia_depot:$HOME/.julia" julia --project=. scripts/mmc_literate.jl
JULIA_DEPOT_PATH="$PWD/.julia_depot:$HOME/.julia" julia --project=. scripts/ross_literate.jl
JULIA_DEPOT_PATH="$PWD/.julia_depot:$HOME/.julia" julia --project=. scripts/params_literate.jl
JULIA_DEPOT_PATH="$PWD/.julia_depot:$HOME/.julia" julia --project=. scripts/generate_literate.jl
python3 scripts/plot_results.py
python3 scripts/render_documents.py
python3 scripts/build_deliverables.py
```

Итоговые файлы для публикации находятся в `deliverables/`.
