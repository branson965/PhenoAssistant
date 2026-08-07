"""Static migration-contract tests for case3_maf.ipynb."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

NOTEBOOK = ROOT / "case3_maf.ipynb"
ORIGINAL = ROOT / "case3.ipynb"


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


def test_case3_maf_notebook_exists_and_is_valid() -> None:
    document = json.loads(
        NOTEBOOK.read_text(
            encoding="utf-8",
        )
    )

    assert document["nbformat"] == 4
    assert len(document["cells"]) == 9


def test_original_case3_notebook_is_preserved() -> None:
    assert ORIGINAL.is_file()

    source = notebook_source()

    assert "case3.ipynb" in source
    assert "from agents import" not in source


def test_current_repository_checkpoint_truth_is_preserved() -> None:
    source = notebook_source()

    assert (
        "winter-wheat_nutri-defi-identify_dndww20_dino2b_lora"
        in source
    )

    assert "post-training state" in source


def test_model_discovery_uses_bounded_tool_once() -> None:
    source = notebook_source()

    assert "get_model_catalogue exactly once" in source
    assert "image-classification" in source


def test_training_readiness_is_explicitly_non_mutating() -> None:
    source = notebook_source()

    assert "assess_case3_readiness exactly once for training" in source
    assert "Do not train, upload data, load a model" in source
    assert "lora" in source
    assert "fullft" in source


def test_inference_readiness_is_explicitly_non_executing() -> None:
    source = notebook_source()

    assert "assess_case3_readiness exactly once for inference" in source
    assert "Do not load the checkpoint or run inference" in source


def test_notebook_uses_case3_production_profile() -> None:
    source = notebook_source()

    assert "model_zoo_path=str(MODEL_ZOO)" in source
    assert "case3_dataset_path=str(CASE3_DATASET)" in source
    assert "case1_data_path=" not in source
    assert "pipeline_zoo_path=" not in source
