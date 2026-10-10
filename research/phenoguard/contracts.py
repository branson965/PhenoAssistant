"""Typed scientific-applicability contracts for Phase 7.

These models encode the research primitive described in
docs/research/SCIENTIFIC_APPLICABILITY_PAPER_PLAN.md. They do not claim that
the operating-envelope method is empirically effective; they provide the frozen,
machine-readable substrate required to test that claim.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ContextField = Literal[
    "species",
    "modality",
    "view",
    "environment",
]

MetadataScalar = str | int | float | bool


class ConstraintSeverity(StrEnum):
    """Whether one applicability mismatch is execution-blocking."""

    HARD = "hard"
    SOFT = "soft"


class ApplicabilityDecision(StrEnum):
    """System-level decisions allowed by the research method."""

    EXECUTE = "EXECUTE"
    RESELECT = "RESELECT"
    CLARIFY = "CLARIFY"
    ABSTAIN = "ABSTAIN"
    RECOMMEND_TRAINING = "RECOMMEND_TRAINING"


def _strip_nonblank(value: str, label: str) -> str:
    stripped = value.strip()

    if not stripped:
        raise ValueError(f"{label} must not be blank")

    return stripped


def _normalise_string_tuple(
    values: tuple[str, ...],
    *,
    label: str,
    allow_empty: bool,
) -> tuple[str, ...]:
    cleaned = tuple(
        _strip_nonblank(value, label)
        for value in values
    )

    if not allow_empty and not cleaned:
        raise ValueError(f"{label} must contain at least one value")

    keys = tuple(value.casefold() for value in cleaned)

    if len(keys) != len(set(keys)):
        raise ValueError(f"{label} must not contain duplicates")

    return cleaned


class ApplicabilityConstraint(BaseModel):
    """One machine-readable condition inside an operating envelope."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    field: ContextField
    allowed_values: tuple[str, ...]
    severity: ConstraintSeverity
    rationale: str

    @field_validator("allowed_values")
    @classmethod
    def validate_allowed_values(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        return _normalise_string_tuple(
            values,
            label="allowed_values",
            allow_empty=False,
        )

    @field_validator("rationale")
    @classmethod
    def validate_rationale(
        cls,
        value: str,
    ) -> str:
        return _strip_nonblank(
            value,
            "rationale",
        )


class ScientificOperatingEnvelope(BaseModel):
    """Machine-readable applicability metadata for one scientific capability."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["0.1"] = "0.1"
    capability_id: str
    scientific_task: str
    constraints: tuple[ApplicabilityConstraint, ...]
    required_context_fields: tuple[ContextField, ...] = ()
    required_metadata_keys: tuple[str, ...] = ()
    output_semantics: str
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    known_failure_conditions: tuple[str, ...] = ()
    provenance: str
    version_or_checkpoint: str

    @field_validator(
        "capability_id",
        "scientific_task",
        "output_semantics",
        "provenance",
        "version_or_checkpoint",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        return _strip_nonblank(
            value,
            "required text",
        )

    @field_validator(
        "required_metadata_keys",
        "assumptions",
        "limitations",
        "known_failure_conditions",
    )
    @classmethod
    def validate_optional_text_tuples(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        return _normalise_string_tuple(
            values,
            label="text tuple",
            allow_empty=True,
        )

    @model_validator(mode="after")
    def validate_unique_fields(
        self,
    ) -> "ScientificOperatingEnvelope":
        constraint_fields = [
            constraint.field
            for constraint in self.constraints
        ]

        if len(constraint_fields) != len(set(constraint_fields)):
            raise ValueError(
                "constraints must contain at most one entry per context field"
            )

        required_fields = list(self.required_context_fields)

        if len(required_fields) != len(set(required_fields)):
            raise ValueError(
                "required_context_fields must not contain duplicates"
            )

        metadata_keys = [
            key.casefold()
            for key in self.required_metadata_keys
        ]

        if len(metadata_keys) != len(set(metadata_keys)):
            raise ValueError(
                "required_metadata_keys must not contain duplicates"
            )

        return self


class ScientificRequestContext(BaseModel):
    """Observed scientific conditions for one proposed tool execution."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    scientific_task: str
    species: str | None = None
    modality: str | None = None
    view: str | None = None
    environment: str | None = None
    metadata: dict[str, MetadataScalar] = Field(
        default_factory=dict,
    )

    @field_validator("scientific_task")
    @classmethod
    def validate_task(
        cls,
        value: str,
    ) -> str:
        return _strip_nonblank(
            value,
            "scientific_task",
        )

    @field_validator(
        "species",
        "modality",
        "view",
        "environment",
    )
    @classmethod
    def validate_optional_context(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return _strip_nonblank(
            value,
            "context value",
        )

    @field_validator("metadata")
    @classmethod
    def validate_metadata(
        cls,
        value: dict[str, MetadataScalar],
    ) -> dict[str, MetadataScalar]:
        cleaned: dict[str, MetadataScalar] = {}

        for key, item in value.items():
            normalised_key = _strip_nonblank(
                key,
                "metadata key",
            )

            if normalised_key.casefold() in {
                existing.casefold()
                for existing in cleaned
            }:
                raise ValueError(
                    "metadata keys must be unique case-insensitively"
                )

            if isinstance(item, str):
                item = _strip_nonblank(
                    item,
                    "metadata value",
                )

            cleaned[normalised_key] = item

        return cleaned


class ConstraintEvaluation(BaseModel):
    """Deterministic evidence for one operating-envelope constraint."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    field: ContextField
    severity: ConstraintSeverity
    observed_value: str | None
    allowed_values: tuple[str, ...]
    matched: bool | None
    rationale: str


class ScientificApplicabilityAssessment(BaseModel):
    """Structured pre-execution applicability decision and evidence."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["0.1"] = "0.1"
    capability_id: str
    decision: ApplicabilityDecision
    safe_to_execute: bool
    task_match: bool
    missing_context_fields: tuple[ContextField, ...]
    missing_metadata_keys: tuple[str, ...]
    hard_violations: tuple[ConstraintEvaluation, ...]
    soft_warnings: tuple[ConstraintEvaluation, ...]
    evaluations: tuple[ConstraintEvaluation, ...]


class CatalogueApplicabilityResolution(BaseModel):
    """Structured resolution across a catalogue of scientific capabilities."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["0.1"] = "0.1"
    decision: ApplicabilityDecision
    requested_capability_id: str | None = None
    selected_capability_id: str | None = None
    executable_capability_ids: tuple[str, ...]
    assessments: tuple[ScientificApplicabilityAssessment, ...]

    @model_validator(mode="after")
    def validate_resolution(
        self,
    ) -> "CatalogueApplicabilityResolution":
        actionable = {
            ApplicabilityDecision.EXECUTE,
            ApplicabilityDecision.RESELECT,
        }

        if self.decision in actionable:
            if self.selected_capability_id is None:
                raise ValueError(
                    "actionable catalogue decisions require a selected capability"
                )

            if self.selected_capability_id not in self.executable_capability_ids:
                raise ValueError(
                    "selected capability must be executable"
                )
        elif self.selected_capability_id is not None:
            raise ValueError(
                "non-actionable catalogue decisions must not select a capability"
            )

        assessment_ids = tuple(
            item.capability_id
            for item in self.assessments
        )

        if len(assessment_ids) != len(set(assessment_ids)):
            raise ValueError(
                "catalogue assessments must use unique capability IDs"
            )

        if len(self.executable_capability_ids) != len(
            set(self.executable_capability_ids)
        ):
            raise ValueError(
                "executable_capability_ids must be unique"
            )

        return self
