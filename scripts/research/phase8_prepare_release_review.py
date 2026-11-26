"""Prepare a private prospective release review record; never approve a trial.

Default action records actual source/environment/fixture identities and the
remaining human decisions. --bind-reviewed transcribes completed human
worksheets into a new structurally validated registry CANDIDATE, not an
approval pin. No network/provider calls, no inference, no hidden gold.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata as md
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.phase8_attempt_ledger import load_verified_controls, MATRIX_SHA
from scripts.research.verify_phenoguard_method_freeze import verify_manifest
from scripts.research.phase8_image_fixture_registry import audit_fixtures
from scripts.research.phase8_prepare_private_review_worksheet import (
    IMAGE_CSV, SCENARIO_CSV, IMAGE_FIELDS, SCENARIO_FIELDS,
)
from scripts.research.phase8_prefill_local_fixture_candidate import CANDIDATE

STAGING = ROOT / "data/_staging"
PACKET = STAGING / "phase8_release_review_packet_v0.1.json"
REVIEWED = STAGING / "phase8_image_fixture_reviewed_candidate_v0.1.json"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_exclusive(path, obj):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
                   "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def read_rows(path, fields, key, count):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != fields:
            raise ValueError("review worksheet schema drift: " + path.name)
        rows = list(reader)
    if len(rows) != count or len({r[key] for r in rows}) != count:
        raise ValueError("review worksheet row count or identity drift: " + path.name)
    return {r[key]: r for r in rows}


def required(row, field):
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing human review field: " + field)
    return value.strip()


def bind_reviewed():
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    images = read_rows(IMAGE_CSV, IMAGE_FIELDS, "image_sha256", 9)
    cases = read_rows(SCENARIO_CSV, SCENARIO_FIELDS, "scenario_id", 12)
    for row in candidate["entries"]:
        case = cases[row["scenario_id_internal_only"]]
        image = images[row["image_sha256"]]
        if (case["image_sha256"] != row["image_sha256"]
                or case["source_image_id"] != row["source_image_id"]
                or image["source_image_id"] != row["source_image_id"]
                or image["source_dataset"] != row["source_dataset"]
                or image["image_path_private"] != row["image_path_internal_only"]
                or row["scenario_id_internal_only"] not in image["scenario_ids"].split(";")):
            raise ValueError("reviewed worksheet no longer matches original fixture binding")
        if required(case, "case_reviewer_decision") != "APPROVE":
            raise ValueError("case not explicitly approved by human reviewer")
        species = required(image, "reviewed_species_actual")
        if required(case, "reviewed_species_actual").casefold() != species.casefold():
            raise ValueError("image and scenario species reviews disagree")
        for field in ("image_view_and_acquisition", "source_rights_evidence",
                      "shift_confound_notes", "reviewer_evidence_id", "review_date_utc"):
            required(image, field)
        for field in ("shift_confound_notes", "reviewer_evidence_id", "review_date_utc"):
            required(case, field)
        row["reviewed_species"] = species
        row["license_or_access_evidence"] = required(case, "license_or_access_evidence")
        row["reviewer_evidence_id"] = required(case, "reviewer_evidence_id")
    audit_fixtures(candidate, trusted_root=ROOT / "data")
    write_exclusive(REVIEWED, candidate)
    print("REVIEWED_CANDIDATE_SHA256=" + sha(REVIEWED))
    print("REVIEWED_CANDIDATE=" + str(REVIEWED.relative_to(ROOT)))
    print("STRUCTURALLY_VALIDATED_CASES=12")
    print("INDEPENDENT_PIN_GRANTED=false")


def prepare_packet():
    matrix, historic = load_verified_controls()
    count, freeze = verify_manifest()
    git = lambda *args: subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("tracked source modifications must be reviewed first")
    paths = git("ls-files", "functions", "utils", "phenoassistant_maf",
                "phenoassistant_mcp", "research/phenoguard", "scripts/research",
                "scripts/gpu", "model_zoo.json", "experiments/ijcai2027").splitlines()
    source = {p: sha(ROOT / p) for p in paths
              if p.endswith((".py", ".json", ".lock", ".txt"))}
    packages = sorted({(d.metadata["Name"].lower().replace("_", "-"), d.version)
                       for d in md.distributions()})
    package_bytes = json.dumps(packages, separators=(",", ":")).encode("utf-8")
    if Path(sys.prefix).name != "phenoassistant-phase8-qualification":
        raise ValueError("use the combined qualification environment")
    packet = {
        "schema": "phase8-release-review-packet-v0.1",
        "status": "PROSPECTIVE_REVIEW_REQUIRED_NOT_APPROVED",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": git("rev-parse", "HEAD"),
        "source_sha256": source,
        "python_version": sys.version.split()[0],
        "installed_packages_name_version": packages,
        "installed_package_inventory_sha256": hashlib.sha256(package_bytes).hexdigest(),
        "method_freeze_file_count": count,
        "method_freeze_sha256": freeze,
        "matrix_sha256": MATRIX_SHA,
        "trial_count": matrix["trial_count"],
        "model": matrix["model"],
        "historical_runtime_status": historic["status"],
        "fixture_candidate_sha256": sha(CANDIDATE),
        "image_worksheet_sha256": sha(IMAGE_CSV),
        "scenario_worksheet_sha256": sha(SCENARIO_CSV),
        "contact_sheet_sha256": sha(STAGING / "phase8_private_fixture_contact_sheet.png"),
        "reviewed_fixture_candidate_sha256": sha(REVIEWED) if REVIEWED.is_file() else None,
        "proposed_qualification_controls": {
            "budget_usd": "8.00",
            "per_trial_worst_case_reserve_usd": None,
            "scientific_tool_timeout_seconds": 1200,
            "native_no_call_policy": "preserve Manager no-call in C8; no new dispatch without native proposal",
            "transport_retry_policy_actual_sdk_max_retries": 0,
            "historical_transport_retry_policy": historic["controls"]["retry_policy"],
            "provider": "OpenRouter->openai",
            "external_key_spend_cap_verified": False,
        },
        "review_requirements": [
            "Independent image/species/acquisition/source/rights and case review; inspect original files.",
            "Approve native no-call limitation and shared capability inventory.",
            "Approve actual model/provider and data-handling rules; verify dedicated credential spending limit.",
            "Review reserve against actual price/call bounds, timeout and zero automatic retry policy.",
            "Bind actual runtime source, package inventory, checkpoints and scorer in final reviewed runtime; pin reviewed runtime and fixture independently.",
        ],
        "scientific_execution_permitted": False,
        "independent_approval_granted": False,
    }
    write_exclusive(PACKET, packet)
    print("RELEASE_REVIEW_PACKET=" + str(PACKET.relative_to(ROOT)))
    print("RELEASE_REVIEW_PACKET_SHA256=" + sha(PACKET))
    print("SOURCE_COMMIT=" + packet["source_commit"])
    print("PACKAGE_INVENTORY_SHA256=" + packet["installed_package_inventory_sha256"])
    print("SCIENTIFIC_EXECUTION_PERMITTED=false")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind-reviewed", action="store_true")
    args = parser.parse_args()
    if args.bind_reviewed:
        bind_reviewed()
    else:
        prepare_packet()


if __name__ == "__main__":
    main()
