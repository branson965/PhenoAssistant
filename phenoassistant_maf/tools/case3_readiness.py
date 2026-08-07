"""CPU-safe readiness contract for the PhenoAssistant Case 3 workflow."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from agent_framework import FunctionTool
from pydantic import BaseModel, ConfigDict

from phenoassistant_maf.tools.model_catalogue import (
    run_model_catalogue,
)


Case3Operation = Literal[
    "inference",
    "training",
]

Case3ExecutionStatus = Literal[
    "gpu_deferred",
]


CASE3_DATASET_NAME = (
    "winter-wheat_nutri-defi-identify_dndww20"
)

CASE3_EXPECTED_CHECKPOINT = (
    "fengchen025/"
    "winter-wheat_nutri-defi-identify_dndww20_dino2b_lora"
)


class Case3ReadinessInput(BaseModel):
    """Model-controlled Case 3 readiness query."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    operation: Case3Operation


class DatasetStructureEvidence(BaseModel):
    """Filesystem evidence for the audited legacy training-data contract."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    dataset_name: str
    root_exists: bool
    train_directory_exists: bool
    train_metadata_exists: bool
    label2id_exists: bool
    test_directory_exists: bool
    test_metadata_exists: bool | None
    ready_for_prepare_dataset: bool
    required_layout: list[str]
    optional_test_rule: str


class LegacyTrainingContractEvidence(BaseModel):
    """Audited non-executing contract of the legacy training workflow."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    model_zoo_task: Literal["image-classification"]
    dataset_prepare_task: Literal["classification"]
    pretrained_model: str
    supported_finetuning_methods: list[
        Literal["lora", "fullft"]
    ]
    default_finetuning_method: Literal["lora"]
    default_train_batch_size: int
    default_validation_batch_size: int
    default_image_width: int
    default_image_height: int
    default_learning_rate: float
    default_epochs: int
    required_environment_variables: list[str]
    credentials_checked: Literal[False] = False


