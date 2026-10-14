"""Verify the captured Phase 8A pre-outcome runtime-control candidate.

This verifier is intentionally content-addressed to the first Plato candidate captured
after the Phase 7 v0.2 Case 3 provenance correction. It performs no network call,
reads no API key, and executes no scientific benchmark.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RUNTIME_DIR = (
    ROOT
    / "experiments"
    / "ijcai2027"
    / "runtime"
)

CANDIDATE = (
    RUNTIME_DIR
    / "runtime_controls_candidate.json"
)

PACKAGE_LOCK = (
    RUNTIME_DIR
    / "requirements_phase8_pilot.lock"
)

EXPECTED_CANDIDATE_SHA256 = (
    "85acd6efd5ae880051548977355f05d6bdd5e048c365a945a512378023355ce1"
)

EXPECTED_PACKAGE_LOCK_SHA256 = (
    "2c67b0b895b81a482c148512ee5ab0de23e333bd21a4d44c31061e2fb19a6391"
)

EXPECTED_PHASE7_AGGREGATE = (
    "25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294"
)

EXPECTED_PHASE7_CLOSURE_BRANCH = (
    "baseline/phenoguard-method-freeze-v0.2-20261014"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def main() -> None:
    if not CANDIDATE.is_file():
        raise SystemExit(
            "runtime-controls candidate is missing"
        )

    if not PACKAGE_LOCK.is_file():
        raise SystemExit(
            "Phase 8 package lock is missing"
        )

    candidate_sha = sha256_file(
        CANDIDATE
    )

    package_lock_sha = sha256_file(
        PACKAGE_LOCK
    )

    if candidate_sha != EXPECTED_CANDIDATE_SHA256:
        raise SystemExit(
            "runtime-controls candidate hash mismatch: "
            + candidate_sha
        )

    if package_lock_sha != EXPECTED_PACKAGE_LOCK_SHA256:
        raise SystemExit(
            "Phase 8 package-lock hash mismatch: "
            + package_lock_sha
        )

    payload = json.loads(
        CANDIDATE.read_text(
            encoding="utf-8",
        )
    )

    if payload["status"] != (
        "CANDIDATE_PRE_OUTCOME_PENDING_SUPERVISOR_CONFIRMATION"
    ):
        raise SystemExit(
            "runtime candidate has unexpected status"
        )

    if (
        payload["phase7_freeze_aggregate_sha256"]
        != EXPECTED_PHASE7_AGGREGATE
    ):
        raise SystemExit(
            "runtime candidate references the wrong Phase 7 freeze"
        )

    if (
        payload["phase7_closure_branch"]
        != EXPECTED_PHASE7_CLOSURE_BRANCH
    ):
        raise SystemExit(
            "runtime candidate references the wrong Phase 7 closure branch"
        )

    if payload["api_key_read"] is not False:
        raise SystemExit(
            "runtime candidate unexpectedly records API-key access"
        )

    if payload["outcome_bearing_work_performed"] is not False:
        raise SystemExit(
            "runtime candidate unexpectedly records outcome-bearing work"
        )

    if (
        payload["controls"]["package_lock_sha256"]
        != EXPECTED_PACKAGE_LOCK_SHA256
    ):
        raise SystemExit(
            "runtime candidate package-lock identity is inconsistent"
        )

    print(
        "PHASE8A_CANDIDATE_SHA256="
        + candidate_sha
    )

    print(
        "PHASE8A_PACKAGE_LOCK_SHA256="
        + package_lock_sha
    )

    print(
        "PHASE8A_PHASE7_AGGREGATE="
        + payload["phase7_freeze_aggregate_sha256"]
    )

    print(
        "PHASE8A_PHASE7_CLOSURE_BRANCH="
        + payload["phase7_closure_branch"]
    )

    print(
        "PHASE8A_CANDIDATE_STATUS="
        + payload["status"]
    )

    print(
        "PHASE8A_CANDIDATE_API_KEY_READ="
        + str(
            payload["api_key_read"]
        ).lower()
    )

    print(
        "PHASE8A_CANDIDATE_OUTCOME_BEARING="
        + str(
            payload["outcome_bearing_work_performed"]
        ).lower()
    )

    print(
        "PHASE8A_RUNTIME_CANDIDATE_VERIFY_PASS=true"
    )


if __name__ == "__main__":
    main()
