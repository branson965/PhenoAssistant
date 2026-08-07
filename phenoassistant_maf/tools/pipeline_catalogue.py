"""Read-only typed MAF catalogue for reusable PhenoAssistant pipelines."""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agent_framework import FunctionTool
from pydantic import BaseModel, ConfigDict


PipelineFamily = Literal[
    "arabidopsis_phenotype_extraction",
    "arabidopsis_longitudinal_plotting",
    "potato_phenotype_extraction",
    "arabidopsis_statistics",
]

PipelineSelection = Literal[
    "all",
    "arabidopsis_phenotype_extraction",
    "arabidopsis_longitudinal_plotting",
    "potato_phenotype_extraction",
    "arabidopsis_statistics",
]

PipelineExecutionStatus = Literal[
    "gpu_deferred",
    "use_maf_replacement",
]


class PipelineCatalogueInput(BaseModel):
    """Model-controlled pipeline catalogue query."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    family: PipelineSelection = "all"


class PipelineArgumentEvidence(BaseModel):
    """One argument declared by a legacy pipeline registry entry."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    type_name: str
    description: str
    default: str | int | float | bool | None


class PipelineVariantEvidence(BaseModel):
    """Read-only evidence for one exact legacy pipeline variant."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    registry_key: str
    function_name: str
    description: str
    arguments: dict[str, PipelineArgumentEvidence]
    output: str


class PipelineCapabilityEvidence(BaseModel):
    """Canonical safe representation of one pipeline capability family."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    family_id: PipelineFamily
    purpose: str
    requires_gpu: bool
    execution_status: PipelineExecutionStatus
    maf_replacement: str | None
    legacy_dynamic_execution_allowed: Literal[False] = False
    variant_count: int
    legacy_variants: list[PipelineVariantEvidence]


