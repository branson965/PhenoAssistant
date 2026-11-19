"""Offline Phase 8 attempt-evidence ledger and budget/approval gates.

This module makes NO model, MCP, network, or scientific calls. It prepares
future trial execution with append-only event records, fail-closed duplicate
attempt checks, and usage-based cost gating. The current pre-outcome runtime
candidate explicitly prohibits starting an experimental attempt.

An estimated token cost is NOT a provider-billed charge. Any missing
per-call billing evidence blocks the next attempt. The software gate alone
does not guarantee a hard upstream spend limit: set a provider key cap.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MATRIX = (
    ROOT / "experiments" / "ijcai2027" / "runtime"
    / "phase8_c3_c4_c8_qualification_matrix_v0.1.json"
)
CANDIDATE = (
    ROOT / "experiments" / "ijcai2027" / "runtime"
    / "runtime_controls_candidate_v0.3.json"
)
MATRIX_SHA = "8a9688aa464564bf99121656430ea09fc93bbf2b1d262a73a9b2276944876692"
CANDIDATE_SHA = "e3a8826b8942f2b0951775b557ce3530b2a54ed7666e827e3687443974718c12"
DEFAULT_BUDGET = Decimal("8.00")
VALID_END_STATES = {"SUCCEEDED", "FAILED", "METERING_MISSING"}


class LedgerGateError(ValueError):
    """An invalid or unapproved trial state."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_verified_controls() -> tuple[dict, dict]:
    if not MATRIX.is_file() or sha256_file(MATRIX) != MATRIX_SHA:
        raise LedgerGateError("matrix missing or hash differs from preserved Plato artifact")
    if not CANDIDATE.is_file() or sha256_file(CANDIDATE) != CANDIDATE_SHA:
        raise LedgerGateError("runtime candidate missing or unverified")
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    if matrix["trial_count"] != 108 or len(matrix["trials"]) != 108:
        raise LedgerGateError("qualification trial count drift")
    if matrix["scientific_execution_permitted"] is not False:
        raise LedgerGateError("planning matrix in unexpected execution state")
    if matrix["api_key_read"] is not False or matrix["outcome_bearing_work_performed"] is not False:
        raise LedgerGateError("planning matrix has unexpected runtime evidence")
    if candidate["phase7_freeze_aggregate_sha256"] != matrix["phase7_method_sha256"]:
        raise LedgerGateError("scientific method hash mismatch")
    return matrix, candidate


def scientific_gate(candidate: dict) -> None:
    """Reject all runs until an *independently verified* approved final freeze.

    This function intentionally has no bypass flag. A later prospective
    reviewed/committed runner version must attach an approved final runtime
    and full C3/C4/C8 harness-adoption evidence, without editing this v0.3
    historical candidate.
    """
    if candidate.get("scientific_execution_permitted") is not True:
        raise LedgerGateError("scientific execution prohibited by preserved runtime candidate")
    if candidate.get("approval", {}).get("researcher_attested_supervisor_provider_billing_and_models") is not True:
        raise LedgerGateError("provider/model/billing approval not attested")
    if candidate.get("http_transport_compatibility", {}).get("scientific_harness_adoption") != "VERIFIED":
        raise LedgerGateError("approved compatibility transport not verified in scientific harness")
    if candidate.get("status") != "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN":
        raise LedgerGateError("runtime is not the final approved freeze")


def parse_money(value: object, *, allow_zero: bool = True) -> Decimal:
    if isinstance(value, bool):
        raise LedgerGateError("money must not be boolean")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise LedgerGateError("unparseable money value") from None
    if not d.is_finite() or d < 0 or (not allow_zero and d <= 0):
        raise LedgerGateError("money value must be finite and non-negative")
    return d


