"""Structural regression test for the migrated Case 1 MAF notebook."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "case1_maf.ipynb"


def test_case1_maf_notebook_is_valid_and_cpu_scoped() -> None:
    assert NOTEBOOK.is_file()

    notebook = json.loads(NOTEBOOK.read_text())

    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) == 10

    sources = [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
    ]
    full_source = "\n".join(sources)

    assert "autogen" not in full_source
    assert "user_proxy" not in full_source
    assert "initiate_chat" not in full_source
    assert "extracted_pipelines" in full_source
    assert "aracrop_phenotypes.csv" in full_source
    assert "case1_data_path=str(CASE1_DATA)" in full_source
    assert "case1_output_dir=str(OUTPUT_DIR)" in full_source

    assert full_source.count("await run_application(") == 3

    for tool_name in (
        "plot_longitudinal_phenotypes",
        "rank_ecotypes_by_phenotype",
        "analyse_repeated_measures_with_posthoc",
    ):
        assert tool_name in full_source

    assert "GPU" in full_source
    assert "RAG" in full_source
    assert "results/maf_case1" in full_source

    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue

        assert cell.get("execution_count") is None
        assert cell.get("outputs") == []

        source = "".join(cell.get("source", []))
        compile(
            source,
            str(NOTEBOOK),
            "exec",
            flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
        )


def test_case1_maf_notebook_preserves_three_migrated_tasks() -> None:
    notebook = json.loads(NOTEBOOK.read_text())
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )

    assert (
        'plot_longitudinal_phenotypes exactly once'
        in code
    )
    assert (
        'rank_ecotypes_by_phenotype\n'
        '    exactly once'
        in code
    )
    assert (
        'analyse_repeated_measures_with_posthoc exactly once'
        in code
    )

    for expected_name in (
        "leaf_count_plot.png",
        "pla_plot.png",
        "plant_diameter_plot.png",
        "plant_perimeter_plot.png",
    ):
        assert expected_name in code
