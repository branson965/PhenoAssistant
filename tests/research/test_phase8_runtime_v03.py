"""Phase 8 v0.3 historical/provenance runtime preparation guards.

These tests run without provider access, model calls or scientific outcomes.
"""

from __future__ import annotations

from pathlib import Path

from scripts.research import prepare_phase8_runtime_v03 as preparation
from scripts.research.prepare_ijcai_runtime_controls import sha256_file


def test_october_evidence_is_immutable_and_separate_from_v03():
    assert preparation.OCT_CANDIDATE.exists()
    assert preparation.PACKAGE_LOCK.exists()
    assert sha256_file(preparation.OCT_CANDIDATE) == preparation.OCT_CANDIDATE_SHA
    assert sha256_file(preparation.PACKAGE_LOCK) == preparation.LOCK_SHA
    assert preparation.OCT_CANDIDATE.name == "runtime_controls_candidate.json"


def test_passed_live_preflight_is_non_scientific_and_no_secrets():
    evidence = preparation.get_json(preparation.EVIDENCE)
    run = evidence["runtime"]
    assert run["preflight_pass"] is True
    assert run["model_returned"] == "openai/gpt-5.6-luna"
    assert run["tool_calls"] == 1
    assert run["seed"] == 2026
    assert run["provider_pin"] == "openai"
    assert run["provider_fallbacks"] is False
    assert run["outcome_bearing"] is False
    assert evidence["scientific_outcomes_observed"] is False
    assert evidence["credential"]["api_key_recorded"] is False


def test_runtime_source_hashes_cover_real_live_adapter():
    assert "scripts/research/openrouter_compat.py" in preparation.RUNTIME_SOURCES
    assert "scripts/research/validate_ijcai_openrouter_preflight.py" in preparation.RUNTIME_SOURCES
    assert "experiments/ijcai2027/runtime/live_preflight_evidence_20261119.json" in preparation.RUNTIME_SOURCES
    for path in preparation.RUNTIME_SOURCES:
        assert (preparation.ROOT / path).is_file()


def test_preparation_is_offline_and_does_not_overwrite_previous_candidate():
    text = Path(preparation.__file__).read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY" not in text
    assert "runtime_controls_candidate_v0.3.json" in text
    assert "runtime_controls_frozen_v0.3.json" in text
    assert "destination.exists()" in text
    assert "refusing to overwrite evidence" in text
    assert '"scientific_execution_permitted": False' in text
    assert '"api_key_read": False' in text
    assert '"outcome_bearing_work_performed": False' in text


def test_current_environment_and_phase7_invariants_still_match():
    oct_candidate, live_evidence, runtime_plan = preparation.check_inputs()
    assert oct_candidate["phase7_freeze_aggregate_sha256"] == preparation.METHOD_SHA
    assert live_evidence["runtime"]["preflight_pass"] is True
    assert runtime_plan["tool_loop"]["max_function_calls"] == 1