def verify_events(events: list[dict], matrix: dict) -> Decimal:
    """Validate an append-only trial-event prefix; report proven billed spend.

    A terminal record must include explicit, non-negative token usage and
    provider billed cost. Missing charge evidence records METERING_MISSING,
    halting further starts rather than treating cost as zero.
    """
    known = {x["trial_id"]: x for x in matrix["trials"]}
    started: set[str] = set()
    ended: set[str] = set()
    active: set[str] = set()
    billed_total = Decimal("0")
    missing_metering = False
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise LedgerGateError("ledger event must be an object")
        if set(event) != {
            "schema", "trial_id", "event", "recorded_utc",
            "model", "condition_id", "seed", "usage", "provider_cost_usd",
            "attempt_trace_sha256", "failure_code",
        }:
            raise LedgerGateError("ledger event has unexpected or missing keys")
        if event["schema"] != "phase8-qualification-attempt-v0.1":
            raise LedgerGateError("unknown event schema")
        trial_id = event["trial_id"]
        if trial_id not in known:
            raise LedgerGateError("unregistered trial identifier")
        trial = known[trial_id]
        if event["condition_id"] != trial["condition_id"] or event["seed"] != trial["seed"]:
            raise LedgerGateError("condition/seed identity drift")
        if event["model"] != matrix["model"]:
            raise LedgerGateError("model identity drift")
        if not isinstance(event["recorded_utc"], str) or not event["recorded_utc"].endswith("+00:00"):
            raise LedgerGateError("non-UTC or invalid recorded time")
        kind = event["event"]
        if kind == "STARTED":
            if trial_id in started or trial_id in ended:
                raise LedgerGateError("duplicate or restarted trial")
            if active:
                raise LedgerGateError("concurrent trial starts are prohibited")
            if missing_metering:
                raise LedgerGateError("metering unavailable: further trials prohibited")
            if event["usage"] is not None or event["provider_cost_usd"] is not None:
                raise LedgerGateError("start event cannot pretend measured usage")
            if event["attempt_trace_sha256"] is not None or event["failure_code"] is not None:
                raise LedgerGateError("start event includes result fields")
            started.add(trial_id)
            active.add(trial_id)
        elif kind in VALID_END_STATES:
            if trial_id not in started or trial_id in ended or trial_id not in active:
                raise LedgerGateError("terminal event without unique start")
            usage = event["usage"]
            if kind == "METERING_MISSING":
                if usage is not None or event["provider_cost_usd"] is not None:
                    raise LedgerGateError("metering-missing event contains charge fields")
                missing_metering = True
            else:
                if not isinstance(usage, dict) or set(usage) != {"input_tokens", "output_tokens"}:
                    raise LedgerGateError("terminal event has no measured token usage")
                if any(type(usage[k]) is not int or usage[k] < 0 for k in usage):
                    raise LedgerGateError("token usage must be non-negative integers")
                if event["provider_cost_usd"] is None:
                    raise LedgerGateError("provider-billed charge evidence is required")
                billed_total += parse_money(event["provider_cost_usd"])
            trace = event["attempt_trace_sha256"]
            if kind == "SUCCEEDED":
                if not isinstance(trace, str) or len(trace) != 64 or any(c not in "0123456789abcdef" for c in trace):
                    raise LedgerGateError("successful attempt missing canonical trace hash")
                if event["failure_code"] is not None:
                    raise LedgerGateError("success cannot include failure code")
            else:
                if trace is not None and (not isinstance(trace, str) or len(trace) != 64):
                    raise LedgerGateError("invalid optional failure trace hash")
                if not isinstance(event["failure_code"], str) or event["failure_code"] not in {
                    "PROVIDER_ERROR", "MODEL_ERROR", "TOOL_ERROR", "POLICY_ERROR",
                    "METERING_MISSING", "TRANSPORT_ERROR", "TRACE_INVALID",
                }:
                    raise LedgerGateError("failure code is missing or unrecognized")
                if kind == "METERING_MISSING" and event["failure_code"] != kind:
                    raise LedgerGateError("metering failure code mismatch")
            ended.add(trial_id)
            active.remove(trial_id)
        else:
            raise LedgerGateError("unknown trial event type")
    return billed_total


