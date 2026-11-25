"""Prospective one-trial native MAF -> MCP -> metered ledger integration.

NOT authorised until independently pinned runtime and fixture registries
exist and the final runtime explicitly binds this runner's reviewed bytes.
No automatic approval, synthetic production credential, or override flag.

Shared integration function is exercised with actual SDK/protocol and
synthetic test responses only in pytest. No benchmark gold in this module.
"""
from __future__ import annotations

import argparse
import asyncio
import fcntl
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phenoassistant_mcp.client_v2 import McpV2Session
from phenoassistant_mcp.scientific_inference_v1 import (
    build_phase8_scientific_mcp_server, verify_trusted_runtime, file_sha256,
)
from research.phenoguard.pilot_manifest import build_development_validation_manifest
from research.phenoguard.contracts import ApplicabilityDecision as D
from scripts.research.phase8_condition_rehearsal import C3, C4, C8
from scripts.research.phase8_maf_decision_v1 import (
    Phase8MafDecisionClient, discover_real_mcp_tool,
)
from scripts.research.phase8_native_condition_mediation_v1 import mediate_one_native_condition
from scripts.research.phase8_image_fixture_registry import verify_trusted_fixture_registry
from scripts.research.phase8_scientific_artifact_validator import validate_scientific_mcp_artifact
from scripts.research.phase8_attempt_ledger import (
    MATRIX_SHA, DEFAULT_BUDGET, load_verified_controls, scientific_gate,
    next_trial_budget_gate, read_events, append_event, event_template, parse_money,
)
from scripts.research.phase8_provider_metering_v1 import summarize_trial_metering
from scripts.research.phase8_trial_metering_reconciliation_v1 import reconcile_metered_terminal
from scripts.research.prepare_phase8_qualification_matrix import model_visible_view, sha256_value
from scripts.research.verify_phenoguard_method_freeze import verify_manifest

EXECUTABLE = {D.EXECUTE, D.RESELECT}
RUN_ROOT = ROOT / "data/_staging/phase8_native_qualification_live_v0.1"


