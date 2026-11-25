"""Retrospective component stress test on the preserved full Case 1 GPU output.

Not a live agent trial, independent accuracy benchmark, or a frozen-method change.
Compare a defined basic COCO structure/reference checker with the existing
Phase 8 validate_coco on all historical image-level records and eight
predeclared one-at-a-time synthetic faults/probes. Retain every failure.
No model inference, API, network, hidden labels, fixture review or approval.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.verify_phenoguard_method_freeze import verify_manifest
from scripts.research.phase8_attempt_ledger import load_verified_controls, sha256_file
from scripts.research.phase8_scientific_artifact_validator import validate_coco

RUN = ROOT / "results/maf_gpu_case1"
ART = RUN / "ins_seg_results.json"
META = ROOT / "data/aracrop_metadata.json"
EVIDENCE = RUN / "gpu_execution_evidence.json"
FAULTS = (
    "wrong_source_filename", "negative_area", "confidence_above_one",
    "unknown_image_reference", "wrong_rle_shape", "empty_rle_counts",
    "invalid_nonempty_rle_probe", "zero_area_inconsistent_with_original_probe",
)


def number(x):
    return type(x) in (int, float) and math.isfinite(x)


def basic_coco(obj):
    """Explicit diagnostic reference, not a formal COCO conformance suite.

    Checks required field types, positive dimensions, unique IDs,
    category/image references and RLE field types; no scientific range,
    source binding, RLE dimension agreement or encoded-content validation.
    """
    try:
        ims, anns, cats = obj["images"], obj["annotations"], obj["categories"]
        if not all(isinstance(x, list) for x in (ims, anns, cats)) or len(ims) != 1 or not cats:
            return False
        im = ims[0]
        if type(im["id"]) is not int or not isinstance(im["file_name"], str) or not im["file_name"]:
            return False
        if any(type(im[k]) is not int or im[k] <= 0 for k in ("width", "height")):
            return False
        if any(type(c["id"]) is not int or not isinstance(c["name"], str) or not c["name"] for c in cats):
            return False
        cat_ids = {c["id"] for c in cats}
        if len(cat_ids) != len(cats):
            return False
        seen = set()
        for a in anns:
            if type(a["id"]) is not int or a["id"] in seen:
                return False
            seen.add(a["id"])
            if type(a["image_id"]) is not int or a["image_id"] != im["id"]:
                return False
            if type(a["category_id"]) is not int or a["category_id"] not in cat_ids:
                return False
            if not number(a["area"]) or not number(a["score"]) or type(a["iscrowd"]) is not int:
                return False
            mask = a["segmentation"]
            if not isinstance(mask["counts"], str) or not isinstance(mask["size"], list):
                return False
            if len(mask["size"]) != 2 or any(type(x) is not int for x in mask["size"]):
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def mutate(obj, fault):
    if fault == "wrong_source_filename":
        obj["images"][0]["file_name"] = "wrong-source-image.png"
        return True
    if not obj["annotations"]:
        return False
    a = obj["annotations"][0]
    im = obj["images"][0]
    if fault == "negative_area":
        a["area"] = -1
    elif fault == "confidence_above_one":
        a["score"] = 1.01
    elif fault == "unknown_image_reference":
        a["image_id"] = im["id"] + 1
    elif fault == "wrong_rle_shape":
        if not isinstance(a.get("segmentation"), dict):
            return False
        a["segmentation"]["size"] = [im["height"] + 1, im["width"]]
    elif fault in {"empty_rle_counts", "invalid_nonempty_rle_probe"}:
        if not isinstance(a.get("segmentation"), dict):
            return False
        a["segmentation"]["counts"] = "" if fault == "empty_rle_counts" else "!"
    elif fault == "zero_area_inconsistent_with_original_probe":
        a = next((x for x in obj["annotations"] if number(x.get("area")) and x["area"] > 0), None)
        if a is None:
            return False
        a["area"] = 0
    else:
        raise ValueError("unknown predeclared fault")
    return True


def assess(obj, expected, tmp):
    tmp.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    result = validate_coco(tmp, expected_image_path=expected)
    return basic_coco(obj), result.safe_to_report, [i.field or i.code.value for i in result.issues]


def run():
    frozen_count, frozen_digest = verify_manifest()
    matrix, candidate = load_verified_controls()
    if candidate["scientific_execution_permitted"] is not False:
        raise ValueError("historical runtime gate changed")
    before = {str(p.relative_to(ROOT)): sha256_file(p) for p in (ART, META, EVIDENCE)}
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if ev["segmentation_sha256"] != before[str(ART.relative_to(ROOT))] or ev["executed_image_count"] != 1248:
        raise ValueError("historical full-run evidence mismatch")
    source = json.loads(ART.read_text(encoding="utf-8"))
    metadata = json.loads(META.read_text(encoding="utf-8"))["file_name"]
    if len(metadata) != 1248 or len(set(metadata)) != 1248:
        raise ValueError("metadata image identity/count mismatch")
    # Historical outputs used relative filenames. Map to absolute paths
    # only after matching their EXACT original metadata strings; no other
    # source content is changed in the per-image control.
    expected = {name: (ROOT / name).resolve(strict=True) for name in metadata}
    if len(set(expected.values())) != 1248 or not all(p.is_relative_to(ROOT / "data") for p in expected.values()):
        raise ValueError("ambiguous or out-of-root metadata image paths")
    images = source["images"]
    annotations = source["annotations"]
    cats = source["categories"]
    if len(images) != 1248 or set(i["file_name"] for i in images) != set(expected):
        raise ValueError("historical output does not match all 1248 metadata names")
    image_ids = [i["id"] for i in images]
    if len(set(image_ids)) != 1248:
        raise ValueError("duplicate global image IDs: cannot partition safely")
    groups = defaultdict(list)
    for ann in annotations:
        groups[ann["image_id"]].append(ann)
    orphans = sum(len(a) for k,a in groups.items() if k not in set(image_ids))
    global_annotation_duplicates = len(annotations) - len({a["id"] for a in annotations})
    if orphans:
        raise ValueError(f"historical artifact contains {orphans} orphan annotations; refusing silent drop")

    originals = Counter()
    original_issues = Counter()
    per_fault = {f: Counter() for f in FAULTS}
    details = []
    with tempfile.TemporaryDirectory(prefix="phenoguard_coco_stress_") as td:
        tmp = Path(td) / "single_image.json"
        for im in images:
            name = im["file_name"]
            path = expected[name]
            # Single-image interface adapter only, no prediction values repaired.
            control = {"images": [dict(im, file_name=str(path))],
                       "annotations": groups.get(im["id"], []), "categories": cats}
            b, v, issues = assess(control, path, tmp)
            originals["images"] += 1
            originals["basic_accepted"] += int(b)
            originals["validator_accepted"] += int(v)
            originals["no_annotations"] += int(not control["annotations"])
            original_issues.update(issues)
            row = {"image_id": im["id"], "annotations": len(control["annotations"]),
                   "basic_original_accepts": b, "validator_original_accepts": v,
                   "original_issue_fields": issues, "faults": {}}
            for f in FAULTS:
                c = per_fault[f]
                variant = copy.deepcopy(control)
                if not mutate(variant, f):
                    c["not_applicable"] += 1
                    row["faults"][f] = None
                    continue
                bb, vv, ii = assess(variant, path, tmp)
                c["tested"] += 1
                c["basic_rejected"] += int(not bb)
                c["validator_rejected"] += int(not vv)
                if b and v:
                    c["both_originals_accepted"] += 1
                    c["basic_rejected_on_joint_clean"] += int(not bb)
                    c["validator_rejected_on_joint_clean"] += int(not vv)
                row["faults"][f] = {"basic_accepts": bb, "validator_accepts": vv, "issues": ii}
            details.append(row)

    after = {str(p.relative_to(ROOT)): sha256_file(p) for p in (ART, META, EVIDENCE)}
    if before != after:
        raise ValueError("historical input bytes changed during replay")
    report = {
        "scope": "RETROSPECTIVE_COMPONENT_ONLY_NOT_LIVE_AGENT_QUALIFICATION",
        "method_freeze": {"count": frozen_count, "sha256": frozen_digest},
        "source_sha256": before,
        "source_filename_adapter": "exact metadata match then canonical absolute name only",
        "global_annotation_count": len(annotations),
        "global_duplicate_annotation_ids": global_annotation_duplicates,
        "originals": dict(originals),
        "original_validator_issue_fields": dict(original_issues),
        "fault_results": {f: dict(c) for f,c in per_fault.items()},
        "limitations": [
            "Original predictions are not expert gold; acceptance is not segmentation accuracy.",
            "Faults are synthetic and correlated within historical images; no independence or significance claims.",
            "Basic checker is an explicit custom structural reference, not C3/C4 or a formal full COCO validator.",
            "Two exploratory probes target known RLE content and area-consistency limitations; retained in all reporting.",
            "Single-image validator does not test cross-image global consistency; global duplicate count reported separately.",
        ],
        "live_qualification_trials_executed": 0,
        "provider_calls": 0, "gpu_calls": 0, "hidden_gold_read": False,
        "per_image": details,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    staging = (ROOT / "data/_staging").resolve(strict=True)
    if not target.is_relative_to(staging) or args.output.is_symlink() or target.exists():
        raise ValueError("output must be a new file under private staging")
    report = run()
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k:v for k,v in report.items() if k != "per_image"}, indent=2, sort_keys=True))
    print("REPORT_SHA256=" + sha256_file(target))
    print("RETROSPECTIVE_COMPONENT_EVALUATION_COMPLETED=true")


if __name__ == "__main__":
    main()
