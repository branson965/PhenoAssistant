"""Acquire pinned PhenoLeaf-TS archive and inspect inventory, without extraction.

No model inference, hidden evaluation labels, or agent approval.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import sys
import zipfile
from collections import Counter,defaultdict
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data/_staging/phenoleaf_ts_source_v0.1"
REPO="rick77a/PhenoLeaf_TS"
ARCHIVE="PhenoLeaf-TS_DS.zip"

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def write(path,obj):
    with path.open("x") as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False)
        f.write("\n")

def main():
    from huggingface_hub import HfApi,hf_hub_download
    os.umask(0o077)
    if os.getenv("OPENROUTER_API_KEY"): raise ValueError("remove provider credential")
    OUT.mkdir(mode=0o700,parents=True,exist_ok=True)
    if (OUT/"inventory.json").exists(): raise FileExistsError("completed inventory already exists")
    pin=OUT/"source_pin.json"
    if pin.exists():
        source=json.loads(pin.read_text())
        revision=source["revision"]
    else:
        info=HfApi().dataset_info(REPO,files_metadata=True,token=False)
        revision=info.sha
        card=info.card_data.to_dict() if info.card_data is not None else {}
        if card.get("license")!="cc-by-4.0": raise ValueError("dataset licence differs from published card")
        entry=next(x for x in info.siblings if x.rfilename==ARCHIVE)
        lfs=entry.lfs
        digest=lfs.get("sha256") if isinstance(lfs,dict) else getattr(lfs,"sha256",None)
        size=entry.size
        if not revision or not digest or len(digest)!=64 or not 0<size<=8_000_000_000:
            raise ValueError("unverified archive identity or size")
        source={"repo":REPO,"revision":revision,"archive":ARCHIVE,"license":card["license"],
                "declared_sha256":digest,"size":size}
        write(pin,source)
    if source["repo"]!=REPO or source["archive"]!=ARCHIVE or source["license"]!="cc-by-4.0":
        raise ValueError("source pin differs")
    print(json.dumps(source,indent=2),flush=True)
    local=OUT/ARCHIVE
    if not local.exists() and shutil.disk_usage(OUT).free<source["size"]+1_000_000_000:
        raise RuntimeError("insufficient filesystem free space; check quota separately")
    p=Path(hf_hub_download(REPO,ARCHIVE,repo_type="dataset",revision=revision,
                           local_dir=OUT,token=False))
    if p.resolve()!=local.resolve() or p.stat().st_size!=source["size"] or sha(p)!=source["declared_sha256"]:
        raise ValueError("downloaded archive identity mismatch")
    examples=defaultdict(list)
    counts=Counter(); prefixes=Counter(); total=0; seen=set()
    with zipfile.ZipFile(p) as z:
        for member in z.infolist():
            q=PurePosixPath(member.filename)
            if q.is_absolute() or ".." in q.parts or "\\" in member.filename or member.filename in seen:
                raise ValueError("unsafe or duplicate archive member")
            seen.add(member.filename)
            if member.is_dir(): continue
            suffix=q.suffix.lower() or "(none)"
            counts[suffix]+=1; total+=member.file_size
            # first few directory components reveal exact layout
            prefix="/".join(q.parts[:min(3,len(q.parts)-1)])
            prefixes[prefix]+=1
            if len(examples[suffix])<12:
                examples[suffix].append({"path":member.filename,"size":member.file_size,"crc32":f"{member.CRC:08x}"})
        listing=[{"path":m.filename,"size":m.file_size,"crc32":f"{m.CRC:08x}"} for m in z.infolist() if not m.is_dir()]
    report={"source":source,"archive_sha256":sha(p),"member_count":len(listing),
            "uncompressed_bytes":total,"extensions":dict(counts),
            "top_prefix_counts":dict(prefixes.most_common(40)),"examples":dict(examples),
            "members":listing,"full_archive_sha256_verified":True,"extracted":False,
            "individual_member_crc_verified":False,"gpu_calls":0,"provider_calls":0}
    write(OUT/"inventory.json",report)
    print(json.dumps({k:v for k,v in report.items() if k!="members"},indent=2))
    print("INVENTORY_SHA256="+sha(OUT/"inventory.json"))
    print("PHENOLEAF_TS_ACQUISITION_COMPLETE=true")

if __name__=="__main__": main()
