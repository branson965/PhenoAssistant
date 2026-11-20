"""Fail-closed, append-only per-call OpenRouter metering for Phase 8.

Captures provider-reported usage.cost from raw non-streaming responses, not a
price estimate. One ledger path is dedicated to one frozen trial; no prompts,
responses, credentials, or gold labels are persisted. Every record is linked
to its predecessor by SHA-256. A missing charge/transport failure poisons
the transport and prevents subsequent provider calls in that session.

This is evidence infrastructure ONLY. It does not approve live provider
access, impose a hard upstream spending cap, or perform scientific inference.
"""

from __future__ import annotations

import asyncio
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx

SCHEMA = "phase8-provider-call-v0.1"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:-]{1,256}$")
EVENT_KEYS = frozenset((
    "schema", "trial_id", "sequence", "recorded_utc", "model",
    "event", "failure_code", "http_status", "provider_response_id",
    "response_sha256", "usage", "provider_cost_usd",
    "previous_entry_sha256", "entry_sha256",
))


class Phase8MeteringError(ValueError):
    """No reliable provider charge, or corrupt/unsafe evidence ledger."""


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _digest(obj: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(obj)).hexdigest()


def _money(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise Phase8MeteringError("provider charge is not a numeric amount")
    try:
        amount = Decimal(str(value))
    except (ValueError, InvalidOperation) as exc:
        raise Phase8MeteringError("invalid provider charge") from exc
    if not amount.is_finite() or amount < 0:
        raise Phase8MeteringError("provider charge must be finite and non-negative")
    return amount


def _tokens(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise Phase8MeteringError("missing or invalid provider token count")
    return value


def extract_provider_metering(response_body: bytes, *, expected_model: str) -> dict:
    """Read *raw* OpenRouter usage.cost, not MAF token estimates."""
    if len(response_body) > MAX_RESPONSE_BYTES:
        raise Phase8MeteringError("provider response exceeds size limit")
    try:
        reply = json.loads(response_body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise Phase8MeteringError("invalid provider response JSON") from exc
    if not isinstance(reply, dict) or reply.get("object") != "chat.completion":
        raise Phase8MeteringError("unexpected response envelope")
    if reply.get("model") != expected_model:
        raise Phase8MeteringError("provider model identity drift")
    response_id = reply.get("id")
    if not isinstance(response_id, str) or not IDENTIFIER.fullmatch(response_id):
        raise Phase8MeteringError("missing or invalid generation identifier")
    usage = reply.get("usage")
    if not isinstance(usage, dict):
        raise Phase8MeteringError("provider usage object missing")
    prompt = _tokens(usage.get("prompt_tokens"))
    completion = _tokens(usage.get("completion_tokens"))
    total = _tokens(usage.get("total_tokens"))
    if total != prompt + completion:
        raise Phase8MeteringError("provider total token count mismatch")
    if "cost" not in usage or usage["cost"] is None:
        raise Phase8MeteringError("provider-billed usage.cost missing")
    cost = _money(usage["cost"])
    return {
        "provider_response_id": response_id,
        "usage": {
            "input_tokens": prompt,
            "output_tokens": completion,
            "total_tokens": total,
        },
        "provider_cost_usd": format(cost, "f"),
        "response_sha256": hashlib.sha256(response_body).hexdigest(),
    }


def read_verified_metering(ledger_path: Path, *, trial_id: str, model: str) -> list[dict]:
    """Verify the entire persisted prefix, including chained entry hashes."""
    if not ledger_path.exists():
        return []
    with ledger_path.open("r", encoding="utf-8") as handle:
        return _read_locked(handle, trial_id=trial_id, model=model)


def _read_locked(handle: Any, *, trial_id: str, model: str) -> list[dict]:
    handle.seek(0)
    events = []
    previous = None
    for line in handle:
        if not line.strip():
            raise Phase8MeteringError("blank line in metering ledger")
        try:
            entry = json.loads(line)
        except (ValueError, TypeError) as exc:
            raise Phase8MeteringError("invalid JSONL metering event") from exc
        if not isinstance(entry, dict) or set(entry) != EVENT_KEYS:
            raise Phase8MeteringError("metering event schema drift")
        if entry["schema"] != SCHEMA or entry["trial_id"] != trial_id or entry["model"] != model:
            raise Phase8MeteringError("metering trial/model identity drift")
        if entry["sequence"] != len(events) + 1 or type(entry["sequence"]) is not int:
            raise Phase8MeteringError("missing, duplicated or reordered call evidence")
        if entry["previous_entry_sha256"] != previous:
            raise Phase8MeteringError("broken metering hash chain")
        if not isinstance(entry["recorded_utc"], str) or not entry["recorded_utc"].endswith("+00:00"):
            raise Phase8MeteringError("invalid metering UTC timestamp")
        digest = entry["entry_sha256"]
        unsigned = {k: v for k, v in entry.items() if k != "entry_sha256"}
        if not isinstance(digest, str) or not HEX64.fullmatch(digest) or _digest(unsigned) != digest:
            raise Phase8MeteringError("metering record was modified")
        if entry["event"] == "METERED":
            if entry["failure_code"] is not None or entry["http_status"] != 200:
                raise Phase8MeteringError("invalid successful metering event")
            _validate_measured_entry(entry)
            if any(
                old["provider_response_id"] == entry["provider_response_id"]
                for old in events if old["event"] == "METERED"
            ):
                raise Phase8MeteringError("duplicate provider generation ID")
        elif entry["event"] == "METERING_MISSING":
            if entry["failure_code"] not in {
                "TRANSPORT_ERROR", "HTTP_ERROR", "INVALID_USAGE"
            }:
                raise Phase8MeteringError("invalid missing-metering failure reason")
            if entry["usage"] is not None or entry["provider_cost_usd"] is not None:
                raise Phase8MeteringError("missing metering event must not invent charges")
        else:
            raise Phase8MeteringError("unknown metering event")
        events.append(entry)
        previous = digest
    return events


def _validate_measured_entry(entry: dict) -> None:
    response_id = entry["provider_response_id"]
    if not isinstance(response_id, str) or not IDENTIFIER.fullmatch(response_id):
        raise Phase8MeteringError("invalid persisted generation identifier")
    if not isinstance(entry["response_sha256"], str) or not HEX64.fullmatch(entry["response_sha256"]):
        raise Phase8MeteringError("invalid response digest")
    usage = entry["usage"]
    if not isinstance(usage, dict) or set(usage) != {
        "input_tokens", "output_tokens", "total_tokens"
    }:
        raise Phase8MeteringError("invalid persisted usage")
    if _tokens(usage["input_tokens"]) + _tokens(usage["output_tokens"]) != _tokens(usage["total_tokens"]):
        raise Phase8MeteringError("invalid persisted token totals")
    if entry["provider_cost_usd"] is None:
        raise Phase8MeteringError("persisted provider charge missing")
    _money(entry["provider_cost_usd"])


def summarize_trial_metering(ledger_path: Path, *, trial_id: str, model: str) -> dict:
    """Only fully metered trial prefixes qualify for budget reconciliation."""
    events = read_verified_metering(ledger_path, trial_id=trial_id, model=model)
    if not events or any(item["event"] != "METERED" for item in events):
        raise Phase8MeteringError("trial has incomplete provider charge evidence")
    return {
        "call_count": len(events),
        "usage": {
            "input_tokens": sum(e["usage"]["input_tokens"] for e in events),
            "output_tokens": sum(e["usage"]["output_tokens"] for e in events),
        },
        "provider_cost_usd": format(
            sum((_money(e["provider_cost_usd"]) for e in events), Decimal("0")),
            "f",
        ),
        "last_entry_sha256": events[-1]["entry_sha256"],
    }


class Phase8ProviderMeteringTransport(httpx.AsyncBaseTransport):
    """Capture one raw response per actual HTTP attempt before the tool guard.

    Transport construction cannot grant any execution permission. Use behind
    the validated request rewrite and ahead of the raw tool-call guard.
    """

    def __init__(
        self, *, upstream: httpx.AsyncBaseTransport, expected_model: str,
        trial_id: str, ledger_path: Path,
    ) -> None:
        if not isinstance(trial_id, str) or not IDENTIFIER.fullmatch(trial_id):
            raise Phase8MeteringError("invalid metering trial identifier")
        self.upstream = upstream
        self.expected_model = expected_model
        self.trial_id = trial_id
        self.ledger_path = Path(ledger_path)
        self._lock = asyncio.Lock()
        self._poisoned = False
        self._sequence = 0

    def _append(self, *, event: str, failure_code: str | None,
                status: int | None, measurement: dict | None,
                response_sha256: str | None = None) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            self.ledger_path,
            os.O_CREAT | os.O_RDWR | os.O_APPEND,
            0o600,
        )
        with os.fdopen(fd, "a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                prior = _read_locked(
                    handle, trial_id=self.trial_id, model=self.expected_model,
                )
                if len(prior) != self._sequence or (
                    prior and prior[-1]["event"] == "METERING_MISSING"
                ):
                    raise Phase8MeteringError("ledger is stale or previous metering failed")
                entry = {
                    "schema": SCHEMA,
                    "trial_id": self.trial_id,
                    "sequence": self._sequence + 1,
                    "recorded_utc": datetime.now(timezone.utc).isoformat(),
                    "model": self.expected_model,
                    "event": event,
                    "failure_code": failure_code,
                    "http_status": status,
                    "provider_response_id": measurement["provider_response_id"] if measurement else None,
                    "response_sha256": measurement["response_sha256"] if measurement else response_sha256,
                    "usage": measurement["usage"] if measurement else None,
                    "provider_cost_usd": measurement["provider_cost_usd"] if measurement else None,
                    "previous_entry_sha256": prior[-1]["entry_sha256"] if prior else None,
                }
                entry["entry_sha256"] = _digest(entry)
                handle.seek(0, os.SEEK_END)
                handle.write(_canonical(entry).decode("utf-8") + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                self._sequence += 1
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _preflight_existing_ledger(self) -> None:
        if not self.ledger_path.exists():
            return
        with self.ledger_path.open("r", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                prior = _read_locked(
                    handle, trial_id=self.trial_id, model=self.expected_model,
                )
                if len(prior) != self._sequence or any(
                    event["event"] != "METERED" for event in prior
                ):
                    raise Phase8MeteringError(
                        "previous call evidence missing or ledger already used by another session"
                    )
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        async with self._lock:
            if self._poisoned:
                raise Phase8MeteringError("session blocked after missing metering")
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            # Separate nonblocking session lease rejects concurrent paid calls
            # against one ledger, even from independent Python processes.
            lease_path = self.ledger_path.with_suffix(self.ledger_path.suffix + ".lock")
            lease_fd = os.open(lease_path, os.O_CREAT | os.O_RDWR, 0o600)
            try:
                try:
                    fcntl.flock(lease_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise Phase8MeteringError("another provider call owns the trial ledger") from exc
                self._preflight_existing_ledger()
                return await self._request_under_lease(request)
            finally:
                os.close(lease_fd)

    async def _request_under_lease(self, request: httpx.Request) -> httpx.Response:
        try:
            response = await self.upstream.handle_async_request(request)
        except Exception as exc:
            self._poisoned = True
            self._append(
                event="METERING_MISSING", failure_code="TRANSPORT_ERROR",
                status=None, measurement=None,
            )
            raise Phase8MeteringError("provider transport failed; billing unknown") from exc
        payload = None
        try:
            if response.status_code != 200:
                raise Phase8MeteringError("non-200 response; charge cannot be verified")
            payload = await response.aread()
            measurement = extract_provider_metering(
                payload, expected_model=self.expected_model,
            )
        except Exception as exc:
            self._poisoned = True
            self._append(
                event="METERING_MISSING",
                failure_code="HTTP_ERROR" if response.status_code != 200 else "INVALID_USAGE",
                status=response.status_code, measurement=None,
                response_sha256=hashlib.sha256(payload).hexdigest() if payload is not None else None,
            )
            await response.aclose()
            raise Phase8MeteringError("provider metering unavailable; session blocked") from exc
        try:
            self._append(
                event="METERED", failure_code=None,
                status=200, measurement=measurement,
            )
        except Exception:
            self._poisoned = True
            # Preserve an unknown-charge receipt when validation rejected
            # an otherwise billed response (e.g. duplicate generation ID).
            try:
                self._append(
                    event="METERING_MISSING", failure_code="INVALID_USAGE",
                    status=200, measurement=None,
                    response_sha256=measurement["response_sha256"],
                )
            except Exception:
                # Persisted evidence may itself be corrupt or unwritable.
                # Never recover by making another provider request.
                pass
            await response.aclose()
            raise
        return response

    async def aclose(self) -> None:
        await self.upstream.aclose()
