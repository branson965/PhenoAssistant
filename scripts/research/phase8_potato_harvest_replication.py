"""Prospective same-dataset expansion, excluding eight observed pilot plants.

Use the original harvest table and all uniquely identified annotated harvest
plants, not a sample selected using model results. Existing canonical pilot
inference and annotation evaluator are reused without editing either. This
is direct-model evidence, not approved registered agent trials.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from PIL import Image,ImageDraw
from scripts.research import phase8_potato_cross_capability_pilot as pilot
from scripts.research import phase8_potato_annotation_eval as ann

OLD=pilot.STAGING
OUT=ROOT/"data/_staging/potato_harvest_replication_v0.1"
OLD_MANIFEST="1efb97145e19bb51eaab0da0d12cecb479e675c5aaa21b4396cf181cb36ce691"
OLD_AUDIT="1e473486b8b9c89a004daf7c63c2b98630988262f335c41d45cfd52bbfe629ed"
OLD_SCORE="9d33a16210869128d6b2d1bf86d626ed89b694c369238a1648474c03f6e03361"
OLD_UTILITY="449320ca3067d6d615d03f9f265654ee4858e6803ee7555feec8dfa87adef7e3"
sha=pilot.file_sha256
write=pilot.write
MODELS=pilot.MODELS

def old_identity():
    for path,digest in (("manifest.json",OLD_MANIFEST),("annotation_eval_v0.1/audit.json",OLD_AUDIT),
                        ("annotation_eval_v0.1/report.json",OLD_SCORE),("report.json",OLD_UTILITY)):
        if sha(OLD/path)!=digest: raise ValueError("pilot identity drift: "+path)
    return pilot.manifest()

def sources():
    return {str(p.relative_to(ROOT)):sha(p) for p in (
        Path(__file__),Path(pilot.__file__),Path(ann.__file__),
        ROOT/"functions/instance_segmentation.py",ROOT/"functions/leaf_only_sam.py",
        ROOT/"functions/generic_tools.py",ROOT/"scripts/research/phase8_scientific_artifact_validator.py",
        ROOT/"scripts/research/phase8_viability_challenge.py")}

def plant_id(value):
    n=float(value)
    if not math.isfinite(n) or not n.is_integer(): raise ValueError("nonintegral plant ID")
    return str(int(n))

def prepare():
    import requests
    from urllib.parse import urlparse
    from concurrent.futures import ThreadPoolExecutor
    old=old_identity()
    if OUT.exists(): raise FileExistsError("preserve previous expansion directory")
    old_audit=json.loads((OLD/"annotation_eval_v0.1/audit.json").read_text())
    excluded_plants={plant_id(x["plant_no"]) for x in old_audit["source_measurements"]}
    excluded_names={Path(x["file_name"]).stem.upper() for x in old["cases"]}
    excluded_hashes={x["sha256"] for x in old["cases"]}
    source_path=OLD/"source_record.json"
    record=json.loads(source_path.read_text())
    meta=record["metadata"]
    if record["id"]!=7938231 or meta["doi"]!="10.5281/zenodo.7938231" or meta["license"]["id"]!="cc-by" or meta["access_right"]!="open":
        raise ValueError("unexpected source identity or rights")
    entries={f["key"].upper():f for f in record["files"]}
    if len(entries)!=len(record["files"]): raise ValueError("case-insensitive source filename collision")
    table_path=OLD/"original_references/pot_data_withimgnames_fullset.csv"
    table=pd.read_csv(table_path)
    ids=[plant_id(x) for x in table["Plant_no"]]
    counts=Counter(ids)
    local={p.name.upper():p for p in (ROOT/"data/PotatoLeaf").glob("*") if p.is_file()}
    candidates=[]
    excluded=[]
    for i,x in table.iterrows():
        ident=ids[i]
        names=re.findall(r"IMG_[0-9]+",str(x["harvest_img"]).upper())
        reason=None
        if ident in excluded_plants: reason="observed_pilot_plant"
        elif counts[ident]!=1: reason="nonunique_plant_id"
        elif len(names)!=1: reason="missing_or_ambiguous_harvest_image"
        elif names[0] in excluded_names: reason="observed_pilot_image"
        elif names[0]+".JPG" not in entries or names[0]+".JSON" not in entries: reason="no_original_image_annotation_pair"
        if reason:
            excluded.append({"plant_no":ident,"reason":reason}); continue
        candidates.append({"plant_no":ident,"tray":plant_id(x["Tray"]),"variety":str(x["Variety"]),
            "stem":names[0],"manual_leaf_area":None if pd.isna(x["Leaf area on harvest"]) else float(x["Leaf area on harvest"]),
            "manual_dry_weight":None if pd.isna(x["Dried weight (7 days later)"]) else float(x["Dried weight (7 days later)"])})
    nc=Counter(x["stem"] for x in candidates)
    unique=[]
    for x in candidates:
        if nc[x["stem"]]!=1: excluded.append({"plant_no":x["plant_no"],"reason":"duplicate_harvest_filename"})
        else: unique.append(x)
    candidates=sorted(unique,key=lambda x:(int(x["tray"]),int(x["plant_no"]),x["stem"]))
    if not candidates or len(candidates)>110: raise ValueError("unexpected candidate count")
    total=sum(int(entries[x["stem"]+ext]["size"]) for x in candidates for ext in (".JPG",".JSON"))
    if total>1_500_000_000: raise ValueError("bounded acquisition size exceeded")
    OUT.mkdir(mode=0o700,parents=True)
    (OUT/"images").mkdir(mode=0o700)
    (OUT/"original_references").mkdir(mode=0o700)
    print(f"SOURCE_CANDIDATES={len(candidates)} DECLARED_BYTES={total}",flush=True)
    def acquire(entry,target,existing=None):
        size=int(entry["size"])
        if not 0<size<=32*1024*1024: raise ValueError("unexpected source file size")
        if existing is not None: raw=existing.read_bytes()
        else:
            url=entry["links"]["self"]
            parsed=urlparse(url)
            if parsed.scheme!="https" or parsed.hostname!="zenodo.org": raise ValueError("unexpected download host")
            with requests.get(url,timeout=(20,120),stream=True) as response:
                response.raise_for_status()
                blocks=[]; received=0
                for block in response.iter_content(65536):
                    received+=len(block)
                    if received>size: raise ValueError("source response too long")
                    blocks.append(block)
                raw=b"".join(blocks)
        if len(raw)!=size or "md5:"+hashlib.md5(raw).hexdigest()!=entry["checksum"]:
            raise ValueError("source checksum mismatch: "+entry["key"])
        if existing is not None: return existing
        with target.open("xb") as f: f.write(raw)
        return target
    def download(x):
        image_entry=entries[x["stem"]+".JPG"]
        ref_entry=entries[x["stem"]+".JSON"]
        image=acquire(image_entry,OUT/"images"/image_entry["key"],local.get(image_entry["key"].upper()))
        ref=acquire(ref_entry,OUT/"original_references"/image.with_suffix(".json").name)
        return x,image,ref
    # Download failure stops preparation; never reinterpret it as missing gold.
    with ThreadPoolExecutor(max_workers=3) as pool:
        downloaded=list(pool.map(download,candidates))
    cases=[]; infos=[]; previews=[]; seen_hash=set()
    ann.STAGING=OUT
    ann.COUNTS=[]
    for x,image,ref in downloaded:
        digest=sha(image)
        if digest in excluded_hashes or digest in seen_hash:
            excluded.append({"plant_no":x["plant_no"],"reason":"duplicate_or_observed_image_content"}); continue
        doc=json.loads(ref.read_text())
        shapes=doc.get("shapes")
        if not isinstance(shapes,list) or not shapes:
            excluded.append({"plant_no":x["plant_no"],"reason":"no_nonempty_polygon_reference"}); continue
        if any(s.get("label")!="leaf" or s.get("shape_type")!="polygon" or s.get("group_id") is not None or s.get("flags") for s in shapes) or doc.get("flags"):
            excluded.append({"plant_no":x["plant_no"],"reason":"unsupported_annotation_semantics"}); continue
        with Image.open(image) as im: dims=list(im.size)
        c={**x,"case":len(cases)+1,"file_name":str(image.relative_to(ROOT)),
           "sha256":digest,"dimensions":dims,"annotation_file":ref.name,"annotation_sha256":sha(ref),
           "source_image_md5":entries[x["stem"]+".JPG"]["checksum"],"source_annotation_md5":entries[x["stem"]+".JSON"]["checksum"]}
        ann.COUNTS.append(len(shapes))
        try: info,_,_,preview=ann.reference(c,True)
        except ValueError as exc:
            ann.COUNTS.pop()
            excluded.append({"plant_no":x["plant_no"],"reason":"annotation_geometry_ineligible","detail":str(exc)}); continue
        seen_hash.add(digest); cases.append(c); infos.append(info); previews.append(preview)
    if not cases: raise ValueError("no eligible reference cases")
    sheets=[]
    for start in range(0,len(cases),12):
        sheet=Image.new("RGB",(1200,4*320),"white"); d=ImageDraw.Draw(sheet)
        for j,(c,im) in enumerate(zip(cases[start:start+12],previews[start:start+12])):
            im.thumbnail((380,275))
            x,y=(j%3)*400,(j//3)*320
            sheet.paste(im,(x+(400-im.width)//2,y+5))
            d.text((x+8,y+286),f"Case {c['case']} | Plant {c['plant_no']} | Tray {c['tray']}",fill="black")
            d.text((x+8,y+302),c["stem"],fill="black")
        p=OUT/f"overlay_{start//12+1:02d}.png"; sheet.save(p)
        sheets.append({"file":p.name,"sha256":sha(p)})
    receipt={"source_rows":len(table),"source_candidates":len(candidates),"eligible_cases":len(cases),
             "excluded":excluded,"reference_cases":infos,"overlays":sheets,
             "visual_independent_approval":False}
    write(OUT/"reference_audit.json",receipt)
    manifest={"scope":"DIRECT_SAME_DATASET_REPLICATION_NOT_AGENT_QUALIFICATION",
              "pilot_manifest_sha256":OLD_MANIFEST,"pilot_audit_sha256":OLD_AUDIT,
              "source_record_sha256":sha(source_path),"source_table_sha256":sha(table_path),
              "reference_audit_sha256":sha(OUT/"reference_audit.json"),
              "source_files":sources(),"method_freeze":old["method_freeze"],"models":MODELS,
              "ara_snapshot_files":old["ara_snapshot_files"],"sam_sha256":old["sam_sha256"],
              "cases":cases,"reference_counts":ann.COUNTS,"primary":"paired macro foreground IoU",
              "secondary":"Dice, count error, union area relative error, instance F1 at .5, XOR area, physical correlations",
              "selection":"all uniquely matched annotated harvest plants excluding pilot plants and image content; eligibility determined before inference",
              "limitations":"same dataset, possible model development overlap, shared trays; no independent expert adjudication or agent efficacy"}
    write(OUT/"manifest.json",manifest)
    print(json.dumps({"eligible_cases":len(cases),"cells":2*len(cases),"excluded_reasons":dict(Counter(x["reason"] for x in excluded)),
        "by_tray":dict(Counter(x["tray"] for x in cases)),"new_source_images":sum(str(x["file_name"]).startswith(str((OUT/"images").relative_to(ROOT))) for x in cases),
        "manifest_sha256":sha(OUT/"manifest.json"),"overlays":sheets},indent=2))
    print("REPLICATION_PREPARED=true",flush=True)

def checked(expected):
    if sha(OUT/"manifest.json")!=expected: raise ValueError("manifest SHA differs")
    m=json.loads((OUT/"manifest.json").read_text())
    count,freeze=pilot.verify_manifest()
    if m["method_freeze"]!={"count":count,"sha256":freeze} or m["source_files"]!=sources() or sha(OUT/"reference_audit.json")!=m["reference_audit_sha256"]:
        raise ValueError("replication source or method drift")
    if sha(OLD/"manifest.json")!=OLD_MANIFEST or sha(OLD/"source_record.json")!=m["source_record_sha256"] or sha(OLD/"original_references/pot_data_withimgnames_fullset.csv")!=m["source_table_sha256"]:
        raise ValueError("historical source drift")
    return m

def run(case,expected):
    m=checked(expected)
    c=next(x for x in m["cases"] if x["case"]==case)
    if sha(OUT/"original_references"/c["annotation_file"])!=c["annotation_sha256"]: raise ValueError("reference changed")
    pilot.STAGING=OUT
    pilot.manifest=lambda: checked(expected)
    pilot.run_case(case)

def score(expected):
    m=checked(expected)
    audit=json.loads((OUT/"reference_audit.json").read_text())
    ann.STAGING=OUT; ann.COUNTS=m["reference_counts"]
    for overlay in audit["overlays"]:
        if sha(OUT/overlay["file"])!=overlay["sha256"]: raise ValueError("overlay drift")
    terminals={}
    for c in m["cases"]:
        for name in MODELS:
            target=OUT/f"tray_{c['case']:02d}"/name
            p=target/"terminal.json"
            # No scoring until every planned cell has a terminal record.
            t=json.loads(p.read_text())
            if t["case"]!=c["case"] or t["model"]!=name or t["manifest_sha256"]!=expected or t["image_sha256"]!=c["sha256"] or t["state"] not in ("FAILED","SUCCEEDED"):
                raise ValueError("terminal identity differs")
            terminals[c["case"],name]=(t,target)
    rows=[]
    for c in m["cases"]:
        if sha(OUT/"original_references"/c["annotation_file"])!=c["annotation_sha256"]: raise ValueError("reference changed")
        info,gt,gu,_=ann.reference(c)
        if info!=audit["reference_cases"][c["case"]-1]: raise ValueError("reference geometry drift")
        row={"case":c["case"],"plant_no":c["plant_no"],"tray":c["tray"],"variety":c["variety"],
             "manual_leaf_area":c["manual_leaf_area"],"manual_dry_weight":c["manual_dry_weight"],"models":{}}
        for name in MODELS:
            t,target=terminals[c["case"],name]
            e={"state":t["state"],"terminal_sha256":sha(target/"terminal.json"),"metrics":None}
            if t["state"]=="SUCCEEDED":
                try: e["metrics"]=ann.evaluate_one(c,info,gt,gu,name,t,target)
                except (ValueError,KeyError,TypeError) as exc: e["evaluation_failure"]=str(exc)
            row["models"][name]=e
        rows.append(row)
    common=[r for r in rows if all(r["models"][n]["metrics"] is not None for n in MODELS)]
    keys=["foreground_iou","dice","count_absolute_error","projected_area_relative_error","instance_f1_at_50"]
    summaries={}
    for name in MODELS:
        own=[r["models"][name]["metrics"] for r in rows if r["models"][name]["metrics"] is not None]
        paired=[r["models"][name]["metrics"] for r in common]
        summaries[name]={"registered":len(rows),"successful":sum(r["models"][name]["state"]=="SUCCEEDED" for r in rows),
            "scorable":len(own),"structural_accepted":sum(x["structurally_accepted"] for x in own),
            "empty":sum(x["predicted_instances"]==0 for x in own),
            "macro_joint":{k:float(np.mean([x[k] for x in paired])) if paired else None for k in keys},
            "median_joint_area_relative_error":float(np.median([x["projected_area_relative_error"] for x in paired])) if paired else None,
            "failure_zero_utility_iou":sum(x["foreground_iou"] for x in own)/len(rows),
            "physical_associations":{}}
        from scipy.stats import pearsonr,spearmanr
        for ref in ("manual_leaf_area","manual_dry_weight"):
            eligible=[r for r in common if r[ref] is not None and math.isfinite(r[ref]) and r[ref]>0]
            for measure in ("projected_union_area_px","historical_xor_area_px"):
                a=[r["models"][name]["metrics"][measure] for r in eligible]; b=[r[ref] for r in eligible]
                corr=None
                if len(a)>=3 and len(set(a))>1 and len(set(b))>1:
                    corr={"pearson_r":float(pearsonr(a,b)[0]),"spearman_rho":float(spearmanr(a,b)[0])}
                summaries[name]["physical_associations"][measure+"_vs_"+ref]={"n":len(a),"correlations":corr}
    deltas=[r["models"]["potato_sam"]["metrics"]["foreground_iou"]-r["models"]["arabidopsis_mask2former"]["metrics"]["foreground_iou"] for r in common]
    by_tray={}
    for tray in sorted({r["tray"] for r in common}):
        ds=[d for r,d in zip(common,deltas) if r["tray"]==tray]
        by_tray[tray]={"n":len(ds),"mean_paired_iou_delta":float(np.mean(ds))}
    report={"scope":m["scope"],"manifest_sha256":expected,"registered_cells":2*len(rows),
        "jointly_scorable":len(common),"summaries":summaries,"paired_mean_iou_delta":float(np.mean(deltas)) if deltas else None,
        "paired_wins_sam":sum(d>0 for d in deltas),"paired_ties":sum(d==0 for d in deltas),
        "paired_losses_sam":sum(d<0 for d in deltas),"by_tray":by_tray,"rows":rows,
        "limitations":m["limitations"],"provider_calls":0,"registered_agent_trials":0}
    write(OUT/"report.json",report)
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2,allow_nan=False))
    print("REPLICATION_REPORT_SHA256="+sha(OUT/"report.json"))

def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["prepare","run","score"])
    p.add_argument("--manifest-sha")
    p.add_argument("--case",type=int)
    a=p.parse_args()
    if a.action=="prepare": prepare()
    else:
        if not a.manifest_sha: p.error("--manifest-sha required")
        if a.action=="run":
            if a.case is None: p.error("--case required")
            run(a.case,a.manifest_sha)
        else: score(a.manifest_sha)

if __name__=="__main__": main()
