"""Structural validation for the migrated production MAF notebook."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "demo_maf.ipynb"
LEGACY_NOTEBOOK = ROOT / "demo.ipynb"


def load_notebook() -> dict:
    return json.loads(NOTEBOOK.read_text())


def code_source(notebook: dict) -> str:
    return "\n\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )


def test_migrated_notebook_is_valid_and_preserves_legacy_demo() -> None:
    assert NOTEBOOK.is_file()
    assert LEGACY_NOTEBOOK.is_file()

    notebook = load_notebook()

    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) == 8
    assert notebook["cells"][0]["cell_type"] == "markdown"

    title = "".join(notebook["cells"][0]["source"])

    assert "Microsoft Agent Framework" in title
    assert "does not rerun instance" in title


def test_all_code_cells_compile_with_top_level_await() -> None:
    notebook = load_notebook()
    code_cells = [
        cell
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    ]

    assert len(code_cells) == 7

    for index, cell in enumerate(code_cells):
        compile(
            "".join(cell.get("source", [])),
            f"demo_maf.ipynb:cell-{index}",
            "exec",
            flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
        )


def test_notebook_uses_only_production_maf_runtime() -> None:
    source = code_source(load_notebook())

    assert "from phenoassistant_maf import" in source
    assert "build_application(" in source
    assert source.count("await run_application(") == 3

    assert "data_path=str(DATA_PATH)" in source
    assert "first_plot_path=str(MANUAL_PLOT)" in source
    assert "second_plot_path=str(ALGORITHM_PLOT)" in source

    assert "from agents import" not in source
    assert "import autogen" not in source
    assert "initiate_chat" not in source


def test_notebook_covers_two_tools_without_credentials() -> None:
    notebook = load_notebook()
    source = code_source(notebook)
    all_text = json.dumps(notebook)

    assert "compare_linear_relationships" in source
    assert source.count("query_csv_statistic") >= 2
    assert "maximum operation" in source
    assert "mean operation" in source

    assert "OPENROUTER_API_KEY" in source
    assert not re.search(
        r"sk-or-v1-[A-Za-z0-9_-]{20,}",
        all_text,
    )
    assert "Bearer " not in all_text
