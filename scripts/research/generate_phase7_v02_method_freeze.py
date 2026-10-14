"""Generate the active Phase 7 v0.2 method-freeze manifest after Case 3 reopen.

This script deliberately preserves the exact 22-path scope of the archived v0.1
manifest. It changes only the manifest metadata and current content hashes. Run it
from a clean experiment-branch checkout after all authorised Case 3 provenance
changes are committed and before any outcome-bearing Phase 8 scientific run.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

ARCHIVED_V01 = (
    ROOT
    / "docs"
    / "research"
    / "IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST_V0.1.json"
)

ACTIVE_MANIFEST = (
    ROOT
    / "docs"
    / "research"
    / "IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST.json"
)

REOPEN_RECORD = (
    "docs/research/"
    "IJCAI_2027_PHASE7_REOPEN_CASE3_20261014.md"
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


def git_head() -> str:
    return subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        cwd=ROOT,
        text=True,
    ).strip()


def main() -> None:
    prior = json.loads(
        ARCHIVED_V01.read_text(
            encoding="utf-8",
        )
    )

    frozen_paths = tuple(
        sorted(
            prior["frozen_files"]
        )
    )

    if len(frozen_paths) != 22:
        raise RuntimeError(
            "v0.1 archive must contain exactly 22 frozen paths"
        )

    observed: dict[str, str] = {}

    for relative in frozen_paths:
        path = ROOT / relative

        if not path.is_file():
            raise FileNotFoundError(
                f"frozen path missing: {relative}"
            )

        observed[relative] = sha256_file(
            path
        )

    canonical = "".join(
        f"{path}\t{observed[path]}\n"
        for path in frozen_paths
    ).encode(
        "utf-8",
    )

    aggregate = hashlib.sha256(
        canonical
    ).hexdigest()

    changed_paths = [
        path
        for path in frozen_paths
        if observed[path]
        != prior["frozen_files"][path]
    ]

    expected_changed = {
        "docs/research/PHASE7_CATALOGUE_RESOLUTION.md",
        "model_zoo.json",
        "research/phenoguard/__init__.py",
        "research/phenoguard/provenance.py",
    }

    if set(changed_paths) != expected_changed:
        raise RuntimeError(
            "unexpected frozen-path delta from v0.1: "
            + json.dumps(
                changed_paths,
                sort_keys=True,
            )
        )

    payload = {
        "schema": (
            "phenoguard-ijcai2027-phase7-method-freeze-v0.2"
        ),
        "status": "FROZEN_PENDING_RUNTIME_VERIFICATION",
        "venue": "IJCAI 2027",
        "date": "2026-10-14",
        "hash_source_commit": git_head(),
        "aggregate_algorithm": (
            "sha256(sorted(path + TAB + sha256 + LF))"
        ),
        "aggregate_sha256": aggregate,
        "frozen_file_count": len(
            observed
        ),
        "frozen_files": observed,
        "reopen": {
            "reason": (
                "collaborator-backed Case 3 provenance correction "
                "before outcome-bearing IJCAI scientific runs"
            ),
            "record": REOPEN_RECORD,
            "prior_schema": prior["schema"],
            "prior_hash_source_commit": prior[
                "hash_source_commit"
            ],
            "prior_aggregate_sha256": prior[
                "aggregate_sha256"
            ],
            "changed_frozen_paths": changed_paths,
            "outcome_bearing_work_performed_before_reopen": False,
            "hidden_labels_inspected_before_reopen": False,
        },
        "freeze_rules": {
            "negative_results_retained": True,
            "hidden_labels_available_to_method": False,
            "post_unblinding_method_changes_authorized": False,
            "phase8_may_modify_frozen_files": False,
            "change_policy": (
                "Any scientific-method change requires an explicit "
                "Phase 7 reopen record, new manifest version, and "
                "re-verification before further outcome inspection."
            ),
        },
    }

    ACTIVE_MANIFEST.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "PHASE7_V02_HASH_SOURCE_COMMIT="
        + payload["hash_source_commit"]
    )
    print(
        "PHASE7_V02_FROZEN_FILE_COUNT="
        + str(
            payload["frozen_file_count"]
        )
    )
    print(
        "PHASE7_V02_CHANGED_FROZEN_PATHS="
        + json.dumps(
            changed_paths
        )
    )
    print(
        "PHASE7_V02_AGGREGATE_SHA256="
        + aggregate
    )
    print(
        "PHASE7_V02_MANIFEST_GENERATED=true"
    )


if __name__ == "__main__":
    main()
