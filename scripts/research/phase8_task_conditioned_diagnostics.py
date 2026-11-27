"""Post-hoc task-conditioned diagnostics, not a proposed agent or new method.
Use the already scored, hash-bound reference outputs only. No threshold fitting,
provider calls, GPU inference, or independent validation claims.
"""
from __future__ import annotations
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.research import phase8_saved_prediction_credibility as prev
OUT=prev.ST/"phase8_task_conditioned_diagnostics_v0.1.json"
PREV_SHA="cbad6b8514cc18b6472d66d52aa86a6c5d1da958189be4eed84043379b77bda4"
# Descriptive cutoffs already reported in previous analysis; no selection from outcomes.
AREA=(.1,.25)
COUNT=(1,2)

def mean(xs): return float(np.mean(xs)) if len(xs) else None

def contingency(rows,a,c):
    counts={"both_within":0,"area_only_within":0,"count_only_within":0,"neither_within":0}
    for r in rows:
        m=r["metrics"]
        x=m["projected_area_relative_error"]<=a
        y=m["count_absolute_error"]<=c
        counts["both_within" if x and y else "area_only_within" if x else "count_only_within" if y else "neither_within"]+=1
    return {**counts,"n":len(rows),"discordant":counts["area_only_within"]+counts["count_only_within"]}

def summarize(rows):
    n=len(rows)
    return {"n":n,"threshold_grid":{f"area_le_{a}_count_le_{c}":contingency(rows,a,c) for a in AREA for c in COUNT},
            "mean_signed_count_error":mean([r["metrics"]["predicted_instances"]-r["metrics"]["reference_instances"] for r in rows]),
            "mean_signed_relative_area_error":mean([(r["metrics"]["projected_union_area_px"]-r["metrics"]["reference_union_area_px"])/r["metrics"]["reference_union_area_px"] for r in rows])}

def task_risk(rows,key):
    # Existing confidence ranking, ties included; no test-label threshold optimization.
    ranked=sorted(rows,key=lambda r:r[key] if r[key] is not None else -1,reverse=True)
    out=[]
    for f in (1,.75,.5,.25):
        k=max(1,math.ceil(f*len(rows)))
        v=ranked[k-1][key]
        cutoff=v if v is not None else -1
        kept=[r for r in ranked if (r[key] if r[key] is not None else -1)>=cutoff]
        d=contingency(kept,.1,2)
        out.append({"target_fraction":f,"actual_coverage":len(kept)/len(rows),"kept":len(kept),
                    "area_error_rate":(d["count_only_within"]+d["neither_within"])/len(kept),
                    "count_error_rate":(d["area_only_within"]+d["neither_within"])/len(kept),
                    "both_task_error_rate":d["neither_within"]/len(kept),
                    "either_task_error_rate":1-d["both_within"]/len(kept)})
    return out

def direction(x): return 1 if x>0 else -1 if x<0 else 0

