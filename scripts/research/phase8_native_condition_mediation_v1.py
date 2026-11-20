"""Offline-qualified native MAF C3/C4/C8 decision mediation.

This composes an actual MAF native @tool proposal (capture ONLY) with:
  C3: unchanged native Manager proposal;
  C4: an independent generic LLM Critic's typed decision;
  C8: the frozen scientific catalogue resolver applied to the model's
      NATIVE proposed capability, only when a tool call was captured.

The pipeline has NO call to the scientific MCP executor, no image paths,
no trial ledger writes, no billing and no ground-truth scoring. A
separately reviewed full runner must attach those components prospectively.

In particular, a generic Critic cannot invent executable native-call
evidence after a no-call Manager response. C8 likewise cannot turn a
no-call Manager response into GPU dispatch without a proposal.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.phenoguard.catalogue import resolve_capability_catalogue  # noqa: E402
from research.phenoguard.contracts import (  # noqa: E402
    ApplicabilityDecision, ScientificRequestContext, TrainingReadinessContext,
)
from research.phenoguard.provenance import build_default_provenance_catalogue  # noqa: E402
from scripts.research.phase8_condition_rehearsal import C3, C4, C8, Proposal  # noqa: E402
from scripts.research.phase8_maf_decision_v1 import (  # noqa: E402
    MODEL, Phase8ProposalError, ProposalEvidence, validate_mcp_schema, validate_view,
)
from scripts.research.phase8_native_tool_capture_v1 import (  # noqa: E402
    IMAGE_ARGUMENT_PLACEHOLDER, REGISTERED_IDS, NativeToolProposal,
    capture_one_native_manager_proposal,
)
from scripts.research.phase8_attempt_ledger import (  # noqa: E402
    load_verified_controls, scientific_gate, LedgerGateError,
)

EXECUTABLE = frozenset((ApplicabilityDecision.EXECUTE, ApplicabilityDecision.RESELECT))


class NativeDecisionClient(Protocol):
    async def critique(
        self, *, condition: str, visible_view: dict[str, Any],
        discovered_tool: dict[str, Any], manager_proposal: Proposal,
    ) -> ProposalEvidence: ...


@dataclass(frozen=True)
class NativeMediationObservation:
    condition: str
    manager_decision: ApplicabilityDecision
    manager_selected_capability_id: str | None
    native_tool_calls_captured: int
    critic_called: bool
    critic_decision: ApplicabilityDecision | None
    critic_selected_capability_id: str | None
    c8_precheck_applied: bool
    final_decision: ApplicabilityDecision
    final_selected_capability_id: str | None
    reviewer_changed_selection: bool
    shared_request_sha256: str
    manager_prompt_sha256: str
    critic_response_sha256: str | None
    model_identity: str
    provider_billed_cost_available: bool = False
    mcp_calls: int = 0
    gpu_calls: int = 0
    result_scope: str = "NATIVE_DECISION_MEDIATION_OFFLINE_NOT_SCIENTIFIC_EVALUATION"


def _hash_view(view: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(view, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        .encode("utf-8")
    ).hexdigest()


def verify_native_capture(captured: NativeToolProposal) -> None:
    """Verify typed model-call evidence, without accepting a JSON-only execution."""
    if not isinstance(captured, NativeToolProposal):
        raise Phase8ProposalError("Manager native function-call evidence missing")
    if captured.response_model != MODEL:
        raise Phase8ProposalError("Manager model identity changed")
    if captured.result_scope != "NATIVE_CALL_CAPTURE_ONLY_NOT_SCIENTIFIC_EVALUATION":
        raise Phase8ProposalError("Manager evidence has unknown execution scope")
    if captured.scientific_mcp_calls != 0 or captured.gpu_inference_calls != 0:
        raise Phase8ProposalError("native capture unexpectedly dispatched a tool")
    if captured.provider_cost_measured is not None:
        raise Phase8ProposalError("native capture must not invent measured billing")
    if not isinstance(captured.decision, Proposal):
        raise Phase8ProposalError("Manager decision must be typed")
    if captured.captured_function_call_count == 1:
        if captured.application_bound_asset_placeholder != IMAGE_ARGUMENT_PLACEHOLDER:
            raise Phase8ProposalError("native call did not use the public image placeholder")
        if captured.decision.decision not in EXECUTABLE:
            raise Phase8ProposalError("native tool call claims a non-execution decision")
        if captured.decision.capability_id not in REGISTERED_IDS:
            raise Phase8ProposalError("native call selected unregistered capability")
    elif captured.captured_function_call_count == 0:
        if captured.application_bound_asset_placeholder is not None:
            raise Phase8ProposalError("no-call response contains an image binding")
        if captured.decision.decision in EXECUTABLE or captured.decision.capability_id is not None:
            raise Phase8ProposalError("executable decision without native call")
    else:
        raise Phase8ProposalError("native function-call count is not zero or one")


def mediate_native_proposal(
    *,
    condition: str,
    visible_view: dict[str, Any],
    manager: NativeToolProposal,
    critic: ProposalEvidence | None,
) -> tuple[ApplicabilityDecision, str | None, bool]:
    """Return final decision, selected capability and C8 precheck status.

    Never consult a benchmark gold label or read a source image. C4's
    post-Manager Critic is a separate, generic model and cannot enable a
    tool call if the Manager did not issue one. C8's deterministic scientific
    verifier is only invoked for a genuine proposed native call.
    """
    if condition not in (C3, C4, C8):
        raise Phase8ProposalError("unknown frozen experimental condition")
    view = validate_view(visible_view)
    verify_native_capture(manager)
    has_native_tool_call = manager.captured_function_call_count == 1
    manager_proposal = manager.decision

    if condition == C4:
        if not isinstance(critic, ProposalEvidence) or critic.role != "generic_critic":
            raise Phase8ProposalError("C4 requires independent generic Critic evidence")
        if critic.response_model != MODEL or not isinstance(critic.proposal, Proposal):
            raise Phase8ProposalError("C4 critic identity/decision invalid")
        if critic.scientific_tool_executed or critic.cost_usd_measured is not None:
            raise Phase8ProposalError("generic Critic cannot execute tools or invent billing")
        selected = critic.proposal
        if selected.decision in EXECUTABLE and not has_native_tool_call:
            raise Phase8ProposalError("Critic cannot create an executable call without native Manager evidence")
        if selected.decision in EXECUTABLE and selected.capability_id not in REGISTERED_IDS:
            raise Phase8ProposalError("Critic selected unregistered capability")
        return selected.decision, selected.capability_id, False

    if critic is not None:
        raise Phase8ProposalError("generic Critic exposed outside C4")
    if condition == C3 or not has_native_tool_call:
        return manager_proposal.decision, manager_proposal.capability_id, False

    # C8 preflight checks the ACTUAL proposed model, not the originally
    # requested model when the Manager proposed a different candidate.
    request = ScientificRequestContext.model_validate(view["scientific_request"])
    training = (
        TrainingReadinessContext.model_validate(view["training_readiness"])
        if view["training_readiness"] is not None else None
    )
    resolution = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        request,
        requested_capability_id=manager_proposal.capability_id,
        training_readiness=training,
    )
    return resolution.decision, resolution.selected_capability_id, True


async def mediate_one_native_condition(
    *,
    client: NativeDecisionClient,
    condition: str,
    visible_view: dict[str, Any],
    discovered_tool: dict[str, Any],
) -> NativeMediationObservation:
    """Use the genuine native capture and separate Critic, with NO MCP dispatch."""
    if condition not in (C3, C4, C8):
        raise Phase8ProposalError("unknown frozen experimental condition")
    view = validate_view(visible_view)
    schema = validate_mcp_schema(discovered_tool)

    captured = await capture_one_native_manager_proposal(
        client=client, condition=condition,
        visible_view=json.loads(json.dumps(view)),
        discovered_tool=json.loads(json.dumps(schema)),
    )
    verify_native_capture(captured)
    critic = None
    if condition == C4:
        critic = await client.critique(
            condition=C4, visible_view=json.loads(json.dumps(view)),
            discovered_tool=json.loads(json.dumps(schema)),
            manager_proposal=captured.decision,
        )
    action, selected, c8_checked = mediate_native_proposal(
        condition=condition, visible_view=view, manager=captured, critic=critic,
    )

    return NativeMediationObservation(
        condition=condition,
        manager_decision=captured.decision.decision,
        manager_selected_capability_id=captured.decision.capability_id,
        native_tool_calls_captured=captured.captured_function_call_count,
        critic_called=critic is not None,
        critic_decision=(critic.proposal.decision if critic is not None else None),
        critic_selected_capability_id=(
            critic.proposal.capability_id if critic is not None else None
        ),
        c8_precheck_applied=c8_checked,
        final_decision=action,
        final_selected_capability_id=selected,
        reviewer_changed_selection=(
            bool(action in EXECUTABLE)
            and selected != captured.decision.capability_id
        ),
        shared_request_sha256=_hash_view(view),
        manager_prompt_sha256=captured.prompt_sha256,
        critic_response_sha256=(
            critic.response_sha256 if critic is not None else None
        ),
        model_identity=captured.response_model,
    )


def main() -> int:
    """Historical v0.3 is never a scientific runtime. No provider calls."""
    matrix, candidate = load_verified_controls()
    try:
        scientific_gate(candidate)
    except LedgerGateError:
        pass
    else:
        raise Phase8ProposalError("unapproved historic runtime unexpectedly authorizes execution")
    print("PHASE8_NATIVE_MEDIATION_TRIALS=" + str(matrix["trial_count"]))
    print("PHASE8_NATIVE_MEDIATION_CONDITIONS=C3,C4,C8")
    print("PHASE8_NATIVE_MEDIATION_C4_CRITIC_IMPLEMENTED=true")
    print("PHASE8_NATIVE_MEDIATION_C8_PRECHECK_IMPLEMENTED=true")
    print("PHASE8_NATIVE_MEDIATION_MCP_CALLS=0")
    print("PHASE8_NATIVE_MEDIATION_PROVIDER_CALLS=0")
    print("PHASE8_NATIVE_MEDIATION_GPU_CALLS=0")
    print("PHASE8_NATIVE_MEDIATION_PROVIDER_BILLING_MEASURED=false")
    print("PHASE8_NATIVE_MEDIATION_OUTCOME_BEARING=false")
    print("PHASE8_NATIVE_MEDIATION_EXECUTION_APPROVED=false")
    print("PHASE8_NATIVE_MEDIATION_OFFLINE_PREFLIGHT_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
