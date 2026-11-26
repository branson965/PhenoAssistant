"""Original LabelMe annotation audit and predeclared paired evaluation.

Both existing inference functions use PIL.Image.open(...).convert("RGB") with
no EXIF transpose. Retain exact raw input bytes and transform predicted masks
losslessly into the EXIF-oriented annotation coordinates for scoring.
No new inference here; no changes to original pilot manifest or frozen method.
"""
from __future__ import annotations
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageOps
from scipy.optimize import linear_sum_assignment
from scipy.stats import pearsonr,spearmanr
from pycocotools import mask as mu
from scripts.research.phase8_potato_cross_capability_pilot import (
    STAGING, META, MODELS, manifest, write, file_sha256,
)
from scripts.research.phase8_viability_challenge import rle_area

EXPECTED_MANIFEST="1efb97145e19bb51eaab0da0d12cecb479e675c5aaa21b4396cf181cb36ce691"
OUT=STAGING/"annotation_eval_v0.1"
COUNTS=[7,7,6,4,12,7,7,1]
T=Image.Transpose
TRANSFORMS={1:None,2:T.FLIP_LEFT_RIGHT,3:T.ROTATE_180,4:T.FLIP_TOP_BOTTOM,
            5:T.TRANSPOSE,6:T.ROTATE_270,7:T.TRANSVERSE,8:T.ROTATE_90}
THRESHOLD=0.5

def checked_manifest():
    m=manifest()
    if file_sha256(STAGING/"manifest.json")!=EXPECTED_MANIFEST:
        raise ValueError("prepared pilot manifest differs")
    if [r["case"] for r in m["cases"]]!=list(range(1,9)):
        raise ValueError("case inventory differs")
    return m

def transform(im,orientation):
    op=TRANSFORMS[orientation]
    return im.transpose(op) if op is not None else im.copy()

def reference(c,preview=False):
    p=(ROOT/c["file_name"]).resolve(strict=True)
    if file_sha256(p)!=c["sha256"]: raise ValueError("source image drift")
    with Image.open(p) as raw:
        orientation=int(raw.getexif().get(274,1))
        if orientation not in TRANSFORMS: raise ValueError("unsupported EXIF orientation")
        if list(raw.size)!=c["dimensions"]: raise ValueError("raw dimensions drift")
        image=ImageOps.exif_transpose(raw).convert("RGB")
    a=STAGING/"original_references"/p.with_suffix(".json").name
    doc=json.loads(a.read_text())
    w,h=doc["imageWidth"],doc["imageHeight"]
    if doc["imagePath"]!=p.name or image.size!=(w,h):
        raise ValueError("EXIF-oriented image/annotation mismatch: "+p.name)
    if len(doc["shapes"])!=COUNTS[c["case"]-1] or doc.get("flags"):
        raise ValueError("unexpected annotation count/flags")
    instances=[]
    points=[]
    for shape in doc["shapes"]:
        if shape["label"]!="leaf" or shape["shape_type"]!="polygon" or shape["group_id"] is not None or shape.get("flags"):
            raise ValueError("unexpected annotation semantics")
        xy=[tuple(float(x) for x in pt) for pt in shape["points"]]
        if len(xy)<3 or any(len(pt)!=2 or not all(math.isfinite(x) for x in pt) for pt in xy):
            raise ValueError("invalid polygon")
        if any(not (0<=x<=w and 0<=y<=h) for x,y in xy):
            raise ValueError("polygon outside annotation frame")
        canvas=Image.new("L",(w,h),0)
        ImageDraw.Draw(canvas).polygon(xy,outline=1,fill=1)
        mask=np.asarray(canvas,dtype=np.uint8)
        if not mask.any(): raise ValueError("empty polygon")
        instances.append(mu.encode(np.asfortranarray(mask)))
        points.append(xy)
    union=mu.merge(instances)
    info={"case":c["case"],"image":p.name,"image_sha256":c["sha256"],
          "annotation_sha256":file_sha256(a),"exif_orientation":orientation,
          "raw_dimensions":c["dimensions"],"annotation_dimensions":[w,h],
          "embedded_image_present":bool(doc.get("imageData")),
          "polygon_instances":len(instances),"reference_union_area_px":int(mu.area(union))}
    if preview:
        image.thumbnail((480,340))
        scale_x=image.width/w
        scale_y=image.height/h
        d=ImageDraw.Draw(image)
        for xy in points:
            pts=[(x*scale_x,y*scale_y) for x,y in xy]
            d.line(pts+[pts[0]],fill="#ffcc00",width=2)
    return info,instances,union,image if preview else None

