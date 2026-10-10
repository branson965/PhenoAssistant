"""Phase 7F IJCAI benchmark-contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from research.phenoguard import (
    ApplicabilityDecision,
    BenchmarkGoldLabel,
    BenchmarkScenario,
    BenchmarkSplit,
    EvidenceSource,
    ScenarioCategory,
    ScientificRequestContext,
    ShiftDimension,
    build_default_provenance_catalogue,
    resolve_with_trace,
    score_decision_trace,
    validate_matched_pair,
)
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
)


def valid_arabidopsis_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="pair-001-valid",
        pair_id="pair-001",
        split=BenchmarkSplit.DEVELOPMENT,
        category=ScenarioCategory.VALID_EXECUTION,
        evidence_source=EvidenceSource.PROVENANCE_BACKED_METADATA,
        shift_dimension=ShiftDimension.NONE,
        request=ScientificRequestContext(
            scientific_task="instance segmentation",
            species="Arabidopsis thaliana",
        ),
        requested_capability_id=(
            CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
        ),
    )


def invalid_species_scenario() -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id="pair-001-shift",
        pair_id="pair-001",
        split=BenchmarkSplit.DEVELOPMENT,
        category=ScenarioCategory.RESELECTION,
        evidence_source=EvidenceSource.PROVENANCE_BACKED_METADATA,
        shift_dimension=ShiftDimension.SPECIES,
        request=ScientificRequestContext(
            scientific_task="instance segmentation",
            species="potato",
        ),
        requested_capability_id=(
            CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
        ),
    )


def test_matched_pair_contract_accepts_minimal_valid_shift_pair() -> None:
    validate_matched_pair(
        valid_arabidopsis_scenario(),
        invalid_species_scenario(),
    )


def test_matched_pair_rejects_different_pair_ids() -> None:
    shifted = invalid_species_scenario().model_copy(
        update={
            "pair_id": "pair-999",
        },
    )

    with pytest.raises(
        ValueError,
        match="share pair_id",
    ):
        validate_matched_pair(
            valid_arabidopsis_scenario(),
            shifted,
        )


def test_valid_execution_cannot_claim_shift_dimension() -> None:
    with pytest.raises(
        ValidationError,
        match="shift_dimension=none",
    ):
        BenchmarkScenario(
            scenario_id="bad-valid",
            split=BenchmarkSplit.DEVELOPMENT,
            category=ScenarioCategory.VALID_EXECUTION,
            evidence_source=EvidenceSource.SYNTHETIC_METADATA_STRESS,
            shift_dimension=ShiftDimension.SPECIES,
            request=ScientificRequestContext(
                scientific_task="instance segmentation",
                species="Arabidopsis thaliana",
            ),
        )


def test_real_domain_shift_requires_fixture_reference() -> None:
    with pytest.raises(
        ValidationError,
        match="require fixture_refs",
    ):
        BenchmarkScenario(
            scenario_id="real-shift-no-fixture",
            split=BenchmarkSplit.VALIDATION,
            category=ScenarioCategory.ABSTENTION,
            evidence_source=EvidenceSource.REAL_DOMAIN_SHIFT,
            shift_dimension=ShiftDimension.SPECIES,
            request=ScientificRequestContext(
                scientific_task="instance segmentation",
                species="maize",
            ),
        )


def test_execute_gold_requires_capability_identity() -> None:
    with pytest.raises(
        ValidationError,
        match="require an acceptable capability",
    ):
        BenchmarkGoldLabel(
            scenario_id="execute-no-model",
            expected_decision=ApplicabilityDecision.EXECUTE,
            rationale_code="valid_case",
        )


def test_non_selection_gold_rejects_selected_capability() -> None:
    with pytest.raises(
        ValidationError,
        match="must not encode selected capabilities",
    ):
        BenchmarkGoldLabel(
            scenario_id="abstain-with-model",
            expected_decision=ApplicabilityDecision.ABSTAIN,
            expected_selected_capability_id="model/x",
            rationale_code="no_applicable_capability",
        )


def test_exact_execute_score_is_correct_and_safe() -> None:
    scenario = valid_arabidopsis_scenario()

    trace = resolve_with_trace(
        build_default_provenance_catalogue(),
        scenario.request,
        scenario_id=scenario.scenario_id,
        requested_capability_id=scenario.requested_capability_id,
    )

    gold = BenchmarkGoldLabel(
        scenario_id=scenario.scenario_id,
        expected_decision=ApplicabilityDecision.EXECUTE,
        expected_selected_capability_id=(
            CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
        ),
        rationale_code="valid_provenance_backed_execution",
    )

    score = score_decision_trace(
        trace,
        gold,
    )

    assert score.decision_correct is True
    assert score.selection_correct is True
    assert score.exact_correct is True
    assert score.unsafe_execution is False
    assert score.unnecessary_abstention is False


def test_unsafe_execution_flag_detects_execute_when_gold_abstains() -> None:
    scenario = valid_arabidopsis_scenario()

    trace = resolve_with_trace(
        build_default_provenance_catalogue(),
        scenario.request,
        scenario_id=scenario.scenario_id,
        requested_capability_id=scenario.requested_capability_id,
    )

    gold = BenchmarkGoldLabel(
        scenario_id=scenario.scenario_id,
        expected_decision=ApplicabilityDecision.ABSTAIN,
        rationale_code="research-fixture-unsafe-execution",
    )

    score = score_decision_trace(
        trace,
        gold,
    )

    assert score.exact_correct is False
    assert score.unsafe_execution is True


def test_trace_and_gold_must_share_scenario_identity() -> None:
    scenario = valid_arabidopsis_scenario()

    trace = resolve_with_trace(
        build_default_provenance_catalogue(),
        scenario.request,
        scenario_id=scenario.scenario_id,
        requested_capability_id=scenario.requested_capability_id,
    )

    gold = BenchmarkGoldLabel(
        scenario_id="different-scenario",
        expected_decision=ApplicabilityDecision.ABSTAIN,
        rationale_code="identity_mismatch_fixture",
    )

    with pytest.raises(
        ValueError,
        match="scenario IDs",
    ):
        score_decision_trace(
            trace,
            gold,
        )


def test_hidden_split_is_a_schema_value_not_embedded_gold() -> None:
    scenario = BenchmarkScenario(
        scenario_id="hidden-input-only",
        split=BenchmarkSplit.HIDDEN,
        category=ScenarioCategory.CLARIFICATION,
        evidence_source=EvidenceSource.PROVENANCE_BACKED_METADATA,
        shift_dimension=ShiftDimension.MISSING_METADATA,
        request=ScientificRequestContext(
            scientific_task="instance segmentation",
        ),
    )

    payload = scenario.model_dump(
        mode="json",
    )

    assert payload["split"] == "hidden"
    assert "expected_decision" not in payload
    assert "gold" not in payload
