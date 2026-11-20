"""Real MAF SDK C4 Critic and C8 verifier, fake provider, no MCP/GPU.

A native Manager function-call callback does NOT execute a scientific
model. The independent generic-Critic review is an additional MAF call.
Provider responses are synthetic httpx.MockTransport replies and do not
represent any empirical scientific outcome or billing evidence.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from phenoassistant_mcp.scientific_inference_v1 import (
    ImageAsset, build_phase8_scientific_mcp_server, file_sha256,
)
from research.phenoguard.contracts import ApplicabilityDecision as Action
from research.phenoguard.pilot_manifest import build_development_validation_manifest
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID as CASE1,
    CASE2_POTATO_SEGMENTATION_MODEL_ID as CASE2,
)
from scripts.research.prepare_phase8_qualification_matrix import model_visible_view
from scripts.research.phase8_condition_rehearsal import C3, C4, C8, Proposal
from scripts.research.phase8_maf_decision_v1 import (
    MODEL, Phase8MafDecisionClient, Phase8ProposalError, ProposalEvidence,
    discover_real_mcp_tool,
)
from scripts.research.phase8_native_tool_capture_v1 import (
    IMAGE_ARGUMENT_PLACEHOLDER, NativeToolProposal,
)
from scripts.research.phase8_native_condition_mediation_v1 import (
    mediate_native_proposal, mediate_one_native_condition,
)


@pytest.fixture
def runtime(tmp_path):
    original = json.loads(Path(
        "experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json"
    ).read_text(encoding="utf-8"))
    original["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    original["scientific_execution_permitted"] = True
    original["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    original["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    file = tmp_path / "TEST_ONLY_SYNTHETIC_APPROVAL_NOT_FOR_SCIENCE.json"
    file.write_text(json.dumps(original, sort_keys=True), encoding="utf-8")
    return file, file_sha256(file)


@pytest.fixture
def schema():
    return {
        "name": "run_scientific_model",
        "description": "Execute one registered model for an approved image asset",
        "input_schema": {
            "type": "object",
            "properties": {
                "capability_id": {"type": "string"},
                "image_asset_id": {"type": "string"},
            },
            "required": ["capability_id", "image_asset_id"],
        },
    }


def view(index=0):
    return model_visible_view(build_development_validation_manifest()[index])


def fake_reply(*, tool=None, decision=None):
    message = {"role": "assistant", "content": (
        json.dumps(decision) if decision is not None else None
    )}
    if tool is not None:
        message["tool_calls"] = [{
            "id": "call_scientific_proposal_local_001",
            "type": "function",
            "function": {
                "name": "run_scientific_model",
                "arguments": json.dumps({
                    "capability_id": tool,
                    "image_asset_id": IMAGE_ARGUMENT_PLACEHOLDER,
                }),
            },
        }]
    return httpx.Response(200, json={
        "id": "chatcmpl-local-native-mediation",
        "object": "chat.completion",
        "created": 1795095000,
        "model": MODEL,
        "choices": [{
            "index": 0,
            "message": message,
            "finish_reason": "tool_calls" if tool is not None else "stop",
        }],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 30,
            "total_tokens": 130,
        },
    })


async def run_condition(*, runtime, condition, scenario, schema, replies):
    sent = []

    async def fake_http(request):
        payload = json.loads(request.content)
        sent.append(payload)
        if len(sent) > len(replies):
            raise AssertionError("unexpected extra provider roundtrip")
        return replies[len(sent) - 1]

    path, digest = runtime
    client = Phase8MafDecisionClient.create(
        approved_runtime_path=path,
        approved_runtime_sha256=digest,
        api_key="sk-or-v1-OFFLINE-ONLY-NEVER-REAL",
        seed=2026,
        upstream=httpx.MockTransport(fake_http),
    )
    try:
        obs = await mediate_one_native_condition(
            client=client,
            condition=condition,
            visible_view=scenario,
            discovered_tool=schema,
        )
        return obs, sent
    finally:
        await client.close()


def test_c4_real_maf_native_tool_then_generic_critic_veto(
    runtime, schema,
):
    replies = [
        fake_reply(tool=CASE1),
        fake_reply(decision=None),  # MAF post-tool confirmation
        fake_reply(decision={"decision": "ABSTAIN", "capability_id": None}),
    ]
    obs, sent = asyncio.run(run_condition(
        runtime=runtime, condition=C4, scenario=view(),
        schema=schema, replies=replies,
    ))
    assert obs.manager_decision is Action.EXECUTE
    assert obs.manager_selected_capability_id == CASE1
    assert obs.native_tool_calls_captured == 1
    assert obs.critic_called is True
    assert obs.critic_decision is Action.ABSTAIN
    assert obs.final_decision is Action.ABSTAIN
    assert obs.final_selected_capability_id is None
    assert obs.c8_precheck_applied is False
    assert obs.mcp_calls == 0
    assert obs.gpu_calls == 0
    assert obs.provider_billed_cost_available is False
    assert obs.critic_response_sha256 is not None
    assert len(sent) == 3
    assert "scientific_operating_envelopes" not in json.dumps(sent)
    assert len(sent[0].get("tools", [])) == 1
    assert sent[2].get("tools") in (None, [])
    assert sent[2].get("tool_choice") in (None, "none")
    assert "run_scientific_model" in json.dumps(sent[2])
    assert "ABSTAIN" not in json.dumps(sent[0])


def test_c4_critic_cannot_fabricate_tool_execution_after_manager_no_call(
    runtime, schema,
):
    replies = [
        fake_reply(decision={"decision": "CLARIFY", "capability_id": None}),
        fake_reply(decision={"decision": "EXECUTE", "capability_id": CASE1}),
    ]
    with pytest.raises(Phase8ProposalError, match="cannot create an executable"):
        asyncio.run(run_condition(
            runtime=runtime, condition=C4, scenario=view(),
            schema=schema, replies=replies,
        ))


def test_c4_can_review_registered_alternative_but_not_forge_native_provenance(
    runtime, schema,
):
    replies = [
        fake_reply(tool=CASE1),
        fake_reply(decision=None),
        fake_reply(decision={"decision": "RESELECT", "capability_id": CASE2}),
    ]
    obs, sent = asyncio.run(run_condition(
        runtime=runtime, condition=C4, scenario=view(),
        schema=schema, replies=replies,
    ))
    assert obs.native_tool_calls_captured == 1
    assert obs.critic_decision is Action.RESELECT
    assert obs.final_selected_capability_id == CASE2
    assert obs.reviewer_changed_selection is True
    assert obs.mcp_calls == 0
    assert obs.gpu_calls == 0
    assert len(sent) == 3


def test_c3_stays_native_and_does_not_invoke_critic(runtime, schema):
    obs, sent = asyncio.run(run_condition(
        runtime=runtime, condition=C3, scenario=view(),
        schema=schema,
        replies=[fake_reply(tool=CASE1), fake_reply(decision=None)],
    ))
    assert obs.critic_called is False
    assert obs.final_decision is Action.EXECUTE
    assert obs.final_selected_capability_id == CASE1
    assert obs.native_tool_calls_captured == 1
    assert len(sent) == 2


def test_c8_verifies_manager_selected_model_not_original_requested_model(
    runtime, schema,
):
    # Original request is Arabidopsis/CASE1; native Manager instead
    # selects potato/CASE2. Real SOE precheck should detect this.
    obs, sent = asyncio.run(run_condition(
        runtime=runtime, condition=C8, scenario=view(0),
        schema=schema,
        replies=[fake_reply(tool=CASE2), fake_reply(decision=None)],
    ))
    assert obs.manager_selected_capability_id == CASE2
    assert obs.manager_decision is Action.RESELECT
    assert obs.c8_precheck_applied is True
    assert obs.final_decision is Action.RESELECT
    assert obs.final_selected_capability_id == CASE1
    assert obs.reviewer_changed_selection is True
    assert obs.native_tool_calls_captured == 1
    assert obs.critic_called is False
    assert "scientific_operating_envelopes" in json.dumps(sent[0])
    assert obs.mcp_calls == 0 and obs.gpu_calls == 0


def test_c8_no_native_call_cannot_start_model(runtime, schema):
    obs, sent = asyncio.run(run_condition(
        runtime=runtime, condition=C8, scenario=view(0),
        schema=schema,
        replies=[fake_reply(decision={"decision": "CLARIFY", "capability_id": None})],
    ))
    assert obs.final_decision is Action.CLARIFY
    assert obs.final_selected_capability_id is None
    assert obs.native_tool_calls_captured == 0
    assert obs.c8_precheck_applied is False
    assert len(sent) == 1


def test_c3_c4_native_manager_wire_first_requests_identical(runtime, schema):
    replies = [fake_reply(tool=CASE1), fake_reply(decision=None)]
    _, sent3 = asyncio.run(run_condition(
        runtime=runtime, condition=C3, scenario=view(), schema=schema,
        replies=replies,
    ))
    _, sent4 = asyncio.run(run_condition(
        runtime=runtime, condition=C4, scenario=view(), schema=schema,
        replies=[
            *replies,
            fake_reply(decision={"decision": "EXECUTE", "capability_id": CASE1}),
        ],
    ))
    assert sent3[0] == sent4[0]
    assert sent3[1] == sent4[1]


def test_c4_critic_receives_actual_mcp_schema_without_tool_execution(
    tmp_path, runtime,
):
    path, digest = runtime
    image = tmp_path / "dummy.png"
    image.write_bytes(b"FAKE-NOT-SCIENTIFIC-IMAGE")
    assets = {"app_image_001": ImageAsset(image, file_sha256(image))}
    observed = []

    def fake_vision(*args):
        raise AssertionError("MCP dispatcher must never be reached by mediation")

    server = build_phase8_scientific_mcp_server(
        approved_runtime_file=path,
        approved_runtime_sha256=digest,
        frozen_trial_id="b" * 24,
        trusted_images=assets,
        output_root=tmp_path / "no-mcp-output",
        inference_delegate=fake_vision,
    )

    async def run():
        discovered = await discover_real_mcp_tool(server)
        assert set(discovered["input_schema"]["properties"]) == {
            "capability_id", "image_asset_id",
        }
        return await run_condition(
            runtime=runtime, condition=C4, scenario=view(),
            schema=discovered,
            replies=[
                fake_reply(tool=CASE1),
                fake_reply(decision=None),
                fake_reply(decision={"decision": "ABSTAIN", "capability_id": None}),
            ],
        )

    obs, sent = asyncio.run(run())
    assert obs.final_decision is Action.ABSTAIN
    assert not (tmp_path / "no-mcp-output").exists()
    assert len(sent) == 3
    assert sent[0]["tools"][0]["function"]["description"] != ""


def test_native_mediation_rejects_fabricated_no_call_execution():
    invalid = NativeToolProposal(
        decision=Proposal(Action.EXECUTE, CASE1),
        captured_function_call_count=0,
        application_bound_asset_placeholder=None,
        response_model=MODEL,
        prompt_sha256="a" * 64,
        response_text_sha256="a" * 64,
    )
    with pytest.raises(Phase8ProposalError, match="executable decision without native call"):
        mediate_native_proposal(
            condition=C3, visible_view=view(), manager=invalid, critic=None,
        )


def test_native_mediation_rejects_critic_in_c8_or_c3():
    valid = NativeToolProposal(
        decision=Proposal(Action.EXECUTE, CASE1),
        captured_function_call_count=1,
        application_bound_asset_placeholder=IMAGE_ARGUMENT_PLACEHOLDER,
        response_model=MODEL,
        prompt_sha256="a" * 64,
        response_text_sha256="b" * 64,
    )
    critic = ProposalEvidence(
        role="generic_critic",
        proposal=Proposal(Action.ABSTAIN, None),
        response_model=MODEL,
        response_sha256="c" * 64,
        fingerprint=None,
        input_tokens=30,
        output_tokens=10,
    )
    for condition in (C3, C8):
        with pytest.raises(Phase8ProposalError, match="outside C4"):
            mediate_native_proposal(
                condition=condition, visible_view=view(), manager=valid, critic=critic,
            )


def test_native_mediation_standalone_preflight_never_uses_key_or_gpu():
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env.pop("OPENROUTER_API_KEY", None)
    run = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/research/phase8_native_condition_mediation_v1.py"),
        ],
        cwd=root, env=env, capture_output=True, text=True, timeout=25,
        check=False,
    )
    assert run.returncode == 0, run.stderr[-1600:]
    assert "PHASE8_NATIVE_MEDIATION_C4_CRITIC_IMPLEMENTED=true" in run.stdout
    assert "PHASE8_NATIVE_MEDIATION_MCP_CALLS=0" in run.stdout
    assert "PHASE8_NATIVE_MEDIATION_PROVIDER_CALLS=0" in run.stdout
    assert "PHASE8_NATIVE_MEDIATION_GPU_CALLS=0" in run.stdout
    assert "PHASE8_NATIVE_MEDIATION_EXECUTION_APPROVED=false" in run.stdout
    assert "PHASE8_NATIVE_MEDIATION_OFFLINE_PREFLIGHT_PASS=true" in run.stdout


def test_native_mediation_has_no_gold_or_outcome_bearing_runner():
    source = Path(
        "scripts/research/phase8_native_condition_mediation_v1.py"
    ).read_text(encoding="utf-8")
    assert "build_development_validation_gold" not in source
    assert "OPENROUTER_API_KEY" not in source
    assert "McpV2Session" not in source
    assert "run_scientific_model" not in source
