"""Native MAF function-call capture qualification, with fake HTTP only.

One SAFE capture-only @tool is given to the REAL MAF client. The test
provider is httpx.MockTransport and cannot reach OpenRouter, a GPU,
or the scientific MCP server. Synthetic approvals are temporary test data.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from phenoassistant_mcp.scientific_inference_v1 import file_sha256
from research.phenoguard.contracts import ApplicabilityDecision
from research.phenoguard.pilot_manifest import build_development_validation_manifest
from research.phenoguard.provenance import CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID as CASE1
from scripts.research.prepare_phase8_qualification_matrix import model_visible_view
from scripts.research.phase8_maf_decision_v1 import (
    C3, C4, C8, MODEL, Phase8MafDecisionClient, Phase8ProposalError,
)
from scripts.research.phase8_native_tool_capture_v1 import (
    IMAGE_ARGUMENT_PLACEHOLDER, NATIVE_INSTRUCTIONS,
    capture_one_native_manager_proposal,
)


@pytest.fixture
def approved_test_runtime(tmp_path):
    historic = json.loads(
        Path("experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json")
        .read_text(encoding="utf-8")
    )
    historic["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    historic["scientific_execution_permitted"] = True
    historic["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    historic["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    path = tmp_path / "SYNTHETIC_TEST_ONLY_NO_REAL_APPROVAL.json"
    path.write_text(json.dumps(historic, sort_keys=True), encoding="utf-8")
    return path, file_sha256(path)


@pytest.fixture
def view():
    return model_visible_view(build_development_validation_manifest()[0])


@pytest.fixture
def schema():
    return {
        "name": "run_scientific_model",
        "description": "Execute registered model on bound image asset",
        "input_schema": {
            "type": "object",
            "properties": {
                "capability_id": {"type": "string"},
                "image_asset_id": {"type": "string"},
            },
            "required": ["capability_id", "image_asset_id"],
        },
    }


def response(*, text=None, calls=None, finished="stop"):
    message = {"role": "assistant", "content": text}
    if calls is not None:
        message["tool_calls"] = [{
            "id": "call_native_capture_001",
            "type": "function",
            "function": {
                "name": "run_scientific_model",
                "arguments": json.dumps(calls),
            },
        }]
    return httpx.Response(200, json={
        "id": "chatcmpl-native-capture-local-only",
        "object": "chat.completion",
        "created": 1795095000,
        "model": MODEL,
        "choices": [{
            "index": 0, "message": message, "finish_reason": finished,
        }],
        "usage": {"prompt_tokens": 180, "completion_tokens": 32, "total_tokens": 212},
    })


async def run_capture(
    *,
    runtime, visible, schema, condition, responses,
):
    sent = []
    async def fake_provider(request):
        payload = json.loads(request.content)
        sent.append(payload)
        index = len(sent) - 1
        if index >= len(responses):
            raise AssertionError("unexpected additional MAF model roundtrip")
        return responses[index]

    path, digest = runtime
    client = Phase8MafDecisionClient.create(
        approved_runtime_path=path,
        approved_runtime_sha256=digest,
        api_key="sk-or-v1-SYNTHETIC-OFFLINE-TEST-KEY",
        seed=2026,
        upstream=httpx.MockTransport(fake_provider),
    )
    try:
        result = await capture_one_native_manager_proposal(
            client=client, condition=condition,
            visible_view=visible, discovered_tool=schema,
        )
        return result, sent
    finally:
        await client.close()


def test_native_function_call_capture_is_real_maf_and_no_scientific_execution(
    approved_test_runtime, view, schema,
):
    expected = {
        "capability_id": CASE1,
        "image_asset_id": IMAGE_ARGUMENT_PLACEHOLDER,
    }
    responses = [
        response(calls=expected, finished="tool_calls"),
        response(text="proposal recorded"),
    ]
    output, sent = asyncio.run(run_capture(
        runtime=approved_test_runtime, visible=view, schema=schema,
        condition=C3, responses=responses,
    ))
    assert output.decision.decision == ApplicabilityDecision.EXECUTE
    assert output.decision.capability_id == CASE1
    assert output.captured_function_call_count == 1
    assert output.application_bound_asset_placeholder == IMAGE_ARGUMENT_PLACEHOLDER
    assert output.scientific_mcp_calls == 0
    assert output.gpu_inference_calls == 0
    assert output.provider_cost_measured is None
    assert output.result_scope == "NATIVE_CALL_CAPTURE_ONLY_NOT_SCIENTIFIC_EVALUATION"
    assert len(sent) == 2  # one tool call and one post-capture message

    first = sent[0]
    assert first["model"] == MODEL
    assert first["seed"] == 2026
    assert first["provider"] == {
        "order": ["openai"], "allow_fallbacks": False,
        "require_parameters": True,
    }
    assert first["reasoning"] == {"effort": "medium"}
    assert first["max_tokens"] == 2048
    assert "max_completion_tokens" not in first
    assert "temperature" not in first
    assert "parallel_tool_calls" not in first
    assert first["tool_choice"] == "auto"
    assert len(first["tools"]) == 1
    function = first["tools"][0]["function"]
    assert function["name"] == "run_scientific_model"
    assert set(function["parameters"]["properties"]) == {
        "capability_id", "image_asset_id",
    }
    assert set(function["parameters"]["required"]) == {
        "capability_id", "image_asset_id",
    }
    assert "expected_decision" not in json.dumps(first)
    assert "scenario_id" not in json.dumps(first)
    assert "image_path_internal_only" not in json.dumps(first)
    assert "scientific_operating_envelopes" not in json.dumps(first)


def test_native_no_call_valid_abstention_has_no_mcp_execution(
    approved_test_runtime, view, schema,
):
    responses = [response(text=json.dumps({
        "decision": "CLARIFY", "capability_id": None,
    }))]
    result, sent = asyncio.run(run_capture(
        runtime=approved_test_runtime, visible=view, schema=schema,
        condition=C3, responses=responses,
    ))
    assert result.captured_function_call_count == 0
    assert result.decision.decision is ApplicabilityDecision.CLARIFY
    assert result.application_bound_asset_placeholder is None
    assert result.gpu_inference_calls == 0
    assert len(sent) == 1


def test_native_no_call_cannot_be_fabricated_as_execution(
    approved_test_runtime, view, schema,
):
    responses = [response(text=json.dumps({
        "decision": "EXECUTE", "capability_id": CASE1,
    }))]
    with pytest.raises(Phase8ProposalError, match="without native tool-call"):
        asyncio.run(run_capture(
            runtime=approved_test_runtime, visible=view, schema=schema,
            condition=C3, responses=responses,
        ))


@pytest.mark.parametrize("arguments", [
    {"capability_id": "bad/unregistered", "image_asset_id": IMAGE_ARGUMENT_PLACEHOLDER},
    {"capability_id": CASE1, "image_asset_id": "/tmp/private_file.png"},
    {"capability_id": CASE1, "image_asset_id": "../escape"},
    {"capability_id": CASE1, "image_asset_id": "unapproved_id"},
])
def test_native_callback_rejects_invalid_capability_or_private_asset(
    approved_test_runtime, view, schema, arguments,
):
    responses = [
        response(calls=arguments, finished="tool_calls"),
        response(text="unreachable"),
    ]
    # MAF may wrap callback exceptions in its own ChatClientException; in
    # either case no safe proposal may be returned by this API.
    with pytest.raises(Exception):
        asyncio.run(run_capture(
            runtime=approved_test_runtime, visible=view, schema=schema,
            condition=C3, responses=responses,
        ))


def test_native_c3_and_c4_manager_request_shapes_equal(
    approved_test_runtime, view, schema,
):
    calls = {
        "capability_id": CASE1, "image_asset_id": IMAGE_ARGUMENT_PLACEHOLDER,
    }
    responses = [
        response(calls=calls, finished="tool_calls"),
        response(text="tool selection captured"),
    ]
    result3, sent3 = asyncio.run(run_capture(
        runtime=approved_test_runtime, visible=view, schema=schema,
        condition=C3, responses=responses,
    ))
    result4, sent4 = asyncio.run(run_capture(
        runtime=approved_test_runtime, visible=view, schema=schema,
        condition=C4, responses=responses,
    ))
    assert sent3 == sent4
    assert result3.prompt_sha256 == result4.prompt_sha256
    assert result4.captured_function_call_count == 1


def test_native_c8_exposes_soe_only_c8(
    approved_test_runtime, view, schema,
):
    choices = [response(text='{"decision":"CLARIFY","capability_id":null}')]
    result8, sent8 = asyncio.run(run_capture(
        runtime=approved_test_runtime, visible=view, schema=schema,
        condition=C8, responses=choices,
    ))
    result3, sent3 = asyncio.run(run_capture(
        runtime=approved_test_runtime, visible=view, schema=schema,
        condition=C3, responses=choices,
    ))
    assert "scientific_operating_envelopes" in json.dumps(sent8[0])
    assert "scientific_operating_envelopes" not in json.dumps(sent3[0])
    assert result8.captured_function_call_count == 0
    assert result3.captured_function_call_count == 0


def test_historical_candidate_never_allows_real_native_capture(view, schema):
    from phenoassistant_mcp.scientific_inference_v1 import (
        ScientificMcpDispatchError,
    )
    candidate = Path(
        "experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json"
    )
    with pytest.raises(ScientificMcpDispatchError):
        Phase8MafDecisionClient.create(
            approved_runtime_path=candidate,
            approved_runtime_sha256=file_sha256(candidate),
            api_key="OFFLINE-TEST-KEY",
            seed=2026,
            upstream=None,
        )


def test_offline_direct_cli_is_not_paid_or_scientific():
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env.pop("OPENROUTER_API_KEY", None)
    run = subprocess.run(
        [sys.executable, str(root / "scripts/research/phase8_native_tool_capture_v1.py")],
        cwd=root, env=env, capture_output=True, text=True, timeout=25,
    )
    assert run.returncode == 0, run.stderr[-2000:]
    assert "PHASE8_NATIVE_CAPTURE_OFFLINE_PREFLIGHT_PASS=true" in run.stdout
    assert "PHASE8_NATIVE_CAPTURE_REAL_MCP_DISPATCH=0" in run.stdout
    assert "PHASE8_NATIVE_CAPTURE_REAL_PROVIDER_CALLS=0" in run.stdout
    assert "PHASE8_NATIVE_CAPTURE_GPU_EXECUTIONS=0" in run.stdout
    assert "PHASE8_NATIVE_CAPTURE_SCIENTIFIC_EXECUTION_APPROVED=false" in run.stdout
