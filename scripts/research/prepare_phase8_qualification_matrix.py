"""Prepare a frozen, NO-INFERENCE 12-case C3/C4/C8 pilot qualification matrix.

This plans experiments only. It never opens gold labels, creates a model
client, reads credentials or performs scientific inference. The 12 cases
qualify the harness; they are NOT the final scientific-shift benchmark.

Critical separation: internal scenario identifiers and category/shift fields
must NEVER be copied into model-facing prompts. A narrow allowlisted
model-visible request view is separately hashed here.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.phenoguard.benchmark import BenchmarkSplit  # noqa: E402
from research.phenoguard.experiment_protocol import ConditionId  # noqa: E402
from research.phenoguard.pilot_manifest import build_development_validation_manifest  # noqa: E402

EXPERIMENT_DIR = ROOT / "experiments" / "ijcai2027"
RUNTIME_DIR = EXPERIMENT_DIR / "runtime"
CANDIDATE = RUNTIME_DIR / "runtime_controls_candidate_v0.3.json"
RUNTIME_PLAN = EXPERIMENT_DIR / "runtime_plan.json"
PROTOCOL = ROOT / "docs" / "research" / "IJCAI_2027_PROTOCOL_FREEZE.json"
CONDITION_PROMPTS = EXPERIMENT_DIR / "condition_prompt_contract.json"
OUTPUT = RUNTIME_DIR / "phase8_c3_c4_c8_qualification_matrix_v0.1.json"
EXPECTED_CANDIDATE_SHA256 = "e3a8826b8942f2b0951775b557ce3530b2a54ed7666e827e3687443974718c12"
METHOD_SHA256 = "25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294"

CONDITIONS = (
    ConditionId.MANAGER_TOOL_SCHEMAS,
    ConditionId.MANAGER_GENERIC_CRITIC,
    ConditionId.FULL_PHENOGUARD,
)
EXPECTED_SEEDS = (2026, 2027, 2028)
# Assumptions only, from authenticated 2026-11-19 model-catalogue pricing.
LUNA_INPUT_USD_PER_MILLION = Decimal("0.20")
LUNA_OUTPUT_USD_PER_MILLION = Decimal("1.20")
ASSUMED_INPUT_TOKENS_PER_ROUND = 4000


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_value(obj: object) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def model_visible_view(scenario) -> dict:
    """The only scenario-derived fields allowed into a model prompt.

    No scenario_id, split, pair_id, category, evidence_source, shift_dimension,
    fixture_ref, benchmark-gold object, or expected decision is returned.
    """
    return {
        "scientific_request": scenario.request.model_dump(mode="json"),
        "requested_capability_id": scenario.requested_capability_id,
        "training_readiness": (
            scenario.training_readiness.model_dump(mode="json")
            if scenario.training_readiness is not None else None
        ),
    }


def make_trial_id(scenario_id: str, condition: str, seed: int) -> str:
    payload = f"phase8-qualification-v0.1\t{scenario_id}\t{condition}\t{seed}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def build_matrix(*, candidate: dict, runtime: dict, protocol: dict, prompt_contract: dict) -> dict:
    if candidate["phase7_freeze_aggregate_sha256"] != METHOD_SHA256:
        raise ValueError("candidate does not refer to the frozen Phase 7 method")
    if candidate["status"] != "PRE_OUTCOME_RUNTIME_CANDIDATE_PENDING_SUPERVISOR_PROVIDER_APPROVAL":
        raise ValueError("the v0.3 candidate state unexpectedly changed")
    if candidate["approval"]["researcher_attested_supervisor_provider_billing_and_models"] is not False:
        raise ValueError("candidate has an unexpected approval state")
    if candidate["scientific_execution_permitted"] is not False:
        raise ValueError("qualification planner must not run against an execution-enabled state")
    if candidate["outcome_bearing_work_performed"] is not False:
        raise ValueError("candidate claims outcomes already observed")
    if candidate["controls"]["model_id"] != "openai/gpt-5.6-luna":
        raise ValueError("unexpected primary model")
    if candidate["http_transport_compatibility"]["verified_live_echo"] is not True:
        raise ValueError("live echo evidence missing")
    if candidate["http_transport_compatibility"]["scientific_harness_adoption"] != "NOT_YET_VERIFIED":
        raise ValueError("unexpected scientific harness status")
    if runtime["sampling"]["seed_schedule"] != list(EXPECTED_SEEDS):
        raise ValueError("seed schedule changed")
    if runtime["sampling"]["max_output_tokens"] != 2048:
        raise ValueError("output-token ceiling changed")
    if runtime["tool_loop"]["max_iterations"] != 2:
        raise ValueError("iteration control changed")
    if runtime["tool_loop"]["max_function_calls"] != 1:
        raise ValueError("maximum function-call count changed")
    if protocol["primary_interface"] != "mcp":
        raise ValueError("primary interface is no longer MCP")
    if protocol["hidden_labels_available_to_method"] is not False:
        raise ValueError("hidden labels may not be exposed")
    if protocol["qualification_manifest"] != {
        "development_cases": 8,
        "validation_cases": 4,
        "hidden_cases": 0,
        "matched_pairs": 5,
        "unpaired_training_policy_cases": 2,
        "purpose": "harness qualification only; not final scientific performance evidence",
    }:
        raise ValueError("frozen qualification manifest changed")
    for condition in CONDITIONS:
        if condition.value not in protocol["conditions"]:
            raise ValueError("required condition not in protocol")
        if condition.value not in prompt_contract["conditions"]:
            raise ValueError("required condition not in prompt contract")

    scenarios = build_development_validation_manifest()
    if len(scenarios) != 12:
        raise ValueError("qualification manifest no longer has exactly 12 cases")
    scenario_ids = [scenario.scenario_id for scenario in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError("duplicate scenario IDs")
    splits = Counter(scenario.split.value for scenario in scenarios)
    if splits != {"development": 8, "validation": 4}:
        raise ValueError("qualification split/counts changed")
    if any(scenario.split is BenchmarkSplit.HIDDEN for scenario in scenarios):
        raise ValueError("hidden cases cannot enter qualification")

    trials = []
    visible_views = []
    for scenario in scenarios:
        view = model_visible_view(scenario)
        if set(view) != {
            "scientific_request", "requested_capability_id", "training_readiness"
        }:
            raise ValueError("unexpected model-visible field")
        fingerprint = sha256_value(view)
        visible_views.append(fingerprint)
        for condition in CONDITIONS:
            for seed in EXPECTED_SEEDS:
                trials.append({
                    # INTERNAL bookkeeping only: never transmit this trial record
                    # or its scenario_id to an LLM.
                    "trial_id": make_trial_id(scenario.scenario_id, condition.value, seed),
                    "scenario_id_internal_only": scenario.scenario_id,
                    "split_internal_only": scenario.split.value,
                    "condition_id": condition.value,
                    "seed": seed,
                    "model_visible_view_sha256": fingerprint,
                    "status": "PLANNED_NO_MODEL_CALL",
                })

    if len(trials) != 108:
        raise ValueError("expected exactly 12 x 3 x 3 = 108 trial records")
    if len({t["trial_id"] for t in trials}) != len(trials):
        raise ValueError("duplicate trial identities")
    for scenario_id in scenario_ids:
        subset = [t for t in trials if t["scenario_id_internal_only"] == scenario_id]
        if len({t["model_visible_view_sha256"] for t in subset}) != 1:
            raise ValueError("model-visible case context differs across conditions")

    rounds = runtime["tool_loop"]["max_iterations"]
    output_tokens = runtime["sampling"]["max_output_tokens"]
    projected = (
        Decimal(len(trials)) * Decimal(rounds) * (
            Decimal(ASSUMED_INPUT_TOKENS_PER_ROUND) * LUNA_INPUT_USD_PER_MILLION
            + Decimal(output_tokens) * LUNA_OUTPUT_USD_PER_MILLION
        ) / Decimal(1_000_000)
    )
    return {
        "schema": "phenoguard-phase8-c3-c4-c8-qualification-matrix-v0.1",
        "status": "OFFLINE_PLANNED_NOT_APPROVED_NOT_EXECUTED",
        "purpose": "harness qualification on frozen development/validation only, NOT a scientific claim",
        "phase7_method_sha256": METHOD_SHA256,
        "runtime_v03_candidate_sha256": EXPECTED_CANDIDATE_SHA256,
        "model": candidate["controls"]["model_id"],
        "interface": "mcp",
        "conditions": [c.value for c in CONDITIONS],
        "seeds": list(EXPECTED_SEEDS),
        "case_count": len(scenarios),
        "split_counts": dict(sorted(splits.items())),
        "trial_count": len(trials),
        "model_visible_context": {
            "field_allowlist": ["scientific_request", "requested_capability_id", "training_readiness"],
            "no_category_shift_labels_pair_ids_or_case_ids": True,
            "unique_scenario_view_hashes": len(set(visible_views)),
            "note": "hashes bind visible case facts; do NOT send trial metadata as prompts",
        },
        "cost_forecast": {
            "usd": str(projected),
            "input_usd_per_million": str(LUNA_INPUT_USD_PER_MILLION),
            "output_usd_per_million": str(LUNA_OUTPUT_USD_PER_MILLION),
            "assumed_input_tokens_per_round": ASSUMED_INPUT_TOKENS_PER_ROUND,
            "assumed_output_tokens_per_round": output_tokens,
            "max_rounds_per_trial": rounds,
            "provider_retry_and_token_drift_not_included": True,
            "forecast_not_measured": True,
        },
        "required_before_paid_scientific_trials": [
            "supervisor-approved credential/provider/billing/model route recorded",
            "final runtime candidate approved and preserved with source hashes",
            "C3/C4/C8 condition-specific tool/prompt exposure verified",
            "same HTTP compatibility adapter applied to all model calls",
            "MCP actual scientific-tool dispatch and sandbox/no-harm policy validated",
            "append-only attempt logs, measured cost cap and no semantic retries tested",
            "scientific C8 pre-and-post validation and C4 generic critic audited",
            "hidden evaluation stays sealed",
        ],
        "scientific_execution_permitted": False,
        "api_key_read": False,
        "outcome_bearing_work_performed": False,
        "trials": trials,
    }


def main() -> int:
    if OUTPUT.exists():
        print("PHASE8_QUALIFICATION_PLAN_PASS=false")
        print("PHASE8_QUALIFICATION_REASON=output-already-exists-refuse-overwrite")
        return 3
    try:
        if hash_file(CANDIDATE) != EXPECTED_CANDIDATE_SHA256:
            raise ValueError("verified v0.3 candidate hash mismatch")
        candidate = read_json(CANDIDATE)
        runtime = read_json(RUNTIME_PLAN)
        protocol = read_json(PROTOCOL)
        prompts = read_json(CONDITION_PROMPTS)
        matrix = build_matrix(
            candidate=candidate,
            runtime=runtime,
            protocol=protocol,
            prompt_contract=prompts,
        )
        OUTPUT.write_text(
            json.dumps(matrix, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print("PHASE8_QUALIFICATION_PLAN_PASS=false")
        print("PHASE8_QUALIFICATION_REASON=" + str(exc))
        return 2

    print("PHASE8_QUALIFICATION_MATRIX=" + OUTPUT.relative_to(ROOT).as_posix())
    print("PHASE8_QUALIFICATION_MATRIX_SHA256=" + hash_file(OUTPUT))
    print("PHASE8_QUALIFICATION_CASE_COUNT=" + str(matrix["case_count"]))
    print("PHASE8_QUALIFICATION_TRIAL_COUNT=" + str(matrix["trial_count"]))
    print("PHASE8_QUALIFICATION_ESTIMATED_USD=" + matrix["cost_forecast"]["usd"])
    print("PHASE8_QUALIFICATION_SCIENTIFIC_EXECUTION_PERMITTED=false")
    print("PHASE8_QUALIFICATION_API_KEY_READ=false")
    print("PHASE8_QUALIFICATION_OUTCOME_BEARING=false")
    print("PHASE8_QUALIFICATION_PLAN_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
