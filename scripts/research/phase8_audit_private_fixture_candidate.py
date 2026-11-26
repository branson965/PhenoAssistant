"""Read-only pre-review audit of the PRIVATE 12-case fixture candidate.

Checks every bound image's real bytes, pinned SHA-256, allowlisted metadata
membership, PlantDoc repository revision, view hashes, and controlled
same-image pairs. This is a *technical* audit only.

No hidden labels, evaluator outcomes, provider/network/GPU calls, dataset
downloads, registry mutation, reviewer impersonation, or runtime approval.
Prints no private image paths or source IDs.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phenoassistant_mcp.scientific_inference_v1 import file_sha256
from scripts.research.phase8_image_fixture_registry import (
    FIELDS, _checked_path, fixture_template,
)

CANDIDATE = ROOT / "data/_staging/phase8_image_fixture_candidate_v0.1.json"
ARA = ROOT / "data/aracrop_metadata.json"
POTATO = ROOT / "data/potato_metadata.csv"
MAIZE_ROOT = ROOT / "data/_staging/PlantDoc-Dataset"
PLANTDOC_PREFIX = "Original PlantDoc-Dataset, https://github.com/pratikkayal/PlantDoc-Dataset @ "

WHOLEPLANT_ROOT = ROOT / "data/_staging/maize_wholeplant_1002675_v3"
WHOLEPLANT_SOURCE = "Brichet and Cabrera-Bosquet (2017), Maize whole plant image dataset, doi:10.5281/zenodo.1002675; original ZIP member in acquisition_receipt.json"
WHOLEPLANT_SELECTION = {
    "dev-p003-species-maize": ("candidate_02_656bc5cd79267679.png", "656bc5cd79267679b6ac144765d0de49ca856934dbdd0cefa0ebc06db86b488d", "6619", "7f9f77eb"),
    "dev-training-ready": ("candidate_03_04df2d7f96e36e92.png", "04df2d7f96e36e922af176e44aba667d1e421c1fd84edeb3627646446033a206", "6652", "ccaa0bdc"),
    "dev-training-missing-data": ("candidate_03_04df2d7f96e36e92.png", "04df2d7f96e36e922af176e44aba667d1e421c1fd84edeb3627646446033a206", "6652", "ccaa0bdc"),
}


def verify_wholeplant(ident, path, digest):
    import zlib
    from PIL import Image
    name, expected_sha, task, crc = WHOLEPLANT_SELECTION[ident]
    if path != WHOLEPLANT_ROOT.resolve(strict=True) / name or digest != expected_sha:
        raise ValueError("whole-plant selected fixture identity differs")
    receipt = json.loads((WHOLEPLANT_ROOT / "acquisition_receipt.json").read_text())
    record = json.loads((WHOLEPLANT_ROOT / "zenodo_record.json").read_text())
    meta = record["metadata"]
    license_id = meta["license"]
    if isinstance(license_id, dict):
        license_id = license_id["id"]
    if (str(record["id"]) != "1002675" or meta["doi"] != "10.5281/zenodo.1002675"
            or license_id.lower() != "cc-by-4.0"
            or receipt["doi"] != meta["doi"] or receipt["license"].lower() != license_id.lower()
            or receipt["full_archive_checksum_verified"] is not False
            or receipt["independent_approval"] is not False):
        raise ValueError("whole-plant source or receipt identity differs")
    archive = next(f for f in record["files"] if f["key"] == "Maize whole plant image dataset.zip")
    if receipt["archive"] != archive["key"] or receipt["archive_checksum_declared"] != archive["checksum"]:
        raise ValueError("archive provenance differs")
    matches = [r for r in receipt["images"] if r["candidate"] == name]
    if len(matches) != 1:
        raise ValueError("missing or duplicate source receipt")
    row = matches[0]
    member = f"article_binarisation_dataset/raw_images/plant-1_task-{task}_tv0_cabin-2.png"
    if (row["original_archive_member"] != member or row["sha256"] != digest
            or row["zip_member_crc32"] != crc or row["fully_opaque"] is not True
            or row["original_bytes_preserved"] is not True
            or f"{zlib.crc32(path.read_bytes()):08x}" != crc):
        raise ValueError("whole-plant member receipt or CRC differs")
    with Image.open(path) as image:
        image.load()
        if image.size != (2448, 2048) or image.mode != "RGBA" or image.getchannel("A").getextrema() != (255, 255):
            raise ValueError("whole-plant original image format differs")


EXPECTED_REUSED_IMAGE_PAIRS = (
    ("dev-p002-valid-arabidopsis", "dev-p002-missing-species"),
    ("val-p002-valid-potato", "val-p002-missing-species"),
    ("dev-training-ready", "dev-training-missing-data"),
)
EXPECTED_SOURCE_TYPES = {
    "dev-p001-valid-arabidopsis": "ara",
    "dev-p001-species-potato": "potato",
    "dev-p002-valid-arabidopsis": "ara",
    "dev-p002-missing-species": "ara",
    "dev-p003-valid-potato": "potato",
    "dev-p003-species-maize": "maize",
    "dev-training-ready": "maize",
    "dev-training-missing-data": "maize",
    "val-p001-valid-potato": "potato",
    "val-p001-species-arabidopsis": "ara",
    "val-p002-valid-potato": "potato",
    "val-p002-missing-species": "potato",
}
SOURCE_LABELS = {
    "ara": "Local PhenoAssistant AraCrop metadata: data/aracrop_metadata.json",
    "potato": "Local PhenoAssistant potato metadata: data/potato_metadata.csv",
}


def read_meta() -> tuple[set[str], set[str]]:
    ara = json.loads(ARA.read_text(encoding="utf-8"))
    imgs = ara.get("file_name")
    if not isinstance(imgs, list) or not all(isinstance(s, str) for s in imgs):
        raise ValueError("AraCrop metadata file_name is invalid")
    with POTATO.open(newline="", encoding="utf-8-sig") as f:
        potato = [r["file_name"] for r in csv.DictReader(f)]
    return set(imgs), set(potato)


def technical_audit(candidate: Path, trusted_root: Path) -> dict[str, object]:
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError("private candidate is missing or a symlink")
    source = json.loads(candidate.read_text(encoding="utf-8"))
    expected = fixture_template()
    if not isinstance(source, dict) or set(source) != set(expected):
        raise ValueError("candidate schema differs from frozen registry template")
    if any(source[k] != expected[k] for k in expected if k != "entries"):
        raise ValueError("candidate metadata differs from frozen registry template")
    rows = source["entries"]
    if not isinstance(rows, list) or len(rows) != 12:
        raise ValueError("expected exactly 12 entries")
    ara, potato = read_meta()
    plantdoc_commit = None
    wholeplant_cases = 0
    assets_by_case: dict[str, str] = {}
    source_counts: Counter[str] = Counter()
    entries = {
        row["scenario_id_internal_only"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("scenario_id_internal_only"), str)
    }
    if len(entries) != 12 or set(entries) != set(EXPECTED_SOURCE_TYPES):
        raise ValueError("missing, duplicate, or unknown frozen case identifiers")
    expected_rows = {row["scenario_id_internal_only"]: row for row in expected["entries"]}
    for ident, source_type in EXPECTED_SOURCE_TYPES.items():
        row = entries[ident]
        if set(row) != FIELDS:
            raise ValueError(f"incorrect private schema: {ident}")
        if row["model_visible_view_sha256"] != expected_rows[ident]["model_visible_view_sha256"]:
            raise ValueError(f"frozen model-visible hash drift: {ident}")
        path = _checked_path(row.get("image_path_internal_only"), trusted_root)
        expected_hash = row.get("image_sha256")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise ValueError(f"invalid image SHA: {ident}")
        actual_hash = file_sha256(path)
        if actual_hash != expected_hash:
            raise ValueError(f"image content SHA mismatch: {ident}")
        if row.get("image_asset_id_internal_only") != "local_" + actual_hash[:24]:
            raise ValueError(f"asset ID differs from bound content: {ident}")
        src_id = row.get("source_image_id")
        if not isinstance(src_id, str) or not src_id.startswith("./data/") or ".." in Path(src_id).parts:
            raise ValueError(f"source image ID malformed: {ident}")
        source_path = (ROOT / src_id).resolve(strict=True)
        if source_path != path:
            raise ValueError(f"source image ID/path binding mismatch: {ident}")
        source_tag = row.get("source_dataset")
        if source_type == "ara":
            if source_tag != SOURCE_LABELS["ara"] or src_id not in ara:
                raise ValueError(f"AraCrop source metadata disagreement: {ident}")
        elif source_type == "potato":
            if source_tag != SOURCE_LABELS["potato"] or src_id not in potato:
                raise ValueError(f"potato source metadata disagreement: {ident}")
        elif source_tag == WHOLEPLANT_SOURCE:
            verify_wholeplant(ident, path, actual_hash)
            wholeplant_cases += 1
        else:
            if not isinstance(source_tag, str) or not source_tag.startswith(PLANTDOC_PREFIX):
                raise ValueError(f"PlantDoc source revision not recorded: {ident}")
            expected_revision = source_tag[len(PLANTDOC_PREFIX):]
            if plantdoc_commit is None:
                if not (MAIZE_ROOT / ".git").exists():
                    raise ValueError("original PlantDoc Git checkout missing")
                plantdoc_commit = subprocess.run(
                    ["git", "-C", str(MAIZE_ROOT), "rev-parse", "--verify", "HEAD"],
                    capture_output=True, text=True, check=True,
                ).stdout.strip()
            if expected_revision != plantdoc_commit:
                raise ValueError(f"PlantDoc revision mismatch: {ident}")
            plantdoc_base = MAIZE_ROOT.resolve(strict=True)
            if not path.is_relative_to(plantdoc_base):
                raise ValueError(f"PlantDoc image outside original checkout: {ident}")
            if path.parent.name not in {"Corn leaf blight", "Corn Gray leaf spot"}:
                raise ValueError(f"PlantDoc maize directory unexpected: {ident}")
        for key in ("reviewed_species", "license_or_access_evidence", "reviewer_evidence_id"):
            if row.get(key) is not None:
                raise ValueError(f"human review field unexpectedly prefilled: {ident} ({key})")
        source_counts[source_type] += 1
        assets_by_case[ident] = actual_hash

    if wholeplant_cases not in (0, 3):
        raise ValueError("mixed maize replacement is not permitted")
    for first, second in EXPECTED_REUSED_IMAGE_PAIRS:
        if assets_by_case[first] != assets_by_case[second]:
            raise ValueError(f"matched metadata-stress image differs: {first}/{second}")

    return {
        "technical_image_bindings_checked": len(assets_by_case),
        "unique_content_hashes": len(set(assets_by_case.values())),
        "source_type_counts": dict(sorted(source_counts.items())),
        "same_image_metadata_pairs": len(EXPECTED_REUSED_IMAGE_PAIRS),
        "image_sha256_checks_passed": True,
        "metadata_membership_checks_passed": True,
        "plantdoc_revision_checked": plantdoc_commit is not None,
        "wholeplant_receipt_cases_checked": wholeplant_cases,
        "full_wholeplant_archive_checksum_verified": False,
        "human_review_fields_filled": 0,
        "scientific_execution_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=CANDIDATE)
    parser.add_argument("--trusted-root", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    print("PHASE8_CANDIDATE_TECHNICAL_AUDIT_NO_PROVIDER_OR_GPU_CALLS=true")
    try:
        report = technical_audit(args.file, args.trusted_root)
    except Exception as exc:
        print("PHASE8_CANDIDATE_TECHNICAL_AUDIT_PASS=false")
        print("PHASE8_CANDIDATE_ERROR=" + type(exc).__name__ + ": " + str(exc))
        return 2
    for k, v in report.items():
        print("PHASE8_CANDIDATE_" + k.upper() + "=" + json.dumps(v, sort_keys=True))
    print("PHASE8_CANDIDATE_TECHNICAL_AUDIT_PASS=true")
    print("PHASE8_CANDIDATE_INDEPENDENT_REVIEW_APPROVED=false")
    print("PHASE8_CANDIDATE_SPECIES_SHIFT_VISUAL_CONFOUNDS_REVIEW_REQUIRED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
