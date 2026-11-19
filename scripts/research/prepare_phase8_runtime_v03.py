"""Prepare an immutable-candidate Phase 8 v0.3 runtime record after live preflight.

Does NOT read an API key, call a model, modify the original October candidate,
or run a scientific case. This script verifies historical hashes, the frozen
Phase 7 method and the current package/prompt/tool/task identities.

The separate approval flag is a *researcher attestation*, not evidence that
the assistant independently verified the supervisor's decision. Without it,
the generated record remains a candidate and forbids scientific execution.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.prepare_ijcai_runtime_controls import (  # noqa: E402
    aggregate_sha256,
    sha256_file,
    pip_freeze,
)
from scripts.research.verify_phenoguard_method_freeze import verify_manifest  # noqa: E402

RUNTIME = ROOT / "experiments" / "ijcai2027" / "runtime"
OCT_CANDIDATE = RUNTIME / "runtime_controls_candidate.json"
PACKAGE_LOCK = RUNTIME / "requirements_phase8_pilot.lock"
EVIDENCE = RUNTIME / "live_preflight_evidence_20261119.json"
MODEL_PLAN = ROOT / "experiments" / "ijcai2027" / "model_plan.json"
RUNTIME_PLAN = ROOT / "experiments" / "ijcai2027" / "runtime_plan.json"

OCT_CANDIDATE_SHA = "85acd6efd5ae880051548977355f05d6bdd5e048c365a945a512378023355ce1"
LOCK_SHA = "2c67b0b895b81a482c148512ee5ab0de23e333bd21a4d44c31061e2fb19a6391"
METHOD_SHA = "25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294"

# These are *not* additions to the frozen Phase 7 v0.2 method. They define
# the concrete post-preflight experiment runtime and its interface.
RUNTIME_SOURCES = (
    "scripts/research/openrouter_compat.py",
    "scripts/research/validate_ijcai_openrouter_preflight.py",
    "scripts/research/capture_phase8_maf_request_shape.py",
    "scripts/research/check_phase8_openrouter_budget.py",
    "tests/research/test_phase8_openrouter_compat.py",
    "experiments/ijcai2027/model_plan.json",
    "experiments/ijcai2027/runtime_plan.json",
    "experiments/ijcai2027/condition_prompt_contract.json",
    "experiments/ijcai2027/runtime/live_preflight_evidence_20261119.json",
)

def get_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(cond: bool, message: str) -> None:
    if not cond:
        raise ValueError(message)


def check_inputs() -> tuple[dict, dict, dict]:
    check(OCT_CANDIDATE.is_file(), "October pre-outcome candidate missing")
    check(PACKAGE_LOCK.is_file(), "October package lock missing")
    check(EVIDENCE.is_file(), "live preflight evidence missing")
    check(sha256_file(OCT_CANDIDATE) == OCT_CANDIDATE_SHA, "October candidate hash changed")
    check(sha256_file(PACKAGE_LOCK) == LOCK_SHA, "October package-lock hash changed")

    count, method = verify_manifest()
    check(count == 22 and method == METHOD_SHA, "Phase 7 v0.2 freeze mismatch")

    old = get_json(OCT_CANDIDATE)
    check(old["phase7_freeze_aggregate_sha256"] == METHOD_SHA, "October freeze reference mismatch")
    check(old["controls"]["package_lock_sha256"] == LOCK_SHA, "October package lock reference mismatch")
    check(old["outcome_bearing_work_performed"] is False, "October candidate unexpectedly outcome-bearing")

    evidence = get_json(EVIDENCE)
    r = evidence.get("runtime", {})
    check(
        evidence.get("evidence_source") == "researcher-provided Plato terminal output",
        "live evidence provenance unexpected",
    )
    check(r.get("model_returned") == "openai/gpt-5.6-luna", "live model mismatch")
    check(r.get("preflight_pass") is True, "live preflight missing pass")
    check(r.get("tool_calls") == 1 and r.get("outcome_bearing") is False, "live echo not bounded")
    check(r.get("provider_pin") == "openai" and r.get("provider_fallbacks") is False, "provider pin changed")
    check(r.get("seed") == 2026 and r.get("temperature_sent") is False, "sampling changed")
    check(r.get("compatibility_adapter_enabled") is True, "adapter not verified live")
    check(evidence.get("scientific_outcomes_observed") is False, "unexpected prior scientific results")
    check(evidence.get("hidden_labels_inspected") is False, "hidden benchmark already opened")

    model_plan = get_json(MODEL_PLAN)
    runtime_plan = get_json(RUNTIME_PLAN)
    check(model_plan["primary"]["model_id"] == r["model_returned"], "model plan differs")
    check(runtime_plan["primary_model"]["model_id"] == r["model_returned"], "runtime model differs")
    check(model_plan["breadth"]["model_id"] == "openai/gpt-5.6-sol", "breadth model differs")
    check(
        model_plan["routing"]["openrouter_provider_object"]
        == {"order": ["openai"], "allow_fallbacks": False, "require_parameters": True},
        "provider routing plan changed",
    )
    check(runtime_plan["sampling"]["seed_schedule"] == [2026, 2027, 2028], "seed plan changed")
    check(runtime_plan["sampling"]["temperature_parameter_sent"] is False, "temperature rule changed")
    check(runtime_plan["sampling"]["reasoning"] == {"effort": "medium"}, "reasoning rule changed")
    check(runtime_plan["tool_loop"]["max_function_calls"] == 1, "tool count changed")
    check(runtime_plan["tool_loop"]["allow_concurrent_invocation"] is False, "parallel tools enabled")

    current_freeze = pip_freeze()
    locked_freeze = tuple(
        sorted(x.strip() for x in PACKAGE_LOCK.read_text(encoding="utf-8").splitlines() if x.strip())
    )
    check(current_freeze == locked_freeze, "environment package lock drifted")
    for package, version in runtime_plan["package_expectations"].items():
        check(importlib.metadata.version(package) == version, "package version changed: " + package)

    pairs = {
        "prompt_bundle_sha256": (
            "phenoassistant_maf/manager.py",
            "experiments/ijcai2027/condition_prompt_contract.json",
        ),
        "tool_catalogue_sha256": (
            "model_zoo.json",
            "phenoassistant_maf/registry.py",
            "phenoassistant_mcp/maf_bridge_v2.py",
        ),
        "task_manifest_sha256": (
            "research/phenoguard/pilot_manifest.py",
            "docs/research/IJCAI_2027_PROTOCOL_FREEZE.json",
        ),
    }
    for field, paths in pairs.items():
        actual = aggregate_sha256(tuple(ROOT / p for p in paths))
        check(actual == old["controls"][field], "frozen runtime input drifted: " + field)
    return old, evidence, runtime_plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--approved-provider-route",
        action="store_true",
        help="Researcher explicitly attests supervisor approval of credential ownership, billing route and Luna/Sol model choices",
    )
    args = parser.parse_args()

    try:
        old, evidence, runtime_plan = check_inputs()
        source_hashes = {}
        for path in RUNTIME_SOURCES:
            candidate = ROOT / path
            check(candidate.is_file(), "runtime source missing: " + path)
            source_hashes[path] = sha256_file(candidate)
    except (OSError, ValueError, KeyError) as exc:
        print("PHASE8_V03_RUNTIME_PREPARE_PASS=false")
        print("PHASE8_V03_REASON=" + str(exc))
        return 2

    approved = bool(args.approved_provider_route)
    status = (
        "PRE_OUTCOME_RUNTIME_FROZEN_PENDING_REPOSITORY_PRESERVATION"
        if approved else
        "PRE_OUTCOME_RUNTIME_CANDIDATE_PENDING_SUPERVISOR_PROVIDER_APPROVAL"
    )
    destination = RUNTIME / (
        "runtime_controls_frozen_v0.3.json"
        if approved else
        "runtime_controls_candidate_v0.3.json"
    )
    if destination.exists():
        print("PHASE8_V03_RUNTIME_PREPARE_PASS=false")
        print("PHASE8_V03_REASON=destination exists; refusing to overwrite evidence")
        return 3

    payload = {
        "schema": "phenoguard-phase8-runtime-v0.3",
        "status": status,
        "captured_utc": datetime.now(UTC).isoformat(),
        "phase7_freeze_aggregate_sha256": METHOD_SHA,
        "october_candidate_sha256": OCT_CANDIDATE_SHA,
        "october_package_lock_sha256": LOCK_SHA,
        "october_candidate_preserved": True,
        "controls": old["controls"],
        "extensions": old["extensions"],
        "hash_inputs": old["hash_inputs"],
        "runtime_plan": runtime_plan,
        "live_evidence": {
            "path": EVIDENCE.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(EVIDENCE),
            "response_model": evidence["runtime"]["model_returned"],
            "system_fingerprint": evidence["runtime"]["system_fingerprint"],
            "system_fingerprint_available": False,
            "tool_calls": 1,
            "seed": 2026,
            "scientific_outcomes_observed": False,
        },
        "http_transport_compatibility": {
            "interface_only": True,
            "rewrite_max_completion_tokens_to_max_tokens": True,
            "omit_parallel_tool_calls_only_if_false": True,
            "provider_require_parameters": True,
            "upstream_provider": "openai",
            "no_provider_fallbacks": True,
            "application_side_max_function_calls": 1,
            "source_hashes_sha256": source_hashes,
            "verified_post_adapter_capture": True,
            "verified_live_echo": True,
            "scientific_harness_adoption": "NOT_YET_VERIFIED",
        },
        "approval": {
            "researcher_attested_supervisor_provider_billing_and_models": approved,
            "independently_verified_by_assistant": False,
        },
        "api_key_read": False,
        "outcome_bearing_work_performed": False,
        "hidden_gold_unblinded": False,
        "scientific_execution_permitted": False,
        "scientific_execution_gate": (
            "Only after this record is verified and preserved as a commit/ref, "
            "provider-route approval exists, and an identical approved transport "
            "is integrated into the scientific evaluation harness."
        ),
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    check(sha256_file(OCT_CANDIDATE) == OCT_CANDIDATE_SHA, "October candidate changed during capture")
    print("PHASE8_V03_FILE=" + destination.relative_to(ROOT).as_posix())
    print("PHASE8_V03_SHA256=" + sha256_file(destination))
    print("PHASE8_V03_STATUS=" + status)
    print("PHASE8_V03_METHOD_AGGREGATE=" + METHOD_SHA)
    print("PHASE8_V03_OLD_CANDIDATE_PRESERVED=true")
    print("PHASE8_V03_API_KEY_READ=false")
    print("PHASE8_V03_OUTCOME_BEARING=false")
    print("PHASE8_V03_SCIENTIFIC_EXECUTION_PERMITTED=false")
    print("PHASE8_V03_RUNTIME_PREPARE_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
