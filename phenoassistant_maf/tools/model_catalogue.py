"""Read-only typed MAF catalogue for registered PhenoAssistant vision models."""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from agent_framework import FunctionTool
from pydantic import BaseModel, ConfigDict


ModelTask = Literal[
    "instance-segmentation",
    "image-classification",
    "image-regression",
]

ModelTaskSelection = Literal[
    "all",
    "instance-segmentation",
    "image-classification",
    "image-regression",
]


class ModelCatalogueInput(BaseModel):
    """Model-controlled read-only model catalogue query."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    task: ModelTaskSelection = "all"


class ModelCheckpointEvidence(BaseModel):
    """One exact checkpoint registered in the trusted model zoo."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    checkpoint: str


class ModelTaskEvidence(BaseModel):
    """Read-only evidence for one registered computer-vision task."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    task: ModelTask
    model_count: int
    models: list[ModelCheckpointEvidence]


class ModelCatalogueResult(BaseModel):
    """Stable result envelope for model-zoo discovery."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["1"] = "1"
    tool_name: Literal["get_model_catalogue"] = "get_model_catalogue"
    arguments: ModelCatalogueInput
    task_count: int
    total_model_count: int
    tasks: list[ModelTaskEvidence]


ModelCatalogueHandler = Callable[
    [str],
    ModelCatalogueResult,
]


_APPROVED_TASKS: tuple[ModelTask, ...] = (
    "instance-segmentation",
    "image-classification",
    "image-regression",
)


def _normalise_trusted_model_zoo_path(
    model_zoo_path: str,
) -> Path:
    """Validate the application-controlled model-zoo path."""
    normalised = model_zoo_path.strip()

    if not normalised:
        raise ValueError(
            "trusted model_zoo_path must not be blank"
        )

    path = Path(normalised)

    if not path.is_file():
        raise FileNotFoundError(
            f"trusted model zoo does not exist: {path}"
        )

    return path


def _load_model_zoo(
    trusted_path: Path,
) -> dict[str, object]:
    """Load the model zoo without importing legacy vision modules."""
    registry = json.loads(
        trusted_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(registry, dict):
        raise TypeError(
            "model zoo root must be a JSON object"
        )

    actual_tasks = set(registry)
    approved_tasks = set(_APPROVED_TASKS)

    unknown_tasks = (
        actual_tasks - approved_tasks
    )

    if unknown_tasks:
        raise ValueError(
            "model zoo contains unrecognised task categories: "
            + ", ".join(sorted(unknown_tasks))
        )

    missing_tasks = (
        approved_tasks - actual_tasks
    )

    if missing_tasks:
        raise ValueError(
            "model zoo is missing required task categories: "
            + ", ".join(sorted(missing_tasks))
        )

    return registry


def _parse_task(
    task: ModelTask,
    raw: object,
) -> ModelTaskEvidence:
    """Convert one exact task registry entry into typed evidence."""
    if not isinstance(raw, list):
        raise TypeError(
            f"model-zoo task {task!r} must contain a list"
        )

    checkpoints = []

    for value in raw:
        if not isinstance(value, str):
            raise TypeError(
                f"model-zoo task {task!r} contains a non-string checkpoint"
            )

        checkpoint = value.strip()

        if not checkpoint:
            raise ValueError(
                f"model-zoo task {task!r} contains a blank checkpoint"
            )

        checkpoints.append(
            checkpoint
        )

    if len(checkpoints) != len(set(checkpoints)):
        raise ValueError(
            f"model-zoo task {task!r} contains duplicate checkpoints"
        )

    evidence = [
        ModelCheckpointEvidence(
            checkpoint=checkpoint,
        )
        for checkpoint in checkpoints
    ]

    return ModelTaskEvidence(
        task=task,
        model_count=len(evidence),
        models=evidence,
    )


def run_model_catalogue(
    model_zoo_path: str,
    task: str = "all",
) -> ModelCatalogueResult:
    """Read model evidence from a trusted model-zoo JSON file."""
    trusted_path = _normalise_trusted_model_zoo_path(
        model_zoo_path
    )

    arguments = ModelCatalogueInput(
        task=task,
    )

    registry = _load_model_zoo(
        trusted_path
    )

    tasks = []

    for approved_task in _APPROVED_TASKS:
        if (
            arguments.task != "all"
            and arguments.task != approved_task
        ):
            continue

        tasks.append(
            _parse_task(
                approved_task,
                registry[approved_task],
            )
        )

    return ModelCatalogueResult(
        arguments=arguments,
        task_count=len(tasks),
        total_model_count=sum(
            item.model_count
            for item in tasks
        ),
        tasks=tasks,
    )


def build_model_catalogue_handler(
    model_zoo_path: str,
) -> ModelCatalogueHandler:
    """Bind the trusted model-zoo path behind a one-field interface."""
    trusted_path = _normalise_trusted_model_zoo_path(
        model_zoo_path
    )

    def get_model_catalogue(
        task: str,
    ) -> ModelCatalogueResult:
        return run_model_catalogue(
            model_zoo_path=str(trusted_path),
            task=task,
        )

    if tuple(
        inspect.signature(
            get_model_catalogue
        ).parameters
    ) != ("task",):
        raise RuntimeError(
            "model catalogue handler exposes an unexpected signature"
        )

    return get_model_catalogue


def create_model_catalogue_tool(
    model_zoo_path: str,
) -> FunctionTool:
    """Expose read-only vision model discovery through MAF."""
    return FunctionTool(
        name="get_model_catalogue",
        description=(
            "Inspect registered PhenoAssistant vision-model checkpoints "
            "for instance segmentation, image classification, or image "
            "regression without loading or executing any vision model."
        ),
        func=build_model_catalogue_handler(
            model_zoo_path=model_zoo_path,
        ),
        input_model=ModelCatalogueInput,
    )
