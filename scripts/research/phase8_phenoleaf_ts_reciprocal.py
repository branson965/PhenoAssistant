"""Private academic reciprocal experiment; no agent trials or redistribution.

Inspect linked terms, exact pairing and palette before prepare. Select at most
3 plants per genotype, 3 chronological positions per plant, without using masks
or predictions for selection. Preserve all source and execution identities.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import sys
import zipfile
from collections import Counter,defaultdict
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.research import phase8_potato_cross_capability_pilot as pilot
from scripts.research import phase8_potato_annotation_eval as ann
import numpy as np
from PIL import Image
from pycocotools import mask as mu
SRC=ROOT/"data/_staging/phenoleaf_ts_source_v0.1"
OUT=ROOT/"data/_staging/phenoleaf_ts_reciprocal_v0.1"
ARCH=SRC/"PhenoLeaf-TS_DS.zip"
INV_SHA="9f5acca765bf046461e702001ed3eae794027a471784fc6565a78660b36d0c92"
ARCH_SHA="608c7b07125281fb92517182c0873d1a9c87d696e2adedcb11c002173887de2f"
REV="ee4c8dac44593a69c8a72e1ca09d686133161d92"
README_SHA="3e3e103dd0c07d59dfb569d41cd12e51eb57cb430dc577c56070eb8eba196c34"
sha=pilot.file_sha256
write=pilot.write
MODELS=pilot.MODELS
PREFIX="PhenoLeaf-TS_DS"
SEED="phenoleaf-reciprocal-20261126-v1"

def inventory():
    if sha(SRC/"inventory.json")!=INV_SHA or sha(SRC/"README.md")!=README_SHA:
        raise ValueError("source inventory or author terms drift")
    inv=json.loads((SRC/"inventory.json").read_text())
    if inv["archive_sha256"]!=ARCH_SHA or inv["source"]["revision"]!=REV or not inv["full_archive_sha256_verified"] or ARCH.stat().st_size!=inv["source"]["size"]:
        raise ValueError("source acquisition identity mismatch")
    return inv

def split(inv):
    raw={}; labels={}
    for row in inv["members"]:
        p=PurePosixPath(row["path"])
        if p.suffix.lower()!=".png": continue
        if len(p.parts)!=5 or p.parts[0]!=PREFIX or p.parts[1] not in ("01_raw_dataset","02_leaf_labels"):
            raise ValueError("unrecognized PNG member structure: "+str(p))
        d=raw if p.parts[1]=="01_raw_dataset" else labels
        key=(p.parts[2],p.parts[3],p.stem)
        if key in d: raise ValueError("ambiguous PNG key")
        d[key]=row
    if len(raw)!=17082 or len(labels)!=17082: raise ValueError("source image count differs")
    return raw,labels

def inspect():
    from huggingface_hub import hf_hub_download
    inv=inventory()
    licence=Path(hf_hub_download("rick77a/PhenoLeaf_TS","LICENSE.md",repo_type="dataset",
                    revision=REV,local_dir=SRC,token=False))
    if licence.resolve()!=(SRC/"LICENSE.md").resolve() or not 0<licence.stat().st_size<=1024*1024:
        raise ValueError("unexpected linked licence file")
    print("=== PINNED LINKED LICENSE ===")
    print(licence.read_text(encoding="utf-8"))
    print("LICENSE_SHA256="+sha(licence))
    raw,labels=split(inv)
    groups=Counter(k[:2] for k in raw)
    print("=== PAIRING AND PLANT INVENTORY ===")
    print(json.dumps({"raw":len(raw),"labels":len(labels),"exact_stem_matches":len(raw.keys()&labels.keys()),
        "plant_sequences":len(groups),"genotypes":dict(Counter(k[0] for k in groups)),
        "raw_examples":list(raw)[:4],"label_examples":list(labels)[:4],
        "unmatched_raw_examples":sorted(raw.keys()-labels.keys())[:4],
        "unmatched_label_examples":sorted(labels.keys()-raw.keys())[:4]},indent=2))
    with zipfile.ZipFile(ARCH) as z:
        print("=== ARCHIVE README ===")
        print(z.read(PREFIX+"/README.md").decode("utf-8-sig"))
        print("=== PALETTE WORKBOOK ===")
        from openpyxl import load_workbook
        w=load_workbook(io.BytesIO(z.read(PREFIX+"/leaves_unique_colours.xlsx")),data_only=True,read_only=True)
        for ws in w:
            print("SHEET",ws.title,"ROWS",ws.max_row,"COLS",ws.max_column)
            for row in ws.iter_rows(max_row=min(ws.max_row,40),max_col=min(ws.max_column,12),values_only=True):
                print(repr(row))
        print("=== LABEL RGB SAMPLES ===")
        for key in sorted(labels)[:3]+sorted(labels)[len(labels)//2:len(labels)//2+3]:
            with Image.open(io.BytesIO(z.read(labels[key]["path"]))) as im:
                rgb=np.asarray(im.convert("RGB"))
                colours,counts=np.unique(rgb.reshape(-1,3),axis=0,return_counts=True)
                order=np.argsort(-counts)
                print(json.dumps({"key":key,"mode":im.mode,"dimensions":im.size,
                    "colours":[{"rgb":colours[i].tolist(),"pixels":int(counts[i])} for i in order[:35]],
                    "unique_colours":len(colours)}))
    print("INSPECTION_COMPLETE=true; NO INFERENCE OR EXTRACTION")

def sources():
    paths=[Path(__file__),Path(pilot.__file__),Path(ann.__file__),
           ROOT/"functions/instance_segmentation.py",ROOT/"functions/leaf_only_sam.py",
           ROOT/"functions/generic_tools.py",ROOT/"scripts/research/phase8_scientific_artifact_validator.py",
           ROOT/"scripts/research/phase8_viability_challenge.py"]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def timestamp(stem):
    match=re.search(r"(?<!\d)(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})(?!\d)",stem)
    if not match: raise ValueError("missing acquisition timestamp: "+stem)
    return dt.datetime.strptime(match.group(1),"%Y_%m_%d_%H_%M_%S").isoformat()

def colors_arg(value):
    values=value.split(",")
    if any(not re.fullmatch("[0-9a-fA-F]{6}",x) for x in values): raise ValueError("palette must be comma-separated six-digit RGB hex")
    rgb=[tuple(bytes.fromhex(x)) for x in values]
    if len(set(rgb))!=len(rgb): raise ValueError("duplicate colours")
    return rgb

def reference(c,palette,bg):
    p=OUT/"references"/c["reference_file"]
    if sha(p)!=c["reference_sha256"]: raise ValueError("reference hash drift")
    with Image.open(p) as im:
        if list(im.size)!=c["dimensions"] or im.getexif().get(274,1)!=1:
            raise ValueError("reference coordinate frame mismatch")
        if "A" in im.getbands() and np.any(np.asarray(im.getchannel("A"))!=255):
            raise ValueError("nonopaque mask not supported")
        rgb=np.asarray(im.convert("RGB"))
    observed={tuple(x) for x in np.unique(rgb.reshape(-1,3),axis=0)}
    if observed-set(palette)-{bg}: raise ValueError("reference contains non-palette colours")
    masks=[]
    for colour in sorted(observed-{bg}):
        b=np.all(rgb==colour,axis=-1)
        masks.append(mu.encode(np.asfortranarray(b.astype(np.uint8))))
    if not masks: return None
    union=mu.merge(masks)
    return {"annotation_dimensions":c["dimensions"],"exif_orientation":1,
            "reference_union_area_px":int(mu.area(union)),"reference_instances":len(masks)},masks,union

def prepare(args):
    inv=inventory()
    if OUT.exists(): raise FileExistsError("preserve existing experiment")
    if not args.reviewed_license_sha or sha(SRC/"LICENSE.md")!=args.reviewed_license_sha:
        raise ValueError("complete linked terms must be reviewed and hash acknowledged")
    if not args.palette or not args.background: raise ValueError("explicit reviewed palette/background required")
    palette=colors_arg(args.palette); bg=colors_arg(args.background)
    if len(palette)!=31 or len(bg)!=1 or bg[0] in palette: raise ValueError("expected 31 distinct leaf colours and separate background")
    bg=bg[0]
    if sha(ARCH)!=ARCH_SHA: raise ValueError("source archive bytes drift")
    raw,labels=split(inv)
    mapped={}
    for (g,p,s),row in labels.items():
        suffix=args.label_suffix
        if suffix and not s.endswith(suffix): raise ValueError("label suffix differs")
        key=(g,p,s[:-len(suffix)] if suffix else s)
        if key in mapped: raise ValueError("duplicate mapped label")
        mapped[key]=row
    if mapped.keys()!=raw.keys(): raise ValueError("image/label mapping is not bijective")
    groups=defaultdict(list)
    for k in raw:
        groups[k[:2]].append((timestamp(k[2]),k))
    genotypes=defaultdict(list)
    for g,p in groups: genotypes[g].append(p)
    if len(groups)!=318 or len(genotypes)!=21: raise ValueError("plant/genotype inventory differs from dataset paper")
    selected=[]
    excluded=[]
    for g,plants in sorted(genotypes.items()):
        # Deterministic, outcome-blind hash ordering of replicate identifiers.
        ranked=sorted(plants,key=lambda p:hashlib.sha256((SEED+"|"+g+"|"+p).encode()).hexdigest())
        for p in ranked[:3]:
            frames=sorted(groups[g,p])
            if len(frames)<3 or len(set(t for t,k in frames))!=len(frames):
                excluded.append({"genotype":g,"replicate":p,"reason":"insufficient_or_ambiguous_timepoints"}); continue
            for name,fraction in (("early",.2),("middle",.5),("late",.8)):
                idx=round(fraction*(len(frames)-1))
                t,k=frames[idx]
                selected.append({"genotype":g,"replicate":p,"time_bin":name,"frame_index":idx,"sequence_length":len(frames),
                                 "timestamp":t,"raw_member":raw[k],"label_member":mapped[k]})
    if not selected: raise ValueError("no selected frames")
    OUT.mkdir(mode=0o700,parents=True)
    (OUT/"images").mkdir(mode=0o700); (OUT/"references").mkdir(mode=0o700)
    write(OUT/"selection.json",{"seed":SEED,"selected":selected,"excluded_plant_sequences":excluded})
    old=pilot.manifest()
    cases=[]; issues=[]; seen=set()
    with zipfile.ZipFile(ARCH) as z:
        for idx,row in enumerate(selected,1):
            ip=OUT/"images"/f"case_{idx:03d}.png"; rp=OUT/"references"/ip.name
            for key,path in (("raw_member",ip),("label_member",rp)):
                entry=row[key]; member=z.getinfo(entry["path"])
                if member.file_size!=entry["size"] or f"{member.CRC:08x}"!=entry["crc32"] or not 0<member.file_size<=16*1024*1024:
                    raise ValueError("archive member identity/size mismatch")
                data=z.read(member) # zipfile verifies CRC
                with path.open("xb") as f: f.write(data)
            with Image.open(ip) as im:
                if im.getexif().get(274,1)!=1 or im.mode!="RGB":
                    raise ValueError("unexpected raw image mode/orientation")
                dims=list(im.size)
            c={**row,"case":idx,"file_name":str(ip.relative_to(ROOT)),"sha256":sha(ip),"dimensions":dims,
               "reference_file":rp.name,"reference_sha256":sha(rp)}
            if c["sha256"] in seen: raise ValueError("duplicate selected image content")
            seen.add(c["sha256"])
            try: r=reference(c,palette,bg)
            except ValueError as exc:
                issues.append({"case":idx,"reason":str(exc)}); continue
            if r is None:
                issues.append({"case":idx,"reason":"empty reference"}); continue
            c["reference_info"]=r[0]; cases.append(c)
    if not cases: raise ValueError("no eligible selected reference frames")
    m={"scope":"DIRECT_RECIPROCAL_ACADEMIC_EVALUATION_NOT_AGENT_TRIALS",
       "source_inventory_sha256":INV_SHA,"source_archive_sha256":ARCH_SHA,"source_revision":REV,
       "reviewed_linked_license_sha256":args.reviewed_license_sha,"redistribution_authorized":False,
       "selection_sha256":sha(OUT/"selection.json"),"selected_frames":len(selected),"excluded_references":issues,
       "sources":sources(),"method_freeze":old["method_freeze"],"models":MODELS,
       "ara_snapshot_files":old["ara_snapshot_files"],"sam_sha256":old["sam_sha256"],
       "palette":[list(x) for x in palette],"background":list(bg),"label_suffix":args.label_suffix,"cases":cases,
       "primary":"mean within-plant paired IoU difference Mask2Former minus SAM, equal weight per represented plant",
       "secondary":"frame macro IoU, Dice, count MAE, relative projected area error, instance F1, sequence bin and genotype summaries; zero utility sensitivity",
       "limitations":["Sequence quantiles, not validated biological growth stages.","Independent checkpoint training overlap not yet established.",
                       "Dataset and acquisition differ from potato; not isolated species causality.",
                       "No expert re-adjudication, no agent intervention evidence."]}
    write(OUT/"manifest.json",m)
    print(json.dumps({"selected_frames":len(selected),"eligible_frames":len(cases),"eligible_plants":len({(x["genotype"],x["replicate"]) for x in cases}),
        "genotypes":len({x["genotype"] for x in cases}),"by_time_bin":dict(Counter(x["time_bin"] for x in cases)),
        "excluded_references":issues,"array_cases":[x["case"] for x in cases],"planned_cells":2*len(cases),"manifest_sha256":sha(OUT/"manifest.json")},indent=2))
    print("RECIPROCAL_PREPARED=true")

def checked(expected):
    if sha(OUT/"manifest.json")!=expected: raise ValueError("manifest identity drift")
    m=json.loads((OUT/"manifest.json").read_text())
    n,freeze=pilot.verify_manifest()
    if m["sources"]!=sources() or m["method_freeze"]!={"count":n,"sha256":freeze} or sha(OUT/"selection.json")!=m["selection_sha256"] or sha(SRC/"LICENSE.md")!=m["reviewed_linked_license_sha256"]:
        raise ValueError("execution source or licence drift")
    return m

def run(case,expected):
    m=checked(expected)
    c=next(x for x in m["cases"] if x["case"]==case)
    if sha(OUT/"references"/c["reference_file"])!=c["reference_sha256"]: raise ValueError("reference drift")
    pilot.STAGING=OUT
    pilot.manifest=lambda:checked(expected)
    pilot.run_case(case)

def score(expected):
    m=checked(expected)
    terms={}
    for c in m["cases"]:
        for model in MODELS:
            target=OUT/f"tray_{c['case']:02d}"/model
            t=json.loads((target/"terminal.json").read_text())
            if t["case"]!=c["case"] or t["model"]!=model or t["manifest_sha256"]!=expected or t["image_sha256"]!=c["sha256"] or t["state"] not in ("FAILED","SUCCEEDED"):
                raise ValueError("terminal identity mismatch")
            terms[c["case"],model]=(t,target)
    rows=[]
    for c in m["cases"]:
        if sha(ROOT/c["file_name"])!=c["sha256"]: raise ValueError("input drift")
        info,gt,gu=reference(c,[tuple(x) for x in m["palette"]],tuple(m["background"]))
        if info!=c["reference_info"]: raise ValueError("reference geometry drift")
        row={k:c[k] for k in ("case","genotype","replicate","time_bin","timestamp")}
        row["models"]={}
        for model in MODELS:
            t,target=terms[c["case"],model]
            e={"state":t["state"],"metrics":None}
            if t["state"]=="SUCCEEDED":
                try: e["metrics"]=ann.evaluate_one(c,info,gt,gu,model,t,target)
                except (ValueError,KeyError,TypeError) as exc: e["evaluation_failure"]=str(exc)
            row["models"][model]=e
        rows.append(row)
    common=[r for r in rows if all(r["models"][n]["metrics"] is not None for n in MODELS)]
    def delta(r):
        return r["models"]["arabidopsis_mask2former"]["metrics"]["foreground_iou"]-r["models"]["potato_sam"]["metrics"]["foreground_iou"]
    def mean(v): return float(np.mean(v)) if len(v) else None
    def group_summary(rs):
        return {"frames":len(rs),"plants":len({(r["genotype"],r["replicate"]) for r in rs}),
                "mean_paired_delta_ara_minus_sam":mean([delta(r) for r in rs])}
    plants=defaultdict(list)
    for r in common: plants[(r["genotype"],r["replicate"])].append(delta(r))
    summaries={}
    keys=("foreground_iou","dice","count_absolute_error","projected_area_relative_error","instance_f1_at_50")
    for name in MODELS:
        own=[r["models"][name]["metrics"] for r in rows if r["models"][name]["metrics"] is not None]
        paired=[r["models"][name]["metrics"] for r in common]
        summaries[name]={"registered":len(rows),"successful":sum(r["models"][name]["state"]=="SUCCEEDED" for r in rows),
            "scorable":len(own),"structural_accepted":sum(x["structurally_accepted"] for x in own),
            "empty":sum(x["predicted_instances"]==0 for x in own),
            "macro_joint":{k:mean([x[k] for x in paired]) for k in keys},
            "zero_utility_iou_sensitivity":sum(x["foreground_iou"] for x in own)/len(rows)}
    report={"scope":m["scope"],"manifest_sha256":expected,"selected_frames":m["selected_frames"],
            "excluded_references":len(m["excluded_references"]),"registered_cells":2*len(rows),
            "jointly_scorable":len(common),"paired_plants":len(plants),
            "primary_equal_plant_mean_delta_ara_minus_sam":mean([mean(v) for v in plants.values()]),
            "frame_mean_delta_ara_minus_sam":mean([delta(r) for r in common]),
            "frame_wins_ara":sum(delta(r)>0 for r in common),"frame_ties":sum(delta(r)==0 for r in common),
            "frame_losses_ara":sum(delta(r)<0 for r in common),"summaries":summaries,
            "by_time_bin":{k:group_summary([r for r in common if r["time_bin"]==k]) for k in ("early","middle","late")},
            "by_genotype":{g:group_summary([r for r in common if r["genotype"]==g]) for g in sorted({r["genotype"] for r in rows})},
            "limitations":m["limitations"],"rows":rows,"provider_calls":0,"registered_agent_trials":0}
    write(OUT/"report.json",report)
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))
    print("RECIPROCAL_REPORT_SHA256="+sha(OUT/"report.json"))

def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["inspect","prepare","run","score"])
    p.add_argument("--reviewed-license-sha"); p.add_argument("--palette"); p.add_argument("--background")
    p.add_argument("--label-suffix",default=""); p.add_argument("--manifest-sha"); p.add_argument("--case",type=int)
    a=p.parse_args()
    if os.getenv("OPENROUTER_API_KEY"): raise ValueError("remove provider credential")
    if a.action=="inspect": inspect()
    elif a.action=="prepare": prepare(a)
    elif not a.manifest_sha: p.error("--manifest-sha required")
    elif a.action=="run":
        if a.case is None: p.error("--case required")
        run(a.case,a.manifest_sha)
    else: score(a.manifest_sha)

if __name__=="__main__": main()
