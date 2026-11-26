"""Prospective three-binding replacement, preserving all original review materials.

No gold, provider calls, GPU inference, or independent approval. Run only
before any qualification outcomes or human review. Build and audit a complete
staged candidate before replacing the active private paths.
"""
from __future__ import annotations

import copy
import csv
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageOps
from scripts.research.phase8_audit_private_fixture_candidate import (
    CANDIDATE, WHOLEPLANT_ROOT, WHOLEPLANT_SOURCE, WHOLEPLANT_SELECTION,
    technical_audit, verify_wholeplant,
)
from scripts.research import phase8_prepare_private_review_worksheet as worksheets
from scripts.research.verify_phenoguard_method_freeze import verify_manifest
from phenoassistant_mcp.scientific_inference_v1 import file_sha256

STAGING = ROOT / "data/_staging"
OLD = STAGING / "phase8_plantdoc_candidate_archive_v0.1"
NEW = STAGING / "phase8_wholeplant_replacement_work_v0.2"
SHEET = STAGING / "phase8_private_fixture_contact_sheet.png"
PACKET = STAGING / "phase8_release_review_packet_v0.1.json"
REVIEW_FIELDS = {
    worksheets.IMAGE_CSV: worksheets.IMAGE_FIELDS[7:],
    worksheets.SCENARIO_CSV: worksheets.SCENARIO_FIELDS[5:],
}


def contact_sheet(csv_path, target):
    with csv_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 9
    assert len({r["image_sha256"] for r in rows}) == 9
    w, h = 500, 420
    sheet = Image.new("RGB", (3*w, 3*h+60), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((20,20), "PhenoGuard - Private Independent Image Review (whole-plant maize)", fill="black")
    for i, row in enumerate(rows):
        path = Path(row["image_path_private"])
        if file_sha256(path) != row["image_sha256"]:
            raise ValueError("image hash drift in contact sheet")
        with Image.open(path) as im:
            preview = ImageOps.exif_transpose(im).convert("RGB")
        preview.thumbnail((w-30,h-65))
        x,y = i%3*w,i//3*h+60
        sheet.paste(preview,(x+(w-preview.width)//2,y+10))
        draw.text((x+15,y+h-40),f"Image {i+1:02d} | {row['image_sha256'][:16]}",fill="black")
    with target.open("xb") as stream:
        sheet.save(stream,format="PNG")


def main():
    os.umask(0o077)
    if OLD.exists() or NEW.exists():
        raise FileExistsError("prior replacement work exists; inspect instead of overwriting")
    if (STAGING / "phase8_native_qualification_live_v0.1").exists():
        raise ValueError("live qualification directory exists; no prospective replacement")
    if (STAGING / "phase8_image_fixture_reviewed_candidate_v0.1.json").exists():
        raise ValueError("reviewed candidate already exists; do not reset review")
    active = [CANDIDATE, worksheets.IMAGE_CSV, worksheets.SCENARIO_CSV, SHEET, PACKET]
    for path in active:
        if not path.is_file() or path.is_symlink():
            raise ValueError("missing or linked original review artifact: "+path.name)
    for path, fields in REVIEW_FIELDS.items():
        with path.open(newline="") as stream:
            if any((row.get(field) or "").strip() for row in csv.DictReader(stream) for field in fields):
                raise ValueError("existing human review fields are not blank")
    old = json.loads(CANDIDATE.read_text())
    technical_audit(CANDIDATE, ROOT / "data")
    candidate = copy.deepcopy(old)
    changed = set()
    for row in candidate["entries"]:
        ident = row["scenario_id_internal_only"]
        if ident not in WHOLEPLANT_SELECTION:
            continue
        name, digest, task, crc = WHOLEPLANT_SELECTION[ident]
        path = (WHOLEPLANT_ROOT / name).resolve(strict=True)
        if file_sha256(path) != digest:
            raise ValueError("replacement image bytes differ")
        verify_wholeplant(ident, path, digest)
        row.update(image_asset_id_internal_only="local_"+digest[:24],
                   image_path_internal_only=str(path), image_sha256=digest,
                   source_dataset=WHOLEPLANT_SOURCE,
                   source_image_id="./"+path.relative_to(ROOT).as_posix())
        changed.add(ident)
    if changed != set(WHOLEPLANT_SELECTION):
        raise ValueError("replacement case identity mismatch")
    for before, after in zip(old["entries"],candidate["entries"],strict=True):
        if before["scenario_id_internal_only"] not in changed and before != after:
            raise ValueError("unrelated fixture changed")
        if before["model_visible_view_sha256"] != after["model_visible_view_sha256"]:
            raise ValueError("frozen visible request changed")
    NEW.mkdir(mode=0o700)
    staged = NEW / CANDIDATE.name
    staged.write_text(json.dumps(candidate,sort_keys=True,indent=2)+"\n")
    report = technical_audit(staged,ROOT / "data")
    if (report["technical_image_bindings_checked"] != 12
        or report["unique_content_hashes"] != 9
        or report["same_image_metadata_pairs"] != 3
        or report["wholeplant_receipt_cases_checked"] != 3):
        raise ValueError("replacement audit failed")
    image_csv, scenario_csv = worksheets.IMAGE_CSV, worksheets.SCENARIO_CSV
    worksheets.CANDIDATE = staged
    worksheets.OUT_DIR = NEW
    worksheets.IMAGE_CSV = NEW / image_csv.name
    worksheets.SCENARIO_CSV = NEW / scenario_csv.name
    worksheets.main()
    contact_sheet(worksheets.IMAGE_CSV, NEW / SHEET.name)
    count, digest = verify_manifest()
    OLD.mkdir(mode=0o700)
    for path in active:
        shutil.copy2(path,OLD/path.name)
        if file_sha256(path) != file_sha256(OLD/path.name):
            raise ValueError("archive copy mismatch")
    try:
        for path in active[:-1]:
            os.replace(NEW/path.name,path)
        # Superseded release packet MUST be regenerated from actual new inputs.
        PACKET.unlink()
        technical_audit(CANDIDATE,ROOT/"data")
    except BaseException:
        for path in active:
            shutil.copy2(OLD/path.name,path)
        raise
    NEW.rmdir()
    print("ORIGINAL_REVIEW_ARCHIVE="+str(OLD.relative_to(ROOT)))
    print("REPLACED_SCENARIO_BINDINGS=3")
    print("UNCHANGED_SCENARIO_BINDINGS=9")
    print("DISTINCT_IMAGE_HASHES=9")
    print("SAME_IMAGE_CONTROL_PAIRS=3")
    print("NEW_FIXTURE_CANDIDATE_SHA256="+file_sha256(CANDIDATE))
    print("METHOD_FREEZE_FILE_COUNT="+str(count))
    print("METHOD_FREEZE_SHA256="+digest)
    print("INDEPENDENT_APPROVAL_GRANTED=false")
    print("SCIENTIFIC_EXECUTION_PERMITTED=false")


if __name__ == "__main__":
    main()
