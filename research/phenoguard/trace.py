"""Deterministic machine-readable traces for PhenoGuard decisions."""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from research.phenoguard.catalogue import resolve_capability_catalogue
from research.phenoguard.contracts import (
    ApplicabilityDecision,
    CatalogueApplicabilityResolution,
    ScientificOperatingEnvelope,
    ScientificRequestContext,
    TrainingReadinessContext,
)


class DecisionReason(StrEnum):
    """Deterministic reason codes for the final catalogue decision."""

    REQUESTED_CAPABILITY_EXECUTABLE = "requested_capability_executable"
    UNIQUE_CAPABILITY_EXECUTABLE = "unique_capability_executable"
    UNIQUE_ALTERNATIVE_EXECUTABLE = "unique_alternative_executable"
    MULTIPLE_CAPABILITIES_EXECUTABLE = "multiple_capabilities_executable"
    MISSING_APPLICABILITY_CONTEXT = "missing_applicability_context"
    TRAINING_READY = "training_ready"
    TRAINING_REQUIREMENTS_MISSING = "training_requirements_missing"
    NO_APPLICABLE_CAPABILITY = "no_applicable_capability"


class ApplicabilityDecisionTrace(BaseModel):
    """Frozen pre-execution trace for one PhenoGuard decision."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["0.1"] = "0.1"
    method_version: Literal["phenoguard-soe-v0.1"] = "phenoguard-soe-v0.1"
    scenario_id: str
    request: ScientificRequestContext
    requested_capability_id: str | None
    catalogue_capability_ids: tuple[str, ...]
    resolution: CatalogueApplicabilityResolution
    decision_reason: DecisionReason

    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_id(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("scenario_id must not be blank")

        return cleaned

    @model_validator(mode="after")
    def validate_trace_consistency(
        self,
    ) -> "ApplicabilityDecisionTrace":
        if len(self.catalogue_capability_ids) != len(
            set(self.catalogue_capability_ids)
        ):
            raise ValueError(
                "catalogue_capability_ids must be unique"
            )

        assessment_ids = tuple(
            assessment.capability_id
            for assessment in self.resolution.assessments
        )

        if assessment_ids != self.catalogue_capability_ids:
            raise ValueError(
                "trace catalogue IDs must match assessment order"
            )

        if (
            self.requested_capability_id
            != self.resolution.requested_capability_id
        ):
            raise ValueError(
                "trace requested capability must match resolution"
            )

        expected_reason = infer_decision_reason(
            self.resolution
        )

        if self.decision_reason is not expected_reason:
            raise ValueError(
                "decision_reason does not match deterministic resolution"
            )

        return self


def infer_decision_reason(
    resolution: CatalogueApplicabilityResolution,
) -> DecisionReason:
    """Map one structured resolution to a stable reason code."""
    if resolution.decision is ApplicabilityDecision.EXECUTE:
        if (
            resolution.requested_capability_id is not None
            and resolution.selected_capability_id
            == resolution.requested_capability_id
        ):
            return DecisionReason.REQUESTED_CAPABILITY_EXECUTABLE

        return DecisionReason.UNIQUE_CAPABILITY_EXECUTABLE

    if resolution.decision is ApplicabilityDecision.RESELECT:
        return DecisionReason.UNIQUE_ALTERNATIVE_EXECUTABLE

    if resolution.decision is ApplicabilityDecision.RECOMMEND_TRAINING:
        return DecisionReason.TRAINING_READY

    if resolution.decision is ApplicabilityDecision.CLARIFY:
        if len(resolution.executable_capability_ids) > 1:
            return DecisionReason.MULTIPLE_CAPABILITIES_EXECUTABLE

        if (
            resolution.training_readiness is not None
            and resolution.training_readiness.missing_requirements
        ):
            return DecisionReason.TRAINING_REQUIREMENTS_MISSING

        return DecisionReason.MISSING_APPLICABILITY_CONTEXT

    return DecisionReason.NO_APPLICABLE_CAPABILITY


def resolve_with_trace(
    envelopes: tuple[ScientificOperatingEnvelope, ...],
    request: ScientificRequestContext,
    *,
    scenario_id: str,
    requested_capability_id: str | None = None,
    training_readiness: TrainingReadinessContext | None = None,
) -> ApplicabilityDecisionTrace:
    """Resolve one request and return its complete deterministic trace."""
    resolution = resolve_capability_catalogue(
        envelopes,
        request,
        requested_capability_id=requested_capability_id,
        training_readiness=training_readiness,
    )

    return ApplicabilityDecisionTrace(
        scenario_id=scenario_id,
        request=request,
        requested_capability_id=requested_capability_id,
        catalogue_capability_ids=tuple(
            envelope.capability_id
            for envelope in envelopes
        ),
        resolution=resolution,
        decision_reason=infer_decision_reason(
            resolution
        ),
    )


def canonical_trace_json(
    trace: ApplicabilityDecisionTrace,
) -> str:
    """Return deterministic JSON suitable for manifests and hashing."""
    return json.dumps(
        trace.model_dump(
            mode="json",
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def trace_sha256(
    trace: ApplicabilityDecisionTrace,
) -> str:
    """Return the SHA-256 digest of the canonical trace."""
    return hashlib.sha256(
        canonical_trace_json(trace).encode(
            "utf-8",
        )
    ).hexdigest()