def write_new(path: Path, obj: dict) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(obj, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


async def execute_mediated_trial(*, client, condition, view, server, asset_id,
                                 asset, output_root, timeout_seconds, trace,
                                 after_mediation):
    """Shared native-MAF scientific dispatch path; caller owns approval gates.

    Tests supply a fake provider and fake inference delegate on real SDK/MCP.
    Production creates only real clients and the trusted real MCP server.
    No scoring labels or asset provenance are passed to Manager/Critic.
    """
    if condition not in (C3, C4, C8):
        raise ValueError("unknown condition")
    trace["stage"] = "DISCOVERY"
    schema = await discover_real_mcp_tool(server)
    trace["stage"] = "NATIVE_MEDIATION"
    obs = await mediate_one_native_condition(
        client=client, condition=condition, visible_view=view,
        discovered_tool=schema,
    )
    trace["mediation"] = asdict(obs)
    trace["scientific_dispatch_attempted"] = False
    trace["scientific_dispatch_completed"] = False
    trace["scientific_artifact_sha256"] = None
    trace["post_validation"] = None
    trace["stage"] = "PROVIDER_METERING"
    after_mediation()
    if obs.final_decision in EXECUTABLE:
        if obs.native_tool_calls_captured != 1 or not obs.final_selected_capability_id:
            raise ValueError("execution without genuine native proposal")
        trace["stage"] = "SCIENTIFIC_DISPATCH"
        trace["scientific_dispatch_attempted"] = True
        async with McpV2Session(server) as session:
            payload = await session.call_structured_tool(
                "run_scientific_model",
                {"capability_id": obs.final_selected_capability_id,
                 "image_asset_id": asset_id},
                timeout_seconds=timeout_seconds,
            )
        if (payload.get("tool_executed") is not True
            or payload.get("capability_id") != obs.final_selected_capability_id
            or payload.get("image_asset_id") != asset_id):
            raise ValueError("scientific dispatch identity mismatch")
        trace["scientific_dispatch_completed"] = True
        trace["scientific_artifact_sha256"] = payload["artifact_sha256"]
        if condition == C8:
            trace["stage"] = "POST_VALIDATION"
            result = validate_scientific_mcp_artifact(
                payload, bound_asset_id=asset_id, bound_asset=asset,
                output_root=output_root,
            )
            trace["post_validation"] = result.model_dump(mode="json")
    # A blocked output is not an infrastructure failure; it is a policy result.
    trace["stage"] = "COMPLETE"
    return trace


def read_live_controls(runtime, fixture):
    matrix, _ = load_verified_controls()
    count, method = verify_manifest()
    record = verify_trusted_runtime(runtime, file_sha256(runtime))
    scientific_gate(record)
    cfg = record.get("qualification_execution")
    if not isinstance(cfg, dict):
        raise ValueError("reviewed runtime lacks integrated qualification controls")
    expected = {
        "matrix_sha256": MATRIX_SHA,
        "fixture_registry_sha256": file_sha256(fixture),
        "runner_sha256": file_sha256(Path(__file__)),
        "method_freeze_sha256": method,
    }
    if any(cfg.get(k) != v for k, v in expected.items()):
        raise ValueError("approved runtime does not bind actual execution inputs")
    if cfg.get("native_no_call_policy_reviewed") is not True or cfg.get("scientific_checkpoint_routing_reviewed") is not True:
        raise ValueError("native no-call and checkpoint routing require explicit review")
    if cfg.get("external_key_spend_cap_verified") is not True:
        raise ValueError("no verified upstream hard spend cap")
    budget = parse_money(cfg.get("budget_usd"), allow_zero=False)
    reserve = parse_money(cfg.get("per_trial_worst_case_reserve_usd"), allow_zero=False)
    if budget > DEFAULT_BUDGET or reserve > budget:
        raise ValueError("unapproved spending bounds")
    timeout = cfg.get("scientific_tool_timeout_seconds")
    if type(timeout) is not int or not 1 <= timeout <= 3600:
        raise ValueError("scientific tool timeout not reviewed/bounded")
    assets = verify_trusted_fixture_registry(file=fixture, trusted_root=ROOT / "data")
    entries = json.loads(fixture.read_text(encoding="utf-8"))["entries"]
    bindings = {r["scenario_id_internal_only"]: r["image_asset_id_internal_only"] for r in entries}
    return matrix, record, assets, bindings, budget, reserve, timeout


async def run_next(runtime, fixture):
    # Both independently pinned approvals are checked BEFORE credentials,
    # client construction, ledger creation or any scientific inference.
    matrix, record, assets, bindings, budget, reserve, timeout = read_live_controls(runtime, fixture)
    if not os.environ.get("SLURM_JOB_ID"):
        raise ValueError("live execution requires a Slurm GPU allocation")
    import torch
    if not torch.cuda.is_available():
        raise ValueError("CUDA unavailable")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("approved provider credential unavailable")
    if RUN_ROOT.is_symlink():
        raise ValueError("unsafe run directory")
    RUN_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    lease = os.open(RUN_ROOT / "run.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ledger = RUN_ROOT / "attempts.jsonl"
        if ledger.exists():
            with ledger.open(encoding="utf-8") as stream:
                events = read_events(stream)
        else:
            events = []
        next_trial_budget_gate(matrix=matrix, candidate=record, events=events,
                               budget_usd=budget, next_call_reserve_usd=reserve)
        prior = {e["trial_id"] for e in events if e["event"] == "STARTED"}
        trial = next(t for t in matrix["trials"] if t["trial_id"] not in prior)
        ident = trial["trial_id"]
        scenario_id = trial["scenario_id_internal_only"]
        scenarios = {s.scenario_id: s for s in build_development_validation_manifest()}
        view = model_visible_view(scenarios[scenario_id])
        if sha256_value(view) != trial["model_visible_view_sha256"]:
            raise ValueError("frozen visible-request hash mismatch")
        asset_id = bindings[scenario_id]
        asset = assets[asset_id]
        directory = RUN_ROOT / ident
        directory.mkdir(mode=0o700, exist_ok=False)
        receipts = directory / "provider_receipts.jsonl"
        output_root = RUN_ROOT / "scientific_outputs"
        trace = {"trial_id": ident, "condition": trial["condition_id"],
                 "seed": trial["seed"], "view_sha256": sha256_value(view),
                 "stage": "STARTED", "scientific_dispatch_attempted": False,
                 "scientific_dispatch_completed": False, "post_validation": None}
        append_event(ledger, event_template(trial, model=matrix["model"], kind="STARTED"), matrix)
        start = time.monotonic()
        failure = None
        client = None
        try:
            trace["stage"] = "CLIENT_SETUP"
            server = build_phase8_scientific_mcp_server(
                approved_runtime_file=runtime,
                approved_runtime_sha256=file_sha256(runtime),
                frozen_trial_id=ident, trusted_images={asset_id: asset},
                output_root=output_root,
            )
            client = Phase8MafDecisionClient.create(
                approved_runtime_path=runtime,
                approved_runtime_sha256=file_sha256(runtime), api_key=key,
                seed=trial["seed"], metering_ledger_path=receipts,
                metering_trial_id=ident,
            )
            def check_metering():
                usage = summarize_trial_metering(receipts, trial_id=ident, model=matrix["model"])
                if parse_money(usage["provider_cost_usd"]) > reserve:
                    raise ValueError("observed provider cost exceeded reviewed trial reserve")
            await execute_mediated_trial(
                client=client, condition=trial["condition_id"], view=view,
                server=server, asset_id=asset_id, asset=asset,
                output_root=output_root, timeout_seconds=timeout,
                trace=trace, after_mediation=check_metering,
            )
        except Exception as exc:
            trace["error_type"] = type(exc).__name__
            failure = {
                "SCIENTIFIC_DISPATCH": "TOOL_ERROR",
                "POST_VALIDATION": "POLICY_ERROR",
                "NATIVE_MEDIATION": "MODEL_ERROR",
                "PROVIDER_METERING": "POLICY_ERROR",
            }.get(trace["stage"], "TRACE_INVALID")
        finally:
            if client is not None:
                try:
                    await client.close()
                except Exception as exc:
                    trace["client_close_error_type"] = type(exc).__name__
                    failure = failure or "TRANSPORT_ERROR"
        trace["elapsed_seconds"] = time.monotonic() - start
        trace["failure_code"] = failure
        trace_path = directory / "trace.json"
        write_new(trace_path, trace)
        try:
            summary = summarize_trial_metering(receipts, trial_id=ident, model=matrix["model"])
            terminal = event_template(trial, model=matrix["model"], kind="FAILED" if failure else "SUCCEEDED")
            terminal.update(usage=summary["usage"],
                            provider_cost_usd=summary["provider_cost_usd"],
                            attempt_trace_sha256=file_sha256(trace_path), failure_code=failure)
            receipt = reconcile_metered_terminal(matrix=matrix, terminal_event=terminal,
                                                 provider_ledger_path=receipts)
            write_new(directory / "reconciliation.json", receipt)
        except Exception:
            terminal = event_template(trial, model=matrix["model"], kind="METERING_MISSING")
            terminal.update(failure_code="METERING_MISSING", attempt_trace_sha256=file_sha256(trace_path))
        total = append_event(ledger, terminal, matrix)
        print(json.dumps({"trial_id": ident, "terminal": terminal["event"],
                          "total_provider_cost_usd": str(total), "stage": trace["stage"],
                          "registered_trials_started": len(prior) + 1}, sort_keys=True))
        return 0 if terminal["event"] == "SUCCEEDED" else 2
    finally:
        os.close(lease)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    return asyncio.run(run_next(args.runtime, args.fixture))


if __name__ == "__main__":
    raise SystemExit(main())
