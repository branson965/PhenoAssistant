"""Static migration-contract tests for case2_maf.ipynb."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

NOTEBOOK = ROOT / "case2_maf.ipynb"
ORIGINAL = ROOT / "case2.ipynb"


def notebook_source() -> str:
    document = json.loads(
        NOTEBOOK.read_text(
            encoding="utf-8",
        )
    )

    return "\n".join(
        "".join(
            cell.get(
                "source",
                [],
            )
        )
        for cell in document["cells"]
    )


def test_case2_maf_notebook_exists_and_is_valid() -> None:
    document = json.loads(
        NOTEBOOK.read_text(
            encoding="utf-8",
        )
    )

    assert document["nbformat"] == 4
    assert len(document["cells"]) == 7


def test_original_case2_notebook_is_preserved() -> None:
    assert ORIGINAL.is_file()

    source = notebook_source()

    assert "case2.ipynb" in source
    assert "from agents import" not in source


def test_notebook_resumes_from_tracked_case2_artifact() -> None:
    source = notebook_source()

    assert (
        "results/Case2/potato_phenotypes.csv"
        in source
    )

    assert (
        "MAF does not claim to have regenerated it"
        in source
    )


def test_task1_gpu_boundary_is_explicit() -> None:
    source = notebook_source()

    assert "GPU-deferred boundary" in source
    assert "Nottingham GPU environment" in source


def test_task2_uses_exactly_one_production_comparison_request() -> None:
    source = notebook_source()

    assert source.count(
        "await run_application("
    ) == 1

    assert (
        "compare_linear_relationships exactly once"
        in source
    )

    assert "manual_leaf_area" in source
    assert "projected_leaf_area" in source
    assert "manual_dried_weight" in source


def test_notebook_writes_new_maf_outputs_not_legacy_plots() -> None:
    source = notebook_source()

    assert 'OUTPUT_DIR = ROOT / "results/maf_case2"' in source

    assert (
        'MANUAL_PLOT = OUTPUT_DIR / "potato_manual.png"'
        in source
    )

    assert (
        'ALGORITHM_PLOT = OUTPUT_DIR / "potato_algorithm.png"'
        in source
    )


def test_notebook_uses_base_profile_only() -> None:
    source = notebook_source()

    assert "case1_data_path=" not in source
    assert "model_zoo_path=" not in source
    assert "pipeline_zoo_path=" not in source
