"""Offline safety tests for the Phase 8 qualification attempt ledger."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.research import phase8_attempt_ledger as ledger


@pytest.fixture
def context():
    matrix, candidate = ledger.load_verified_controls()
    return matrix, candidate


def test_validates_exact_plato_matrix_and_current_execution_block(context):
    matrix, candidate = context
    assert matrix["trial_count"] == 108
    assert matrix["scientific_execution_permitted"] is False
    assert candidate["scientific_execution_permitted"] is False
    with pytest.raises(ledger.LedgerGateError, match="prohibited"):
        ledger.scientific_gate(candidate)


def test_append_only_start_then_metered_success_and_reject_duplicate(context, tmp_path):
    matrix, _ = context
    path = tmp_path / "trials.jsonl"
    trial = matrix["trials"][0]
    started = ledger.event_template(trial, model=matrix["model"], kind="STARTED")
    billed = ledger.append_event(path, started, matrix)
    assert billed == Decimal("0")
    assert path.read_text("utf-8").count("\n") == 1

    finished = ledger.event_template(trial, model=matrix["model"], kind="SUCCEEDED")
    finished["usage"] = {"input_tokens": 400, "output_tokens": 75}
    finished["provider_cost_usd"] = "0.001234"
    finished["attempt_trace_sha256"] = "a" * 64
    assert ledger.append_event(path, finished, matrix) == Decimal("0.001234")
    before = path.read_bytes()
    with pytest.raises(ledger.LedgerGateError, match="duplicate"):
        ledger.append_event(path, started, matrix)
    assert path.read_bytes() == before


def test_no_parallel_starts_or_semantic_retry(context, tmp_path):
    matrix, _ = context
    path = tmp_path / "attempts.jsonl"
    first, second = matrix["trials"][:2]
    start_first = ledger.event_template(first, model=matrix["model"], kind="STARTED")
    start_second = ledger.event_template(second, model=matrix["model"], kind="STARTED")
    ledger.append_event(path, start_first, matrix)
    with pytest.raises(ledger.LedgerGateError, match="concurrent"):
        ledger.append_event(path, start_second, matrix)
    assert path.read_text("utf-8").count("\n") == 1


def test_missing_provider_billing_stops_next_attempt(context):
    matrix, candidate = context
    trial = matrix["trials"][0]
    start = ledger.event_template(trial, model=matrix["model"], kind="STARTED")
    missing = ledger.event_template(trial, model=matrix["model"], kind="METERING_MISSING")
    missing["failure_code"] = "METERING_MISSING"
    events = [start, missing]
    assert ledger.verify_events(events, matrix) == Decimal("0")
    final = deepcopy(candidate)
    final["scientific_execution_permitted"] = True
    final["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    final["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    final["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    with pytest.raises(ledger.LedgerGateError, match="unknown provider charges"):
        ledger.next_trial_budget_gate(
            matrix=matrix,
            candidate=final,
            events=events,
            budget_usd=Decimal("8.00"),
            next_call_reserve_usd=Decimal("0.10"),
        )


def test_started_unfinished_attempt_blocks_next_call(context):
    matrix, candidate = context
    final = deepcopy(candidate)
    final["scientific_execution_permitted"] = True
    final["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    final["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    final["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    events = [ledger.event_template(matrix["trials"][0], model=matrix["model"], kind="STARTED")]
    with pytest.raises(ledger.LedgerGateError, match="in flight"):
        ledger.next_trial_budget_gate(
            matrix=matrix,
            candidate=final,
            events=events,
            budget_usd=Decimal("8.00"),
            next_call_reserve_usd=Decimal("0.10"),
        )


@pytest.mark.parametrize("bad", [
    {"usage": {"input_tokens": -1, "output_tokens": 2}},
    {"usage": {"input_tokens": True, "output_tokens": 2}},
    {"usage": {"input_tokens": 5, "output_tokens": 2}, "provider_cost_usd": None},
    {"usage": {"input_tokens": 5, "output_tokens": 2}, "provider_cost_usd": "-0.01"},
    {"usage": {"input_tokens": 5, "output_tokens": 2}, "provider_cost_usd": "NaN"},
])
def test_missing_or_malformed_usage_rejected(context, bad):
    matrix, _ = context
    trial = matrix["trials"][0]
    first = ledger.event_template(trial, model=matrix["model"], kind="STARTED")
    second = ledger.event_template(trial, model=matrix["model"], kind="SUCCEEDED")
    second["attempt_trace_sha256"] = "b" * 64
    second["usage"] = {"input_tokens": 2, "output_tokens": 3}
    second["provider_cost_usd"] = "0.0001"
    second.update(bad)
    with pytest.raises(ledger.LedgerGateError):
        ledger.verify_events([first, second], matrix)


def test_budget_reserve_blocks_next_paid_call(context):
    matrix, candidate = context
    final = deepcopy(candidate)
    final["scientific_execution_permitted"] = True
    final["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    final["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    final["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    assert ledger.next_trial_budget_gate(
        matrix=matrix, candidate=final, events=[],
        budget_usd=Decimal("8.00"), next_call_reserve_usd=Decimal("0.1"),
    ) == Decimal("8.00")
    with pytest.raises(ledger.LedgerGateError, match="ceiling"):
        ledger.next_trial_budget_gate(
            matrix=matrix, candidate=final, events=[],
            budget_usd=Decimal("8.00"), next_call_reserve_usd=Decimal("9.00"),
        )


def test_ledger_does_not_disclose_request_text_credential_or_gold(context):
    matrix, _ = context
    data = ledger.event_template(matrix["trials"][0], model=matrix["model"], kind="STARTED")
    assert set(data) == {
        "schema", "trial_id", "event", "recorded_utc", "model",
        "condition_id", "seed", "usage", "provider_cost_usd",
        "attempt_trace_sha256", "failure_code",
    }
    source = Path(ledger.__file__).read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY" not in source
    assert "build_development_validation_gold" not in source
    assert "AsyncOpenAI" not in source
    assert "chat/completions" not in source


def test_unapproved_candidate_is_not_overridden_by_cli_flags(context):
    _, candidate = context
    assert "scientific_execution_permitted" in candidate
    with pytest.raises(ledger.LedgerGateError):
        ledger.scientific_gate(candidate)
    assert "PHASE8_LEDGER_NO_PROVIDER_CALLS=true" in Path(ledger.__file__).read_text("utf-8")