def temporal(rows):
    plants=defaultdict(dict)
    for r in rows:
        key=(r["genotype"],r["replicate"])
        if r["time_bin"] in plants[key]: raise ValueError("duplicate timepoint")
        plants[key][r["time_bin"]]=r["metrics"]
    if len(plants)!=63 or any(set(v)!={"early","middle","late"} for v in plants.values()):
        raise ValueError("incomplete plant inventory")
    result={}
    for start,end in (("early","middle"),("middle","late"),("early","late")):
        vals=[]
        for v in plants.values():
            a,b=v[start],v[end]
            # Signed change in visible foreground pixels, normalized by initial
            # reference area. Not physical growth, unless acquisition calibrated.
            ar=b["reference_union_area_px"]-a["reference_union_area_px"]
            ap=b["projected_union_area_px"]-a["projected_union_area_px"]
            cr=b["reference_instances"]-a["reference_instances"]
            cp=b["predicted_instances"]-a["predicted_instances"]
            vals.append({"area_change_abs_error_normalized_initial":abs(ap-ar)/a["reference_union_area_px"],
                         "count_change_abs_error":abs(cp-cr),
                         "area_direction_correct":direction(ar)==direction(ap),
                         "count_direction_correct":direction(cr)==direction(cp),
                         "reference_area_no_change":ar==0,"reference_count_no_change":cr==0,
                         "area_change_error_above_10pct_initial":abs(ap-ar)/a["reference_union_area_px"]>.1,
                         "count_change_error_above_2":abs(cp-cr)>2,
                         "endpoint_area_both_within_10pct":max(a["projected_area_relative_error"],b["projected_area_relative_error"])<=.1,
                         "endpoint_count_both_within_2":max(a["count_absolute_error"],b["count_absolute_error"])<=2})
        result[start+"_to_"+end]={"n_plants":len(vals),
            "mean_normalized_area_change_error":mean([v["area_change_abs_error_normalized_initial"] for v in vals]),
            "median_normalized_area_change_error":float(np.median([v["area_change_abs_error_normalized_initial"] for v in vals])),
            "mean_absolute_count_change_error":mean([v["count_change_abs_error"] for v in vals]),
            **{k:sum(v[k] for v in vals) for k in ("area_direction_correct","count_direction_correct","reference_area_no_change","reference_count_no_change","area_change_error_above_10pct_initial","count_change_error_above_2")},
            "area_endpoints_within_but_change_error":sum(v["endpoint_area_both_within_10pct"] and v["area_change_error_above_10pct_initial"] for v in vals),
            "count_endpoints_within_but_change_error":sum(v["endpoint_count_both_within_2"] and v["count_change_error_above_2"] for v in vals)}
    return result

def main():
    os.umask(0o077)
    if OUT.exists(): raise FileExistsError("preserve original report")
    prev.checked(prev.OUT,PREV_SHA)
    if prev.sha(Path(prev.__file__))!="9bc0b88cd575ad190e97b897a531184b9d43cbdd3edcf610e546e6062926e3dc":
        raise ValueError("credibility source drift")
    rows=[r for r in prev.gather() if r["applicable"]]
    if len(rows)!=221 or any(r["state"]!="SUCCEEDED" or not r["metrics"]["structurally_accepted"] for r in rows):
        raise ValueError("applicable inventory drift")
    groups={g:[r for r in rows if r["cohort"]==g] for g,*_ in prev.SOURCES}
    report={"scope":"EXPLORATORY_TASK_SPECIFIC_ERROR_DISCORDANCE_NOT_AGENT_EFFICACY",
            "credibility_report_sha256":PREV_SHA,"source_report_sha256":{x[0]:x[3] for x in prev.SOURCES},
            "script_sha256":prev.sha(Path(__file__)),
            "groups":{g:{**summarize(rs),"confidence_task_risk":{k:task_risk(rs,k) for k in ("score_mean","score_min")}} for g,rs in groups.items()},
            "pooled_descriptive":summarize(rows),
            "arabidopsis_projected_pixel_and_visible_instance_change":temporal(groups["arabidopsis"]),
            "limitations":["Thresholds are exploratory, not reviewer-approved scientific tolerances.",
              "Discordance is an observed difference in task errors; no policy detects it yet.",
              "Pixel area changes may reflect camera/crop/acquisition differences; not physical growth.",
              "Direction uses exact sign, including zero; no biological minimum change threshold.",
              "Repeated frames correlated; no independent validation or intervention evidence."],
            "gpu_calls":0,"provider_calls":0,"registered_agent_trials":0}
    with OUT.open("x") as f: json.dump(report,f,indent=2,allow_nan=False); f.write("\n")
    print(json.dumps(report,indent=2,allow_nan=False))
    print("TASK_DIAGNOSTICS_SHA256="+prev.sha(OUT))

if __name__=="__main__": main()
