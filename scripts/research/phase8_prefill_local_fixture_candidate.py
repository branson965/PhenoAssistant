"""Prepare a PRIVATE partial Phase 8 fixture candidate from local metadata.

Reads the actual AraCrop and potato metadata, chooses distinct real input
images, reuses the exact same image for missing-species paired cases,
hashes/validates images, and writes a separate candidate JSON under the
ignored data/_staging directory.

Never supplies independent species review, licence/access evidence, or
reviewer IDs. Maize slots remain empty until legitimate source images
are selected. No provider/GPU/hidden-label use or runtime approval.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.phase8_image_fixture_registry import (
    DEFAULT_TEMPLATE,
    SCHEMA,
    fixture_template,
)
from phenoassistant_mcp.scientific_inference_v1 import file_sha256

CANDIDATE = ROOT / "data/_staging/phase8_image_fixture_candidate_v0.1.json"
ARA_META = ROOT / "data/aracrop_metadata.json"
POTATO_META = ROOT / "data/potato_metadata.csv"
DATA_ROOT = ROOT / "data"


def checked_local_image(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("metadata image path is not a safe relative path")
    original = ROOT / path
    if original.is_symlink() or not original.is_file():
        raise ValueError("source image missing or symbolic link")
    resolved = original.resolve(strict=True)
    if not resolved.is_relative_to(DATA_ROOT.resolve(strict=True)):
        raise ValueError("source image escapes data root")
    if not 0 < resolved.stat().st_size <= 64 * 1024 * 1024:
        raise ValueError("source image outside approved size bounds")
    from PIL import Image
    with Image.open(resolved) as image:
        image.verify()
    return resolved


def source_entry(raw: str, dataset: str) -> dict[str, str]:
    path = checked_local_image(raw)
    digest = file_sha256(path)
    return {
        "image_asset_id_internal_only": "local_" + digest[:24],
        "image_path_internal_only": str(path),
        "image_sha256": digest,
        "source_dataset": dataset,
        "source_image_id": raw,
    }


def load_sources() -> dict[str, dict[str, str]]:
    ara = json.loads(ARA_META.read_text(encoding="utf-8"))
    ara_images = ara.get("file_name")
    if not isinstance(ara_images, list):
        raise ValueError("AraCrop metadata lacks file_name list")
    by_plant: dict[str, str] = {}
    for raw in ara_images:
        if not isinstance(raw, str):
            raise ValueError("invalid AraCrop image reference")
        parent = Path(raw).parent.name
        if parent not in by_plant:
            by_plant[parent] = raw
    if len(by_plant) < 3:
        raise ValueError("need three distinct AraCrop plants")
    ara_selected = list(by_plant.values())[:3]

    with POTATO_META.open("r", encoding="utf-8-sig", newline="") as stream:
        potato_images = [
            row["file_name"] for row in csv.DictReader(stream)
            if row.get("file_name")
        ]
    potato_images = list(dict.fromkeys(potato_images))
    known_smoke = "./data/PotatoLeaf/IMG_8064.JPG"
    if known_smoke not in potato_images:
        raise ValueError("potato smoke image absent from original metadata")
    potato_other = [x for x in potato_images if x != known_smoke]
    if len(potato_other) < 3:
        raise ValueError("need three more distinct potato metadata images")
    potato_selected = [
        potato_other[0], known_smoke, potato_other[1], potato_other[2]
    ]

    selected = {
        "dev-p001-valid-arabidopsis": ("ara", ara_selected[0]),
        "dev-p001-species-potato": ("potato", potato_selected[0]),
        "dev-p002-valid-arabidopsis": ("ara", ara_selected[1]),
        "dev-p002-missing-species": ("ara", ara_selected[1]),
        "dev-p003-valid-potato": ("potato", potato_selected[1]),
        "val-p001-valid-potato": ("potato", potato_selected[2]),
        "val-p001-species-arabidopsis": ("ara", ara_selected[2]),
        "val-p002-valid-potato": ("potato", potato_selected[3]),
        "val-p002-missing-species": ("potato", potato_selected[3]),
    }
    names = {
        "ara": "Local PhenoAssistant AraCrop metadata: data/aracrop_metadata.json",
        "potato": "Local PhenoAssistant potato metadata: data/potato_metadata.csv",
    }
    return {
        scenario_id: source_entry(raw, names[dataset])
        for scenario_id, (dataset, raw) in selected.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-candidate", action="store_true")
    args = parser.parse_args()
    if CANDIDATE.exists() or CANDIDATE.is_symlink():
        raise FileExistsError("private candidate already exists: refuse overwrite")
    if not DEFAULT_TEMPLATE.is_file() or DEFAULT_TEMPLATE.is_symlink():
        raise ValueError("private source template missing or unsafe")
    template = fixture_template()
    source = json.loads(DEFAULT_TEMPLATE.read_text(encoding="utf-8"))
    if source != template:
        raise ValueError("private source template was modified; refuse automated prefill")
    if source.get("schema") != SCHEMA:
        raise ValueError("fixture schema drift")
    bound = load_sources()
    rows = source["entries"]
    if len(rows) != 12:
        raise ValueError("frozen 12-case count changed")
    for row in rows:
        proposal = bound.get(row["scenario_id_internal_only"])
        if proposal is not None:
            row.update(proposal)
    counts = {
        "entries": len(rows),
        "image_and_source_fields_prefilled": len(bound),
        "maize_slots_unbound": len(rows) - len(bound),
        "independent_species_reviews": 0,
        "license_or_access_reviews": 0,
        "reviewer_evidence_ids": 0,
        "approved_for_scientific_execution": False,
        "provider_calls": 0,
        "gpu_calls": 0,
    }
    if args.write_candidate:
        CANDIDATE.parent.mkdir(parents=True, exist_ok=True)
        CANDIDATE.write_text(
            json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )
        print("PRIVATE_CANDIDATE_WRITTEN=true")
        print("PRIVATE_CANDIDATE_SHA256=" + file_sha256(CANDIDATE))
        print("PRIVATE_CANDIDATE_PATH=data/_staging/phase8_image_fixture_candidate_v0.1.json")
    else:
        print("PRIVATE_CANDIDATE_WRITTEN=false")
    print("PREFILL_STATUS=" + json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
