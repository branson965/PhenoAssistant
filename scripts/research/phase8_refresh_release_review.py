"""Refresh prospective review evidence without modifying the old packet or approval pins."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.research import phase8_prepare_release_review as review
from scripts.research import phase8_potato_cross_capability_pilot as pilot

OLD=review.PACKET
OLD_SHA="b72982eec2ac49a53749dce18c90e1ca2d371c26ba1b8c93af3ecc43f0edefce"
NEW=review.STAGING/"phase8_release_review_packet_v0.2.json"
BIND=review.STAGING/"phase8_release_review_checkpoint_receipt_v0.2.json"
PILOT_SHA="1efb97145e19bb51eaab0da0d12cecb479e675c5aaa21b4396cf181cb36ce691"

def main():
    from huggingface_hub import snapshot_download
    os.umask(0o077)
    if os.getenv("OPENROUTER_API_KEY"): raise ValueError("remove provider credential")
    if NEW.exists() or BIND.exists(): raise FileExistsError("preserve existing refresh evidence")
    if review.sha(OLD)!=OLD_SHA: raise ValueError("original packet drift")
    old=json.loads(OLD.read_text())
    if old["scientific_execution_permitted"] or old["independent_approval_granted"]:
        raise ValueError("old review status unexpected")
    p=pilot.STAGING/"manifest.json"
    if review.sha(p)!=PILOT_SHA: raise ValueError("checkpoint reference manifest drift")
    m=json.loads(p.read_text())
    snapshot=Path(snapshot_download(repo_id=pilot.ARA,revision=pilot.REV,local_files_only=True))
    files={p.relative_to(snapshot).as_posix():review.sha(p) for p in sorted(snapshot.rglob("*")) if p.is_file()}
    if snapshot.name!=pilot.REV or files!=m["ara_snapshot_files"]:
        raise ValueError("Arabidopsis snapshot drift")
    sam=review.sha(pilot.SAM)
    if sam!=pilot.SAM_SHA or sam!=m["sam_sha256"]:
        raise ValueError("SAM checkpoint drift")
    # Reuse reviewed packet construction, changing only the destination.
    review.PACKET=NEW
    review.prepare_packet()
    review.write_exclusive(BIND,{
        "status":"CHECKPOINT_IDENTITY_RECEIPT_NOT_APPROVAL",
        "previous_packet_sha256":OLD_SHA,"refreshed_packet_sha256":review.sha(NEW),
        "checkpoint_reference_manifest_sha256":PILOT_SHA,
        "arabidopsis_model":pilot.ARA,"arabidopsis_revision":pilot.REV,
        "arabidopsis_snapshot_files":files,"potato_model":pilot.POT,"sam_sha256":sam,
        "scientific_execution_permitted":False,"independent_approval_granted":False,
        "provider_calls":0,"gpu_calls":0})
    print("CHECKPOINT_RECEIPT_SHA256="+review.sha(BIND))
    print("REVIEW_REFRESH_COMPLETE=true")
    print("SCIENTIFIC_EXECUTION_PERMITTED=false")

if __name__=="__main__": main()
