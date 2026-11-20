"""Offline-qualifiable native MAF tool-call capture for Phase 8.

MAF is given an actual @tool with the SAME tool name and argument names
as the trusted scientific MCP tool. Crucially, the @tool implementation
only captures a selection proposal; it does NOT invoke inference/MCP/GPU.
For real HTTP, Phase8MafDecisionClient.create requires the independent
reviewed runtime SHA (currently unset). Fake httpx.MockTransport tests
can exercise the real MAF SDK without spending credits.

The tool's image argument is a *public non-path placeholder* rather than a
private approved image identifier. The application later binds that
placeholder to an approved asset only after the separate SOE/Critic and
ledger gates. This is native model function-call capture, NOT native
scientific execution nor an outcome-bearing benchmark run.

This intentionally does not change the frozen C3/C4/C8 methods or the
historical text-JSON proposal adapter, which remains separate evidence.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_framework import Message, tool

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.phenoguard.contracts import ApplicabilityDecision  # noqa: E402
from research.phenoguard.provenance import build_default_provenance_catalogue  # noqa: E402
from scripts.research.phase8_condition_rehearsal import C3, C4, C8, Proposal  # noqa: E402
from scripts.research.phase8_maf_decision_v1 import (  # noqa: E402
    MODEL, OUTPUT_TOKENS, Phase8MafDecisionClient, Phase8ProposalError,
    manager_prompt, parse_proposal, validate_mcp_schema, validate_view,
)
from scripts.research.phase8_attempt_ledger import (  # noqa: E402
    load_verified_controls, scientific_gate, LedgerGateError,
)

# Never expose the actual image ID, dataset path, or reviewed species to the
# manager or critic. This is a non-secret protocol placeholder only.
IMAGE_ARGUMENT_PLACEHOLDER = "application_bound_image"

NATIVE_INSTRUCTIONS = (
    "You are a scientific tool-selection Manager. The available native "
    "function run_scientific_model may be proposed for later verified "
    "scientific execution. Your selection is captured without running a "
    "vision model until the external guards approve it. If you can propose a registered "
    "capability, make exactly one native function call with capability_id "
    "set to that capability and image_asset_id set literally to "
    "'application_bound_image'. Never provide an image path, a private "
    "asset identifier, or any made-up model measurement. If a safe tool "
    "selection cannot be made, do NOT call a function and instead emit "
    "exactly one JSON object with decision CLARIFY, ABSTAIN or "
    "RECOMMEND_TRAINING and capability_id null. C3/C4 lack scientific "
    "operating envelopes "
    "and must not assume unseen provenance. Do not include explanations."
)

REGISTERED_IDS = frozenset(
    item.capability_id for item in build_default_provenance_catalogue()
)
NON_EXECUTION = frozenset((
    ApplicabilityDecision.CLARIFY,
    ApplicabilityDecision.ABSTAIN,
    ApplicabilityDecision.RECOMMEND_TRAINING,
))


@dataclass(frozen=True)
class NativeToolProposal:
    decision: Proposal
    captured_function_call_count: int
    application_bound_asset_placeholder: str | None
    response_model: str
    prompt_sha256: str
    response_text_sha256: str | None
    raw_wire_function_call_count: int = 0
    scientific_mcp_calls: int = 0
    gpu_inference_calls: int = 0
    provider_cost_measured: None = None
    result_scope: str = "NATIVE_CALL_CAPTURE_ONLY_NOT_SCIENTIFIC_EVALUATION"


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def check_native_schema(discovered_tool: dict[str, Any]) -> dict[str, Any]:
    """Only the reviewed MCP tool's exact two arguments are accepted."""
    return validate_mcp_schema(discovered_tool)