class Case3ReadinessResult(BaseModel):
    """Stable evidence envelope for the Case 3 CPU/GPU boundary."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["1"] = "1"
    tool_name: Literal[
        "assess_case3_readiness"
    ] = "assess_case3_readiness"

    arguments: Case3ReadinessInput

    target_dataset: str
    expected_checkpoint: str
    checkpoint_registered: bool
    registered_classification_model_count: int

    dataset: DatasetStructureEvidence
    training_contract: LegacyTrainingContractEvidence

    operation_preconditions_satisfied: bool

    requires_gpu: Literal[True] = True
    execution_status: Case3ExecutionStatus = "gpu_deferred"
    execution_allowed_in_cpu_phase: Literal[False] = False

    blockers: list[str]
    scope_notes: list[str]


Case3ReadinessHandler = Callable[
    [str],
    Case3ReadinessResult,
]


def _normalise_trusted_path(
    value: str,
    *,
    label: str,
) -> Path:
    """Normalise an application-controlled filesystem path."""
    normalised = value.strip()

    if not normalised:
        raise ValueError(
            f"trusted {label} must not be blank"
        )

    return Path(normalised)


def _inspect_dataset(
    dataset_path: Path,
) -> DatasetStructureEvidence:
    """Inspect only the filesystem contract used by prepare_dataset."""
    root_exists = dataset_path.is_dir()

    train_directory = (
        dataset_path / "train"
    )
    train_metadata = (
        train_directory / "metadata.csv"
    )
    label2id = (
        dataset_path / "label2id.json"
    )

    test_directory = (
        dataset_path / "test"
    )
    test_metadata = (
        test_directory / "metadata.csv"
    )

    train_directory_exists = (
        train_directory.is_dir()
    )
    train_metadata_exists = (
        train_metadata.is_file()
    )
    label2id_exists = (
        label2id.is_file()
    )

    test_directory_exists = (
        test_directory.is_dir()
    )

    test_metadata_exists = (
        test_metadata.is_file()
        if test_directory_exists
        else None
    )

    ready = (
        root_exists
        and train_directory_exists
        and train_metadata_exists
        and label2id_exists
        and (
            not test_directory_exists
            or test_metadata_exists is True
        )
    )

    return DatasetStructureEvidence(
        dataset_name=CASE3_DATASET_NAME,
        root_exists=root_exists,
        train_directory_exists=train_directory_exists,
        train_metadata_exists=train_metadata_exists,
        label2id_exists=label2id_exists,
        test_directory_exists=test_directory_exists,
        test_metadata_exists=test_metadata_exists,
        ready_for_prepare_dataset=ready,
        required_layout=[
            "train/",
            "train/metadata.csv",
            "label2id.json",
        ],
        optional_test_rule=(
            "If test/ exists, test/metadata.csv must also exist."
        ),
    )


def _training_contract() -> LegacyTrainingContractEvidence:
    """Return the audited defaults without importing the training stack."""
    return LegacyTrainingContractEvidence(
        model_zoo_task="image-classification",
        dataset_prepare_task="classification",
        pretrained_model="facebook/dinov2-base",
        supported_finetuning_methods=[
            "lora",
            "fullft",
        ],
        default_finetuning_method="lora",
        default_train_batch_size=32,
        default_validation_batch_size=1,
        default_image_width=512,
        default_image_height=512,
        default_learning_rate=1e-4,
        default_epochs=1,
        required_environment_variables=[
            "HF_USER",
            "HF_TOKEN",
        ],
    )


def run_case3_readiness(
    *,
    model_zoo_path: str,
    dataset_path: str,
    operation: str,
) -> Case3ReadinessResult:
    """Assess Case 3 without importing or executing vision functionality."""
    model_path = _normalise_trusted_path(
        model_zoo_path,
        label="model_zoo_path",
    )

    dataset_root = _normalise_trusted_path(
        dataset_path,
        label="dataset_path",
    )

    arguments = Case3ReadinessInput(
        operation=operation,
    )

    catalogue = run_model_catalogue(
        model_zoo_path=str(model_path),
        task="image-classification",
    )

    classification = catalogue.tasks[0]

    registered_checkpoints = [
        model.checkpoint
        for model in classification.models
    ]

    checkpoint_registered = (
        CASE3_EXPECTED_CHECKPOINT
        in registered_checkpoints
    )

    dataset = _inspect_dataset(
        dataset_root
    )

    blockers = []
    scope_notes = []

    if arguments.operation == "inference":
        operation_preconditions_satisfied = (
            checkpoint_registered
        )

        if not checkpoint_registered:
            blockers.append(
                "expected Case 3 classifier is not registered"
            )

        scope_notes.append(
            "Input images are not inspected by this CPU readiness tool."
        )

    else:
        operation_preconditions_satisfied = (
            dataset.ready_for_prepare_dataset
        )

        if not dataset.root_exists:
            blockers.append(
                "local Case 3 dataset directory is missing"
            )
        elif not dataset.ready_for_prepare_dataset:
            blockers.append(
                "local Case 3 dataset does not satisfy the "
                "audited preparation layout"
            )

        scope_notes.append(
            "HF_USER and HF_TOKEN are required by the legacy "
            "Hugging Face training workflow but their values are "
            "not inspected or exposed."
        )

    blockers.append(
        "GPU execution is deferred until the canonical "
        "Nottingham GPU environment is available"
    )

    scope_notes.append(
        "No model is loaded and no training, inference, dataset "
        "upload, or Hugging Face mutation is performed."
    )

    return Case3ReadinessResult(
        arguments=arguments,
        target_dataset=CASE3_DATASET_NAME,
        expected_checkpoint=CASE3_EXPECTED_CHECKPOINT,
        checkpoint_registered=checkpoint_registered,
        registered_classification_model_count=(
            classification.model_count
        ),
        dataset=dataset,
        training_contract=_training_contract(),
        operation_preconditions_satisfied=(
            operation_preconditions_satisfied
        ),
        blockers=blockers,
        scope_notes=scope_notes,
    )


def build_case3_readiness_handler(
    *,
    model_zoo_path: str,
    dataset_path: str,
) -> Case3ReadinessHandler:
    """Bind trusted repository paths behind a one-field MAF interface."""
    trusted_model_zoo = _normalise_trusted_path(
        model_zoo_path,
        label="model_zoo_path",
    )

    if not trusted_model_zoo.is_file():
        raise FileNotFoundError(
            "trusted model zoo does not exist: "
            f"{trusted_model_zoo}"
        )

    trusted_dataset = _normalise_trusted_path(
        dataset_path,
        label="dataset_path",
    )

    def assess_case3_readiness(
        operation: str,
    ) -> Case3ReadinessResult:
        return run_case3_readiness(
            model_zoo_path=str(trusted_model_zoo),
            dataset_path=str(trusted_dataset),
            operation=operation,
        )

    if tuple(
        inspect.signature(
            assess_case3_readiness
        ).parameters
    ) != ("operation",):
        raise RuntimeError(
            "Case 3 readiness handler exposes an unexpected signature"
        )

    return assess_case3_readiness


def create_case3_readiness_tool(
    *,
    model_zoo_path: str,
    dataset_path: str,
) -> FunctionTool:
    """Expose bounded Case 3 readiness evidence through MAF."""
    return FunctionTool(
        name="assess_case3_readiness",
        description=(
            "Assess whether the PhenoAssistant winter-wheat Case 3 "
            "image-classification workflow is ready for inference or "
            "training, including registered-model and local-dataset "
            "preconditions, without loading a model or executing GPU work."
        ),
        func=build_case3_readiness_handler(
            model_zoo_path=model_zoo_path,
            dataset_path=dataset_path,
        ),
        input_model=Case3ReadinessInput,
    )
