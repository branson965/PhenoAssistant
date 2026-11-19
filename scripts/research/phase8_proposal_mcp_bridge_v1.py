"""Mediated MAF proposal -> MCP scientific tool orchestration.

This module composes the *real* MAF proposal client, independent C4
Critic, frozen C8 SOE catalogue resolver, and the same MCP scientific
server for all three conditions. It does NOT claim that text-JSON
proposals are native MAF tool calls. This intermediate bridge is not
a final scientific evaluation runner: provider-billed cost, approved
image fixtures, scientific post-validation and a final runtime trust
anchor remain external gates.

Never load hidden labels, never execute model-selected paths, never
substitute the application's bound image for any arbitrary model path.
The base frozen request is identical across conditions.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Protocol

from mcp.server import MCPServer

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phenoassistant_mcp.client_v2 import McpV2Session  # noqa: E402
from phenoassistant_mcp.scientific_inference_v1 import verify_approved_runtime  # noqa: E402
from research.phenoguard.catalogue import resolve_capability_catalogue  # noqa: E402
from research.phenoguard.contracts import (  # noqa: E402
    ApplicabilityDecision, ScientificRequestContext, TrainingReadinessContext,
)
from research.phenoguard.post_validation import PostExecutionValidation  # noqa: E402
from research.phenoguard.provenance import build_default_provenance_catalogue  # noqa: E402
from scripts.research.phase8_condition_rehearsal import C3, C4, C8, Proposal  # noqa: E402
from scripts.research.phase8_maf_decision_v1 import (  # noqa: E402
    Phase8ProposalError, ProposalEvidence, discover_real_mcp_tool, validate_view,
)
from scripts.research.phase8_attempt_ledger import load_verified_controls, scientific_gate, LedgerGateError  # noqa: E402

EXECUTABLE = frozenset((ApplicabilityDecision.EXECUTE, ApplicabilityDecision.RESELECT))


class DecisionClient(Protocol):
    async def propose_manager(
        self, *, condition: str, visible_view: dict, discovered_tool: dict
    ) -> ProposalEvidence: ...

    async def critique(
        self, *, condition: str, visible_view: dict, discovered_tool: dict,
        manager_proposal: Proposal
    ) -> ProposalEvidence: ...


# This callback must come from a separately reviewed output-specific
# validation implementation. There is intentionally no unconditional
# "always safe" validator available here.
PostValidator = Callable[[dict[str, Any]], Awaitable[PostExecutionValidation]]


@dataclass(frozen=True)
class BridgeObservation:
    condition: str
    manager_decision: str
    critic_decision: str | None
    final_decision: str
    selected_capability_id: str | None
    scientific_tool_attempted: bool
    mcp_dispatch_completed: bool
    c8_soe_check_applied: bool
    c8_post_validation_applied: bool
    safe_to_report: bool | None  # None: no C8 post-validity assessment was performed
    shared_request_sha256: str
    model_call_count: int
    scientific_output_sha256: str | None
    result_scope: str = "INTEGRATION_ONLY_NOT_SCIENTIFIC_EVALUATION"


def _hash_view(view: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(view, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        .encode("utf-8")
    ).hexdigest()


def select_proposal(
    *, condition: str, visible_view: dict[str, Any],
    manager: Proposal, critic: Proposal | None,
) -> tuple[ApplicabilityDecision, str | None]:
    """No counterfactual scorer or expected answer is consulted."""
    if condition not in (C3, C4, C8):
        raise Phase8ProposalError("unknown experimental condition")
    if not isinstance(manager, Proposal):
        raise Phase8ProposalError("Manager did not return typed decision")
    if condition == C4:
        if not isinstance(critic, Proposal):
            raise Phase8ProposalError("C4 requires an independent typed Critic decision")
        proposal = critic
    else:
        if critic is not None:
            raise Phase8ProposalError("Critic must be absent outside C4")
        proposal = manager
    if condition != C8:
        return proposal.decision, proposal.capability_id

    request = ScientificRequestContext.model_validate(visible_view["scientific_request"])
    training = (
        TrainingReadinessContext.model_validate(visible_view["training_readiness"])
        if visible_view["training_readiness"] is not None else None
    )
    requested_id = visible_view["requested_capability_id"] or proposal.capability_id
    resolved = resolve_capability_catalogue(
        build_default_provenance_catalogue(), request,
        requested_capability_id=requested_id, training_readiness=training,
    )
    return resolved.decision, resolved.selected_capability_id


async def bridge_one(
    *,
    condition: str,
    visible_view: dict[str, Any],
    approved_runtime_path: Path,
    approved_runtime_sha256: str,
    decision_client: DecisionClient,
    mcp_server: MCPServer,
    bound_image_asset_id: str,
    post_validator: PostValidator | None,
    timeout_seconds: float = 10.0,
) -> BridgeObservation:
    """Connect proposal+Critic+SOE+MCP; no direct HTTP/GPU call is created here.

    This entrypoint is approval gated and requires the caller to provide
    the existing server with the *same* final runtime. A higher-level
    scientific runner must also supply ledger, provider cost, real image
    fixture and a verified C8 validator before using this for outcomes.
    """
    verify_approved_runtime(approved_runtime_path, approved_runtime_sha256)
    if condition not in (C3, C4, C8):
        raise Phase8ProposalError("unknown condition")
    view = validate_view(visible_view)
    if not isinstance(bound_image_asset_id, str) or not bound_image_asset_id.strip():
        raise Phase8ProposalError("missing trusted image asset binding")
    if condition == C8 and post_validator is None:
        raise Phase8ProposalError("C8 requires output-specific post-validator")
    if condition != C8 and post_validator is not None:
        raise Phase8ProposalError("C3/C4 must not receive scientific post-validation")
    if not (0 < timeout_seconds <= 60):
        raise Phase8ProposalError("MCP timeout outside reviewed range")

    # Fetch actual MCP schema, not a reconstructed or invented description.
    schema = await discover_real_mcp_tool(mcp_server)
    manager_evidence = await decision_client.propose_manager(
        condition=condition, visible_view=json.loads(json.dumps(view)),
        discovered_tool=schema,
    )
    if not isinstance(manager_evidence, ProposalEvidence) or manager_evidence.role != "manager":
        raise Phase8ProposalError("invalid MAF Manager evidence")
    critic_evidence = None
    if condition == C4:
        critic_evidence = await decision_client.critique(
            condition=C4, visible_view=json.loads(json.dumps(view)),
            discovered_tool=schema, manager_proposal=manager_evidence.proposal,
        )
        if not isinstance(critic_evidence, ProposalEvidence) or critic_evidence.role != "generic_critic":
            raise Phase8ProposalError("invalid independent Critic evidence")

    decision, selected = select_proposal(
        condition=condition, visible_view=view,
        manager=manager_evidence.proposal,
        critic=critic_evidence.proposal if critic_evidence else None,
    )
    attempted = decision in EXECUTABLE
    completed = False
    applied = False
    # No C8 scientific post-validation means "unassessed", never "invalid".
    # Baseline outputs cannot be marked unsafe merely because C3/C4 lacks
    # the special C8 validator; that would create a refusal/coverage artefact.
    safe_to_report: bool | None = None
    output_sha = None
    if attempted:
        if selected is None:
            raise Phase8ProposalError("executable decision without model")
        # This *same* MCP scientific tool is invoked for C3, C4 and C8.
        # Application-bound image_asset_id is never model-proposed.
        async with McpV2Session(mcp_server) as session:
            result = await session.call_structured_tool(
                "run_scientific_model",
                {"capability_id": selected, "image_asset_id": bound_image_asset_id},
                timeout_seconds=timeout_seconds,
            )
        if not isinstance(result, dict) or result.get("tool_executed") is not True:
            raise Phase8ProposalError("MCP did not confirm actual tool execution")
        if result.get("capability_id") != selected or result.get("image_asset_id") != bound_image_asset_id:
            raise Phase8ProposalError("MCP returned mismatched capability or asset")
        artifact_hash = result.get("artifact_sha256")
        if not isinstance(artifact_hash, str) or len(artifact_hash) != 64:
            raise Phase8ProposalError("MCP response omitted artifact identity")
        output_sha = artifact_hash
        completed = True
        if condition == C8:
            assert post_validator is not None
            validated = await post_validator(json.loads(json.dumps(result)))
            if not isinstance(validated, PostExecutionValidation):
                raise Phase8ProposalError("C8 post validator returned untyped evidence")
            applied = True
            safe_to_report = validated.safe_to_report
        else:
            # C3/C4 are unassessed, not scored as unsafe. Only the
            # independent expert/evaluation layer assigns safety labels.
            safe_to_report = None

    return BridgeObservation(
        condition=condition,
        manager_decision=manager_evidence.proposal.decision.value,
        critic_decision=(critic_evidence.proposal.decision.value if critic_evidence else None),
        final_decision=decision.value,
        selected_capability_id=selected,
        scientific_tool_attempted=attempted,
        mcp_dispatch_completed=completed,
        c8_soe_check_applied=condition == C8,
        c8_post_validation_applied=applied,
        safe_to_report=safe_to_report,
        shared_request_sha256=_hash_view(view),
        model_call_count=2 if condition == C4 else 1,
        scientific_output_sha256=output_sha,
    )


def main() -> int:
    """Intentionally offline: no model/vision tool/ledger execution."""
    matrix, candidate = load_verified_controls()
    try:
        scientific_gate(candidate)
    except LedgerGateError:
        pass
    else:
        raise Phase8ProposalError("historical runtime unexpectedly approved")
    print("PHASE8_BRIDGE_REGISTERED_TRIALS=" + str(matrix["trial_count"]))
    print("PHASE8_BRIDGE_IMPLEMENTED_CONDITIONS=C3,C4,C8")
    print("PHASE8_BRIDGE_NATIVE_TOOL_CALLING=false")
    print("PHASE8_BRIDGE_PROVIDER_CALLS=0")
    print("PHASE8_BRIDGE_SCIENTIFIC_DISPATCH=0")
    print("PHASE8_BRIDGE_C8_REAL_OUTPUT_VALIDATION=not-yet-integrated")
    print("PHASE8_BRIDGE_OUTCOME_BEARING=false")
    print("PHASE8_BRIDGE_EXECUTION_APPROVED=false")
    print("PHASE8_BRIDGE_OFFLINE_PREFLIGHT_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
