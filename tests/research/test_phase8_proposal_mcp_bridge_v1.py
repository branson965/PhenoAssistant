"""No-network full-path MAF proposal to real MCP protocol tests.

MCP and SDK are REAL protocols, but vision output and OpenRouter responses
are FAKE. Synthetic temporary runtime approvals are never production grants.
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from phenoassistant_mcp.scientific_inference_v1 import (
    ImageAsset, ScientificMcpDispatchError,
    build_phase8_scientific_mcp_server, file_sha256,
)
from research.phenoguard.contracts import ApplicabilityDecision
from research.phenoguard.post_validation import validate_phenotype_records
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID as CASE1,
    CASE2_POTATO_SEGMENTATION_MODEL_ID as CASE2,
    CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID as CASE3,
)
from research.phenoguard.pilot_manifest import build_development_validation_manifest
from scripts.research.phase8_condition_rehearsal import C3, C4, C8, Proposal
from scripts.research.phase8_maf_decision_v1 import (
    MODEL, Phase8MafDecisionClient, ProposalEvidence,
)
from scripts.research.phase8_proposal_mcp_bridge_v1 import (
    BridgeObservation, bridge_one, select_proposal, Phase8ProposalError,
)
from scripts.research.prepare_phase8_qualification_matrix import model_visible_view


@pytest.fixture
def approval(tmp_path):
    historic = json.loads(Path(
        "experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json"
    ).read_text(encoding="utf-8"))
    historic["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    historic["scientific_execution_permitted"] = True
    historic["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    historic["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    file = tmp_path / "SYNTHETIC_TEST_ONLY_UNAPPROVED_FOR_PRODUCTION.json"
    file.write_text(json.dumps(historic, sort_keys=True), encoding="utf-8")
    return file, file_sha256(file)


@pytest.fixture
def mcp(tmp_path, approval):
    path, digest = approval
    image = tmp_path / "bound_image.png"
    image.write_bytes(b"OFFLINE_TEST_ONLY_IMAGE")
    assets = {"bound_image_1": ImageAsset(image, file_sha256(image))}
    seen = []

    def fake_inference(capability_id, asset_id, image_path, output_dir):
        seen.append((capability_id, asset_id, str(image_path)))
        if capability_id in (CASE1, CASE2):
            (output_dir / "ins_seg_results.json").write_text(
                json.dumps({
                    "images": [{"id": 0, "file_name": "bound_image_1"}],
                    "annotations": [],
                }), encoding="utf-8",
            )
        elif capability_id == CASE3:
            with (output_dir / "img_classification_results.csv").open(
                "w", newline="", encoding="utf-8",
            ) as fp:
                writer = csv.DictWriter(fp, fieldnames=[
                    "file_name", "class_ids", "class_labels", "class_scores",
                ])
                writer.writeheader()
                writer.writerow({
                    "file_name": "bound_image_1",
                    "class_ids": 1,
                    "class_labels": "offline-test",
                    "class_scores": 0.9,
                })
        else:
            raise AssertionError("unregistered model executed by fake")
        return "fake output created, not a scientific observation"

    server = build_phase8_scientific_mcp_server(
        approved_runtime_file=path,
        approved_runtime_sha256=digest,
        frozen_trial_id="a" * 24,
        trusted_images=assets,
        output_root=tmp_path / "mcp-results",
        inference_delegate=fake_inference,
    )
    return server, seen


def evidence(role: str, proposal: Proposal) -> ProposalEvidence:
    return ProposalEvidence(
        role=role, proposal=proposal, response_model=MODEL,
        response_sha256="f" * 64, fingerprint=None, input_tokens=50,
        output_tokens=20,
    )


class MockAgent:
    def __init__(self, manager: Proposal, critic: Proposal | None = None):
        self.manager = manager
        self.critic = critic
        self.calls = []

    async def propose_manager(self, *, condition, visible_view, discovered_tool):
        self.calls.append(("manager", condition))
        assert discovered_tool["name"] == "run_scientific_model"
        assert set(visible_view) == {
            "scientific_request", "requested_capability_id", "training_readiness"
        }
        return evidence("manager", self.manager)

    async def critique(
        self, *, condition, visible_view, discovered_tool, manager_proposal
    ):
        self.calls.append(("critic", condition))
        assert condition == C4
        assert self.critic is not None
        return evidence("generic_critic", self.critic)


async def typed_post_validator(result):
    assert result["tool_executed"] is True
    assert result["artifact_sha256"]
    # Synthetic test-only record, NOT a real output-derived phenotype check.
    return validate_phenotype_records(
        ({"leaf_count": 2, "projected_leaf_area": 17.2},)
    )


def view(index=0):
    return model_visible_view(build_development_validation_manifest()[index])


def test_c3_manager_proposal_dispatches_real_mcp_protocol_with_fake_inference(
    mcp, approval,
):
    server, seen = mcp
    path, digest = approval
    agent = MockAgent(Proposal(ApplicabilityDecision.EXECUTE, CASE1))

    async def run():
        return await bridge_one(
            condition=C3, visible_view=view(),
            approved_runtime_path=path, approved_runtime_sha256=digest,
            decision_client=agent, mcp_server=server,
            bound_image_asset_id="bound_image_1", post_validator=None,
        )

    result = asyncio.run(run())
    assert isinstance(result, BridgeObservation)
    assert result.final_decision == "EXECUTE"
    assert result.mcp_dispatch_completed is True
    assert result.scientific_tool_attempted is True
    assert result.c8_soe_check_applied is False
    assert result.c8_post_validation_applied is False
    assert result.safe_to_report is None
    assert result.scientific_output_sha256 is not None
    assert result.result_scope == "INTEGRATION_ONLY_NOT_SCIENTIFIC_EVALUATION"
    assert len(seen) == 1
    assert seen[0][0] == CASE1
    assert seen[0][1] == "bound_image_1"


def test_c4_independent_critic_rejects_before_mcp_dispatch(mcp, approval):
    server, seen = mcp
    path, digest = approval
    agent = MockAgent(
        Proposal(ApplicabilityDecision.EXECUTE, CASE1),
        Proposal(ApplicabilityDecision.CLARIFY, None),
    )

    async def run():
        return await bridge_one(
            condition=C4, visible_view=view(),
            approved_runtime_path=path, approved_runtime_sha256=digest,
            decision_client=agent, mcp_server=server,
            bound_image_asset_id="bound_image_1", post_validator=None,
        )

    result = asyncio.run(run())
    assert result.manager_decision == "EXECUTE"
    assert result.critic_decision == "CLARIFY"
    assert result.final_decision == "CLARIFY"
    assert result.scientific_tool_attempted is False
    assert result.safe_to_report is None
    assert result.model_call_count == 2
    assert agent.calls == [("manager", C4), ("critic", C4)]
    assert seen == []


def test_c8_reselects_wrong_species_and_applies_typed_post_check(mcp, approval):
    server, seen = mcp
    path, digest = approval
    manager = MockAgent(Proposal(ApplicabilityDecision.EXECUTE, CASE1))

    async def run():
        return await bridge_one(
            condition=C8, visible_view=view(1),
            approved_runtime_path=path, approved_runtime_sha256=digest,
            decision_client=manager, mcp_server=server,
            bound_image_asset_id="bound_image_1",
            post_validator=typed_post_validator,
        )

    result = asyncio.run(run())
    assert result.manager_decision == "EXECUTE"
    assert result.final_decision == "RESELECT"
    assert result.selected_capability_id == CASE2
    assert result.scientific_tool_attempted is True
    assert result.c8_soe_check_applied is True
    assert result.c8_post_validation_applied is True
    assert result.safe_to_report is True
    assert len(seen) == 1 and seen[0][0] == CASE2
    assert result.result_scope == "INTEGRATION_ONLY_NOT_SCIENTIFIC_EVALUATION"


def test_c8_missing_post_validator_blocks_before_looking_up_tool(mcp, approval):
    server, seen = mcp
    path, digest = approval
    agent = MockAgent(Proposal(ApplicabilityDecision.EXECUTE, CASE1))

    async def run():
        return await bridge_one(
            condition=C8, visible_view=view(),
            approved_runtime_path=path, approved_runtime_sha256=digest,
            decision_client=agent, mcp_server=server,
            bound_image_asset_id="bound_image_1", post_validator=None,
        )

    with pytest.raises(Phase8ProposalError, match="requires output-specific"):
        asyncio.run(run())
    assert agent.calls == []
    assert seen == []


def test_unapproved_historical_candidate_blocks_everything(mcp):
    server, seen = mcp
    agent = MockAgent(Proposal(ApplicabilityDecision.EXECUTE, CASE1))
    path = Path("experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json")

    async def run():
        return await bridge_one(
            condition=C3, visible_view=view(),
            approved_runtime_path=path,
            approved_runtime_sha256=file_sha256(path),
            decision_client=agent, mcp_server=server,
            bound_image_asset_id="bound_image_1", post_validator=None,
        )

    with pytest.raises(ScientificMcpDispatchError, match="not been approved"):
        asyncio.run(run())
    assert agent.calls == []
    assert seen == []


def test_c3_c4_do_not_receive_c8_post_validator(mcp, approval):
    server, seen = mcp
    path, digest = approval
    for condition in (C3, C4):
        agent = MockAgent(Proposal(ApplicabilityDecision.CLARIFY, None))
        async def run():
            return await bridge_one(
                condition=condition, visible_view=view(),
                approved_runtime_path=path, approved_runtime_sha256=digest,
                decision_client=agent, mcp_server=server,
                bound_image_asset_id="bound_image_1",
                post_validator=typed_post_validator,
            )
        with pytest.raises(Phase8ProposalError, match="must not receive"):
            asyncio.run(run())
    assert seen == []


def test_c8_ignores_unregistered_manager_selection_when_explicit_requested_model():
    v = view()
    result = select_proposal(
        condition=C8, visible_view=v,
        manager=Proposal(ApplicabilityDecision.EXECUTE, CASE2),
        critic=None,
    )
    assert result[0] == ApplicabilityDecision.EXECUTE
    assert result[1] == CASE1


def test_cli_can_run_directly_without_key_and_never_dispatch():
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env.pop("OPENROUTER_API_KEY", None)
    r = subprocess.run(
        [sys.executable, str(root / "scripts/research/phase8_proposal_mcp_bridge_v1.py")],
        cwd=root, env=env, capture_output=True, text=True, timeout=25,
    )
    assert r.returncode == 0, r.stderr[-1200:]
    assert "PHASE8_BRIDGE_PROVIDER_CALLS=0" in r.stdout
    assert "PHASE8_BRIDGE_SCIENTIFIC_DISPATCH=0" in r.stdout
    assert "PHASE8_BRIDGE_EXECUTION_APPROVED=false" in r.stdout
    assert "PHASE8_BRIDGE_OFFLINE_PREFLIGHT_PASS=true" in r.stdout
    assert "PHASE8_BRIDGE_NATIVE_TOOL_CALLING=false" in r.stdout


def test_missing_asset_id_is_rejected(mcp, approval):
    server, seen = mcp
    path, digest = approval
    agent = MockAgent(Proposal(ApplicabilityDecision.EXECUTE, CASE1))

    async def run():
        return await bridge_one(
            condition=C3, visible_view=view(),
            approved_runtime_path=path, approved_runtime_sha256=digest,
            decision_client=agent, mcp_server=server,
            bound_image_asset_id="", post_validator=None,
        )
    with pytest.raises(Phase8ProposalError, match="missing trusted"):
        asyncio.run(run())
    assert agent.calls == []
    assert seen == []


def test_end_to_end_real_maf_mock_http_to_real_mcp_fake_vision(
    mcp, approval,
):
    """A full SDK+HTTP-transport+MCP cycle, with zero external network."""
    path, digest = approval
    server, seen = mcp
    sent = []
    response_text = json.dumps({"decision": "EXECUTE", "capability_id": CASE1})

    async def offline_provider(request):
        payload = json.loads(request.content)
        sent.append(payload)
        return httpx.Response(200, json={
            "id": "chatcmpl-offline-maf-mcp-bridge",
            "object": "chat.completion",
            "created": 1795095000,
            "model": MODEL,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 150, "completion_tokens": 40, "total_tokens": 190,
            },
        })

    async def run():
        service = Phase8MafDecisionClient.create(
            approved_runtime_path=path,
            approved_runtime_sha256=digest,
            api_key="sk-or-v1-SYNTHETIC-TEST-NOT-A-REAL-KEY",
            seed=2026,
            upstream=httpx.MockTransport(offline_provider),
        )
        try:
            return await bridge_one(
                condition=C3,
                visible_view=view(),
                approved_runtime_path=path,
                approved_runtime_sha256=digest,
                decision_client=service,
                mcp_server=server,
                bound_image_asset_id="bound_image_1",
                post_validator=None,
            )
        finally:
            await service.close()

    result = asyncio.run(run())
    assert result.model_call_count == 1
    assert result.mcp_dispatch_completed is True
    assert result.safe_to_report is None
    assert result.final_decision == "EXECUTE"
    assert len(seen) == 1 and len(sent) == 1
    request = sent[0]
    assert request["model"] == MODEL
    assert request["provider"] == {
        "order": ["openai"],
        "allow_fallbacks": False,
        "require_parameters": True,
    }
    assert request["seed"] == 2026
    assert request["reasoning"] == {"effort": "medium"}
    assert request["max_tokens"] == 2048
    assert "max_completion_tokens" not in request
    assert "parallel_tool_calls" not in request
    assert "temperature" not in request
    assert "scientific_operating_envelopes" not in json.dumps(request)
    assert "expected_decision" not in json.dumps(request)
    assert result.result_scope == "INTEGRATION_ONLY_NOT_SCIENTIFIC_EVALUATION"
