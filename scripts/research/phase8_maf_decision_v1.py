"""Pre-outcome MAF Manager + independent generic LLM Critic wiring.

Unlike the *mocked* condition rehearsal, this module contains real MAF
ChatClient calls with the validated OpenRouter transport. The only exposed
result is a typed, non-executing *proposal*: vision model execution MUST be
authorized and performed later by the separate bounded MCP dispatcher.

Safety boundaries:
- No CLI flag can approve scientific execution. The CLI is offline-only.
- Real-client construction requires a SHA-pinned final approved runtime.
- This module never reads an API key from the environment itself.
- C3/C4 Manager messages are byte-identical given the same base request.
- C4 Critic is a separate LLM roundtrip, and receives NO SOE information.
- C8 alone sees provenance-backed scientific operating envelopes.
- No gold, shift labels, internal case IDs or raw file paths in prompt data.
- This is proposal transport, NOT finished live scientific evaluation.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from agent_framework import Message
from agent_framework.openai import OpenAIChatCompletionClient
from openai import AsyncOpenAI
from mcp import Client
from mcp.server import MCPServer

from phenoassistant_mcp.client_v2 import MCP_PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phenoassistant_mcp.scientific_inference_v1 import verify_approved_runtime  # noqa: E402
from research.phenoguard.contracts import ApplicabilityDecision, ScientificRequestContext, TrainingReadinessContext  # noqa: E402
from research.phenoguard.provenance import build_default_provenance_catalogue  # noqa: E402
from scripts.research.openrouter_compat import OpenRouterCompatTransport  # noqa: E402
from scripts.research.phase8_condition_rehearsal import C3, C4, C8, Proposal  # noqa: E402
from scripts.research.phase8_attempt_ledger import load_verified_controls, scientific_gate, LedgerGateError  # noqa: E402

MODEL = "openai/gpt-5.6-luna"
PROVIDER = {"order": ["openai"], "allow_fallbacks": False, "require_parameters": True}
SEEDS = (2026, 2027, 2028)
OUTPUT_TOKENS = 2048
BANNED_KEYS = frozenset((
    "scenario_id", "pair_id", "split", "category", "shift_dimension",
    "evidence_source", "fixture_refs", "expected_decision",
    "expected_selected_capability_id", "rationale_code", "gold",
))
TOOL_NAME = "run_scientific_model"
TOOL_PROPERTIES = frozenset(("capability_id", "image_asset_id"))

BASE_INSTRUCTIONS = (
    "You are the PhenoAssistant scientific-capability proposal Manager. "
    "Select a registered scientific model using only the supplied scientific "
    "request and MCP tool schema. Produce exactly one JSON object with keys "
    "decision and capability_id. decision must be EXECUTE, RESELECT, CLARIFY, "
    "ABSTAIN, or RECOMMEND_TRAINING. For EXECUTE/RESELECT provide the exact "
    "catalogue capability_id; otherwise capability_id must be null. "
    "You are proposing a possible tool action, NOT executing the model. "
    "Never invent results, output artefacts, scientific applicability evidence, "
    "or completed tool calls. Do not include markdown or explanation."
)

CRITIC_INSTRUCTIONS = (
    "You are an independent, GENERIC LLM Critic reviewing the Manager's "
    "proposed tool action. Examine general tool-schema consistency, task fit, "
    "ambiguity and uncertainty using only the supplied request, MCP schema "
    "and proposal. You have no scientific operating envelopes or hidden "
    "ground-truth labels; do not assume any. Produce only a JSON object "
    "with keys decision and capability_id using the same five allowed "
    "decision types. For non-execution decisions use null capability_id. "
    "Do not execute tools or invent model results."
)


class Phase8ProposalError(ValueError):
    """Local fail-closed model/prompt/response error."""


@dataclass(frozen=True)
class ProposalEvidence:
    role: str
    proposal: Proposal
    response_model: str
    response_sha256: str
    fingerprint: str | None
    input_tokens: int | None
    output_tokens: int | None
    cost_usd_measured: None = None
    scientific_tool_executed: bool = False


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _reject_leakage(value: Any) -> None:
    """Reject prohibited bookkeeping fields anywhere in model-facing data."""
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise Phase8ProposalError("non-string model-visible metadata key")
        if BANNED_KEYS.intersection(value):
            raise Phase8ProposalError("benchmark label or scenario identifier in prompt")
        for item in value.values():
            _reject_leakage(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _reject_leakage(item)


def validate_view(view: dict[str, Any]) -> dict:
    if not isinstance(view, dict) or set(view) != {
        "scientific_request", "requested_capability_id", "training_readiness"
    }:
        raise Phase8ProposalError("unexpected manager-visible request fields")
    _reject_leakage(view)
    try:
        ScientificRequestContext.model_validate(view["scientific_request"])
        if view["training_readiness"] is not None:
            TrainingReadinessContext.model_validate(view["training_readiness"])
    except (ValueError, TypeError) as exc:
        raise Phase8ProposalError("untyped scientific request") from exc
    requested = view["requested_capability_id"]
    if requested is not None and (not isinstance(requested, str) or not requested.strip()):
        raise Phase8ProposalError("invalid requested capability")
    return json.loads(json.dumps(view))


def validate_mcp_schema(tool: dict[str, Any]) -> dict:
    """Use the exact trusted MCP server's discovered schema, not a guess."""
    if not isinstance(tool, dict) or set(tool) != {
        "name", "description", "input_schema"
    }:
        raise Phase8ProposalError("MCP tool metadata malformed")
    if tool["name"] != TOOL_NAME or not isinstance(tool["description"], str):
        raise Phase8ProposalError("unexpected MCP tool")
    if not tool["description"].strip():
        raise Phase8ProposalError("MCP tool description is blank")
    schema = tool["input_schema"]
    if not isinstance(schema, dict) or schema.get("type") != "object":
        raise Phase8ProposalError("MCP input schema is not an object")
    properties = schema.get("properties")
    if not isinstance(properties, dict) or set(properties) != TOOL_PROPERTIES:
        raise Phase8ProposalError("MCP schema must expose only capability_id and image_asset_id")
    if set(schema.get("required", [])) != TOOL_PROPERTIES:
        raise Phase8ProposalError("both MCP tool parameters must be required")
    if any(p.get("type") != "string" for p in properties.values() if isinstance(p, dict)):
        raise Phase8ProposalError("MCP tool parameters must be strings")
    if not all(isinstance(p, dict) for p in properties.values()):
        raise Phase8ProposalError("MCP schema property malformed")
    _reject_leakage(tool)
    return json.loads(json.dumps(tool))


