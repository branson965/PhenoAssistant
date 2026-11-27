"""Exploratory post-hoc CPU analysis of frozen direct-model reports.
No fitted thresholds, inference, provider calls, or alteration of source runs.
Thresholds are descriptive diagnostics, not biological acceptance standards.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
ST=ROOT/"data/_staging"
OUT=ST/"phase8_saved_prediction_credibility_v0.1.json"
SOURCES=[
 ("potato_pilot","potato_cross_capability_pilot_v0.1","annotation_eval_v0.1/report.json",
  "9d33a16210869128d6b2d1bf86d626ed89b694c369238a1648474c03f6e03361","1efb97145e19bb51eaab0da0d12cecb479e675c5aaa21b4396cf181cb36ce691",8,"potato_sam"),
 ("potato_replication","potato_harvest_replication_v0.1","report.json",
  "fbca7856f8281977a5d204a2becf5b93c22993097ad4fe62dc9b93317bbce77d","ba98804c64a040b8fbc164fd40e66319b6696a52c811c78febb197a77eb13d71",24,"potato_sam"),
 ("arabidopsis","phenoleaf_ts_reciprocal_v0.1","report.json",
  "9be2b13316325f0959db50e5361b0d06ad39fd2469101615006c4a87ca78be5d","b3461d3eb709987adac3e3126d6f5fc8970dcba50c3d0808bc02c45023fb4d93",189,"arabidopsis_mask2former"),
]
MODELS=("potato_sam","arabidopsis_mask2former")

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def checked(p,digest):
    if sha(p)!=digest: raise ValueError("hash drift: "+str(p))
    return json.loads(p.read_text())

def mean(v):
    return float(np.mean(v)) if len(v) else None

def gather():
    rows=[]
    for cohort,folder,report_path,report_sha,manifest_sha,n,applicable in SOURCES:
        base=ST/folder
        report=checked(base/report_path,report_sha)
        manifest=checked(base/"manifest.json",manifest_sha)
        cases={c["case"]:c for c in manifest["cases"]}
        if len(cases)!=n or len(report["rows"])!=n or set(cases)!={r["case"] for r in report["rows"]}:
            raise ValueError("case inventory mismatch")
        for row in report["rows"]:
            c=cases[row["case"]]
            for model in MODELS:
                target=base/f"tray_{c['case']:02d}"/model
                p=target/"terminal.json"
                e=row["models"][model]
                t=checked(p,e["terminal_sha256"]) if "terminal_sha256" in e else json.loads(p.read_text())
                if t["manifest_sha256"]!=manifest_sha or t["image_sha256"]!=c["sha256"] or t["model"]!=model or t["case"]!=c["case"] or t["state"]!=e.get("state",e.get("inference_state")):
                    raise ValueError("terminal mismatch")
                m=e["metrics"]
                d={"cohort":cohort,"case":c["case"],"model":model,"applicable":model==applicable,
                   "genotype":row.get("genotype"),"replicate":row.get("replicate"),"time_bin":row.get("time_bin"),
                   "state":t["state"],"failure":t.get("failure_message"),"metrics":m,
                   "score_mean":None,"score_min":None,"foreground_fraction":None,"overlap_fraction":None}
                if m is not None:
                    a=checked(target/t["artifact_path"],t["artifact_sha256"])
                    scores=[float(x["score"]) for x in a["annotations"]]
                    if len(scores)!=m["predicted_instances"] or any(not math.isfinite(s) or not 0<=s<=1 for s in scores):
                        raise ValueError("score/count drift")
                    if m["projected_union_area_px"]!=t["union_area_px"] or m["historical_xor_area_px"]!=t["historical_xor_area_px"]:
                        raise ValueError("area drift")
                    if scores:
                        d["score_mean"]=mean(scores); d["score_min"]=min(scores)
                    area=m["projected_union_area_px"]
                    d["foreground_fraction"]=area/(c["dimensions"][0]*c["dimensions"][1])
                    d["overlap_fraction"]=(area-m["historical_xor_area_px"])/area if area else None
                rows.append(d)
    if len(rows)!=442: raise ValueError("registered cell count differs")
    return rows

def summarize(rs):
    accepted=[r for r in rs if r["metrics"] is not None and r["metrics"]["structurally_accepted"]]
    ms=[r["metrics"] for r in accepted]
    n=len(rs)
    out={"attempted":n,"accepted":len(ms),"failed":sum(r["state"]=="FAILED" for r in rs),
         "accepted_iou_below":{str(t):sum(m["foreground_iou"]<t for m in ms) for t in (.5,.75,.9)},
         "accepted_area_relative_error_above":{str(t):sum(m["projected_area_relative_error"]>t for m in ms) for t in (.1,.25,.5)},
         "accepted_count_error_above_2":sum(m["count_absolute_error"]>2 for m in ms),
         "accepted_xor_loss_above_half":sum(r["overlap_fraction"] is not None and r["overlap_fraction"]>.5 for r in accepted),
         "accepted_macro_iou":mean([m["foreground_iou"] for m in ms]),
         "confidence_ranking":{}}
    # Rank within model and cohort only: SAM score is stability, not the
    # same quantity as Mask2Former score. Include ties at cutoffs.
    for key in ("score_mean","score_min"):
        ranked=sorted(accepted,key=lambda r:r[key] if r[key] is not None else -1,reverse=True)
        curve=[]
        for target in (1,.75,.5,.25):
            if not ranked: continue
            k=max(1,math.ceil(target*len(ranked)))
            cutoff=ranked[k-1][key]
            val=cutoff if cutoff is not None else -1
            kept=[r for r in ranked if (r[key] if r[key] is not None else -1)>=val]
            risk=mean([1-r["metrics"]["foreground_iou"] for r in kept])
            curve.append({"target_fraction_of_accepted":target,"kept":len(kept),"coverage_all_attempts":len(kept)/n,
                          "mean_iou_risk":risk,"bad_iou_below_half":sum(r["metrics"]["foreground_iou"]<.5 for r in kept),
                          "random_acceptance_expected_mean_risk":1-out["accepted_macro_iou"]})
        out["confidence_ranking"][key]=curve
    return out

def utility(r):
    return r["metrics"]["foreground_iou"] if r["metrics"] is not None else 0.

def main():
    os.umask(0o077)
    if OUT.exists(): raise FileExistsError("preserve original analysis")
    rows=gather()
    groups={}
    for cohort,*_ in SOURCES:
        groups[cohort]={model:summarize([r for r in rows if r["cohort"]==cohort and r["model"]==model]) for model in MODELS}
    pairs=defaultdict(dict)
    for r in rows: pairs[r["cohort"],r["case"]][r["model"]]=r
    routes={}
    for cohort in ["potato_pilot","potato_replication","arabidopsis"]:
        ps=[v for (g,c),v in pairs.items() if g==cohort]
        correct=[next(r for r in p.values() if r["applicable"]) for p in ps]
        wrong=[next(r for r in p.values() if not r["applicable"]) for p in ps]
        routes[cohort]={"frames":len(ps),"species_lookup_mean_utility":mean([utility(r) for r in correct]),
                        "always_sam_mean_utility":mean([utility(p["potato_sam"]) for p in ps]),
                        "always_mask2former_mean_utility":mean([utility(p["arabidopsis_mask2former"]) for p in ps]),
                        "oracle_best_of_two_mean_utility":mean([max(map(utility,p.values())) for p in ps]),
                        "species_lookup_wins":sum(utility(a)>utility(b) for a,b in zip(correct,wrong)),
                        "ties":sum(utility(a)==utility(b) for a,b in zip(correct,wrong))}
    plants=defaultdict(dict)
    for (g,c),p in pairs.items():
        if g!="arabidopsis": continue
        a=p["arabidopsis_mask2former"]; b=p["potato_sam"]
        key=(a["genotype"],a["replicate"])
        if a["time_bin"] in plants[key]: raise ValueError("duplicate time bin")
        plants[key][a["time_bin"]]=(a,b)
    if len(plants)!=63 or any(set(v)!={"early","middle","late"} for v in plants.values()):
        raise ValueError("trajectory inventory drift")
    complete=[v for v in plants.values() if all(r["metrics"] is not None for pair in v.values() for r in pair)]
    def temporal(vs):
        ds={k:[utility(v[k][0])-utility(v[k][1]) for v in vs] for k in ("early","middle","late")}
        return {"plants":len(vs),"mean_delta_by_bin":{k:mean(x) for k,x in ds.items()},
                "within_plant_late_minus_early_delta":mean([b-a for a,b in zip(ds["early"],ds["late"])]),
                "within_plant_gap_decreases":sum(b<a for a,b in zip(ds["early"],ds["late"])),
                "winner_switches":sum(len({np.sign(utility(a)-utility(b)) for a,b in v.values()})>1 for v in vs)}
    report={"scope":"POST_HOC_EXPLORATORY_SAVED_PREDICTIONS_NOT_INDEPENDENT_VALIDATION",
            "source_report_sha256":{x[0]:x[3] for x in SOURCES},"script_sha256":sha(Path(__file__)),
            "groups":groups,"species_lookup_vs_constant_and_oracle":routes,
            "temporal_complete_trajectories":temporal(complete),"temporal_all_plants_zero_utility":temporal(list(plants.values())),
            "limitations":["Outcome summaries known before analysis; no threshold optimization or independent confirmation.",
             "IoU/area cutoffs are descriptive sensitivity analyses, not expert-approved acceptance thresholds.",
             "Confidence rankings within model and cohort; SAM stability score is not calibrated correctness probability.",
             "Frame-level risk coverage descriptive; repeated frames clustered within plants.",
             "No agent calls, no intervention superiority, no proof of species causality."],
            "provider_calls":0,"gpu_calls":0,"registered_agent_trials":0}
    with OUT.open("x") as f: json.dump(report,f,indent=2,allow_nan=False); f.write("\n")
    print(json.dumps(report,indent=2,allow_nan=False))
    print("CREDIBILITY_REPORT_SHA256="+sha(OUT))

if __name__=="__main__": main()
