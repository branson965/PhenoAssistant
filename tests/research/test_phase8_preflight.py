"""Phase 8A pre-outcome experiment-branch guardrail tests."""

from __future__ import annotations

import json
from pathlib import Path

from research.phenoguard import ConditionId
from scripts.research.verify_phenoguard_method_freeze import verify_manifest


ROOT = Path(__file__).resolve().parents[2]


def test_experiment_branch_preserves_phase7_freeze() -> None:
    count, aggregate = verify_manifest()

    assert count == 22
    assert aggregate == (
        "337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f"
    )


def test_prompt_contract_covers_all_frozen_conditions() -> None:
    path = (
        ROOT
        / "experiments"
        / "ijcai2027"
        / "condition_prompt_contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert set(payload["conditions"]) == {
        item.value
        for item in ConditionId
    }


def test_prompt_contract_explicitly_blocks_hidden_gold_leakage() -> None:
    path = (
        ROOT
        / "experiments"
        / "ijcai2027"
        / "condition_prompt_contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert any(
        "gold labels" in item.lower()
        for item in payload["invariants"]
    )


def test_runtime_capture_source_never_reads_api_key() -> None:
    source = (
        ROOT
        / "scripts"
        / "research"
        / "prepare_ijcai_runtime_controls.py"
    ).read_text(
        encoding="utf-8",
    )

    assert "OPENROUTER_API_KEY" not in source
    assert "api_key_read" in source
    assert '"api_key_read": False' in source



def load_experiment_json(name: str) -> dict:
    path = (
        ROOT
        / "experiments"
        / "ijcai2027"
        / name
    )

    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def test_model_plan_uses_fixed_primary_and_predeclared_breadth_models() -> None:
    payload = load_experiment_json(
        "model_plan.json"
    )

    assert payload["status"] == "PROVISIONAL_PRE_OUTCOME_PENDING_SUPERVISOR_CONFIRMATION"
    assert payload["primary"]["model_id"] == (
        "openai/gpt-5.6-luna"
    )
    assert payload["breadth"]["model_id"] == (
        "openai/gpt-5.6-sol"
    )
    assert payload["historical_migration_model"][
        "allowed_for_ijcai_main_evaluation"
    ] is False


def test_model_plan_pins_openai_provider_without_fallbacks() -> None:
    payload = load_experiment_json(
        "model_plan.json"
    )

    routing = payload["routing"][
        "openrouter_provider_object"
    ]

    assert routing["order"] == [
        "openai",
    ]
    assert routing["allow_fallbacks"] is False
    assert routing["require_parameters"] is True


def test_runtime_plan_freezes_seed_schedule_and_one_tool_budget() -> None:
    payload = load_experiment_json(
        "runtime_plan.json"
    )

    sampling = payload["sampling"]
    tool_loop = payload["tool_loop"]

    assert payload["status"] == "PROVISIONAL_PRE_OUTCOME_PENDING_SUPERVISOR_CONFIRMATION"
    assert sampling["temperature_parameter_sent"] is False
    assert sampling["seed_schedule"] == [
        2026,
        2027,
        2028,
    ]
    assert sampling["reasoning"] == {
        "effort": "medium",
    }
    assert tool_loop["max_iterations"] == 2
    assert tool_loop["max_function_calls"] == 1
    assert tool_loop["allow_concurrent_invocation"] is False
    assert tool_loop["terminate_on_unknown_calls"] is True


def test_runtime_plan_locks_phase8a_package_versions() -> None:
    payload = load_experiment_json(
        "runtime_plan.json"
    )

    assert payload["package_expectations"] == {
        "agent-framework-core": "1.11.0",
        "agent-framework-openai": "1.11.0",
        "mcp": "2.3.0",
        "pydantic": "2.13.4",
    }


def test_live_preflight_is_non_scientific_and_does_not_log_api_key() -> None:
    source = (
        ROOT
        / "scripts"
        / "research"
        / "validate_ijcai_openrouter_preflight.py"
    ).read_text(
        encoding="utf-8",
    )

    assert "phase8_preflight_echo" in source
    assert "OPENROUTER_API_KEY" in source
    assert "print(api_key" not in source
    assert "PHASE8A_LIVE_PREFLIGHT_OUTCOME_BEARING=false" in source
    assert "temperature" not in (
        source.split(
            "options = {",
            maxsplit=1,
        )[1].split(
            "try:",
            maxsplit=1,
        )[0]
    )



def test_runtime_capture_bootstraps_repo_root_before_project_import() -> None:
    source = (
        ROOT
        / "scripts"
        / "research"
        / "prepare_ijcai_runtime_controls.py"
    ).read_text(
        encoding="utf-8",
    )

    root_index = source.index(
        "ROOT = Path(__file__).resolve().parents[2]"
    )

    bootstrap_index = source.index(
        "sys.path.insert"
    )

    project_import_index = source.index(
        "from research.phenoguard import ControlledVariables"
    )

    assert root_index < bootstrap_index < project_import_index



def test_model_and_runtime_plans_require_supervisor_confirmation() -> None:
    model = load_experiment_json(
        "model_plan.json"
    )

    runtime = load_experiment_json(
        "runtime_plan.json"
    )

    assert model["supervisor_confirmation_required"] is True
    assert runtime["supervisor_confirmation_required"] is True
