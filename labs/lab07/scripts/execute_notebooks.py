from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_DIR = ROOT / "generated" / "notebooks"
TMP_DIR = ROOT / "generated" / "tmp"


def notebook_to_script(path: Path) -> Path:
    data = json.loads(path.read_text(encoding="utf-8"))
    chunks: list[str] = []
    for cell in data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        chunks.append(source)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    script = TMP_DIR / f"{path.stem}_executed.jl"
    script.write_text("\n\n".join(chunks), encoding="utf-8")
    return script


def main() -> None:
    env = os.environ.copy()
    env["JULIA_DEPOT_PATH"] = f"{ROOT / '.julia_depot'}:{Path.home() / '.julia'}"
    for notebook in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        script = notebook_to_script(notebook)
        print(f"Executing notebook source: {notebook.name}")
        subprocess.run(
            ["julia", "--startup-file=no", "--project=.", str(script)],
            cwd=ROOT,
            env=env,
            check=True,
        )


if __name__ == "__main__":
    main()