def measurement_rows(m):
    original=pd.read_csv(STAGING/"original_references/pot_data_withimgnames_fullset.csv")
    local=pd.read_csv(META).set_index("file_name",verify_integrity=True)
    results=[]
    for c in m["cases"]:
        stem=Path(c["file_name"]).stem.upper()
        # Only harvest_img is appropriate for harvest measurements.
        matches=original["harvest_img"].fillna("").astype(str).map(
            lambda s: stem in re.findall(r"IMG_[0-9]+",s.upper()))
        found=original.loc[matches]
        row={"case":c["case"],"harvest_image_matches":len(found),"source_measurements_usable":False}
        if len(found)==1:
            x=found.iloc[0]
            l=local.loc[c["file_name"]]
            same_tray=str(x["Tray"]).strip()==str(c["case"]) or str(x["Tray"]).strip()==str(float(c["case"]))
            same_variety=str(x["Variety"]).strip().casefold()==c["variety"].casefold()
            area=pd.to_numeric(x["Leaf area on harvest"],errors="coerce")
            weight=pd.to_numeric(x["Dried weight (7 days later)"],errors="coerce")
            row.update(plant_no=str(x["Plant_no"]),same_tray=same_tray,same_variety=same_variety)
            if same_tray and same_variety and pd.notna(area) and pd.notna(weight) and math.isfinite(float(area)) and math.isfinite(float(weight)) and area>0 and weight>0:
                row.update(source_measurements_usable=True,source_leaf_area=float(area),source_dry_weight=float(weight),
                           local_leaf_area=float(l.manual_leaf_area),local_dry_weight=float(l.manual_dried_weight),
                           local_area_matches=bool(math.isclose(float(area),float(l.manual_leaf_area),rel_tol=1e-9)),
                           local_weight_matches=bool(math.isclose(float(weight),float(l.manual_dried_weight),rel_tol=1e-9)))
        results.append(row)
    return results

