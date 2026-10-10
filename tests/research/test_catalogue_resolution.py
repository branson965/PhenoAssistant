"""Phase 7C catalogue-level applicability resolution tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.phenoguard import (
    ApplicabilityDecision,
    ScientificRequestContext,
    build_case1_arabidopsis_segmentation_envelope,
    build_case2_potato_segmentation_envelope,
    build_default_provenance_catalogue,
    resolve_capability_catalogue,
)
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    CASE2_POTATO_SEGMENTATION_MODEL_ID,
)


ROOT = Path(__file__).resolve().parents[2]


def test_both_real_segmentation_capabilities_are_registered() -> None:
    model_zoo = json.loads(
        (ROOT / "model_zoo.json").read_text(
            encoding="utf-8",
        )
    )

    registered = set(
        model_zoo["instance-segmentation"]
    )

    assert CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID in registered
    assert CASE2_POTATO_SEGMENTATION_MODEL_ID in registered


def test_potato_envelope_freezes_only_evidenced_species_rule() -> None:
    envelope = build_case2_potato_segmentation_envelope()

    assert tuple(
        item.field
        for item in envelope.constraints
    ) == ("species",)
    assert envelope.constraints[0].allowed_values == ("potato",)
    assert envelope.required_context_fields == ("species",)


def test_requested_valid_arabidopsis_capability_executes() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="Arabidopsis thaliana",
        ),
        requested_capability_id=(
            CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
        ),
    )

    assert result.decision is ApplicabilityDecision.EXECUTE
    assert result.selected_capability_id == (
        CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
    )
    assert result.executable_capability_ids == (
        CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    )


def test_wrong_requested_capability_reselects_unique_potato_model() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="potato",
        ),
        requested_capability_id=(
            CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
        ),
    )

    assert result.decision is ApplicabilityDecision.RESELECT
    assert result.selected_capability_id == (
        CASE2_POTATO_SEGMENTATION_MODEL_ID
    )
    assert result.executable_capability_ids == (
        CASE2_POTATO_SEGMENTATION_MODEL_ID,
    )


def test_unique_valid_capability_executes_without_preselection() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="potato",
        ),
    )

    assert result.decision is ApplicabilityDecision.EXECUTE
    assert result.selected_capability_id == (
        CASE2_POTATO_SEGMENTATION_MODEL_ID
    )


def test_missing_species_clarifies_across_catalogue() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
        ),
    )

    assert result.decision is ApplicabilityDecision.CLARIFY
    assert result.selected_capability_id is None
    assert result.executable_capability_ids == ()


def test_no_applicable_capability_abstains_without_training_claim() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="maize",
        ),
    )

    assert result.decision is ApplicabilityDecision.ABSTAIN
    assert result.selected_capability_id is None
    assert result.executable_capability_ids == ()


def test_duplicate_capability_ids_are_rejected() -> None:
    arabidopsis = build_case1_arabidopsis_segmentation_envelope()

    with pytest.raises(
        ValueError,
        match="unique capability IDs",
    ):
        resolve_capability_catalogue(
            (
                arabidopsis,
                arabidopsis,
            ),
            ScientificRequestContext(
                scientific_task="instance segmentation",
                species="Arabidopsis thaliana",
            ),
        )


def test_multiple_executable_capabilities_require_clarification_without_choice() -> None:
    first = build_case1_arabidopsis_segmentation_envelope()
    second = first.model_copy(
        update={
            "capability_id": "research-fixture/arabidopsis-alternative",
            "version_or_checkpoint": "research-fixture-v1",
        },
    )

    result = resolve_capability_catalogue(
        (
            first,
            second,
        ),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="Arabidopsis thaliana",
        ),
    )

    assert result.decision is ApplicabilityDecision.CLARIFY
    assert result.selected_capability_id is None
    assert result.executable_capability_ids == (
        first.capability_id,
        second.capability_id,
    )


def test_explicit_choice_resolves_multiple_executable_capabilities() -> None:
    first = build_case1_arabidopsis_segmentation_envelope()
    second = first.model_copy(
        update={
            "capability_id": "research-fixture/arabidopsis-alternative",
            "version_or_checkpoint": "research-fixture-v1",
        },
    )

    result = resolve_capability_catalogue(
        (
            first,
            second,
        ),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="Arabidopsis thaliana",
        ),
        requested_capability_id=second.capability_id,
    )

    assert result.decision is ApplicabilityDecision.EXECUTE
    assert result.selected_capability_id == second.capability_id
