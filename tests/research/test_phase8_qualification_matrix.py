"""Offline, no-outcome checks for C3/C4/C8 qualification matrix planning."""

from __future__ import annotations

import json
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from research.phenoguard.pilot_manifest import build_development_validation_manifest
from scripts.research import prepare_phase8_qualification_matrix as planner


def fixtures():
    return (
        planner.read_json(planner.CANDIDATE),
        planner.read_json(planner.RUNTIME_PLAN),
        planner.read_json(planner.PROTOCOL),
        planner.read_json(planner.CONDITION_PROMPTS),
    )


def make():
    c, r, p, prompts = fixtures()
    return planner.build_matrix(
        candidate=c, runtime=r, protocol=p, prompt_contract=prompts
    )


def test_locked_candidate_sha_matches_on_plato():
    assert planner.CANDIDATE.is_file()
    assert planner.hash_file(planner.CANDIDATE) == planner.EXPECTED_CANDIDATE_SHA256


def test_exact_trial_matrix_and_no_scientific_execution():
    plan = make()
    assert plan["case_count"] == 12
    assert plan["trial_count"] == 108
    assert plan["split_counts"] == {"development": 8, "validation": 4}
    assert plan["conditions"] == [
        "C3_MANAGER_TOOL_SCHEMAS",
        "C4_MANAGER_GENERIC_CRITIC",
        "C8_FULL_PHENOGUARD",
    ]
    assert plan["seeds"] == [2026, 2027, 2028]
    assert plan["status"] == "OFFLINE_PLANNED_NOT_APPROVED_NOT_EXECUTED"
    assert plan["scientific_execution_permitted"] is False
    assert plan["api_key_read"] is False
    assert plan["outcome_bearing_work_performed"] is False
    assert len({row["trial_id"] for row in plan["trials"]}) == 108
    assert set(row["status"] for row in plan["trials"]) == {
        "PLANNED_NO_MODEL_CALL"
    }
    assert all(row["split_internal_only"] != "hidden" for row in plan["trials"])
    assert Decimal(plan["cost_forecast"]["usd"]) == Decimal("0.7036416")
    assert plan["cost_forecast"]["additional_generic_critic_calls_not_included"] is True
    assert plan["cost_forecast"]["forecast_not_measured"] is True
    assert plan["cost_forecast"]["not_a_spending_authorization"] is True


def test_narrow_model_visible_allowlist_prevents_label_and_id_leakage():
    scenarios = build_development_validation_manifest()
    assert len(scenarios) == 12
    for scenario in scenarios:
        view = planner.model_visible_view(scenario)
        assert set(view) == {
            "scientific_request",
            "requested_capability_id",
            "training_readiness",
        }
        serialized = json.dumps(view).lower()
        assert "expected_decision" not in serialized
        assert "rationale_code" not in serialized
        assert "scenario_id" not in serialized
        assert "pair_id" not in serialized
        assert "shift_dimension" not in serialized
        assert "evidence_source" not in serialized
        assert "category" not in serialized
        assert scenario.scenario_id not in serialized


def test_same_scenario_exactly_same_visible_context_across_conditions_and_seeds():
    trials = make()["trials"]
    for scenario_id in {t["scenario_id_internal_only"] for t in trials}:
        matching = [t for t in trials if t["scenario_id_internal_only"] == scenario_id]
        assert len(matching) == 9
        assert len({row["model_visible_view_sha256"] for row in matching}) == 1
        assert len({row["trial_id"] for row in matching}) == 9


@pytest.mark.parametrize("field,illegal", [
    ("scientific_execution_permitted", True),
    ("outcome_bearing_work_performed", True),
])
def test_unexpected_candidate_execution_state_fails_closed(field, illegal):
    c, r, p, prompts = fixtures()
    c[field] = illegal
    with pytest.raises(ValueError):
        planner.build_matrix(
            candidate=c, runtime=r, protocol=p, prompt_contract=prompts
        )


def test_no_runtime_billing_or_gold_import():
    source = Path(planner.__file__).read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY" not in source
    assert "build_development_validation_gold" not in source
    assert "AsyncOpenAI" not in source
    assert "OpenAIChatCompletionClient" not in source
    assert "chat/completions" not in source
    assert "httpx" not in source
    assert "scientific_execution_permitted" in source


def test_seed_or_provider_drift_fails_closed():
    c, r, p, prompts = fixtures()
    r["sampling"]["seed_schedule"] = [2026, 2027]
    with pytest.raises(ValueError, match="seed schedule"):
        planner.build_matrix(
            candidate=c, runtime=r, protocol=p, prompt_contract=prompts
        )
    c, r, p, prompts = fixtures()
    c["controls"]["model_id"] = "unapproved-model"
    with pytest.raises(ValueError, match="primary model"):
        planner.build_matrix(
            candidate=c, runtime=r, protocol=p, prompt_contract=prompts
        )


def test_prompt_contract_and_protocol_cannot_drop_baselines():
    c, r, p, prompts = fixtures()
    prompts["conditions"].pop("C4_MANAGER_GENERIC_CRITIC")
    with pytest.raises(ValueError, match="prompt contract"):
        planner.build_matrix(
            candidate=c, runtime=r, protocol=p, prompt_contract=prompts
        )


def test_matrix_deterministic_before_write():
    assert planner.sha256_value(make()) == planner.sha256_value(make())