def audit():
    m=checked_manifest()
    if OUT.exists() or any(STAGING.glob("tray_*")):
        raise ValueError("audit must precede all pilot inference")
    infos=[]
    sheet=Image.new("RGB",(1000,1600),"white")
    draw=ImageDraw.Draw(sheet)
    for c in m["cases"]:
        info,_,_,preview=reference(c,True)
        infos.append(info)
        i=c["case"]-1
        x,y=(i%2)*500,(i//2)*400
        sheet.paste(preview,(x+(500-preview.width)//2,y+15))
        draw.text((x+12,y+360),f"Tray {c['case']} | {info['image']} | EXIF {info['exif_orientation']}",fill="black")
        draw.text((x+12,y+378),f"{info['polygon_instances']} source polygons",fill="black")
    physical=measurement_rows(m)
    OUT.mkdir(mode=0o700)
    sheet.save(OUT/"annotation_overlay.png")
    receipt={"manifest_sha256":EXPECTED_MANIFEST,"evaluator_sha256":file_sha256(Path(__file__)),
             "cases":infos,"source_measurements":physical,
             "overlay_sha256":file_sha256(OUT/"annotation_overlay.png"),
             "rasterization":"PIL polygon outline and fill, full-resolution EXIF display frame",
             "instance_rule":"one ungrouped leaf polygon per reference instance; overlapping masks allowed",
             "primary_metric":"foreground IoU; macro mean on jointly successful pairs; failures separately and zero-utility sensitivity",
             "secondary_metrics":"Dice, count absolute error, projected union area absolute/relative error, IoU>=0.5 one-to-one matches",
             "independent_approval":False}
    write(OUT/"audit.json",receipt)
    print(json.dumps(receipt,indent=2))
    print("ANNOTATION_AUDIT_SHA256="+file_sha256(OUT/"audit.json"))
    print("OVERLAY="+str((OUT/"annotation_overlay.png").relative_to(ROOT)))
    print("ANNOTATION_COORDINATE_AUDIT_PASSED=true")

def evaluate_one(c,info,gt,gu,name,term,target):
    artifact=target/term["artifact_path"]
    if file_sha256(artifact)!=term["artifact_sha256"]: raise ValueError("artifact drift")
    obj=json.loads(artifact.read_text())
    raw=obj["images"][0]
    if len(obj["images"])!=1 or raw["file_name"]!=str((ROOT/c["file_name"]).resolve()) or [raw["width"],raw["height"]]!=c["dimensions"]:
        raise ValueError("artifact image binding differs")
    w,h=c["dimensions"]
    aw,ah=info["annotation_dimensions"]
    preds=[]
    seen=set()
    categories={a["id"]:str(a["name"]).strip().casefold() for a in obj["categories"]}
    for a in obj["annotations"]:
        if a["id"] in seen or a["image_id"]!=raw["id"] or categories.get(a["category_id"])!="leaf":
            raise ValueError("unexpected prediction identity/category")
        seen.add(a["id"])
        seg=a["segmentation"]
        if seg["size"]!=[h,w] or rle_area(h,w,seg["counts"])!=a["area"]:
            raise ValueError("invalid prediction mask")
        ar=mu.decode({"size":[h,w],"counts":seg["counts"].encode("ascii")})
        oriented=transform(Image.fromarray(ar),info["exif_orientation"])
        if oriented.size!=(aw,ah): raise ValueError("prediction orientation drift")
        preds.append(mu.encode(np.asfortranarray(np.asarray(oriented,dtype=np.uint8))))
    if len(preds)!=term["predicted_instances"]: raise ValueError("prediction count drift")
    pu=mu.merge(preds) if preds else mu.encode(np.asfortranarray(np.zeros((ah,aw),dtype=np.uint8)))
    pa,ga=int(mu.area(pu)),int(mu.area(gu))
    if pa!=term["union_area_px"] or ga!=info["reference_union_area_px"]:
        raise ValueError("union area differs after lossless orientation")
    inter=int(mu.area(mu.merge([pu,gu],intersect=True)))
    denom=pa+ga-inter
    iou=inter/denom
    dice=2*inter/(pa+ga)
    n,g=len(preds),len(gt)
    tp=0
    if n:
        matrix=mu.iou(preds,gt,[0]*g)
        valid=matrix>=THRESHOLD
        # Cardinality first; total matched IoU breaks ties.
        rr,cc=linear_sum_assignment(-(valid.astype(float)*(min(n,g)+1)+matrix))
        tp=int(valid[rr,cc].sum())
    fp,fn=n-tp,g-tp
    return {"foreground_iou":iou,"dice":dice,"predicted_instances":n,
            "reference_instances":g,"count_absolute_error":abs(n-g),
            "projected_union_area_px":pa,"reference_union_area_px":ga,
            "projected_area_absolute_error_px":abs(pa-ga),
            "projected_area_relative_error":abs(pa-ga)/ga,
            "instance_tp_at_50":tp,"instance_fp_at_50":fp,"instance_fn_at_50":fn,
            "instance_f1_at_50":2*tp/(2*tp+fp+fn),
            "historical_xor_area_px":term["historical_xor_area_px"],
            "union_minus_xor_px":pa-term["historical_xor_area_px"],
            "structurally_accepted":term["structural_validator_accepts"]}

def score():
    m=checked_manifest()
    audit=json.loads((OUT/"audit.json").read_text())
    if audit["manifest_sha256"]!=EXPECTED_MANIFEST or audit["evaluator_sha256"]!=file_sha256(Path(__file__)) or audit["overlay_sha256"]!=file_sha256(OUT/"annotation_overlay.png"):
        raise ValueError("prospective evaluator identity drift")
    terms={}
    for c in m["cases"]:
        for name in MODELS:
            target=STAGING/f"tray_{c['case']:02d}"/name
            t=json.loads((target/"terminal.json").read_text())
            if t["case"]!=c["case"] or t["model"]!=name or t["manifest_sha256"]!=EXPECTED_MANIFEST or t["image_sha256"]!=c["sha256"] or t["state"] not in ("FAILED","SUCCEEDED"):
                raise ValueError("terminal identity mismatch")
            terms[c["case"],name]=(t,target)
    rows=[]
    for c in m["cases"]:
        info,gt,gu,_=reference(c)
        if info!=audit["cases"][c["case"]-1]: raise ValueError("reference drift")
        row={"case":c["case"],"models":{}}
        for name in MODELS:
            term,target=terms[c["case"],name]
            entry={"inference_state":term["state"],"metrics":None}
            if term["state"]=="SUCCEEDED":
                try: entry["metrics"]=evaluate_one(c,info,gt,gu,name,term,target)
                except (ValueError,KeyError,TypeError) as exc: entry["evaluation_failure"]=str(exc)
            row["models"][name]=entry
        rows.append(row)
    common=[r for r in rows if all(r["models"][n]["metrics"] is not None for n in MODELS)]
    summaries={}
    metrics=("foreground_iou","dice","count_absolute_error","projected_area_relative_error","instance_f1_at_50")
    for name in MODELS:
        ms=[r["models"][name]["metrics"] for r in rows if r["models"][name]["metrics"] is not None]
        paired=[r["models"][name]["metrics"] for r in common]
        summaries[name]={"registered":8,"inference_successes":sum(r["models"][name]["inference_state"]=="SUCCEEDED" for r in rows),
            "scorable":len(ms),"structurally_accepted_scorable":sum(x["structurally_accepted"] for x in ms),
            "jointly_scorable":len(common),
            "macro_joint":{k:float(np.mean([x[k] for x in paired])) if paired else None for k in metrics},
            "failure_zero_utility_iou_sensitivity":sum(x["foreground_iou"] for x in ms)/8}
    delta=[r["models"]["potato_sam"]["metrics"]["foreground_iou"]-r["models"]["arabidopsis_mask2former"]["metrics"]["foreground_iou"] for r in common]
    report={"scope":"EXPLORATORY_DIRECT_MODEL_PILOT_NOT_AGENT_EVALUATION","audit_sha256":file_sha256(OUT/"audit.json"),
            "summaries":summaries,"paired_iou_delta_sam_minus_mask2former":delta,
            "mean_paired_iou_delta":float(np.mean(delta)) if delta else None,
            "rows":rows,"source_measurement_reconciliation":audit["source_measurements"],
            "limitations":["Original published annotations, not newly independently adjudicated; may have been used in SAM development.",
              "One ungrouped polygon per instance assumed, not expert verified completeness.",
              "Eight tray representatives, descriptive paired comparisons, not isolated species effect.",
              "Source measurement reconciliation only; original table associations must be interpreted separately.",
              "No live agent trials or intervention superiority."]}
    write(OUT/"report.json",report)
    print(json.dumps(report,indent=2,allow_nan=False))
    print("ANNOTATED_PILOT_REPORT_SHA256="+file_sha256(OUT/"report.json"))

def main():
    os.umask(0o077)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["audit","score"])
    args=p.parse_args()
    audit() if args.action=="audit" else score()

if __name__=="__main__": main()
