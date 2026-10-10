"""Phase 7E deterministic trace and evidence-contract tests."""

from __future__ import annotations

import json

from research.phenoguard import (
    ApplicabilityDecision,
    DecisionReason,
    ScientificRequestContext,
    TrainingReadinessContext,
    build_default_provenance_catalogue,
    canonical_trace_json,
    resolve_with_trace,
    trace_sha256,
)
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    CASE2_POTATO_SEGMENTATION_MODEL_ID,
)


def catalogue():
    return build_default_provenance_catalogue()


def test_execute_trace_records_requested_capability_reason() -> None:
    trace = resolve_with_trace(
        catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="Arabidopsis thaliana",
        ),
        scenario_id="execute-arabidopsis",
        requested_capability_id=(
            CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
        ),
    )

    assert trace.resolution.decision is ApplicabilityDecision.EXECUTE
    assert trace.decision_reason is (
        DecisionReason.REQUESTED_CAPABILITY_EXECUTABLE
    )
    assert trace.resolution.selected_capability_id == (
        CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
    )


def test_reselect_trace_records_unique_alternative_reason() -> None:
    trace = resolve_with_trace(
        catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="potato",
        ),
        scenario_id="reselect-potato",
        requested_capability_id=(
            CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
        ),
    )

    assert trace.resolution.decision is ApplicabilityDecision.RESELECT
    assert trace.decision_reason is (
        DecisionReason.UNIQUE_ALTERNATIVE_EXECUTABLE
    )
    assert trace.resolution.selected_capability_id == (
        CASE2_POTATO_SEGMENTATION_MODEL_ID
    )


def test_missing_context_trace_is_clarification() -> None:
    trace = resolve_with_trace(
        catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
        ),
        scenario_id="clarify-species",
    )

    assert trace.resolution.decision is ApplicabilityDecision.CLARIFY
    assert trace.decision_reason is (
        DecisionReason.MISSING_APPLICABILITY_CONTEXT
    )


def test_unsupported_case_trace_abstains() -> None:
    trace = resolve_with_trace(
        catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="maize",
        ),
        scenario_id="abstain-maize",
    )

    assert trace.resolution.decision is ApplicabilityDecision.ABSTAIN
    assert trace.decision_reason is (
        DecisionReason.NO_APPLICABLE_CAPABILITY
    )


def test_training_ready_trace_records_recommendation_reason() -> None:
    trace = resolve_with_trace(
        catalogue(),
        ScientificRequestContext(
            scientific_task="image classification",
            species="maize",
        ),
        scenario_id="train-classifier",
        training_readiness=TrainingReadinessContext(
            dataset_available=True,
            labels_available=True,
            dataset_format_valid=True,
        ),
    )

    assert (
        trace.resolution.decision
        is ApplicabilityDecision.RECOMMEND_TRAINING
    )
    assert trace.decision_reason is DecisionReason.TRAINING_READY


def test_missing_training_evidence_trace_clarifies() -> None:
    trace = resolve_with_trace(
        catalogue(),
        ScientificRequestContext(
            scientific_task="image classification",
            species="maize",
        ),
        scenario_id="clarify-training-inputs",
        training_readiness=TrainingReadinessContext(
            dataset_available=False,
            labels_available=False,
            dataset_format_valid=False,
        ),
    )

    assert trace.resolution.decision is ApplicabilityDecision.CLARIFY
    assert trace.decision_reason is (
        DecisionReason.TRAINING_REQUIREMENTS_MISSING
    )


def test_trace_json_is_deterministic_and_roundtrippable() -> None:
    kwargs = dict(
        envelopes=catalogue(),
        request=ScientificRequestContext(
            scientific_task="instance segmentation",
            species="potato",
        ),
        scenario_id="deterministic-potato",
    )

    first = resolve_with_trace(**kwargs)
    second = resolve_with_trace(**kwargs)

    first_json = canonical_trace_json(first)
    second_json = canonical_trace_json(second)

    assert first_json == second_json
    assert trace_sha256(first) == trace_sha256(second)

    payload = json.loads(first_json)

    assert payload["scenario_id"] == "deterministic-potato"
    assert payload["resolution"]["decision"] == "EXECUTE"
    assert payload["decision_reason"] == "unique_capability_executable"


def test_trace_digest_changes_when_scenario_identity_changes() -> None:
    request = ScientificRequestContext(
        scientific_task="instance segmentation",
        species="potato",
    )

    first = resolve_with_trace(
        catalogue(),
        request,
        scenario_id="scenario-a",
    )

    second = resolve_with_trace(
        catalogue(),
        request,
        scenario_id="scenario-b",
    )

    assert trace_sha256(first) != trace_sha256(second)


def test_trace_contains_no_runtime_timestamp_field() -> None:
    trace = resolve_with_trace(
        catalogue(),
        ScientificRequestContext(
            scientific_task="instance segmentation",
            species="potato",
        ),
        scenario_id="no-clock-dependence",
    )

    payload = trace.model_dump(
        mode="json",
    )

    assert "timestamp" not in payload
    assert "created_at" not in payload
    assert "duration" not in payload
