"""Create two PRIVATE CSV review worksheets from a hash-verified fixture candidate.

The 9-image worksheet helps a real reviewer inspect distinct photos once.
The 12-case worksheet distinguishes per-scenario applicability and paired
controls. All reviewer, species-verification, licence and approval fields
remain BLANK. Creating these files never authorises Phase 8 trials.

No LLM/provider, GPU, network access, hidden gold or execution approval.
Files are created with owner-only permissions under ignored data/_staging.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image
from research.phenoguard.pilot_manifest import build_development_validation_manifest
from scripts.research.phase8_audit_private_fixture_candidate import (
    CANDIDATE, technical_audit,
)

OUT_DIR = ROOT / "data" / "_staging"
IMAGE_CSV = OUT_DIR / "phase8_private_image_review_9unique_v0.1.csv"
SCENARIO_CSV = OUT_DIR / "phase8_private_scenario_review_12cases_v0.1.csv"

IMAGE_FIELDS = [
    "image_sha256", "image_path_private", "source_dataset", "source_image_id",
    "image_width_px", "image_height_px", "scenario_ids",
    "reviewed_species_actual", "image_view_and_acquisition", "source_rights_evidence",
    "shift_confound_notes", "reviewer_evidence_id", "review_date_utc",
]
SCENARIO_FIELDS = [
    "scenario_id", "request_species_model_visible",
    "image_sha256", "source_image_id", "pair_id",
    "reviewed_species_actual", "license_or_access_evidence",
    "reviewer_evidence_id", "shift_confound_notes",
    "case_reviewer_decision", "review_date_utc",
]


def write_csv_exclusive(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def main() -> int:
    if any(p.exists() or p.is_symlink() for p in (IMAGE_CSV, SCENARIO_CSV)):
        raise FileExistsError("private review worksheet already exists; refusing overwrite")
    if not OUT_DIR.is_dir() or OUT_DIR.is_symlink():
        raise ValueError("private data staging directory missing or symlinked")
    report = technical_audit(CANDIDATE, ROOT / "data")
    if report["technical_image_bindings_checked"] != 12:
        raise ValueError("technical audit did not verify all 12 images")
    rows = json.loads(CANDIDATE.read_text(encoding="utf-8"))["entries"]
    fixtures = {row["scenario_id_internal_only"]: row for row in rows}
    unique: dict[str, dict[str, Any]] = {}
    scenarios = []
    for scenario in build_development_validation_manifest():
        row = fixtures[scenario.scenario_id]
        digest = row["image_sha256"]
        if digest not in unique:
            p = Path(row["image_path_internal_only"])
            with Image.open(p) as im:
                width, height = im.size
            unique[digest] = {
                "image_sha256": digest,
                "image_path_private": str(p),
                "source_dataset": row["source_dataset"],
                "source_image_id": row["source_image_id"],
                "image_width_px": width,
                "image_height_px": height,
                "scenario_ids": [],
                "reviewed_species_actual": "",
                "image_view_and_acquisition": "",
                "source_rights_evidence": "",
                "shift_confound_notes": "",
                "reviewer_evidence_id": "",
                "review_date_utc": "",
            }
        unique[digest]["scenario_ids"].append(scenario.scenario_id)
        scenarios.append({
            "scenario_id": scenario.scenario_id,
            "request_species_model_visible": scenario.request.species or "UNSPECIFIED",
            "image_sha256": digest,
            "source_image_id": row["source_image_id"],
            "pair_id": scenario.pair_id or "",
            "reviewed_species_actual": "",
            "license_or_access_evidence": "",
            "reviewer_evidence_id": "",
            "shift_confound_notes": "",
            "case_reviewer_decision": "",
            "review_date_utc": "",
        })
    if len(unique) != 9 or len(scenarios) != 12:
        raise ValueError("image uniqueness or frozen scenario count drift")
    for item in unique.values():
        item["scenario_ids"] = ";".join(item["scenario_ids"])
    write_csv_exclusive(IMAGE_CSV, IMAGE_FIELDS, list(unique.values()))
    write_csv_exclusive(SCENARIO_CSV, SCENARIO_FIELDS, scenarios)
    print("PHASE8_REVIEW_IMAGE_WORKSHEET=data/_staging/" + IMAGE_CSV.name)
    print("PHASE8_REVIEW_CASE_WORKSHEET=data/_staging/" + SCENARIO_CSV.name)
    print("PHASE8_REVIEW_DISTINCT_IMAGES=" + str(len(unique)))
    print("PHASE8_REVIEW_SCENARIOS=" + str(len(scenarios)))
    print("PHASE8_REVIEW_HUMAN_ATTESTATIONS_GENERATED=0")
    print("PHASE8_REVIEW_INDEPENDENT_APPROVAL_GRANTED=false")
    print("PHASE8_REVIEW_SCIENTIFIC_TRIALS_EXECUTED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
