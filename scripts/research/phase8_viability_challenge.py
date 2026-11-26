"""Pre-outcome falsification study on mechanical cases and historical outputs.

NOT the registered agent matrix. No provider, GPU, hidden labels, new image
fixtures, approval pins or frozen-method modifications. Stronger references
are explicitly diagnostic, not implementations of C3/C4/C5.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.phenoguard.contracts import ApplicabilityDecision as D
from research.phenoguard.catalogue import resolve_capability_catalogue
from research.phenoguard.provenance import build_default_provenance_catalogue
from research.phenoguard.pilot_manifest import (
    build_development_validation_manifest, build_development_validation_gold,
)
from scripts.research.verify_phenoguard_method_freeze import verify_manifest
from scripts.research.phase8_attempt_ledger import load_verified_controls, sha256_file
from scripts.research.phase8_retrospective_coco_stress import (
    ART, META, EVIDENCE, FAULTS, basic_coco, mutate, assess,
)

EXEC = {D.EXECUTE, D.RESELECT}
EXPECTED_ART = "4d779ee715b9c54fe3e6e3bfc9a02275eedc9f5e9412edd34e644361005798d1"


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.casefold()))


def name_task_reference(request, requested, readiness, zoo):
    """Generic lexical species/task match; no envelope, gold or model lookup."""
    candidates = [ident for task, ids in zoo.items()
                  if tokens(task) == tokens(request.scientific_task) for ident in ids]
    if not request.species and candidates:
        return D.CLARIFY, None
    # Allow a scientific binomial's genus to match a genus-only checkpoint name.
    species = tokens(request.species or "")
    matches = [ident for ident in candidates if species & tokens(ident)]
    if requested in matches:
        return D.EXECUTE, requested
    if len(matches) == 1:
        return (D.RESELECT if requested is not None else D.EXECUTE), matches[0]
    if len(matches) > 1:
        return D.CLARIFY, None
    if readiness is not None and tokens(request.scientific_task) == {"image","classification"}:
        ready = readiness.dataset_available and readiness.labels_available and readiness.dataset_format_valid
        return (D.RECOMMEND_TRAINING if ready else D.CLARIFY), None
    return D.ABSTAIN, None


def decision_audit():
    zoo = json.loads((ROOT/"model_zoo.json").read_text())
    envs = build_default_provenance_catalogue()
    predictions = {}
    for s in build_development_validation_manifest():
        r = resolve_capability_catalogue(envs,s.request,requested_capability_id=s.requested_capability_id,training_readiness=s.training_readiness)
        predictions[s.scenario_id] = {
            "name_task_reference": name_task_reference(s.request,s.requested_capability_id,s.training_readiness,zoo),
            "requested_tool_passthrough": (D.EXECUTE,s.requested_capability_id) if s.requested_capability_id else (D.CLARIFY,None),
            "frozen_resolver": (r.decision,r.selected_capability_id),
        }
    gold = {g.scenario_id:g for g in build_development_validation_gold()}
    assert len(gold) == len(predictions) == 12 and set(gold) == set(predictions)
    totals = defaultdict(Counter)
    rows = []
    for ident, methods in predictions.items():
        g = gold[ident]
        row = {"case":ident,"expected_action":g.expected_decision.value,"methods":{}}
        for name,(action,selected) in methods.items():
            ok = selected == g.expected_selected_capability_id if not g.acceptable_selected_capability_ids else selected in g.acceptable_selected_capability_ids
            c = totals[name]
            c["n"] += 1
            c["exact_correct"] += int(action == g.expected_decision and ok)
            c["proposed_execution"] += int(action in EXEC)
            c["inappropriate_proposal"] += int(action in EXEC and (g.expected_decision not in EXEC or not ok))
            c["correct_executable_case"] += int(g.expected_decision in EXEC and action == g.expected_decision and ok)
            row["methods"][name] = {"action":action.value,"capability":selected}
        rows.append(row)
    return {"counts":{k:dict(v) for k,v in totals.items()},"cases":rows}


@lru_cache(maxsize=2048)
def rle_area(height,width,counts):
    """Bounded pure-Python validation of compressed COCO run lengths.

    Reject malformed input before invoking the C extension. COCO compressed
    counts use signed 5-bit groups and a two-run differential from index 3.
    """
    if not isinstance(counts,str) or not counts or not 0 < height*width <= 100_000_000:
        raise ValueError("bad mask extent/counts")
    runs, i, total, area = [], 0, 0, 0
    while i < len(counts):
        value, shift = 0, 0
        while True:
            if i >= len(counts) or shift > 35:
                raise ValueError("truncated or oversized count")
            c = ord(counts[i])-48
            i += 1
            if not 0 <= c <= 63:
                raise ValueError("non-COCO character")
            value |= (c & 31) << shift
            shift += 5
            if not c & 32:
                if c & 16:
                    value -= 1 << shift
                break
        if len(runs) > 2:
            value += runs[-2]
        if value < 0 or total+value > height*width:
            raise ValueError("invalid run extent")
        if len(runs)%2:
            area += value
        total += value
        runs.append(value)
        if len(runs) > 2*height*width+2:
            raise ValueError("too many runs")
    if total != height*width:
        raise ValueError("run lengths do not cover mask")
    return area


def reference(obj, expected=None):
    """Strong ordinary structural/range/mask-consistency reference.

    Optional source filename equality is an explicit separate provenance
    check. No claim that this is an official complete COCO validator.
    """
    from pycocotools import mask as mask_utils
    if not basic_coco(obj):
        return False
    im = obj["images"][0]
    h,w = im["height"],im["width"]
    if expected is not None and im["file_name"] != str(expected):
        return False
    try:
        for a in obj["annotations"]:
            m = a["segmentation"]
            if m["size"] != [h,w] or not 0 <= a["score"] <= 1 or not 0 <= a["area"] <= h*w or a["iscrowd"] not in (0,1):
                return False
            area = rle_area(h,w,m["counts"])
            # C library receives only prevalidated counts/dimensions.
            library = int(mask_utils.area({"size":[h,w],"counts":m["counts"].encode("ascii")}))
            if library != area or a["area"] != area:
                return False
        return True
    except (ValueError, TypeError, OverflowError, UnicodeError):
        return False


def artifact_audit():
    before = {str(p.relative_to(ROOT)):sha256_file(p) for p in (ART,META,EVIDENCE)}
    if before[str(ART.relative_to(ROOT))] != EXPECTED_ART:
        raise ValueError("historical artifact digest differs")
    ev = json.loads(EVIDENCE.read_text())
    if ev["segmentation_sha256"] != EXPECTED_ART or ev["executed_image_count"] != 1248:
        raise ValueError("historical run evidence mismatch")
    source = json.loads(ART.read_text())
    meta = json.loads(META.read_text())["file_name"]
    images = source["images"]
    if len(meta)!=1248 or len(set(meta))!=1248 or len(images)!=1248 or set(i["file_name"] for i in images)!=set(meta):
        raise ValueError("historical image membership mismatch")
    ids = {i["id"] for i in images}
    if len(ids)!=1248 or len(source["annotations"])!=11848 or len({a["id"] for a in source["annotations"]})!=11848:
        raise ValueError("historical image/annotation count or identity drift")
    groups = defaultdict(list)
    for a in source["annotations"]:
        if a["image_id"] not in ids:
            raise ValueError("orphan annotation")
        groups[a["image_id"]].append(a)
    images = sorted(images,key=lambda i:i["id"])
    controls = []
    for im in images:
        path = (ROOT/im["file_name"]).resolve(strict=True)
        if not path.is_relative_to(ROOT/"data"):
            raise ValueError("image outside trusted data")
        controls.append((path,{"images":[dict(im,file_name=str(path))],"annotations":groups[im["id"]],"categories":source["categories"]}))
    originals, mask_stats = Counter(), Counter()
    faults = defaultdict(Counter)
    with tempfile.TemporaryDirectory(prefix="pg_viability_") as td:
        tmp = Path(td)/"artifact.json"
        def score(obj,path):
            b,pg,_ = assess(obj,path,tmp)
            strict = reference(obj)
            return {"basic_reference":b,"frozen_validator":pg,
                    "mask_consistency_reference":strict,
                    "source_bound_mask_reference":strict and obj["images"][0]["file_name"]==str(path)}
        for i,(path,control) in enumerate(controls):
            original = score(control,path)
            originals["n"] += 1
            for method,accepted in original.items():
                originals[method+"_accepted"] += int(accepted)
            h,w = control["images"][0]["height"],control["images"][0]["width"]
            for a in control["annotations"]:
                mask_stats["n"] += 1
                try:
                    area = rle_area(h,w,a["segmentation"]["counts"])
                    mask_stats["valid_run_extent"] += 1
                    mask_stats["stored_area_matches_runs"] += int(area == a["area"])
                except (ValueError,TypeError,KeyError):
                    mask_stats["invalid_run_extent"] += 1
            def evaluate(name,variant):
                c = faults[name]
                c["n"] += 1
                for method,accepted in score(variant,path).items():
                    c[method+"_rejected"] += int(not accepted)
                    if original[method]:
                        c[method+"_clean_original_n"] += 1
                        c[method+"_rejected_on_clean_original"] += int(not accepted)
            for fault in FAULTS:
                variant = copy.deepcopy(control)
                if mutate(variant,fault):
                    evaluate(fault,variant)
                else:
                    faults[fault]["not_applicable"] += 1
            # A real prediction from a different image, without modifying its
            # masks or annotations. Second probe relabels only the filename.
            _,donor = controls[(i+1)%len(controls)]
            if donor["images"][0]["id"] == control["images"][0]["id"]:
                raise ValueError("same source selected as donor")
            evaluate("actual_wrong_image_artifact",donor)
            relabelled = copy.deepcopy(donor)
            relabelled["images"][0]["file_name"] = str(path)
            evaluate("actual_wrong_image_artifact_relabelled",relabelled)
    if before != {str(p.relative_to(ROOT)):sha256_file(p) for p in (ART,META,EVIDENCE)}:
        raise ValueError("historical input changed")
    return {"source_sha256":before,"originals":dict(originals),"original_mask_audit":dict(mask_stats),
            "faults_and_source_swap_probes":{k:dict(v) for k,v in faults.items()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",required=True,type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to((ROOT/"data/_staging").resolve()) or args.output.is_symlink() or out.exists():
        raise ValueError("new private staging output required")
    count,freeze = verify_manifest()
    _,candidate = load_verified_controls()
    if candidate["scientific_execution_permitted"] is not False:
        raise ValueError("historical runtime unexpectedly approved")
    report = {"scope":"DIAGNOSTIC_ONLY_NOT_REGISTERED_AGENT_TRIALS",
              "method_freeze":{"count":count,"sha256":freeze},
              "decisions":decision_audit(),"artifacts":artifact_audit(),
              "provider_calls":0,"gpu_calls":0,"live_qualification_trials":0,"hidden_gold_accessed":False,
              "limitations":["Known mechanical cases, lexical baseline designed after case exposure; not independent performance.",
              "Synthetic faults correlated within images; no natural failure prevalence or biological accuracy.",
              "Real swapped outputs establish wrong source identity, not necessarily biologically incorrect masks.",
              "Strong ordinary reference is a local diagnostic, not C5 or a competing published method."]}
    with os.fdopen(os.open(out,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),"w") as f:
        json.dump(report,f,indent=2,sort_keys=True,allow_nan=False)
        f.write("\n")
    print(json.dumps({**report,"decisions":report["decisions"]["counts"]},indent=2,sort_keys=True))
    print("VIABILITY_CHALLENGE_REPORT_SHA256="+sha256_file(out))
    print("VIABILITY_CHALLENGE_COMPLETED=true")


if __name__ == "__main__":
    main()
