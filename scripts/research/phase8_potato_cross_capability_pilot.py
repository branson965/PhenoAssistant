"""Local direct-inference exploratory pilot, separate from registered agent trials.

Eight fixed tray representatives, both checkpoints on identical original bytes.
Manual total leaf area and dry weight are reference covariates, NOT pixel mask
gold or directly comparable projected area. No provider or hidden labels.
Prepare before inference; score only after all 16 terminal cell records exist.
"""
from __future__ import annotations
import argparse
import gc
import json
import math
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts.research.verify_phenoguard_method_freeze import verify_manifest
from phenoassistant_mcp.scientific_inference_v1 import file_sha256
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID as ARA,
    CASE2_POTATO_SEGMENTATION_MODEL_ID as POT,
    CASE1_ARABIDOPSIS_SEGMENTATION_REVISION as REV,
)
STAGING = ROOT/"data/_staging/potato_cross_capability_pilot_v0.1"
META = ROOT/"data/potato_metadata.csv"
SAM = ROOT/"models/sam_vit_h_4b8939.pth"
SAM_SHA = "a7bf3b02f3ebf1267aba913ff637d9a2d5c33d3173bb679e46d9f338c26f262e"
MODELS = {"potato_sam":POT,"arabidopsis_mask2former":ARA}

def write(path,obj):
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

def prepare():
    import pandas as pd
    import requests
    from PIL import Image
    from huggingface_hub import snapshot_download
    count,freeze=verify_manifest()
    if STAGING.exists():
        raise FileExistsError("preserve original pilot")
    r=requests.get("https://zenodo.org/api/records/7938231",timeout=(15,60))
    r.raise_for_status()
    record=r.json()
    meta=record["metadata"]
    lic=meta.get("license")
    if isinstance(lic,dict): lic=lic.get("id")
    if str(record["id"])!="7938231" or meta.get("doi")!="10.5281/zenodo.7938231" or str(lic).lower() not in {"cc-by-4.0","cc0-1.0","cc-by-3.0"}:
        raise ValueError("source licence/identity not confirmed; review original record before local pilot")
    # Outcome-blind ordering: one earliest filename per published tray.
    table=pd.read_csv(META,usecols=["file_name","Tray","Variety"])
    if len(table)!=32 or table.file_name.duplicated().any() or set(table.Tray)!=set(range(1,9)):
        raise ValueError("original potato inventory changed")
    chosen=table.sort_values("file_name").groupby("Tray",sort=True).first().reset_index()
    cases=[]
    for _,row in chosen.iterrows():
        image=(ROOT/row.file_name).resolve(strict=True)
        if not image.is_relative_to(ROOT/"data/PotatoLeaf"):
            raise ValueError("image outside original data")
        with Image.open(image) as im:
            im.load()
            dims=list(im.size)
        cases.append({"case":int(row.Tray),"file_name":str(row.file_name),
            "variety":str(row.Variety),"sha256":file_sha256(image),"dimensions":dims})
    snapshot=Path(snapshot_download(repo_id=ARA,revision=REV,local_files_only=True))
    if snapshot.name!=REV: raise ValueError("checkpoint revision drift")
    # Pin all actual cached checkpoint files, not merely directory name.
    files={p.relative_to(snapshot).as_posix():file_sha256(p)
           for p in sorted(snapshot.rglob("*")) if p.is_file()}
    if not {"config.json","preprocessor_config.json","label2id.json","id2label.json"}.issubset(files) or not any(n.endswith((".bin",".safetensors")) for n in files):
        raise ValueError("incomplete checkpoint")
    if file_sha256(SAM)!=SAM_SHA: raise ValueError("SAM SHA mismatch")
    STAGING.mkdir(mode=0o700,parents=True)
    write(STAGING/"source_record.json",record)
    manifest={"scope":"DIRECT_LOCAL_EXPLORATORY_PILOT_NOT_AGENT_QUALIFICATION",
        "source_doi":meta["doi"],"source_license":lic,"source_record_sha256":file_sha256(STAGING/"source_record.json"),
        "method_freeze":{"count":count,"sha256":freeze},"metadata_sha256":file_sha256(META),
        "runner_sha256":file_sha256(Path(__file__)),"models":MODELS,"ara_revision":REV,
        "ara_snapshot_files":files,"sam_sha256":SAM_SHA,"cases":cases,
        "selection":"first lexicographic filename per tray, independent of measurements",
        "note":"source record licence checked; existing repository image membership not independently compared to original archive; in-domain development pilot"}
    write(STAGING/"manifest.json",manifest)
    print(json.dumps({"cases":cases,"license":lic,"manifest_sha256":file_sha256(STAGING/"manifest.json")},indent=2))
    print("PILOT_PLANNED_CELLS=16 REGISTERED_AGENT_TRIALS=0")