class PipelineCatalogueResult(BaseModel):
    """Stable result envelope for read-only pipeline discovery."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["1"] = "1"
    tool_name: Literal["get_pipeline_catalogue"] = "get_pipeline_catalogue"
    arguments: PipelineCatalogueInput
    capability_count: int
    capabilities: list[PipelineCapabilityEvidence]


@dataclass(frozen=True)
class _FamilySpec:
    family_id: PipelineFamily
    registry_prefix: str
    purpose: str
    requires_gpu: bool
    execution_status: PipelineExecutionStatus
    maf_replacement: str | None


_FAMILY_SPECS = (
    _FamilySpec(
        family_id="arabidopsis_phenotype_extraction",
        registry_prefix="ara_crop_pipeline",
        purpose=(
            "Compute Arabidopsis phenotypes from instance-segmentation "
            "outputs, merge them with metadata, and save phenotype data."
        ),
        requires_gpu=True,
        execution_status="gpu_deferred",
        maf_replacement=None,
    ),
    _FamilySpec(
        family_id="arabidopsis_longitudinal_plotting",
        registry_prefix="ara_crop_plot",
        purpose=(
            "Summarise longitudinal Arabidopsis phenotypes by ecotype "
            "and time and produce mean/standard-deviation plots."
        ),
        requires_gpu=False,
        execution_status="use_maf_replacement",
        maf_replacement="plot_longitudinal_phenotypes",
    ),
    _FamilySpec(
        family_id="potato_phenotype_extraction",
        registry_prefix="potato_crop_pipeline",
        purpose=(
            "Compute potato projected leaf area from instance-segmentation "
            "outputs, merge with metadata, and save phenotype data."
        ),
        requires_gpu=True,
        execution_status="gpu_deferred",
        maf_replacement=None,
    ),
    _FamilySpec(
        family_id="arabidopsis_statistics",
        registry_prefix="ara_crop_stat",
        purpose=(
            "Perform repeated-measures mixed ANOVA and Tukey-Kramer "
            "post-hoc analysis on Arabidopsis phenotype data."
        ),
        requires_gpu=False,
        execution_status="use_maf_replacement",
        maf_replacement="analyse_repeated_measures_with_posthoc",
    ),
)


PipelineCatalogueHandler = Callable[
    [str],
    PipelineCatalogueResult,
]


def _normalise_trusted_registry_path(
    pipeline_zoo_path: str,
) -> Path:
    """Validate an application-controlled pipeline registry path."""
    normalised = pipeline_zoo_path.strip()

    if not normalised:
        raise ValueError(
            "trusted pipeline_zoo_path must not be blank"
        )

    path = Path(normalised)

    if not path.is_file():
        raise FileNotFoundError(
            f"trusted pipeline registry does not exist: {path}"
        )

    return path


def _family_for_registry_key(
    registry_key: str,
) -> _FamilySpec:
    """Resolve one exact registry key to an approved canonical family."""
    for spec in _FAMILY_SPECS:
        if (
            registry_key == spec.registry_prefix
            or registry_key.startswith(
                spec.registry_prefix + "_"
            )
        ):
            return spec

    raise ValueError(
        "unrecognised pipeline registry entry: "
        f"{registry_key}"
    )


def _load_registry(
    trusted_path: Path,
) -> dict[str, object]:
    """Load and validate the root pipeline registry structure."""
    registry = json.loads(
        trusted_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(registry, dict):
        raise TypeError(
            "pipeline registry root must be a JSON object"
        )

    return registry


def _parse_argument(
    name: str,
    raw: object,
) -> PipelineArgumentEvidence:
    """Convert one legacy registry argument into typed evidence."""
    if not isinstance(raw, dict):
        raise TypeError(
            f"pipeline argument {name!r} must be an object"
        )

    type_name = raw.get("type")
    description = raw.get("description", "")
    default = raw.get("default")

    if not isinstance(type_name, str):
        raise TypeError(
            f"pipeline argument {name!r} has invalid type metadata"
        )

    if not isinstance(description, str):
        raise TypeError(
            f"pipeline argument {name!r} has invalid description"
        )

    if default is not None and not isinstance(
        default,
        (str, int, float, bool),
    ):
        raise TypeError(
            f"pipeline argument {name!r} has unsupported default"
        )

    return PipelineArgumentEvidence(
        type_name=type_name,
        description=description,
        default=default,
    )


def _parse_variant(
    registry_key: str,
    raw: object,
) -> PipelineVariantEvidence:
    """Convert one exact registry entry without importing its Python code."""
    if not isinstance(raw, dict):
        raise TypeError(
            f"pipeline registry entry {registry_key!r} must be an object"
        )

    function_name = raw.get("function_name")
    description = raw.get("description")
    arguments = raw.get("args")
    output = raw.get("output")

    if not isinstance(function_name, str) or not function_name.strip():
        raise TypeError(
            f"pipeline {registry_key!r} has invalid function_name"
        )

    if not isinstance(description, str):
        raise TypeError(
            f"pipeline {registry_key!r} has invalid description"
        )

    if not isinstance(arguments, dict):
        raise TypeError(
            f"pipeline {registry_key!r} has invalid args"
        )

    if not isinstance(output, str):
        raise TypeError(
            f"pipeline {registry_key!r} has invalid output"
        )

    parsed_arguments = {
        str(name): _parse_argument(
            str(name),
            value,
        )
        for name, value in arguments.items()
    }

    return PipelineVariantEvidence(
        registry_key=registry_key,
        function_name=function_name,
        description=description,
        arguments=parsed_arguments,
        output=output,
    )


def run_pipeline_catalogue(
    pipeline_zoo_path: str,
    family: str = "all",
) -> PipelineCatalogueResult:
    """Read canonical pipeline capability evidence from a trusted registry."""
    trusted_path = _normalise_trusted_registry_path(
        pipeline_zoo_path
    )

    arguments = PipelineCatalogueInput(
        family=family,
    )

    registry = _load_registry(
        trusted_path
    )

    variants_by_family: dict[
        str,
        list[PipelineVariantEvidence],
    ] = {
        spec.family_id: []
        for spec in _FAMILY_SPECS
    }

    for registry_key, raw in registry.items():
        if not isinstance(registry_key, str):
            raise TypeError(
                "pipeline registry keys must be strings"
            )

        spec = _family_for_registry_key(
            registry_key
        )

        variants_by_family[
            spec.family_id
        ].append(
            _parse_variant(
                registry_key,
                raw,
            )
        )

    capabilities = []

    for spec in _FAMILY_SPECS:
        if (
            arguments.family != "all"
            and arguments.family != spec.family_id
        ):
            continue

        variants = sorted(
            variants_by_family[
                spec.family_id
            ],
            key=lambda item: item.registry_key,
        )

        if not variants:
            raise ValueError(
                "pipeline registry is missing canonical family: "
                f"{spec.family_id}"
            )

        capabilities.append(
            PipelineCapabilityEvidence(
                family_id=spec.family_id,
                purpose=spec.purpose,
                requires_gpu=spec.requires_gpu,
                execution_status=spec.execution_status,
                maf_replacement=spec.maf_replacement,
                variant_count=len(variants),
                legacy_variants=variants,
            )
        )

    return PipelineCatalogueResult(
        arguments=arguments,
        capability_count=len(capabilities),
        capabilities=capabilities,
    )


def build_pipeline_catalogue_handler(
    pipeline_zoo_path: str,
) -> PipelineCatalogueHandler:
    """Bind the trusted registry path behind a one-field read-only interface."""
    trusted_path = _normalise_trusted_registry_path(
        pipeline_zoo_path
    )

    def get_pipeline_catalogue(
        family: str,
    ) -> PipelineCatalogueResult:
        return run_pipeline_catalogue(
            pipeline_zoo_path=str(trusted_path),
            family=family,
        )

    if tuple(
        inspect.signature(
            get_pipeline_catalogue
        ).parameters
    ) != ("family",):
        raise RuntimeError(
            "pipeline catalogue handler exposes an unexpected signature"
        )

    return get_pipeline_catalogue


def create_pipeline_catalogue_tool(
    pipeline_zoo_path: str,
) -> FunctionTool:
    """Expose canonical read-only pipeline discovery through MAF."""
    return FunctionTool(
        name="get_pipeline_catalogue",
        description=(
            "Inspect canonical reusable PhenoAssistant pipeline families "
            "and their exact legacy variants without importing or "
            "executing legacy pipeline Python code."
        ),
        func=build_pipeline_catalogue_handler(
            pipeline_zoo_path=pipeline_zoo_path,
        ),
        input_model=PipelineCatalogueInput,
    )
