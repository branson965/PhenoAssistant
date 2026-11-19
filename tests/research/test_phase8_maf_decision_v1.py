"""Real MAF SDK request-shape tests with a MOCK HTTP provider.

All requests stay inside httpx.MockTransport. The synthetic approval JSON
exists only under pytest's tmp_path; it is not a supervisor attestation and
does not enable production scientific runs.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from phenoassistant_mcp.scientific_inference_v1 import (
    ImageAsset, build_phase8_scientific_mcp_server, file_sha256,
    verify_approved_runtime, ScientificMcpDispatchError,
)
from research.phenoguard.contracts import ApplicabilityDecision
from research.phenoguard.pilot_manifest import build_development_validation_manifest
from research.phenoguard.provenance import CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
from scripts.research.prepare_phase8_qualification_matrix import model_visible_view
from scripts.research.phase8_maf_decision_v1 import (
    C3, C4, C8, MODEL, Phase8MafDecisionClient, Phase8ProposalError,
    Proposal, _reject_leakage, critic_prompt, discover_real_mcp_tool,
    manager_prompt, parse_proposal, response_evidence, validate_mcp_schema,
)


@pytest.fixture
def view():
    return model_visible_view(build_development_validation_manifest()[0])


@pytest.fixture
def exact_tool():
    return {
        "name": "run_scientific_model",
        "description": "Run one approved scientific model on an approved image",
        "input_schema": {
            "type": "object",
            "properties": {
                "capability_id": {"type": "string"},
                "image_asset_id": {"type": "string"},
            },
            "required": ["capability_id", "image_asset_id"],
        },
    }


@pytest.fixture
def test_only_approved_record(tmp_path):
    historic = Path(
        "experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json"
    )
    record = json.loads(historic.read_text(encoding="utf-8"))
    record["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    record["scientific_execution_permitted"] = True
    record["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    record["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    path = tmp_path / "TEST_ONLY_NOT_VALID_SUPERVISOR_APPROVAL.json"
    path.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    return path, file_sha256(path)


def test_original_candidate_cannot_initialize_real_decision_client():
    historic = Path(
        "experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json"
    )
    with pytest.raises(ScientificMcpDispatchError, match="not been approved"):
        Phase8MafDecisionClient.create(
            approved_runtime_path=historic,
            approved_runtime_sha256=file_sha256(historic),
            api_key="SYNTHETIC-NO-REAL-KEY",
            seed=2026,
            upstream=httpx.MockTransport(lambda request: httpx.Response(500)),
        )


def test_c3_c4_manager_messages_exactly_equal_and_c8_soe_only(view, exact_tool):
    three = manager_prompt(C3, view, exact_tool)
    four = manager_prompt(C4, view, exact_tool)
    eight = manager_prompt(C8, view, exact_tool)
    assert three == four
    assert three[0] == eight[0]
    base = json.loads(three[1])
    c8 = json.loads(eight[1])
    assert "scientific_operating_envelopes" not in base
    assert len(c8["scientific_operating_envelopes"]) == 3
    assert c8["request"] == base["request"]
    assert c8["mcp_tool_schema"] == base["mcp_tool_schema"]
    assert "expected_decision" not in eight[1]
    assert "scenario_id" not in eight[1]


def test_generic_critic_does_not_receive_scientific_operating_envelopes(view, exact_tool):
    previous = Proposal(ApplicabilityDecision.EXECUTE, CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID)
    system, user = critic_prompt(view, exact_tool, previous)
    parsed = json.loads(user)
    assert "scientific_operating_envelopes" not in user
    assert "gold" not in parsed
    assert parsed["manager_proposal"]["decision"] == "EXECUTE"
    assert parsed["mcp_tool_schema"]["name"] == "run_scientific_model"
    assert "GENERIC LLM Critic" in system


@pytest.mark.parametrize("field", [
    "scenario_id", "category", "shift_dimension", "expected_decision",
    "pair_id", "split", "evidence_source", "fixture_refs",
])
def test_banned_internal_case_fields_rejected(field, view, exact_tool):
    tampered = dict(view)
    tampered[field] = "untrusted"
    with pytest.raises(Phase8ProposalError):
        manager_prompt(C3, tampered, exact_tool)


@pytest.mark.parametrize("parsed", [
    "Not JSON",
    '["EXECUTE", "model"]',
    '{"decision":"EXECUTE","capability_id":null}',
    '{"decision":"ABSTAIN","capability_id":"some-model"}',
    '{"decision":"EXECUTE","capability_id":"unknown/unsafe"}',
    '{"decision":"INVALID","capability_id":null}',
    '{"decision":"CLARIFY","capability_id":null,"explanation":"unfrozen"}',
])
def test_malformed_or_unregistered_model_proposal_rejected(parsed):
    with pytest.raises(Phase8ProposalError):
        parse_proposal(parsed)


def test_valid_registered_proposal_accepted():
    value = parse_proposal(json.dumps({
        "decision": "EXECUTE",
        "capability_id": CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    }))
    assert value.decision is ApplicabilityDecision.EXECUTE
    assert value.capability_id == CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID


@pytest.mark.parametrize("field,value", [
    ("name", "other_tool"),
    ("description", ""),
    ("input_schema", {"type": "object", "properties": {}}),
])
def test_untrusted_tool_schema_rejected(field, value, exact_tool):
    changed = dict(exact_tool)
    changed[field] = value
    with pytest.raises(Phase8ProposalError):
        validate_mcp_schema(changed)


def test_real_mcp_discovery_returns_exact_two_parameter_schema(
    tmp_path, test_only_approved_record,
):
    path, digest = test_only_approved_record
    image = tmp_path / "asset.png"
    image.write_bytes(b"FAKE_IMAGE_MCP_SCHEMA_INSPECTION_ONLY")
    asset = {"image_1": ImageAsset(image, file_sha256(image))}

    def fake_delegate(*_args):
        raise AssertionError("schema discovery must not dispatch a GPU tool")

    server = build_phase8_scientific_mcp_server(
        approved_runtime_file=path,
        approved_runtime_sha256=digest,
        frozen_trial_id="f" * 24,
        trusted_images=asset,
        output_root=tmp_path / "results",
        inference_delegate=fake_delegate,
    )
    tool = asyncio.run(discover_real_mcp_tool(server))
    assert tool["name"] == "run_scientific_model"
    assert set(tool["input_schema"]["properties"]) == {
        "capability_id", "image_asset_id"
    }
    assert set(tool["input_schema"]["required"]) == {
        "capability_id", "image_asset_id"
    }


def test_real_maf_manager_critic_wire_roundtrips_are_mock_only(
    tmp_path, view, exact_tool, test_only_approved_record,
):
    """Exercise genuine MAF + OpenAI SDK + compatibility transport, no network."""
    sent = []
    answer = json.dumps({
        "decision": "EXECUTE",
        "capability_id": CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    })

    async def fake_openrouter(request):
        payload = json.loads(request.content)
        sent.append(payload)
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-phase8-offline-mock",
                "object": "chat.completion",
                "created": 1795095000,
                "model": MODEL,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": answer},
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": 250,
                    "completion_tokens": 40,
                    "total_tokens": 290,
                },
            },
        )

    path, digest = test_only_approved_record
    async def run():
        service = Phase8MafDecisionClient.create(
            approved_runtime_path=path,
            approved_runtime_sha256=digest,
            api_key="sk-or-v1-OFFLINE-TEST-NOT-A-REAL-KEY",
            seed=2026,
            upstream=httpx.MockTransport(fake_openrouter),
        )
        try:
            c3 = await service.propose_manager(
                condition=C3, visible_view=view, discovered_tool=exact_tool,
            )
            c4 = await service.propose_manager(
                condition=C4, visible_view=view, discovered_tool=exact_tool,
            )
            critic = await service.critique(
                condition=C4, visible_view=view, discovered_tool=exact_tool,
                manager_proposal=c4.proposal,
            )
            c8 = await service.propose_manager(
                condition=C8, visible_view=view, discovered_tool=exact_tool,
            )
            return c3, c4, critic, c8
        finally:
            await service.close()

    c3, c4, critic, c8 = asyncio.run(run())
    assert c3.proposal.decision is ApplicabilityDecision.EXECUTE
    assert c4.proposal == c3.proposal
    assert critic.role == "generic_critic"
    assert c8.role == "manager"
    assert len(sent) == 4
    for payload in sent:
        assert payload["model"] == MODEL
        assert payload["seed"] == 2026
        assert payload["reasoning"] == {"effort": "medium"}
        assert payload["provider"] == {
            "order": ["openai"],
            "allow_fallbacks": False,
            "require_parameters": True,
        }
        assert payload["max_tokens"] == 2048
        assert "max_completion_tokens" not in payload
        assert "parallel_tool_calls" not in payload
        assert "temperature" not in payload
        assert payload.get("tool_choice") in ("none", None)
        assert "run_scientific_model" in json.dumps(payload)
    # Manager C3 and C4 are matched in their entire request except possible
    # protocol-assigned IDs, which do not appear in these payloads.
    assert sent[0] == sent[1]
    assert "scientific_operating_envelopes" not in json.dumps(sent[0])
    assert "scientific_operating_envelopes" not in json.dumps(sent[2])
    assert "scientific_operating_envelopes" in json.dumps(sent[3])


def test_real_client_rejects_critic_in_other_conditions(
    test_only_approved_record, exact_tool, view,
):
    path, digest = test_only_approved_record
    async def run():
        service = Phase8MafDecisionClient.create(
            approved_runtime_path=path,
            approved_runtime_sha256=digest,
            api_key="OFFLINE-NO-INFERENCE",
            seed=2026,
            upstream=httpx.MockTransport(
                lambda req: (_ for _ in ()).throw(
                    AssertionError("blocked C3 critic must not send request")
                )
            ),
        )
        try:
            with pytest.raises(Phase8ProposalError, match="only in C4"):
                await service.critique(
                    condition=C3, visible_view=view, discovered_tool=exact_tool,
                    manager_proposal=Proposal(ApplicabilityDecision.CLARIFY, None),
                )
        finally:
            await service.close()
    asyncio.run(run())


def test_no_scientific_cli_execution_or_hidden_gold_access():
    source = Path("scripts/research/phase8_maf_decision_v1.py").read_text("utf-8")
    assert "build_development_validation_gold" not in source
    assert 'os.environ.get("OPENROUTER_API_KEY")' not in source
    assert "PHASE8_MAF_DECISION_ACTUAL_REQUESTS=0" in source
    assert "PHASE8_MAF_DECISION_APPROVED_TO_RUN=false" in source
    assert "OpenRouterCompatTransport" in source
