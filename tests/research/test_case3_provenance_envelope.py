"""Phase 7 controlled-reopen tests for the verified Case 3 full-FT capability."""

from __future__ import annotations

import json
from pathlib import Path

from research.phenoguard import (
    ApplicabilityDecision,
    ScientificRequestContext,
    build_case3_winter_wheat_classification_envelope,
    build_default_provenance_catalogue,
    resolve_capability_catalogue,
)
from research.phenoguard.provenance import (
    CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
    CASE3_WINTER_WHEAT_CLASSIFICATION_REVISION,
    CASE3_WINTER_WHEAT_CLASSIFICATION_WEIGHT_SHA256,
)


ROOT = Path(__file__).resolve().parents[2]


def test_case3_fullft_is_registered_in_model_zoo() -> None:
    model_zoo = json.loads(
        (ROOT / "model_zoo.json").read_text(
            encoding="utf-8",
        )
    )

    assert model_zoo["image-classification"] == [
        CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
    ]


def test_case3_envelope_pins_runtime_verified_identity() -> None:
    envelope = build_case3_winter_wheat_classification_envelope()

    assert envelope.capability_id == (
        CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID
    )

    assert (
        CASE3_WINTER_WHEAT_CLASSIFICATION_REVISION
        in envelope.version_or_checkpoint
    )

    assert (
        CASE3_WINTER_WHEAT_CLASSIFICATION_WEIGHT_SHA256
        in envelope.version_or_checkpoint
    )

    assert tuple(
        item.field
        for item in envelope.constraints
    ) == (
        "species",
        "modality",
    )

    assert envelope.required_context_fields == (
        "species",
        "modality",
    )


def test_case3_valid_winter_wheat_rgb_executes() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        ScientificRequestContext(
            scientific_task="image classification",
            species="winter wheat",
            modality="RGB",
        ),
        requested_capability_id=(
            CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID
        ),
    )

    assert result.decision is ApplicabilityDecision.EXECUTE
    assert result.selected_capability_id == (
        CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID
    )


def test_case3_missing_modality_clarifies() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        ScientificRequestContext(
            scientific_task="image classification",
            species="winter wheat",
        ),
        requested_capability_id=(
            CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID
        ),
    )

    assert result.decision is ApplicabilityDecision.CLARIFY
    assert result.selected_capability_id is None


def test_case3_non_rgb_or_wrong_species_abstains() -> None:
    non_rgb = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        ScientificRequestContext(
            scientific_task="image classification",
            species="winter wheat",
            modality="hyperspectral",
        ),
        requested_capability_id=(
            CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID
        ),
    )

    wrong_species = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        ScientificRequestContext(
            scientific_task="image classification",
            species="maize",
            modality="RGB",
        ),
        requested_capability_id=(
            CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID
        ),
    )

    assert non_rgb.decision is ApplicabilityDecision.ABSTAIN
    assert wrong_species.decision is ApplicabilityDecision.ABSTAIN