def manifest():
    m=json.loads((STAGING/"manifest.json").read_text())
    count,freeze=verify_manifest()
    if m["method_freeze"]!={"count":count,"sha256":freeze} or m["metadata_sha256"]!=file_sha256(META) or m["runner_sha256"]!=file_sha256(Path(__file__)) or m["source_record_sha256"]!=file_sha256(STAGING/"source_record.json"):
        raise ValueError("pilot identity drift")
    return m

def run_case(case):
    import torch
    import numpy as np
    from PIL import Image
    from pycocotools import mask as masks
    from huggingface_hub import snapshot_download
    from functions.instance_segmentation import infer_instance_segmentation
    from scripts.research.phase8_scientific_artifact_validator import validate_coco
    from scripts.research.phase8_viability_challenge import rle_area
    if not os.environ.get("SLURM_JOB_ID") or not torch.cuda.is_available():
        raise ValueError("Slurm GPU allocation required")
    if os.environ.get("OPENROUTER_API_KEY"): raise ValueError("remove provider credential")
    m=manifest()
    row=next(x for x in m["cases"] if x["case"]==case)
    image=(ROOT/row["file_name"]).resolve(strict=True)
    if file_sha256(image)!=row["sha256"]: raise ValueError("image drift")
    snapshot=Path(snapshot_download(repo_id=ARA,revision=REV,local_files_only=True))
    files={p.relative_to(snapshot).as_posix():file_sha256(p) for p in sorted(snapshot.rglob("*")) if p.is_file()}
    if snapshot.name!=REV or files!=m["ara_snapshot_files"] or file_sha256(SAM)!=SAM_SHA:
        raise ValueError("checkpoint drift")
    # Alternating order by tray. No retries, including on failure.
    order=list(MODELS) if case%2 else list(reversed(MODELS))
    for name in order:
        target=STAGING/f"tray_{case:02d}"/name
        target.mkdir(mode=0o700,parents=True,exist_ok=False)
        result={"case":case,"model":name,"image_sha256":row["sha256"],
                "manifest_sha256":file_sha256(STAGING/"manifest.json"),
                "job_id":os.environ["SLURM_JOB_ID"],"gpu":torch.cuda.get_device_name(0),
                "state":"FAILED","artifact_sha256":None}
        started=time.monotonic()
        try:
            checkpoint=str(snapshot) if name=="arabidopsis_mask2former" else POT
            msg=infer_instance_segmentation(image_urls=[str(image)],checkpoint=checkpoint,
                       batch_size=1,device="cuda",output_dir=str(target))
            if not isinstance(msg,str) or msg.startswith("Error"):
                raise ValueError("inference error")
            path=target/("leaf_only_sam_results.json" if name=="potato_sam" else "ins_seg_results.json")
            result["artifact_sha256"]=file_sha256(path)
            obj=json.loads(path.read_text())
            if len(obj["images"])!=1 or obj["images"][0]["file_name"]!=str(image):
                raise ValueError("wrong image identity")
            im=obj["images"][0]
            w,h=im["width"],im["height"]
            if [w,h]!=row["dimensions"]: raise ValueError("output dimensions differ")
            verdict=validate_coco(path,expected_image_path=image)
            result["structural_validator_accepts"]=verdict.safe_to_report
            union=np.zeros((h,w),dtype=bool)
            parity=np.zeros((h,w),dtype=bool)
            total=0
            seen=set()
            for a in obj["annotations"]:
                seg=a["segmentation"]
                if a["image_id"]!=im["id"] or a["id"] in seen or seg["size"]!=[h,w]:
                    raise ValueError("annotation identity or shape mismatch")
                seen.add(a["id"])
                area=rle_area(h,w,seg["counts"])
                if area!=a["area"]: raise ValueError("mask area mismatch")
                binary=masks.decode({"size":[h,w],"counts":seg["counts"].encode("ascii")}).astype(bool)
                union|=binary
                parity^=binary
                total+=area
            result.update(state="SUCCEEDED",predicted_instances=len(seen),
                union_area_px=int(union.sum()),historical_xor_area_px=int(parity.sum()),
                sum_instance_area_px=int(total),image_area_px=w*h,
                artifact_path=path.name)
        except Exception as exc:
            result["failure_type"]=type(exc).__name__
            result["failure_message"]=str(exc)[:500]
        finally:
            result["elapsed_seconds"]=time.monotonic()-started
            write(target/"terminal.json",result)
            print(json.dumps(result,sort_keys=True),flush=True)
            gc.collect()
            torch.cuda.empty_cache()

