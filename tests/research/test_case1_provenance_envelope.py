"""Phase 7B provenance-backed envelope tests for real repository capabilities."""

from __future__ import annotations

import json
from pathlib import Path

from research.phenoguard import (
    ApplicabilityDecision,
    ScientificRequestContext,
    assess_scientific_applicability,
)
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    CASE1_ARABIDOPSIS_SEGMENTATION_REVISION,
    build_case1_arabidopsis_segmentation_envelope,
)


ROOT = Path(__file__).resolve().parents[2]


def test_case1_envelope_is_tied_to_registered_model_zoo_entry() -> None:
    model_zoo = json.loads(
        (ROOT / "model_zoo.json").read_text(
            encoding="utf-8",
        )
    )

    assert (
        CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
        in model_zoo["instance-segmentation"]
    )

    envelope = build_case1_arabidopsis_segmentation_envelope()

    assert envelope.capability_id == (
        CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
    )
    assert envelope.version_or_checkpoint.endswith(
        "@" + CASE1_ARABIDOPSIS_SEGMENTATION_REVISION
    )


def test_case1_envelope_contains_only_currently_evidenced_context_rule() -> None:
    envelope = build_case1_arabidopsis_segmentation_envelope()

    constrained_fields = tuple(
        constraint.field
        for constraint in envelope.constraints
    )

    assert constrained_fields == ("species",)
    assert envelope.required_context_fields == ("species",)
    assert "view" not in constrained_fields
    assert "modality" not in constrained_fields
    assert "environment" not in constrained_fields


def test_case1_arabidopsis_request_executes() -> None:
    envelope = build_case1_arabidopsis_segmentation_envelope()

    request = ScientificRequestContext(
        scientific_task="instance segmentation",
        species="Arabidopsis thaliana",
    )

    result = assess_scientific_applicability(
        envelope,
        request,
    )

    assert result.decision is ApplicabilityDecision.EXECUTE
    assert result.safe_to_execute is True


def test_case1_missing_species_requires_clarification() -> None:
    envelope = build_case1_arabidopsis_segmentation_envelope()

    request = ScientificRequestContext(
        scientific_task="instance segmentation",
    )

    result = assess_scientific_applicability(
        envelope,
        request,
    )

    assert result.decision is ApplicabilityDecision.CLARIFY
    assert result.safe_to_execute is False
    assert result.missing_context_fields == ("species",)


def test_case1_non_arabidopsis_species_abstains() -> None:
    envelope = build_case1_arabidopsis_segmentation_envelope()

    request = ScientificRequestContext(
        scientific_task="instance segmentation",
        species="Solanum tuberosum",
    )

    result = assess_scientific_applicability(
        envelope,
        request,
    )

    assert result.decision is ApplicabilityDecision.ABSTAIN
    assert result.safe_to_execute is False
    assert len(result.hard_violations) == 1
    assert result.hard_violations[0].field == "species"
