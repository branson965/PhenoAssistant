"""Executable, NO-NETWORK C3/C4/C8 condition-isolation rehearsal.

This is a reusable *orchestration contract check*, NOT the scientific
runner. Inputs are injected async fakes; no API key, LLM client, MCP
server or scientific model is constructed. The rehearsal can show that
the intended three branches differ; it cannot prove that a generic
Critic LLM, real MCP tool, or live post-validation has been integrated.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.phenoguard.catalogue import resolve_capability_catalogue  # noqa: E402
from research.phenoguard.contracts import ApplicabilityDecision  # noqa: E402
from research.phenoguard.provenance import build_default_provenance_catalogue  # noqa: E402
from research.phenoguard.post_validation import PostExecutionValidation  # noqa: E402
from research.phenoguard.pilot_manifest import build_development_validation_manifest  # noqa: E402
from scripts.research.prepare_phase8_qualification_matrix import model_visible_view  # noqa: E402
from scripts.research.phase8_attempt_ledger import load_verified_controls, scientific_gate, LedgerGateError  # noqa: E402


C3 = "C3_MANAGER_TOOL_SCHEMAS"
C4 = "C4_MANAGER_GENERIC_CRITIC"
C8 = "C8_FULL_PHENOGUARD"
CONDITIONS = {C3, C4, C8}
ACTIONS = {ApplicabilityDecision.EXECUTE, ApplicabilityDecision.RESELECT}
USER_VISIBLE_KEYS = {"scientific_request", "requested_capability_id", "training_readiness"}

# Manager and critic callbacks see ONLY the explicit dictionaries passed to
# them, not a BenchmarkScenario object, category, split, pair ID or gold label.
Manager = Callable[[dict[str, Any]], Awaitable["Proposal"]]
Critic = Callable[[dict[str, Any], "Proposal"], Awaitable["Proposal"]]
Executor = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]
Validator = Callable[[dict[str, Any]], Awaitable[PostExecutionValidation]]


@dataclass(frozen=True)
class Proposal:
    decision: ApplicabilityDecision
    capability_id: str | None

    def __post_init__(self) -> None:
        if self.decision in ACTIONS:
            if not isinstance(self.capability_id, str) or not self.capability_id.strip():
                raise ValueError("executable proposal requires capability ID")
        elif self.capability_id is not None:
            raise ValueError("non-executable proposal cannot select a capability")


@dataclass(frozen=True)
class RehearsalObservation:
    condition: str
    decision: ApplicabilityDecision
    selected_capability_id: str | None
    critic_used: bool
    soe_pre_verifier_used: bool
    tool_attempted_in_mock: bool
    post_validator_used: bool
    safe_to_report: bool
    model_visible_sha256: str
    report_scope: str = "SIMULATED_OFFLINE_NOT_SCIENTIFIC_EVIDENCE"


def _sha(obj: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        .encode("utf-8")
    ).hexdigest()


def _validate_view(view: dict[str, Any]) -> None:
    if set(view) != USER_VISIBLE_KEYS:
        raise ValueError("model-visible view contains internal or unexpected fields")
    if not isinstance(view["scientific_request"], dict):
        raise ValueError("scientific request is not typed JSON")
    if not isinstance(view["scientific_request"].get("scientific_task"), str):
        raise ValueError("scientific task missing")
    if view["requested_capability_id"] is not None and not isinstance(
        view["requested_capability_id"], str
    ):
        raise ValueError("invalid requested capability identifier")


async def rehearse_one(
    *,
    condition: str,
    visible_view: dict[str, Any],
    manager: Manager,
    critic: Critic | None,
    mock_executor: Executor,
    post_validator: Validator | None,
) -> RehearsalObservation:
    """No provider calls; fail closed if condition wiring is incomplete."""
    if condition not in CONDITIONS:
        raise ValueError("unregistered condition")
    _validate_view(visible_view)
    if condition == C4 and critic is None:
        raise ValueError("C4 requires a separate Critic callback")
    if condition != C4 and critic is not None:
        raise ValueError("generic Critic exposure is forbidden outside C4")
    if condition == C8 and post_validator is None:
        raise ValueError("C8 requires a post-execution validator")
    if condition != C8 and post_validator is not None:
        raise ValueError("C3/C4 must not receive PhenoGuard post-validation")

    # Fresh deep copy prevents one mocked component from modifying a
    # shared request used by another experimental condition.
    view = json.loads(json.dumps(visible_view))
    proposal = await manager(json.loads(json.dumps(view)))
    if not isinstance(proposal, Proposal):
        raise ValueError("manager did not produce a typed proposal")
    original_visible_hash = _sha(view)

    if condition == C4:
        assert critic is not None
        proposal = await critic(json.loads(json.dumps(view)), proposal)
        if not isinstance(proposal, Proposal):
            raise ValueError("Critic did not produce a typed proposal")

    pre_used = condition == C8
    if pre_used:
        # Scientific envelopes are available ONLY to C8. The generic
        # Critic never gets this provenance/compatibility contract.
        from research.phenoguard.contracts import (
            ScientificRequestContext, TrainingReadinessContext,
        )
        request = ScientificRequestContext.model_validate(view["scientific_request"])
        training = (
            TrainingReadinessContext.model_validate(view["training_readiness"])
            if view["training_readiness"] is not None else None
        )
        # Respect an explicit user-requested capability. Otherwise assess
        # the manager's proposed capability as its execution candidate.
        requested = view["requested_capability_id"] or proposal.capability_id
        resolution = resolve_capability_catalogue(
            build_default_provenance_catalogue(),
            request,
            requested_capability_id=requested,
            training_readiness=training,
        )
        decision = resolution.decision
        selected = resolution.selected_capability_id
    else:
        decision = proposal.decision
        selected = proposal.capability_id

    attempted = decision in ACTIONS
    validated = False
    safe_to_report = True
    if attempted:
        if selected is None:
            raise ValueError("unsafe execution without selected capability")
        mock_result = await mock_executor(
            selected, json.loads(json.dumps(view["scientific_request"]))
        )
        if not isinstance(mock_result, dict):
            raise ValueError("mock executor returned invalid result")
        if pre_used:
            assert post_validator is not None
            post = await post_validator(json.loads(json.dumps(mock_result)))
            if not isinstance(post, PostExecutionValidation):
                raise ValueError("post-validator did not produce typed validation")
            validated = True
            safe_to_report = post.safe_to_report

    if _sha(view) != original_visible_hash:
        raise ValueError("base visible request mutated during experiment")
    return RehearsalObservation(
        condition=condition,
        decision=decision,
        selected_capability_id=selected,
        critic_used=condition == C4,
        soe_pre_verifier_used=pre_used,
        tool_attempted_in_mock=attempted,
        post_validator_used=validated,
        safe_to_report=safe_to_report,
        model_visible_sha256=original_visible_hash,
    )


def main() -> int:
    try:
        matrix, candidate = load_verified_controls()
        # Do not run a real LLM, scientific model, or MCP tool. Even if
        # callers eventually add an approved runtime, this CLI remains
        # a synthetic rehearsal with the same fixed no-inference markers.
        try:
            scientific_gate(candidate)
        except LedgerGateError:
            approved = False
        else:
            approved = True
        if approved:
            raise ValueError("unexpected approval in historic v0.3 candidate")

        scenario = build_development_validation_manifest()[0]
        visible = model_visible_view(scenario)
        observed = []

        async def manager(_visible):
            return Proposal(
                decision=ApplicabilityDecision.EXECUTE,
                capability_id=scenario.requested_capability_id,
            )

        async def critic(_visible, proposal):
            return proposal

        async def executor(_selected, _request):
            return {"leaf_count": 2, "projected_leaf_area": 15.0}

        async def validate(result):
            from research.phenoguard.post_validation import validate_phenotype_records
            return validate_phenotype_records((result,))

        async def rehearsals():
            for condition in (C3, C4, C8):
                observation = await rehearse_one(
                    condition=condition,
                    visible_view=visible,
                    manager=manager,
                    critic=critic if condition == C4 else None,
                    mock_executor=executor,
                    post_validator=validate if condition == C8 else None,
                )
                observed.append(observation)

        asyncio.run(rehearsals())
        if len(observed) != 3:
            raise ValueError("incomplete rehearsal conditions")
        if any(x.model_visible_sha256 != observed[0].model_visible_sha256 for x in observed):
            raise ValueError("same-case model-visible request diverged")
        if not observed[1].critic_used or not observed[2].soe_pre_verifier_used:
            raise ValueError("condition verification modes not distinct")
        if not observed[2].post_validator_used:
            raise ValueError("C8 did not validate the fake tool result")
        if matrix["trial_count"] != 108:
            raise ValueError("trial plan changed")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("PHASE8_CONDITION_REHEARSAL_PASS=false")
        print("PHASE8_CONDITION_REASON=" + str(exc))
        return 2

    print("PHASE8_CONDITION_REHEARSAL_MODES=C3,C4,C8")
    print("PHASE8_CONDITION_REHEARSAL_SHARED_REQUEST_HASH=" + observed[0].model_visible_sha256)
    print("PHASE8_CONDITION_REHEARSAL_MOCK_EXECUTIONS=3")
    print("PHASE8_CONDITION_REHEARSAL_REAL_SCIENTIFIC_DISPATCH=false")
    print("PHASE8_CONDITION_REHEARSAL_REAL_GENERIC_LLM_CRITIC=false")
    print("PHASE8_CONDITION_REHEARSAL_PROVIDER_CALLS=0")
    print("PHASE8_CONDITION_REHEARSAL_GOLD_LABELS_READ=false")
    print("PHASE8_CONDITION_REHEARSAL_OUTCOME_BEARING=false")
    print("PHASE8_CONDITION_REHEARSAL_EXECUTION_APPROVED=false")
    print("PHASE8_CONDITION_REHEARSAL_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
