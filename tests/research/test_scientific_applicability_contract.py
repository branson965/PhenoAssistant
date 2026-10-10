"""Phase 7A tests for the scientific operating-envelope primitive."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from research.phenoguard import (
    ApplicabilityConstraint,
    ApplicabilityDecision,
    ConstraintSeverity,
    ScientificOperatingEnvelope,
    ScientificRequestContext,
    assess_scientific_applicability,
)


def envelope() -> ScientificOperatingEnvelope:
    return ScientificOperatingEnvelope(
        capability_id="arabidopsis-topview-segmentation-v1",
        scientific_task="instance segmentation",
        constraints=(
            ApplicabilityConstraint(
                field="species",
                allowed_values=("Arabidopsis thaliana",),
                severity=ConstraintSeverity.HARD,
                rationale="checkpoint species coverage",
            ),
            ApplicabilityConstraint(
                field="modality",
                allowed_values=("RGB",),
                severity=ConstraintSeverity.HARD,
                rationale="training modality",
            ),
            ApplicabilityConstraint(
                field="view",
                allowed_values=("top-view",),
                severity=ConstraintSeverity.HARD,
                rationale="training acquisition geometry",
            ),
            ApplicabilityConstraint(
                field="environment",
                allowed_values=("controlled",),
                severity=ConstraintSeverity.SOFT,
                rationale="deployment evidence is strongest in controlled imaging",
            ),
        ),
        required_context_fields=(
            "species",
            "modality",
            "view",
        ),
        required_metadata_keys=(
            "image_id",
        ),
        output_semantics="instance masks for visible rosette leaves",
        assumptions=(
            "single plant is the primary subject",
        ),
        limitations=(
            "field clutter has not been validated",
        ),
        known_failure_conditions=(
            "side-view imagery",
        ),
        provenance="PhenoAssistant Case 1 fixture",
        version_or_checkpoint="fixture-v1",
    )


def valid_request() -> ScientificRequestContext:
    return ScientificRequestContext(
        scientific_task="instance segmentation",
        species="Arabidopsis thaliana",
        modality="RGB",
        view="top-view",
        environment="controlled",
        metadata={
            "image_id": "plant-001",
        },
    )


def test_valid_context_executes() -> None:
    result = assess_scientific_applicability(
        envelope(),
        valid_request(),
    )

    assert result.decision is ApplicabilityDecision.EXECUTE
    assert result.safe_to_execute is True
    assert result.task_match is True
    assert result.hard_violations == ()
    assert result.soft_warnings == ()


def test_missing_required_context_clarifies() -> None:
    request = valid_request().model_copy(
        update={
            "view": None,
        },
    )

    result = assess_scientific_applicability(
        envelope(),
        request,
    )

    assert result.decision is ApplicabilityDecision.CLARIFY
    assert result.safe_to_execute is False
    assert result.missing_context_fields == ("view",)


def test_hard_view_mismatch_abstains() -> None:
    request = valid_request().model_copy(
        update={
            "view": "side-view",
        },
    )

    result = assess_scientific_applicability(
        envelope(),
        request,
    )

    assert result.decision is ApplicabilityDecision.ABSTAIN
    assert result.safe_to_execute is False
    assert len(result.hard_violations) == 1
    assert result.hard_violations[0].field == "view"


def test_soft_environment_mismatch_warns_but_executes() -> None:
    request = valid_request().model_copy(
        update={
            "environment": "field",
        },
    )

    result = assess_scientific_applicability(
        envelope(),
        request,
    )

    assert result.decision is ApplicabilityDecision.EXECUTE
    assert result.safe_to_execute is True
    assert len(result.soft_warnings) == 1
    assert result.soft_warnings[0].field == "environment"


def test_task_mismatch_abstains() -> None:
    request = valid_request().model_copy(
        update={
            "scientific_task": "image classification",
        },
    )

    result = assess_scientific_applicability(
        envelope(),
        request,
    )

    assert result.decision is ApplicabilityDecision.ABSTAIN
    assert result.task_match is False


def test_missing_required_metadata_clarifies() -> None:
    request = valid_request().model_copy(
        update={
            "metadata": {},
        },
    )

    result = assess_scientific_applicability(
        envelope(),
        request,
    )

    assert result.decision is ApplicabilityDecision.CLARIFY
    assert result.missing_metadata_keys == ("image_id",)


def test_matching_is_case_insensitive_but_evidence_preserves_input() -> None:
    request = valid_request().model_copy(
        update={
            "species": "arabidopsis THALIANA",
            "modality": "rgb",
            "view": "TOP-VIEW",
        },
    )

    result = assess_scientific_applicability(
        envelope(),
        request,
    )

    assert result.decision is ApplicabilityDecision.EXECUTE

    species_evaluation = next(
        item
        for item in result.evaluations
        if item.field == "species"
    )

    assert species_evaluation.observed_value == "arabidopsis THALIANA"
    assert species_evaluation.matched is True


def test_duplicate_constraint_field_is_rejected() -> None:
    with pytest.raises(
        ValidationError,
        match="at most one entry per context field",
    ):
        ScientificOperatingEnvelope(
            capability_id="duplicate-test",
            scientific_task="instance segmentation",
            constraints=(
                ApplicabilityConstraint(
                    field="view",
                    allowed_values=("top-view",),
                    severity=ConstraintSeverity.HARD,
                    rationale="first",
                ),
                ApplicabilityConstraint(
                    field="view",
                    allowed_values=("side-view",),
                    severity=ConstraintSeverity.SOFT,
                    rationale="second",
                ),
            ),
            output_semantics="test",
            provenance="test",
            version_or_checkpoint="test-v1",
        )