async def discover_real_mcp_tool(server: MCPServer) -> dict[str, Any]:
    """Discover the scientific tool from the real MCP protocol without calling it.

    This queries exactly one advertised tool and returns only schema metadata,
    not a fixture, raw path, gold label or scientific result.
    """
    async with Client(server, mode=MCP_PROTOCOL_VERSION) as client:
        listing = await asyncio.wait_for(client.list_tools(), timeout=10)
    if len(listing.tools) != 1 or listing.tools[0].name != TOOL_NAME:
        raise Phase8ProposalError("unexpected number or identity of MCP tools")
    tool = listing.tools[0]
    serialized = tool.model_dump(by_alias=True)
    schema = serialized.get("inputSchema", serialized.get("input_schema"))
    return validate_mcp_schema({
        "name": tool.name,
        "description": tool.description,
        "input_schema": schema,
    })


def manager_prompt(
    condition: str, visible_view: dict[str, Any], discovered_tool: dict[str, Any],
) -> tuple[str, str]:
    if condition not in (C3, C4, C8):
        raise Phase8ProposalError("unregistered condition")
    view = validate_view(visible_view)
    tool = validate_mcp_schema(discovered_tool)
    message = {"request": view, "mcp_tool_schema": tool}
    if condition == C8:
        message["scientific_operating_envelopes"] = [
            e.model_dump(mode="json") for e in build_default_provenance_catalogue()
        ]
    _reject_leakage(message)
    return BASE_INSTRUCTIONS, json.dumps(message, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def critic_prompt(
    visible_view: dict[str, Any], discovered_tool: dict[str, Any],
    manager_proposal: Proposal,
) -> tuple[str, str]:
    view = validate_view(visible_view)
    tool = validate_mcp_schema(discovered_tool)
    if not isinstance(manager_proposal, Proposal):
        raise Phase8ProposalError("untyped manager proposal")
    body = {
        "request": view,
        "mcp_tool_schema": tool,
        "manager_proposal": {
            "decision": manager_proposal.decision.value,
            "capability_id": manager_proposal.capability_id,
        },
    }
    _reject_leakage(body)
    return CRITIC_INSTRUCTIONS, json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def parse_proposal(raw: str) -> Proposal:
    if not isinstance(raw, str) or len(raw) > 8192:
        raise Phase8ProposalError("missing or oversized model decision")
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise Phase8ProposalError("model decision must be strict JSON") from exc
    if not isinstance(parsed, dict) or set(parsed) != {"decision", "capability_id"}:
        raise Phase8ProposalError("decision JSON has wrong fields")
    try:
        action = ApplicabilityDecision(parsed["decision"])
        selected = parsed["capability_id"]
        proposal = Proposal(action, selected)
    except (ValueError, TypeError) as exc:
        raise Phase8ProposalError("invalid model decision or capability ID") from exc
    if proposal.capability_id is not None and proposal.capability_id not in {
        e.capability_id for e in build_default_provenance_catalogue()
    }:
        raise Phase8ProposalError("model selected unregistered scientific checkpoint")
    return proposal


def response_evidence(response: Any, *, role: str) -> ProposalEvidence:
    model = getattr(response, "model", None)
    if model != MODEL:
        raise Phase8ProposalError("response model identity drift")
    raw = getattr(response, "text", None)
    proposal = parse_proposal(raw)
    props = getattr(response, "additional_properties", None)
    fingerprint = props.get("system_fingerprint") if isinstance(props, dict) else None
    if fingerprint is not None and not isinstance(fingerprint, str):
        fingerprint = None
    usage = getattr(response, "usage", None)
    if isinstance(usage, dict):
        input_tokens = usage.get("input_token_count")
        output_tokens = usage.get("output_token_count")
    else:
        input_tokens = getattr(usage, "input_token_count", None)
        output_tokens = getattr(usage, "output_token_count", None)
    if not isinstance(input_tokens, int) or isinstance(input_tokens, bool) or input_tokens < 0:
        input_tokens = None
    if not isinstance(output_tokens, int) or isinstance(output_tokens, bool) or output_tokens < 0:
        output_tokens = None
    return ProposalEvidence(
        role=role,
        proposal=proposal,
        response_model=model,
        response_sha256=_hash_text(raw),
        fingerprint=fingerprint,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


class Phase8MafDecisionClient:
    """Real MAF service; model calls occur ONLY through explicit methods."""

    def __init__(self, *, chat: OpenAIChatCompletionClient, sdk: AsyncOpenAI,
                 http_client: httpx.AsyncClient, seed: int) -> None:
        if seed not in SEEDS or isinstance(seed, bool):
            raise Phase8ProposalError("seed schedule changed")
        self.chat = chat
        self.sdk = sdk
        self.http_client = http_client
        self.seed = seed

    @classmethod
    def create(
        cls, *,
        approved_runtime_path: Path,
        approved_runtime_sha256: str,
        api_key: str,
        seed: int,
        upstream: httpx.AsyncBaseTransport | None = None,
    ) -> "Phase8MafDecisionClient":
        # Real-model construction is impossible with historic unapproved v0.3.
        verify_approved_runtime(approved_runtime_path, approved_runtime_sha256)
        if not isinstance(api_key, str) or not api_key.strip():
            raise Phase8ProposalError("approved runtime requires an explicit key")
        if type(seed) is not int or seed not in SEEDS:
            raise Phase8ProposalError("unapproved seed")
        transport = OpenRouterCompatTransport(
            expected_model=MODEL, token_ceiling=OUTPUT_TOKENS, upstream=upstream,
        )
        http_client = httpx.AsyncClient(transport=transport)
        sdk = AsyncOpenAI(
            api_key=api_key, base_url="https://openrouter.ai/api/v1",
            http_client=http_client, max_retries=0,
        )
        chat = OpenAIChatCompletionClient(
            model=MODEL,
            async_client=sdk,
            function_invocation_configuration={
                "max_iterations": 2,
                "max_function_calls": 1,
                "allow_concurrent_invocation": False,
                "terminate_on_unknown_calls": True,
            },
        )
        return cls(chat=chat, sdk=sdk, http_client=http_client, seed=seed)

    def _options(self) -> dict[str, Any]:
        return {
            "tools": [],
            "tool_choice": "none",
            "allow_multiple_tool_calls": False,
            "max_tokens": OUTPUT_TOKENS,
            "seed": self.seed,
            "extra_body": {"provider": dict(PROVIDER), "reasoning": {"effort": "medium"}},
        }

    async def _call(self, system: str, user: str, *, role: str) -> ProposalEvidence:
        response = await self.chat.get_response(
            [
                Message(role="system", contents=[system]),
                Message(role="user", contents=[user]),
            ],
            options=self._options(),
        )
        return response_evidence(response, role=role)

    async def propose_manager(self, *, condition: str, visible_view: dict[str, Any],
                              discovered_tool: dict[str, Any]) -> ProposalEvidence:
        system, user = manager_prompt(condition, visible_view, discovered_tool)
        return await self._call(system, user, role="manager")

    async def critique(self, *, condition: str, visible_view: dict[str, Any],
                      discovered_tool: dict[str, Any],
                      manager_proposal: Proposal) -> ProposalEvidence:
        if condition != C4:
            raise Phase8ProposalError("Critic may be invoked only in C4")
        system, user = critic_prompt(visible_view, discovered_tool, manager_proposal)
        return await self._call(system, user, role="generic_critic")

    async def close(self) -> None:
        await self.sdk.close()
        await self.http_client.aclose()


def main() -> int:
    """Print non-scientific, non-inference authorization state only."""
    matrix, candidate = load_verified_controls()
    try:
        scientific_gate(candidate)
    except LedgerGateError:
        approved = False
    else:
        approved = True
    if approved:
        raise Phase8ProposalError("historic v0.3 candidate unexpectedly authorizes inference")
    print("PHASE8_MAF_DECISION_MODEL=" + MODEL)
    print("PHASE8_MAF_DECISION_TRIALS=" + str(matrix["trial_count"]))
    print("PHASE8_MAF_DECISION_C3_C4_MANAGER_PROMPTS_MATCH=true")
    print("PHASE8_MAF_DECISION_REAL_OPENROUTER_IMPLEMENTATION=present")
    print("PHASE8_MAF_DECISION_ACTUAL_REQUESTS=0")
    print("PHASE8_MAF_DECISION_REAL_CRITIC_CALLS=0")
    print("PHASE8_MAF_DECISION_SCIENTIFIC_TOOL_CALLS=0")
    print("PHASE8_MAF_DECISION_OUTCOME_BEARING=false")
    print("PHASE8_MAF_DECISION_APPROVED_TO_RUN=false")
    print("PHASE8_MAF_DECISION_OFFLINE_PREFLIGHT_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