def next_trial_budget_gate(
    *, matrix: dict, candidate: dict, events: list[dict],
    budget_usd: Decimal, next_call_reserve_usd: Decimal,
) -> Decimal:
    scientific_gate(candidate)
    spent = verify_events(events, matrix)
    if len({e["trial_id"] for e in events if e["event"] == "STARTED"}) >= matrix["trial_count"]:
        raise LedgerGateError("all trials already started")
    if any(e["event"] == "METERING_MISSING" for e in events):
        raise LedgerGateError("unknown provider charges: stop further model calls")
    if {e["trial_id"] for e in events if e["event"] == "STARTED"} - {e["trial_id"] for e in events if e["event"] in VALID_END_STATES}:
        raise LedgerGateError("previous trial still in flight: no concurrent paid calls")
    if next_call_reserve_usd <= 0:
        raise LedgerGateError("reserve must be strictly positive")
    if spent + next_call_reserve_usd > budget_usd:
        raise LedgerGateError("next-call reserve exceeds software spending ceiling")
    return budget_usd - spent


def read_events(handle) -> list[dict]:
    handle.seek(0)
    events = []
    for line in handle:
        if not line.strip():
            raise LedgerGateError("blank/corrupt ledger line")
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise LedgerGateError("corrupt ledger JSON") from exc
    return events


def append_event(
    ledger: Path, event: dict, matrix: dict,
) -> Decimal:
    """Atomic append-only state-machine operation with POSIX file lock.

    This records an event; it does NOT authorize execution by itself.
    The future actual runner must separately invoke next_trial_budget_gate
    before any model call, with the approved final runtime.
    """
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            events = read_events(handle)
            new_events = [*events, event]
            total = verify_events(new_events, matrix)
            handle.seek(0, os.SEEK_END)
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
            return total
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def event_template(trial: dict, *, model: str, kind: str) -> dict:
    """A safe template; do not include prompts, labels, keys, or response text."""
    return {
        "schema": "phase8-qualification-attempt-v0.1",
        "trial_id": trial["trial_id"],
        "event": kind,
        "recorded_utc": datetime.now(UTC).isoformat(),
        "model": model,
        "condition_id": trial["condition_id"],
        "seed": trial["seed"],
        "usage": None,
        "provider_cost_usd": None,
        "attempt_trace_sha256": None,
        "failure_code": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget-usd", default="8.00")
    args = parser.parse_args()
    try:
        matrix, candidate = load_verified_controls()
        budget = parse_money(args.budget_usd, allow_zero=False)
        if budget > DEFAULT_BUDGET:
            raise LedgerGateError("budget exceeds the frozen $8 pilot planning ceiling")
        trial_ids = [trial["trial_id"] for trial in matrix["trials"]]
        if len(trial_ids) != len(set(trial_ids)):
            raise LedgerGateError("duplicate trial IDs in matrix")
        authorized = True
        reason = ""
        try:
            scientific_gate(candidate)
        except LedgerGateError as exc:
            authorized = False
            reason = str(exc)
    except (OSError, ValueError, KeyError) as exc:
        print("PHASE8_LEDGER_PREFLIGHT_PASS=false")
        print("PHASE8_LEDGER_REASON=" + str(exc))
        return 2

    print("PHASE8_LEDGER_MATRIX_SHA256=" + MATRIX_SHA)
    print("PHASE8_LEDGER_REGISTERED_TRIALS=" + str(len(trial_ids)))
    print("PHASE8_LEDGER_BUDGET_CEILING_USD=" + str(budget))
    print("PHASE8_LEDGER_APPROVED_TO_RUN=" + str(authorized).lower())
    if not authorized:
        print("PHASE8_LEDGER_RUN_GATE_REASON=" + reason)
    print("PHASE8_LEDGER_NO_PROVIDER_CALLS=true")
    print("PHASE8_LEDGER_GOLD_LABELS_READ=false")
    print("PHASE8_LEDGER_OUTCOME_BEARING=false")
    print("PHASE8_LEDGER_PREFLIGHT_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
