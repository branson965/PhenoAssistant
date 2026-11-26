"""Replay the already observed wrong-source mechanism through Case 1 science.

Retrospective diagnostic: transfer complete historical predicted phenotype
vectors, not invented measurements. Compare the original image-ID rotation
from viability challenge with a prespecified same-day cross-ecotype trajectory
swap. Neither is an observed operational error rate or biological gold.
No GPU, API, hidden labels, live trial, or changes to the method freeze.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from scripts.research.phase8_attempt_ledger import sha256_file
from scripts.research.verify_phenoguard_method_freeze import verify_manifest
from scripts.research.phase8_retrospective_coco_stress import ART, META, EVIDENCE
from scripts.gpu.compare_case1_scientific_conclusions import _interaction, _pairwise
from scripts.gpu.compare_case1_gpu_to_tracked import PHENOTYPES, _rank_ecotypes

RUN = ROOT / "results/maf_gpu_case1"
RAW = RUN / "phenotypes.csv"
MERGED = RUN / "aracrop_phenotypes.csv"
COMPARISON = RUN / "comparison_to_tracked.json"
VIABILITY = ROOT / "data/_staging/phase8_viability_challenge_v0.1.json"
VIABILITY_SHA = "b3a5cd4d9be75d575c74db30958e6a797a4ff333d3f623018e894c0b36ee13eb"
EXPECTED_ART = "4d779ee715b9c54fe3e6e3bfc9a02275eedc9f5e9412edd34e644361005798d1"
COLS = list(PHENOTYPES)


def summarize(frame, path):
    frame.to_csv(path, index=False)
    with contextlib.redirect_stdout(io.StringIO()):
        interaction = _interaction(path)
        pairs, groups = _pairwise(path)
    means = {}
    ranks = {}
    for metric in ("leaf_count", "projected_leaf_area"):
        per_plant = frame.groupby(["ecotype","plant_id"])[metric].mean()
        means[metric] = {str(k):float(v) for k,v in per_plant.groupby(level=0).mean().items()}
        ranks[metric] = _rank_ecotypes(frame, metric)
    return {"interaction":interaction,"tukey_pairs":pairs,"tukey_groups":groups,
            "ecotype_means":means,"ecotype_ranks":ranks}


def trajectory_swap(frame):
    """Deterministic disjoint cross-ecotype pairs with identical time schedules.

    Greedy lexicographic pairing uses only metadata, never phenotype values.
    Exchange complete trajectories so the within-plant time ordering survives.
    """
    groups = defaultdict(list)
    lookup = {}
    for plant, rows in frame.groupby("plant_id", sort=True):
        if rows["ecotype"].nunique() != 1 or rows["days_after_sowing"].duplicated().any():
            raise ValueError("ambiguous plant trajectory")
        schedule = tuple(sorted(rows["days_after_sowing"].tolist()))
        groups[schedule].append((str(plant),str(rows["ecotype"].iloc[0])))
        lookup[str(plant)] = dict(zip(rows["days_after_sowing"],rows["file_name"],strict=True))
    mapping = {name:name for name in frame["file_name"]}
    pairs = []
    for schedule, plants in sorted(groups.items()):
        remaining = sorted(plants)
        while remaining:
            a, ea = remaining.pop(0)
            idx = next((i for i,(_,eb) in enumerate(remaining) if eb!=ea),None)
            if idx is None:
                continue
            b, eb = remaining.pop(idx)
            pairs.append({"plant_a":a,"plant_b":b,"ecotype_a":ea,"ecotype_b":eb,"observations":len(schedule)})
            for day in schedule:
                x,y = lookup[a][day],lookup[b][day]
                mapping[x],mapping[y] = y,x
    if not pairs:
        raise ValueError("no compatible cross-ecotype trajectory pairs")
    return mapping,pairs


def apply(frame, mapping):
    by = frame.set_index("file_name",verify_integrity=True)
    names = frame["file_name"].tolist()
    if set(mapping)!=set(names) or set(mapping.values())!=set(names):
        raise ValueError("swap is not a bijection")
    donor = [mapping[n] for n in names]
    perturbed = frame.copy()
    perturbed[COLS] = by.loc[donor,COLS].to_numpy()
    cross = by.loc[donor,"ecotype"].to_numpy()!=frame["ecotype"].to_numpy()
    same_day = by.loc[donor,"days_after_sowing"].to_numpy()==frame["days_after_sowing"].to_numpy()
    changed = np.asarray([a!=b for a,b in zip(names,donor)])
    stats = {"rows":len(frame),"swapped_rows":int(changed.sum()),
             "cross_ecotype_rows":int((changed & cross).sum()),
             "same_day_swapped_rows":int((changed & same_day).sum())}
    for metric in ("leaf_count","projected_leaf_area"):
        diff = np.abs(perturbed[metric].to_numpy()-frame[metric].to_numpy())
        stats[metric] = {"changed_rows":int((diff>1e-10).sum()),
                         "mean_abs_difference":float(diff.mean()),
                         "median_abs_difference":float(np.median(diff)),
                         "max_abs_difference":float(diff.max())}
    return perturbed,stats


def run():
    count,freeze = verify_manifest()
    inputs = [ART,META,EVIDENCE,RAW,MERGED,COMPARISON,VIABILITY]
    before = {str(p.relative_to(ROOT)):sha256_file(p) for p in inputs}
    if sha256_file(VIABILITY)!=VIABILITY_SHA or sha256_file(ART)!=EXPECTED_ART:
        raise ValueError("historical challenge or artifact identity differs")
    prior = json.loads(VIABILITY.read_text())
    probe = prior["artifacts"]["faults_and_source_swap_probes"]["actual_wrong_image_artifact_relabelled"]
    if probe["n"]!=1248 or probe["frozen_validator_rejected"]!=0:
        raise ValueError("historical source-swap result differs")
    ev = json.loads(EVIDENCE.read_text())
    comp = json.loads(COMPARISON.read_text())
    if ev["segmentation_sha256"]!=EXPECTED_ART or ev["phenotype_sha256"]!=sha256_file(RAW) or comp["merge"]["output_sha256"]!=sha256_file(MERGED):
        raise ValueError("phenotype provenance mismatch")
    meta = pd.DataFrame(json.loads(META.read_text()))
    raw = pd.read_csv(RAW)
    frame = raw.merge(meta[["file_name","plant_id","ecotype","days_after_sowing"]],on="file_name",validate="one_to_one")
    historical = pd.read_csv(MERGED)
    if len(frame)!=1248 or len(historical)!=1248 or set(frame["file_name"])!=set(historical["file_name"]):
        raise ValueError("historical metadata membership differs")
    keys = ["file_name","plant_id","ecotype","days_after_sowing"]+COLS
    pd.testing.assert_frame_equal(frame[keys].sort_values("file_name").reset_index(drop=True),
                                 historical[keys].sort_values("file_name").reset_index(drop=True),
                                 check_dtype=False,check_exact=False,rtol=1e-12,atol=1e-12)
    if frame[keys].isna().any().any() or not np.isfinite(frame[COLS].to_numpy()).all():
        raise ValueError("missing or nonfinite original scientific measurements")
    images = sorted(json.loads(ART.read_text())["images"],key=lambda r:r["id"])
    names = [im["file_name"] for im in images]
    if len(set(names))!=1248 or set(names)!=set(frame["file_name"]):
        raise ValueError("historical image identity differs")
    rotation = dict(zip(names,names[1:]+names[:1],strict=True))
    trajectory,pairs = trajectory_swap(frame)
    result = {"scope":"RETROSPECTIVE_SCIENTIFIC_CONSEQUENCE_DIAGNOSTIC_ONLY",
              "method_freeze":{"count":count,"sha256":freeze},"source_sha256":before,
              "biological_plants":int(frame["plant_id"].nunique()),
              "ecotypes":sorted(str(v) for v in frame["ecotype"].unique()),
              "observations":len(frame),"prior_relabelled_swap_rejections":0,
              "conditions":{},"trajectory_pairs":pairs,
              "provider_calls":0,"gpu_calls":0,"live_qualification_trials":0,
              "limitations":["Historical model predictions, not independent biological gold.",
              "Constructed source misassociation, not observed pipeline failure frequency.",
              "Trajectory exchange is a separate hypothetical stress test; its artifacts were not revalidated in this run.",
              "Changed significance decisions are sensitivity diagnostics, not tests of biological truth or treatment effect."]}
    with tempfile.TemporaryDirectory(prefix="pg_consequence_") as td:
        tmp = Path(td)/"phenotypes.csv"
        original = summarize(frame,tmp)
        result["original"]=original
        for name,mapping in (("prior_image_id_rotation",rotation),("matched_cross_ecotype_trajectory_swap",trajectory)):
            swapped,stats = apply(frame,mapping)
            summary = summarize(swapped,tmp)
            changes = {}
            for key in original["tukey_pairs"]:
                a,b=original["tukey_pairs"][key],summary["tukey_pairs"][key]
                if a["significant"]!=b["significant"]:
                    changes[key]={"original":a,"swapped":b}
            result["conditions"][name]={"swap_metrics":stats,"conclusions":summary,
                "interaction_significance_changed":original["interaction"]["significant"]!=summary["interaction"]["significant"],
                "tukey_significance_changes":changes,
                "ecotype_rank_changed":{k:original["ecotype_ranks"][k]!=summary["ecotype_ranks"][k] for k in original["ecotype_ranks"]}}
    if before != {str(p.relative_to(ROOT)):sha256_file(p) for p in inputs}:
        raise ValueError("historical inputs changed")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    out=args.output.resolve()
    if not out.is_relative_to((ROOT/"data/_staging").resolve()) or out.exists() or args.output.is_symlink():
        raise ValueError("new private staging output required")
    result=run()
    with os.fdopen(os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as f:
        json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
        f.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k!="trajectory_pairs"},indent=2,sort_keys=True,allow_nan=False))
    print("TRAJECTORY_PAIRS="+str(len(result["trajectory_pairs"])))
    print("SCIENTIFIC_CONSEQUENCE_REPORT_SHA256="+sha256_file(out))
    print("SCIENTIFIC_CONSEQUENCE_REPLAY_COMPLETED=true")


if __name__=="__main__":
    main()
