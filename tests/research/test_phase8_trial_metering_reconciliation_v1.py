"""No-network trial-to-provider metering reconciliation tests."""

from __future__ import annotations

import asyncio
import fcntl
import json
import os

import httpx
import pytest

from scripts.research.phase8_attempt_ledger import (
    event_template, load_verified_controls,
)
from scripts.research.phase8_provider_metering_v1 import (
    Phase8MeteringError, Phase8ProviderMeteringTransport,
)
from scripts.research.phase8_trial_metering_reconciliation_v1 import (
    Phase8TrialReconciliationError, reconcile_metered_terminal,
)


@pytest.fixture
def context():
    matrix, candidate = load_verified_controls()
    assert candidate["scientific_execution_permitted"] is False
    return matrix, matrix["trials"][0]


def write_mock_provider_calls(path, *, trial_id, model, costs=("0.001", "0.0025")):
    """Generate local receipts through the actual transport, never a provider."""
    next_response = iter(costs)

    def sink(_request):
        idx, cost = next_response.__next__()
        return httpx.Response(200, json={
            "id": f"gen-offline-{idx}",
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "OFFLINE_ONLY"},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 25,
                "total_tokens": 125,
                "cost": cost,
            },
        })

    enumerated_costs = tuple(enumerate(costs, start=1))
    next_response = iter(enumerated_costs)
    transport = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(sink), expected_model=model,
        trial_id=trial_id, ledger_path=path,
    )

    async def run():
        try:
            for _ in enumerated_costs:
                response = await transport.handle_async_request(httpx.Request(
                    "POST", "https://openrouter.ai/api/v1/chat/completions",
                    json={"model": model, "messages": []},
                ))
                assert response.status_code == 200
        finally:
            await transport.aclose()

    asyncio.run(run())


def terminal(matrix, trial, *, kind="SUCCEEDED"):
    event = event_template(trial, model=matrix["model"], kind=kind)
    event["usage"] = {"input_tokens": 200, "output_tokens": 50}
    event["provider_cost_usd"] = "0.0035"
    if kind == "SUCCEEDED":
        event["attempt_trace_sha256"] = "a" * 64
    else:
        event["failure_code"] = "MODEL_ERROR"
    return event


def test_two_raw_calls_exactly_match_trial_terminal(context, tmp_path):
    matrix, trial = context
    ledger = tmp_path / "metering.jsonl"
    write_mock_provider_calls(ledger, trial_id=trial["trial_id"], model=matrix["model"])
    evidence = reconcile_metered_terminal(
        matrix=matrix, terminal_event=terminal(matrix, trial),
        provider_ledger_path=ledger,
    )
    assert evidence["locally_reconciled"] is True
    assert evidence["independent_provider_billing_reconciled"] is False
    assert evidence["scientific_execution_approved"] is False
    assert evidence["provider_call_count"] == 2
    assert evidence["provider_usage"] == {"input_tokens": 200, "output_tokens": 50}
    assert evidence["provider_cost_usd"] == "0.0035"
    assert len(evidence["provider_ledger_sha256"]) == 64
    assert len(evidence["terminal_event_sha256"]) == 64
    assert "OFFLINE_ONLY" not in json.dumps(evidence)


def test_failed_terminal_can_reconcile_without_fabricating_success(context, tmp_path):
    matrix, trial = context
    ledger = tmp_path / "metering.jsonl"
    write_mock_provider_calls(ledger, trial_id=trial["trial_id"], model=matrix["model"])
    evidence = reconcile_metered_terminal(
        matrix=matrix, terminal_event=terminal(matrix, trial, kind="FAILED"),
        provider_ledger_path=ledger,
    )
    assert evidence["locally_reconciled"] is True
    assert evidence["scientific_execution_approved"] is False


