"""Tests for the CPU-safe Case 3 readiness boundary."""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from phenoassistant_maf.tools.case3_readiness import (
    CASE3_EXPECTED_CHECKPOINT,
    Case3ReadinessInput,
    build_case3_readiness_handler,
    create_case3_readiness_tool,
    run_case3_readiness,
)


ROOT = Path(__file__).resolve().parents[2]

MODEL_ZOO = ROOT / "model_zoo.json"

MISSING_CASE3_DATASET = (
    ROOT
    / "data"
    / "winter-wheat_nutri-defi-identify_dndww20"
)


def test_current_repository_training_readiness_stops_at_missing_dataset() -> None:
    result = run_case3_readiness(
        model_zoo_path=str(MODEL_ZOO),
        dataset_path=str(MISSING_CASE3_DATASET),
        operation="training",
    )

    assert result.schema_version == "1"
    assert result.tool_name == "assess_case3_readiness"

    assert result.arguments.operation == "training"

    assert result.checkpoint_registered is True
    assert result.registered_classification_model_count == 1

    assert result.dataset.root_exists is False
    assert result.dataset.ready_for_prepare_dataset is False

    assert result.operation_preconditions_satisfied is False

    assert result.requires_gpu is True
    assert result.execution_status == "gpu_deferred"
    assert result.execution_allowed_in_cpu_phase is False

    assert (
        "local Case 3 dataset directory is missing"
        in result.blockers
    )

    assert any(
        "GPU execution is deferred"
        in blocker
        for blocker in result.blockers
    )


def test_current_repository_inference_has_registered_case3_model() -> None:
    result = run_case3_readiness(
        model_zoo_path=str(MODEL_ZOO),
        dataset_path=str(MISSING_CASE3_DATASET),
        operation="inference",
    )

    assert result.checkpoint_registered is True

    assert (
        result.expected_checkpoint
        == CASE3_EXPECTED_CHECKPOINT
    )

    assert result.operation_preconditions_satisfied is True

    assert result.execution_status == "gpu_deferred"
    assert result.execution_allowed_in_cpu_phase is False

    assert (
        result.blockers
        == [
            "GPU execution is deferred until the canonical "
            "Nottingham GPU environment is available"
        ]
    )


def test_training_contract_matches_audited_legacy_defaults() -> None:
    result = run_case3_readiness(
        model_zoo_path=str(MODEL_ZOO),
        dataset_path=str(MISSING_CASE3_DATASET),
        operation="training",
    )

    contract = result.training_contract

    assert contract.model_zoo_task == "image-classification"
    assert contract.dataset_prepare_task == "classification"

    assert contract.pretrained_model == "facebook/dinov2-base"

    assert contract.supported_finetuning_methods == [
        "lora",
        "fullft",
    ]

    assert contract.default_finetuning_method == "lora"
    assert contract.default_train_batch_size == 32
    assert contract.default_validation_batch_size == 1
    assert contract.default_image_width == 512
    assert contract.default_image_height == 512
    assert contract.default_learning_rate == 1e-4
    assert contract.default_epochs == 1

    assert contract.required_environment_variables == [
        "HF_USER",
        "HF_TOKEN",
    ]

    assert contract.credentials_checked is False


def test_complete_local_training_layout_is_recognised(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "case3"
    train = dataset / "train"

    train.mkdir(
        parents=True
    )

    (train / "metadata.csv").write_text(
        "file_name,label\nimage.png,N\n",
        encoding="utf-8",
    )

    (dataset / "label2id.json").write_text(
        json.dumps(
            {
                "N": 0,
            }
        ),
        encoding="utf-8",
    )

    result = run_case3_readiness(
        model_zoo_path=str(MODEL_ZOO),
        dataset_path=str(dataset),
        operation="training",
    )

    assert result.dataset.root_exists is True
    assert result.dataset.train_directory_exists is True
    assert result.dataset.train_metadata_exists is True
    assert result.dataset.label2id_exists is True

    assert result.dataset.test_directory_exists is False
    assert result.dataset.test_metadata_exists is None

    assert result.dataset.ready_for_prepare_dataset is True
    assert result.operation_preconditions_satisfied is True

    assert result.blockers == [
        "GPU execution is deferred until the canonical "
        "Nottingham GPU environment is available"
    ]


def test_test_directory_requires_test_metadata(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "case3"

    (dataset / "train").mkdir(
        parents=True
    )

    (dataset / "train" / "metadata.csv").write_text(
        "file_name,label\nimage.png,N\n",
        encoding="utf-8",
    )

    (dataset / "label2id.json").write_text(
        '{"N": 0}',
        encoding="utf-8",
    )

    (dataset / "test").mkdir()

    result = run_case3_readiness(
        model_zoo_path=str(MODEL_ZOO),
        dataset_path=str(dataset),
        operation="training",
    )

    assert result.dataset.test_directory_exists is True
    assert result.dataset.test_metadata_exists is False
    assert result.dataset.ready_for_prepare_dataset is False

    assert result.operation_preconditions_satisfied is False

    assert any(
        "does not satisfy"
        in blocker
        for blocker in result.blockers
    )


def test_case3_readiness_input_rejects_unknown_operation() -> None:
    with pytest.raises(ValidationError):
        Case3ReadinessInput(
            operation="arbitrary-operation",
        )


def test_handler_exposes_only_operation() -> None:
    handler = build_case3_readiness_handler(
        model_zoo_path=str(MODEL_ZOO),
        dataset_path=str(MISSING_CASE3_DATASET),
    )

    assert tuple(
        inspect.signature(handler).parameters
    ) == ("operation",)

    result = handler(
        "inference"
    )

    assert result.arguments.operation == "inference"


def test_function_tool_hides_paths_and_checkpoint_selection() -> None:
    tool = create_case3_readiness_tool(
        model_zoo_path=str(MODEL_ZOO),
        dataset_path=str(MISSING_CASE3_DATASET),
    )

    assert tool.name == "assess_case3_readiness"

    schema = Case3ReadinessInput.model_json_schema()

    assert set(
        schema["properties"]
    ) == {"operation"}

    serialised = json.dumps(
        schema
    )

    assert "model_zoo_path" not in serialised
    assert "dataset_path" not in serialised
    assert "checkpoint" not in schema["properties"]


def test_case3_readiness_import_does_not_load_vision_stack() -> None:
    for name in (
        "functions.image_classification",
        "functions.create_hf_dataset",
        "functions.generic_tools",
        "transformers",
        "torch",
    ):
        assert name not in sys.modules
