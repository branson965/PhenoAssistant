"""Tests for safe read-only MAF model-zoo discovery."""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from phenoassistant_maf.tools.model_catalogue import (
    ModelCatalogueInput,
    build_model_catalogue_handler,
    create_model_catalogue_tool,
    run_model_catalogue,
)


ROOT = Path(__file__).resolve().parents[2]
MODEL_ZOO = ROOT / "model_zoo.json"

WINTER_WHEAT_MODEL = (
    "fengchen025/"
    "winter-wheat_nutri-defi-identify_dndww20_dino2b_lora"
)


def test_real_model_zoo_is_read_without_loading_models() -> None:
    result = run_model_catalogue(
        str(MODEL_ZOO),
    )

    assert result.schema_version == "1"
    assert result.tool_name == "get_model_catalogue"
    assert result.arguments.task == "all"

    assert result.task_count == 3
    assert result.total_model_count == 3

    by_task = {
        item.task: item
        for item in result.tasks
    }

    assert set(by_task) == {
        "instance-segmentation",
        "image-classification",
        "image-regression",
    }

    assert (
        by_task["instance-segmentation"].model_count
        == 2
    )

    assert (
        by_task["image-classification"].model_count
        == 1
    )

    assert (
        by_task["image-regression"].model_count
        == 0
    )

    classification_models = [
        item.checkpoint
        for item in by_task[
            "image-classification"
        ].models
    ]

    assert classification_models == [
        WINTER_WHEAT_MODEL
    ]


def test_image_classification_filter_returns_case3_model() -> None:
    result = run_model_catalogue(
        str(MODEL_ZOO),
        task="image-classification",
    )

    assert result.task_count == 1
    assert result.total_model_count == 1

    task = result.tasks[0]

    assert task.task == "image-classification"
    assert task.model_count == 1
    assert (
        task.models[0].checkpoint
        == WINTER_WHEAT_MODEL
    )


def test_model_catalogue_input_rejects_unknown_task() -> None:
    with pytest.raises(ValidationError):
        ModelCatalogueInput(
            task="arbitrary-task",
        )


def test_unknown_registry_task_fails_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "model_zoo.json"

    path.write_text(
        json.dumps(
            {
                "instance-segmentation": [],
                "image-classification": [],
                "image-regression": [],
                "unknown-task": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="unrecognised task categories",
    ):
        run_model_catalogue(
            str(path),
        )


def test_handler_exposes_only_task_not_model_zoo_path() -> None:
    handler = build_model_catalogue_handler(
        str(MODEL_ZOO)
    )

    assert tuple(
        inspect.signature(handler).parameters
    ) == ("task",)

    result = handler(
        "image-classification"
    )

    assert result.task_count == 1
    assert result.total_model_count == 1


def test_function_tool_has_read_only_contract() -> None:
    tool = create_model_catalogue_tool(
        str(MODEL_ZOO)
    )

    assert tool.name == "get_model_catalogue"

    schema = ModelCatalogueInput.model_json_schema()

    assert set(
        schema["properties"]
    ) == {"task"}

    serialised = json.dumps(
        schema
    )

    assert "model_zoo_path" not in serialised
    assert "checkpoint" not in schema["properties"]


def test_catalogue_import_does_not_load_vision_stack() -> None:
    forbidden = (
        "functions.image_classification",
        "functions.create_hf_dataset",
        "functions.generic_tools",
        "transformers",
        "torch",
    )

    for name in forbidden:
        assert name not in sys.modules