@pytest.mark.parametrize("field,value", [
    ("provider_cost_usd", "0.0034"),
    ("provider_cost_usd", "NaN"),
    ("provider_cost_usd", None),
    ("usage", {"input_tokens": 199, "output_tokens": 50}),
    ("usage", {"input_tokens": True, "output_tokens": 50}),
    ("usage", {"input_tokens": 200, "output_tokens": 50, "total_tokens": 250}),
])
def test_declared_trial_totals_must_match_real_receipts(context, tmp_path, field, value):
    matrix, trial = context
    ledger = tmp_path / "metering.jsonl"
    write_mock_provider_calls(ledger, trial_id=trial["trial_id"], model=matrix["model"])
    event = terminal(matrix, trial)
    event[field] = value
    with pytest.raises(Phase8TrialReconciliationError):
        reconcile_metered_terminal(
            matrix=matrix, terminal_event=event,
            provider_ledger_path=ledger,
        )


def test_missing_provider_call_ledger_blocks_reconciliation(context, tmp_path):
    matrix, trial = context
    with pytest.raises(Phase8TrialReconciliationError, match="missing"):
        reconcile_metered_terminal(
            matrix=matrix, terminal_event=terminal(matrix, trial),
            provider_ledger_path=tmp_path / "not_written.jsonl",
        )


def test_wrong_trial_binding_blocks_reconciliation(context, tmp_path):
    matrix, trial = context
    ledger = tmp_path / "metering.jsonl"
    write_mock_provider_calls(ledger, trial_id=trial["trial_id"], model=matrix["model"])
    event = terminal(matrix, matrix["trials"][1])
    with pytest.raises(Phase8TrialReconciliationError, match="unverified or incomplete"):
        reconcile_metered_terminal(
            matrix=matrix, terminal_event=event,
            provider_ledger_path=ledger,
        )


def test_corrupt_local_provider_receipt_blocks_reconciliation(context, tmp_path):
    matrix, trial = context
    ledger = tmp_path / "metering.jsonl"
    write_mock_provider_calls(ledger, trial_id=trial["trial_id"], model=matrix["model"])
    lines = ledger.read_text().splitlines()
    data = json.loads(lines[0])
    data["provider_cost_usd"] = "0"
    lines[0] = json.dumps(data)
    ledger.write_text("\n".join(lines) + "\n")
    with pytest.raises(Phase8TrialReconciliationError, match="unverified"):
        reconcile_metered_terminal(
            matrix=matrix, terminal_event=terminal(matrix, trial),
            provider_ledger_path=ledger,
        )


def test_active_provider_session_lease_blocks_reconciliation(context, tmp_path):
    matrix, trial = context
    ledger = tmp_path / "metering.jsonl"
    write_mock_provider_calls(ledger, trial_id=trial["trial_id"], model=matrix["model"])
    lock_path = ledger.with_suffix(ledger.suffix + ".lock")
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        with pytest.raises(Phase8TrialReconciliationError, match="in flight"):
            reconcile_metered_terminal(
                matrix=matrix, terminal_event=terminal(matrix, trial),
                provider_ledger_path=ledger,
            )
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def test_not_a_terminal_and_invalid_science_trace_rejected(context, tmp_path):
    matrix, trial = context
    ledger = tmp_path / "metering.jsonl"
    write_mock_provider_calls(ledger, trial_id=trial["trial_id"], model=matrix["model"])
    started = event_template(trial, model=matrix["model"], kind="STARTED")
    with pytest.raises(Phase8TrialReconciliationError, match="terminal"):
        reconcile_metered_terminal(
            matrix=matrix, terminal_event=started,
            provider_ledger_path=ledger,
        )
    invalid = terminal(matrix, trial)
    invalid["attempt_trace_sha256"] = None
    with pytest.raises(Phase8TrialReconciliationError, match="invalid attempt terminal"):
        reconcile_metered_terminal(
            matrix=matrix, terminal_event=invalid,
            provider_ledger_path=ledger,
        )
