"""Offline tests for exact OpenRouter per-call charge provenance (no network)."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest

from scripts.research.phase8_provider_metering_v1 import (
    Phase8MeteringError,
    Phase8ProviderMeteringTransport,
    extract_provider_metering,
    read_verified_metering,
    summarize_trial_metering,
)

MODEL = "openai/gpt-5.6-luna"
TRIAL = "PHASE8-TEST-ONLY"


def reply(*, cost="0.001234", usage_changes=None, **changes):
    usage = {
        "prompt_tokens": 100,
        "completion_tokens": 25,
        "total_tokens": 125,
        "cost": cost,
    }
    usage.update(usage_changes or {})
    body = {
        "id": "gen-offline-0001",
        "object": "chat.completion",
        "created": 1795095000,
        "model": MODEL,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "synthetic"},
            "finish_reason": "stop",
        }],
        "usage": usage,
    }
    body.update(changes)
    return httpx.Response(200, json=body)


def request():
    return httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": "Bearer SYNTHETIC-SECRET"},
        json={"model": MODEL, "messages": [
            {"role": "user", "content": "SECRET_PRIVATE_PROMPT"},
        ]},
    )


def run_roundtrips(transport, count=1):
    async def run():
        try:
            return [
                (await transport.handle_async_request(request())).status_code
                for _ in range(count)
            ]
        finally:
            await transport.aclose()
    return asyncio.run(run())


def test_raw_usage_cost_is_preserved_not_computed_from_tokens():
    response = reply(cost=0.00012345)
    result = extract_provider_metering(response.content, expected_model=MODEL)
    assert result["usage"] == {
        "input_tokens": 100, "output_tokens": 25, "total_tokens": 125,
    }
    assert result["provider_cost_usd"] == "0.00012345"
    assert len(result["response_sha256"]) == 64


def test_two_calls_write_private_chained_append_only_records(tmp_path):
    calls = []

    def sink(req):
        calls.append(req)
        answer = reply(cost="0.0025" if len(calls) == 2 else "0.001234")
        if len(calls) == 2:
            body = json.loads(answer.content)
            body["id"] = "gen-offline-0002"
            return httpx.Response(200, json=body)
        return answer

    ledger = tmp_path / "metering.jsonl"
    transport = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(sink), expected_model=MODEL,
        trial_id=TRIAL, ledger_path=ledger,
    )
    assert run_roundtrips(transport, 2) == [200, 200]
    events = read_verified_metering(ledger, trial_id=TRIAL, model=MODEL)
    assert len(events) == 2
    assert events[0]["event"] == events[1]["event"] == "METERED"
    assert events[0]["previous_entry_sha256"] is None
    assert events[1]["previous_entry_sha256"] == events[0]["entry_sha256"]
    assert events[0]["provider_response_id"] == "gen-offline-0001"
    assert len(events[0]["response_sha256"]) == 64
    aggregate = summarize_trial_metering(ledger, trial_id=TRIAL, model=MODEL)
    assert aggregate["call_count"] == 2
    assert aggregate["usage"] == {"input_tokens": 200, "output_tokens": 50}
    assert aggregate["provider_cost_usd"] == "0.003734"
    assert aggregate["last_entry_sha256"] == events[-1]["entry_sha256"]
    raw = ledger.read_text()
    assert "SECRET_PRIVATE_PROMPT" not in raw
    assert "SYNTHETIC-SECRET" not in raw
    assert "synthetic" not in raw
    assert os.stat(ledger).st_mode & 0o077 == 0


@pytest.mark.parametrize("bad_cost", [None, "", "-0.01", "NaN", True])
def test_missing_or_invalid_charge_halts_next_call(tmp_path, bad_cost):
    calls = []

    def sink(req):
        calls.append(1)
        if bad_cost is None:
            body = json.loads(reply().content)
            del body["usage"]["cost"]
            return httpx.Response(200, json=body)
        return reply(cost=bad_cost)

    ledger = tmp_path / "usage_missing.jsonl"
    transport = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(sink), expected_model=MODEL,
        trial_id=TRIAL, ledger_path=ledger,
    )

    async def run():
        try:
            with pytest.raises(Phase8MeteringError, match="metering unavailable"):
                await transport.handle_async_request(request())
            with pytest.raises(Phase8MeteringError, match="session blocked"):
                await transport.handle_async_request(request())
        finally:
            await transport.aclose()

    asyncio.run(run())
    assert len(calls) == 1
    events = read_verified_metering(ledger, trial_id=TRIAL, model=MODEL)
    assert len(events) == 1
    assert events[0]["event"] == "METERING_MISSING"
    assert events[0]["failure_code"] == "INVALID_USAGE"
    assert events[0]["provider_cost_usd"] is None
    with pytest.raises(Phase8MeteringError, match="incomplete"):
        summarize_trial_metering(ledger, trial_id=TRIAL, model=MODEL)


@pytest.mark.parametrize("changed", [
    {"usage_changes": {"prompt_tokens": True}},
    {"usage_changes": {"total_tokens": 126}},
    {"usage_changes": {"completion_tokens": -1}},
    {"model": "other/provider-model"},
    {"id": ""},
    {"usage": None},
    {"object": "not-a-chat-completion"},
])
def test_malformed_provider_usage_or_identity_fails_closed(tmp_path, changed):
    def sink(req):
        usage_changes = changed.get("usage_changes")
        kwargs = {k: v for k, v in changed.items() if k != "usage_changes"}
        return reply(usage_changes=usage_changes, **kwargs)

    ledger = tmp_path / "rejected.jsonl"
    transport = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(sink), expected_model=MODEL,
        trial_id=TRIAL, ledger_path=ledger,
    )

    async def run():
        try:
            with pytest.raises(Phase8MeteringError):
                await transport.handle_async_request(request())
        finally:
            await transport.aclose()
    asyncio.run(run())
    assert read_verified_metering(ledger, trial_id=TRIAL, model=MODEL)[0]["event"] == "METERING_MISSING"


@pytest.mark.parametrize("kind", ["http", "network"])
def test_http_error_or_network_failure_records_unknown_billing(tmp_path, kind):
    def sink(req):
        if kind == "network":
            raise httpx.ConnectError("OFFLINE TEST CONNECT FAILED")
        return httpx.Response(429, json={"error": "rate limit"})

    ledger = tmp_path / "failed.jsonl"
    transport = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(sink), expected_model=MODEL,
        trial_id=TRIAL, ledger_path=ledger,
    )
    async def run():
        try:
            with pytest.raises(Phase8MeteringError):
                await transport.handle_async_request(request())
        finally:
            await transport.aclose()
    asyncio.run(run())
    events = read_verified_metering(ledger, trial_id=TRIAL, model=MODEL)
    assert len(events) == 1
    assert events[0]["event"] == "METERING_MISSING"
    assert events[0]["failure_code"] == ("TRANSPORT_ERROR" if kind == "network" else "HTTP_ERROR")


def test_corrupted_evidence_is_rejected_not_silently_overwritten(tmp_path):
    ledger = tmp_path / "corrupt.jsonl"
    transport = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(lambda req: reply()),
        expected_model=MODEL, trial_id=TRIAL, ledger_path=ledger,
    )
    assert run_roundtrips(transport) == [200]
    data = json.loads(ledger.read_text())
    data["provider_cost_usd"] = "0.00"
    ledger.write_text(json.dumps(data) + "\n")
    with pytest.raises(Phase8MeteringError, match="modified"):
        read_verified_metering(ledger, trial_id=TRIAL, model=MODEL)


def test_preexisting_ledger_blocks_new_transport_before_network(tmp_path):
    ledger = tmp_path / "existing.jsonl"
    transport = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(lambda req: reply()),
        expected_model=MODEL, trial_id=TRIAL, ledger_path=ledger,
    )
    assert run_roundtrips(transport) == [200]
    called = []
    second = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(lambda req: (called.append(1), reply())[1]),
        expected_model=MODEL, trial_id=TRIAL, ledger_path=ledger,
    )
    async def run():
        try:
            with pytest.raises(Phase8MeteringError, match="already used"):
                await second.handle_async_request(request())
        finally:
            await second.aclose()
    asyncio.run(run())
    assert called == []


def test_no_provider_call_on_concurrent_trial_lease(tmp_path):
    ledger = tmp_path / "locked.jsonl"
    lock_path = ledger.with_suffix(".jsonl.lock")
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    import fcntl
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    calls = []
    transport = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(lambda req: (calls.append(1), reply())[1]),
        expected_model=MODEL, trial_id=TRIAL, ledger_path=ledger,
    )
    async def run():
        try:
            with pytest.raises(Phase8MeteringError, match="another provider call"):
                await transport.handle_async_request(request())
        finally:
            await transport.aclose()
    try:
        asyncio.run(run())
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
    assert not calls


def test_guarded_maf_client_records_raw_billing_without_live_network(tmp_path):
    """Actual client transport stack, MockTransport only, no GPU or paid provider."""
    from phenoassistant_mcp.scientific_inference_v1 import file_sha256
    from scripts.research.phase8_maf_decision_v1 import (
        MODEL as MAF_MODEL, Phase8MafDecisionClient, Phase8ProposalError,
    )

    candidate = json.loads(Path(
        "experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json"
    ).read_text(encoding="utf-8"))
    candidate["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    candidate["scientific_execution_permitted"] = True
    candidate["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    candidate["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    runtime = tmp_path / "SYNTHETIC_MOCK_ONLY_APPROVAL.json"
    runtime.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
    ledger = tmp_path / "provider.jsonl"
    sent = []

    async def provider(req):
        sent.append(json.loads(req.content))
        return reply(cost="0.008")

    async def run():
        client = Phase8MafDecisionClient.create(
            approved_runtime_path=runtime,
            approved_runtime_sha256=file_sha256(runtime),
            api_key="SYNTHETIC-NOT-A-PROVIDER-KEY",
            seed=2026,
            upstream=httpx.MockTransport(provider),
            metering_trial_id=TRIAL,
            metering_ledger_path=ledger,
        )
        try:
            payload = {
                "model": MAF_MODEL,
                "messages": [{"role": "user", "content": "OFFLINE TEST ONLY"}],
                "tools": [],
                "tool_choice": "none",
                "max_completion_tokens": 2048,
                "seed": 2026,
                "reasoning": {"effort": "medium"},
                "provider": {
                    "order": ["openai"],
                    "allow_fallbacks": False,
                    "require_parameters": True,
                },
                "stream": False,
            }
            response = await client.http_client.post(
                "https://openrouter.ai/api/v1/chat/completions", json=payload,
            )
            assert response.status_code == 200
            assert client.provider_metering is not None
            assert client.raw_tool_guard.provider_replies_checked == 1
        finally:
            await client.close()

    asyncio.run(run())
    assert len(sent) == 1
    assert sent[0]["max_tokens"] == 2048
    assert "max_completion_tokens" not in sent[0]
    assert summarize_trial_metering(
        ledger, trial_id=TRIAL, model=MODEL,
    )["provider_cost_usd"] == "0.008"
    assert "OFFLINE TEST ONLY" not in ledger.read_text()


def test_maf_client_rejects_half_configured_metering(tmp_path):
    from phenoassistant_mcp.scientific_inference_v1 import file_sha256
    from scripts.research.phase8_maf_decision_v1 import (
        Phase8MafDecisionClient, Phase8ProposalError,
    )

    candidate = json.loads(Path(
        "experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json"
    ).read_text(encoding="utf-8"))
    candidate["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    candidate["scientific_execution_permitted"] = True
    candidate["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    candidate["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    runtime = tmp_path / "MOCK_ONLY_RUNTIME.json"
    runtime.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")

    with pytest.raises(Phase8ProposalError, match="supplied together"):
        Phase8MafDecisionClient.create(
            approved_runtime_path=runtime,
            approved_runtime_sha256=file_sha256(runtime),
            api_key="SYNTHETIC-NOT-A-PROVIDER-KEY",
            seed=2026,
            upstream=httpx.MockTransport(lambda req: reply()),
            metering_ledger_path=tmp_path / "missing-trial.jsonl",
        )

def test_duplicate_provider_generation_cannot_be_double_counted(tmp_path):
    ledger = tmp_path / "duplicate.jsonl"
    transport = Phase8ProviderMeteringTransport(
        upstream=httpx.MockTransport(lambda req: reply()),
        expected_model=MODEL, trial_id=TRIAL, ledger_path=ledger,
    )
    async def run():
        try:
            first = await transport.handle_async_request(request())
            assert first.status_code == 200
            with pytest.raises(Phase8MeteringError, match="duplicate provider generation"):
                await transport.handle_async_request(request())
        finally:
            await transport.aclose()
    asyncio.run(run())
    assert len(read_verified_metering(ledger, trial_id=TRIAL, model=MODEL)) == 1