async def capture_one_native_manager_proposal(
    *,
    client: Phase8MafDecisionClient,
    condition: str,
    visible_view: dict[str, Any],
    discovered_tool: dict[str, Any],
) -> NativeToolProposal:
    if condition not in (C3, C4, C8):
        raise Phase8ProposalError("unknown frozen condition")
    # No case metadata/hidden gold, image filenames, or private IDs.
    view = validate_view(visible_view)
    mcp_schema = check_native_schema(discovered_tool)
    _, base_user = manager_prompt(condition, view, mcp_schema)
    raw_guard = client.raw_tool_guard
    if raw_guard is None:
        raise Phase8ProposalError("native capture requires a raw provider-response guard")
    if raw_guard.native_tool_calls != 0 or raw_guard.provider_replies_checked != 0:
        raise Phase8ProposalError("native capture requires a fresh per-trial MAF client")
    calls: list[tuple[str, str]] = []
    invalid_attempts: list[str] = []

    @tool(
        name="run_scientific_model",
        # The actual MCP-advertised description, not a special 'capture'
        # description, preserves the C3/C4 tool-information exposure.
        # The capture-only behaviour is entirely on the application side.
        description=mcp_schema["description"],
    )
    def capture_scientific_tool_proposal(
        capability_id: str,
        image_asset_id: str,
    ) -> str:
        # MAF may automatically invoke tool callbacks. This callback NEVER
        # calls the scientific MCP server; it records the model's choice.
        # Guard before side effects. Two calls in a turn are always invalid.
        if calls:
            invalid_attempts.append("duplicate-native-call")
            raise Phase8ProposalError("more than one native tool call requested")
        if capability_id not in REGISTERED_IDS:
            invalid_attempts.append("unknown-capability")
            raise Phase8ProposalError("native tool proposal references unknown checkpoint")
        if image_asset_id != IMAGE_ARGUMENT_PLACEHOLDER:
            invalid_attempts.append("unbound-image-argument")
            raise Phase8ProposalError("native tool proposal used unbound image argument")
        calls.append((capability_id, image_asset_id))
        return "PROPOSAL_CAPTURED_NO_SCIENTIFIC_EXECUTION"

    options = client._options()
    options["tools"] = [capture_scientific_tool_proposal]
    options["tool_choice"] = "auto"
    options["allow_multiple_tool_calls"] = False

    response = await client.chat.get_response(
        [
            Message(role="system", contents=[NATIVE_INSTRUCTIONS]),
            Message(role="user", contents=[base_user]),
        ],
        options=options,
    )
    # Some MAF versions convert tool callback exceptions into tool-result
    # messages. Such a rejection cannot be treated as a valid model proposal.
    if invalid_attempts:
        raise Phase8ProposalError(
            "native tool callback rejected model proposal: " + invalid_attempts[0]
        )
    if raw_guard.native_tool_calls != len(calls):
        raise Phase8ProposalError(
            "MAF callback count differs from raw provider native tool-call count"
        )
    response_model = getattr(response, "model", None)
    if response_model != MODEL:
        raise Phase8ProposalError("native proposal response model identity drift")
    text = getattr(response, "text", None)
    if calls:
        # The actual native function call, not the assistant's summary text,
        # is the ONLY source of the proposed capability. No extra native call
        # is possible without the callback rejecting it.
        # RESELECT is an observable fact when the native call selects a
        # different registered capability from the explicitly requested one.
        # This classification does not consult scientific gold or SOE data.
        requested = view["requested_capability_id"]
        action = Proposal(
            decision=(
                ApplicabilityDecision.RESELECT
                if requested is not None and calls[0][0] != requested
                else ApplicabilityDecision.EXECUTE
            ),
            capability_id=calls[0][0],
        )
    else:
        # A no-tool answer cannot be silently scored as execution.
        action = parse_proposal(text)
        if action.decision not in NON_EXECUTION:
            raise Phase8ProposalError("execution decision without native tool-call evidence")

    return NativeToolProposal(
        decision=action,
        captured_function_call_count=len(calls),
        application_bound_asset_placeholder=(
            calls[0][1] if calls else None
        ),
        response_model=response_model,
        prompt_sha256=_sha(NATIVE_INSTRUCTIONS + "\n" + base_user),
        response_text_sha256=_sha(text) if isinstance(text, str) else None,
        raw_wire_function_call_count=raw_guard.native_tool_calls,
    )


def main() -> int:
    """Safe offline-only readiness display, never creates a provider client."""
    matrix, candidate = load_verified_controls()
    try:
        scientific_gate(candidate)
    except LedgerGateError:
        pass
    else:
        raise Phase8ProposalError("historic candidate unexpectedly grants scientific execution")
    print("PHASE8_NATIVE_CAPTURE_TRIALS=" + str(matrix["trial_count"]))
    print("PHASE8_NATIVE_CAPTURE_CONDITIONS=C3,C4,C8")
    print("PHASE8_NATIVE_CAPTURE_TOOL_NAME=run_scientific_model")
    print("PHASE8_NATIVE_CAPTURE_REAL_MAF_SDK_WIRING=present-not-yet-Plato-qualified")
    print("PHASE8_NATIVE_CAPTURE_REAL_MCP_DISPATCH=0")
    print("PHASE8_NATIVE_CAPTURE_REAL_PROVIDER_CALLS=0")
    print("PHASE8_NATIVE_CAPTURE_GPU_EXECUTIONS=0")
    print("PHASE8_NATIVE_CAPTURE_OUTCOME_BEARING=false")
    print("PHASE8_NATIVE_CAPTURE_SCIENTIFIC_EXECUTION_APPROVED=false")
    print("PHASE8_NATIVE_CAPTURE_OFFLINE_PREFLIGHT_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
