"""Offline reconciliation of provider-call receipts with a Phase 8 trial terminal.

Read-only: checks that the existing append-only attempt event's declared
tokens and billed cost exactly match the complete, hash-verified per-call
provider ledger. This does NOT authorize an experimental trial, perform
provider/network/scientific calls, or independently verify provider invoices.

Call only after all provider calls have stopped. The provider session lease
is acquired non-blockingly while reading, preventing an in-flight request
from racing the reconciliation snapshot.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from scripts.research.phase8_attempt_ledger import (
    LedgerGateError, event_template, parse_money, sha256_file, verify_events,
)
from scripts.research.phase8_provider_metering_v1 import (
    Phase8MeteringError, summarize_trial_metering,
)


class Phase8TrialReconciliationError(ValueError):
    """Attempt and provider-call evidence disagree, or cannot be verified."""


def _canonical_sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def reconcile_metered_terminal(
    *, matrix: dict, terminal_event: dict,
    provider_ledger_path: Path,
) -> dict[str, Any]:
    """Return a privacy-minimized matching receipt, never alter either ledger.

    A locally matching receipt is NOT proof of independent provider billing.
    In particular, it cannot mark any scientific execution as approved.
    """
    if not isinstance(terminal_event, dict):
        raise Phase8TrialReconciliationError("terminal attempt is not an object")
    if terminal_event.get("event") not in ("SUCCEEDED", "FAILED"):
        raise Phase8TrialReconciliationError("only metered trial terminal events can reconcile")
    trial_id = terminal_event.get("trial_id")
    model = terminal_event.get("model")
    if not isinstance(trial_id, str) or not isinstance(model, str):
        raise Phase8TrialReconciliationError("missing trial or model identity")
    trials = {
        trial["trial_id"]: trial for trial in matrix["trials"]
    }
    trial = trials.get(trial_id)
    if trial is None or model != matrix["model"]:
        raise Phase8TrialReconciliationError("unregistered trial or model")

    # Reuse the original attempt-ledger state machine to validate terminal
    # schema and identity. The synthetic STARTED object here is NOT written,
    # and is NOT evidence that a real trial was started or authorised.
    synthetic_start = event_template(trial, model=model, kind="STARTED")
    try:
        verify_events([synthetic_start, terminal_event], matrix)
    except (LedgerGateError, KeyError, TypeError) as exc:
        raise Phase8TrialReconciliationError("invalid attempt terminal") from exc

    path = Path(provider_ledger_path)
    if not path.is_file():
        raise Phase8TrialReconciliationError("provider per-call ledger is missing")
    lease = path.with_suffix(path.suffix + ".lock")
    lease_fd = os.open(lease, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(lease_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Phase8TrialReconciliationError(
                "provider call still in flight; cannot reconcile"
            ) from exc
        try:
            summary = summarize_trial_metering(
                path, trial_id=trial_id, model=model,
            )
            ledger_sha256 = sha256_file(path)
        except (Phase8MeteringError, OSError) as exc:
            raise Phase8TrialReconciliationError(
                "unverified or incomplete provider call receipts"
            ) from exc

        expected_usage = summary["usage"]
        declared_usage = terminal_event["usage"]
        if not isinstance(declared_usage, dict) or set(declared_usage) != {
            "input_tokens", "output_tokens"
        } or any(
            type(declared_usage[key]) is not int
            or declared_usage[key] != expected_usage[key]
            for key in expected_usage
        ):
            raise Phase8TrialReconciliationError(
                "terminal token totals do not match raw provider receipts"
            )
        try:
            declared_cost = parse_money(terminal_event["provider_cost_usd"])
        except LedgerGateError as exc:
            raise Phase8TrialReconciliationError("invalid terminal billed charge") from exc
        if declared_cost != Decimal(summary["provider_cost_usd"]):
            raise Phase8TrialReconciliationError(
                "terminal billed charge does not match raw provider receipts"
            )
        return {
            "schema": "phase8-trial-metering-reconciliation-v0.1",
            "trial_id": trial_id,
            "model": model,
            "terminal_event_sha256": _canonical_sha256(terminal_event),
            "provider_ledger_sha256": ledger_sha256,
            "last_provider_entry_sha256": summary["last_entry_sha256"],
            "provider_call_count": summary["call_count"],
            "provider_usage": expected_usage,
            "provider_cost_usd": summary["provider_cost_usd"],
            "locally_reconciled": True,
            "independent_provider_billing_reconciled": False,
            "scientific_execution_approved": False,
        }
    finally:
        os.close(lease_fd)
