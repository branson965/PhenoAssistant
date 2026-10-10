"""Phase 7H prospective IJCAI protocol-freeze tests."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from research.phenoguard import (
    AgentArchitecture,
    BenchmarkSplit,
    ConditionId,
    ControlledVariables,
    InterfaceMode,
    RequiredMetric,
    ScenarioCategory,
    VerificationMode,
    build_default_provenance_catalogue,
    build_development_validation_gold,
    build_development_validation_manifest,
    build_frozen_condition_catalogue,
    build_protocol_freeze,
    resolve_with_trace,
    score_decision_trace,
    validate_matched_pair,
)


def test_condition_catalogue_contains_exact_authoritative_baselines() -> None:
    conditions = build_frozen_condition_catalogue()

    assert tuple(
        item.condition_id
        for item in conditions
    ) == tuple(ConditionId)

    assert len(conditions) == 10
    assert len({
        item.condition_id
        for item in conditions
    }) == 10


def test_full_phenoguard_condition_includes_post_validation() -> None:
    by_id = {
        item.condition_id: item
        for item in build_frozen_condition_catalogue()
    }

    full = by_id[ConditionId.FULL_PHENOGUARD]

    assert full.architecture is AgentArchitecture.MANAGER
    assert full.interface is InterfaceMode.MCP
    assert full.verification is VerificationMode.FULL_PHENOGUARD
    assert full.post_validation_enabled is True


def test_model_only_and_expert_oracle_have_distinct_boundaries() -> None:
    by_id = {
        item.condition_id: item
        for item in build_frozen_condition_catalogue()
    }

    model_only = by_id[ConditionId.MODEL_ONLY]
    oracle = by_id[ConditionId.EXPERT_ORACLE]

    assert model_only.tools_available is False
    assert model_only.interface is InterfaceMode.NONE
    assert oracle.architecture is AgentArchitecture.EXPERT
    assert oracle.interface is InterfaceMode.EXPERT


def test_protocol_retains_all_required_metrics() -> None:
    protocol = build_protocol_freeze()

    assert set(protocol.required_metrics) == set(RequiredMetric)
    assert len(protocol.required_metrics) == len(RequiredMetric)


def test_protocol_freezes_mcp_primary_and_direct_mcp_portability_subset() -> None:
    protocol = build_protocol_freeze()

    assert protocol.primary_interface is InterfaceMode.MCP
    assert set(protocol.portability_interfaces) == {
        InterfaceMode.DIRECT,
        InterfaceMode.MCP,
    }
    assert ConditionId.MANAGER_TOOL_SCHEMAS in (
        protocol.portability_condition_ids
    )
    assert ConditionId.FULL_PHENOGUARD in (
        protocol.portability_condition_ids
    )


def test_protocol_freezes_hidden_label_and_negative_result_discipline() -> None:
    protocol = build_protocol_freeze()

    assert protocol.venue == "IJCAI 2027"
    assert protocol.internal_go_no_go == "2026-11-30"
    assert protocol.hidden_labels_available_to_method is False
    assert protocol.negative_results_retained is True
    assert protocol.post_unblinding_method_changes_authorized is False


def test_controlled_variables_reject_blank_runtime_identity() -> None:
    with pytest.raises(
        ValidationError,
        match="must not be blank",
    ):
        ControlledVariables(
            provider="",
            model_id="model",
            model_revision="revision",
            temperature=0.0,
            max_output_tokens=1000,
            prompt_bundle_sha256="prompt-hash",
            tool_catalogue_sha256="tool-hash",
            task_manifest_sha256="task-hash",
            retry_policy="none",
            iteration_limit=1,
            session_reset_policy="fresh_session",
            package_lock_sha256="package-hash",
            hardware_class="cpu",
        )


def test_controlled_variables_reject_nonpositive_iteration_limit() -> None:
    with pytest.raises(
        ValidationError,
        match="must be positive",
    ):
        ControlledVariables(
            provider="OpenRouter",
            model_id="model",
            model_revision="revision",
            temperature=0.0,
            max_output_tokens=1000,
            prompt_bundle_sha256="prompt-hash",
            tool_catalogue_sha256="tool-hash",
            task_manifest_sha256="task-hash",
            retry_policy="none",
            iteration_limit=0,
            session_reset_policy="fresh_session",
            package_lock_sha256="package-hash",
            hardware_class="cpu",
        )


def test_qualification_manifest_has_no_hidden_cases_and_unique_ids() -> None:
    scenarios = build_development_validation_manifest()

    assert len(scenarios) == 12
    assert len({
        item.scenario_id
        for item in scenarios
    }) == 12
    assert all(
        item.split is not BenchmarkSplit.HIDDEN
        for item in scenarios
    )

    counts = Counter(
        item.split
        for item in scenarios
    )

    assert counts[BenchmarkSplit.DEVELOPMENT] == 8
    assert counts[BenchmarkSplit.VALIDATION] == 4


def test_qualification_manifest_contains_five_valid_shift_pairs() -> None:
    scenarios = build_development_validation_manifest()
    by_pair: dict[str, list] = defaultdict(list)

    for item in scenarios:
        if item.pair_id is not None:
            by_pair[item.pair_id].append(item)

    assert len(by_pair) == 5

    for pair in by_pair.values():
        assert len(pair) == 2
        validate_matched_pair(
            pair[0],
            pair[1],
        )


def test_qualification_manifest_keeps_training_cases_unpaired() -> None:
    scenarios = build_development_validation_manifest()

    training = [
        item
        for item in scenarios
        if item.category
        is ScenarioCategory.TRAINING_RECOMMENDATION
    ]

    assert len(training) == 1
    assert training[0].pair_id is None


def test_manifest_and_gold_have_exact_identity_alignment() -> None:
    scenarios = build_development_validation_manifest()
    gold = build_development_validation_gold()

    assert tuple(
        item.scenario_id
        for item in scenarios
    ) == tuple(
        item.scenario_id
        for item in gold
    )


def test_frozen_method_scores_exactly_on_mechanical_qualification_manifest() -> None:
    scenarios = build_development_validation_manifest()
    gold = {
        item.scenario_id: item
        for item in build_development_validation_gold()
    }
    catalogue = build_default_provenance_catalogue()

    scores = []

    for scenario in scenarios:
        trace = resolve_with_trace(
            catalogue,
            scenario.request,
            scenario_id=scenario.scenario_id,
            requested_capability_id=scenario.requested_capability_id,
            training_readiness=scenario.training_readiness,
        )

        score = score_decision_trace(
            trace,
            gold[scenario.scenario_id],
        )

        scores.append(score)

    assert len(scores) == 12
    assert all(
        item.exact_correct
        for item in scores
    )
    assert not any(
        item.unsafe_execution
        for item in scores
    )



def test_machine_readable_protocol_freeze_matches_code_contract() -> None:
    payload = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "research"
            / "IJCAI_2027_PROTOCOL_FREEZE.json"
        ).read_text(
            encoding="utf-8",
        )
    )

    protocol = build_protocol_freeze()

    assert payload["venue"] == protocol.venue
    assert payload["internal_go_no_go"] == protocol.internal_go_no_go
    assert payload["primary_interface"] == protocol.primary_interface.value
    assert payload["conditions"] == [
        item.condition_id.value
        for item in protocol.conditions
    ]
    assert payload["required_metrics"] == [
        item.value
        for item in protocol.required_metrics
    ]


def test_machine_readable_freeze_preserves_blinding_and_negative_results() -> None:
    payload = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "research"
            / "IJCAI_2027_PROTOCOL_FREEZE.json"
        ).read_text(
            encoding="utf-8",
        )
    )

    assert payload["hidden_labels_available_to_method"] is False
    assert payload["negative_results_retained"] is True
    assert payload["post_unblinding_method_changes_authorized"] is False
    assert payload["qualification_manifest"]["hidden_cases"] == 0