def score():
    import pandas as pd
    import numpy as np
    from scipy.stats import spearmanr,pearsonr
    m=manifest()
    # No measurement-based selection, score only after all terminals.
    rows=[]
    for c in m["cases"]:
        for name in MODELS:
            target=STAGING/f"tray_{c['case']:02d}"/name
            p=target/"terminal.json"
            if not p.is_file(): raise ValueError("incomplete 16-cell pilot; no outcome scoring")
            row=json.loads(p.read_text())
            if row["case"]!=c["case"] or row["model"]!=name or row["image_sha256"]!=c["sha256"] or row["manifest_sha256"]!=file_sha256(STAGING/"manifest.json"):
                raise ValueError("terminal identity mismatch")
            if row["state"]=="SUCCEEDED" and file_sha256(target/row["artifact_path"])!=row["artifact_sha256"]:
                raise ValueError("artifact drift")
            rows.append(row)
    meta=pd.read_csv(META).set_index("file_name",verify_integrity=True)
    by={(r["case"],r["model"]):r for r in rows}
    common=[c for c in m["cases"] if all(by[c["case"],name]["state"]=="SUCCEEDED" for name in MODELS)]
    def corr(x,y):
        if len(x)<3 or len(set(x))<2 or len(set(y))<2: return None
        a,b=float(pearsonr(x,y)[0]),float(spearmanr(x,y)[0])
        return {"pearson_r":a,"spearman_rho":b} if math.isfinite(a) and math.isfinite(b) else None
    details=[]
    for c in common:
        a,b=by[c["case"],"potato_sam"],by[c["case"],"arabidopsis_mask2former"]
        label=meta.loc[c["file_name"]]
        details.append({"case":c["case"],"manual_leaf_area":float(label.manual_leaf_area),
            "manual_dried_weight":float(label.manual_dried_weight),"potato_sam":a,"arabidopsis_mask2former":b})
    summaries={}
    for name in MODELS:
        own=[r for r in rows if r["model"]==name]
        complete=[r for r in own if r["state"]=="SUCCEEDED"]
        stats={"registered":len(own),"successful":len(complete),"failed":len(own)-len(complete),
            "structurally_accepted_successes":sum(r["structural_validator_accepts"] for r in complete),
            "zero_instance_successes":sum(r["predicted_instances"]==0 for r in complete),
            "common_successful_pairs":len(common)}
        for measure in ("union_area_px","historical_xor_area_px"):
            for reference in ("manual_leaf_area","manual_dried_weight"):
                stats[measure+"_vs_"+reference]=corr([d[name][measure] for d in details],[d[reference] for d in details])
        summaries[name]=stats
    report={"scope":m["scope"],"manifest_sha256":file_sha256(STAGING/"manifest.json"),
            "summaries":summaries,"manual_area_vs_weight":corr([d["manual_leaf_area"] for d in details],[d["manual_dried_weight"] for d in details]),
            "paired_mean_absolute_union_area_difference_px":float(np.mean([abs(d["potato_sam"]["union_area_px"]-d["arabidopsis_mask2former"]["union_area_px"]) for d in details])) if details else None,
            "terminal_records":rows,"paired_details":details,"provider_calls":0,"registered_agent_trials":0,
            "limitations":["Eight selected trays, exploratory not independent benchmark.",
              "Manual total area/dry weight are reference covariates; pixel projected area is not identical to manual leaf area.",
              "No biological mask/count accuracy or intervention superiority claim.",
              "Native model preprocessing differs; entire capability comparison, not isolated species effect.",
              "Historical XOR area differs from union when masks overlap; both are reported.",
              "Source licence checked, repository bytes not compared against original archive; labels may have transcription issues.",
              "Descriptive correlation on jointly successful cases only; report failures separately."]}
    write(STAGING/"report.json",report)
    print(json.dumps({k:v for k,v in report.items() if k not in {"terminal_records","paired_details"}},indent=2,sort_keys=True))
    print("PILOT_REPORT_SHA256="+file_sha256(STAGING/"report.json"))

def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["prepare","run","score"])
    p.add_argument("--case",type=int,choices=range(1,9))
    args=p.parse_args()
    if args.action=="prepare": prepare()
    elif args.action=="run":
        if args.case is None: p.error("--case required")
        run_case(args.case)
    else: score()
if __name__=="__main__": main()
