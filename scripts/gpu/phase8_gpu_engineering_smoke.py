"""One-image GPU engineering smoke for PhenoGuard scientific capabilities.

NOT a Phase 8 scientific trial, benchmark, or approval bypass. No model
decision, provider API, hidden labels, or PhenoGuard scoring is performed.
Requires an explicitly selected authorised image and a Slurm GPU allocation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE_MODELS = {
    "arabidopsis": "fengchen025/arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft",
    "potato": "potato_leaf-instance-segmentation_leaf-only-sam",
    "wheat": "fengchen025/dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020",
}
SAM_CHECKPOINT = ROOT / "models" / "sam_vit_h_4b8939.pth"
SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_image(image: Path) -> None:
    if not image.is_file() or image.is_symlink() or image.suffix.lower() not in SUFFIXES:
        raise ValueError("approved image missing, symlinked, or unsupported format")
    from PIL import Image
    with Image.open(image) as obj:
        obj.verify()


def preflight(case: str, image: Path) -> dict:
    if case not in CASE_MODELS:
        raise ValueError("unknown case")
    inspect_image(image)
    checkpoint_exists = SAM_CHECKPOINT.is_file() and not SAM_CHECKPOINT.is_symlink()
    if case == "potato" and not checkpoint_exists:
        raise FileNotFoundError("potato SAM checkpoint missing: models/sam_vit_h_4b8939.pth")
    return {
        "case": case,
        "model": CASE_MODELS[case],
        "image_sha256": sha256(image),
        "potato_sam_checkpoint_present": checkpoint_exists,
        "engineering_smoke_only": True,
        "scientific_outcome": False,
    }


def verify_output(case: str, output_dir: Path, image: Path) -> tuple[Path, int]:
    if case == "wheat":
        output = output_dir / "img_classification_results.csv"
        with output.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            expected = {"file_name", "class_ids", "class_labels", "class_scores"}
            if not expected.issubset(reader.fieldnames or []):
                raise ValueError("invalid scientific classification artifact columns")
            rows = list(reader)
        if len(rows) != 1 or rows[0]["file_name"] != str(image):
            raise ValueError("classification artifact does not match input")
        confidence = float(rows[0]["class_scores"])
        if not (0 <= confidence <= 1):
            raise ValueError("classification confidence outside [0,1]")
        return output, 1
    filename = "leaf_only_sam_results.json" if case == "potato" else "ins_seg_results.json"
    output = output_dir / filename
    document = json.loads(output.read_text(encoding="utf-8"))
    images = document.get("images")
    annotations = document.get("annotations")
    if (not isinstance(images, list) or len(images) != 1
            or not isinstance(images[0], dict)
            or images[0].get("file_name") != str(image)):
        raise ValueError("COCO image record does not match input")
    if not isinstance(annotations, list):
        raise ValueError("COCO annotation records missing")
    return output, len(annotations)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(CASE_MODELS), required=True)
    parser.add_argument("--image", type=Path, required=True,
                        help="One explicitly reviewed/authorised local image")
    parser.add_argument("--output-root", type=Path,
                        default=ROOT / "results" / "phase8_gpu_engineering_smoke")
    parser.add_argument("--dry-run", action="store_true",
                        help="Check image/checkpoint only, with no GPU or provider calls")
    args = parser.parse_args()
    requested_image = args.image.expanduser()
    if requested_image.is_symlink():
        raise ValueError("image cannot be a symlink")
    image = requested_image.resolve(strict=True)
    info = preflight(args.case, image)
    if args.dry_run:
        print(json.dumps({"status": "PREFLIGHT_ONLY", **info}, sort_keys=True))
        return 0

    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("GPU smoke must run in a Slurm allocation")
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable in GPU job")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + str(os.getpid())
    output_dir = args.output_root.expanduser().resolve() / args.case / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    wheat_checkpoint_provenance = None
    if args.case == "wheat":
        # The published repository may contain PEFT sidecar files alongside
        # full fine-tuned weights. Reuse the previously audited pinned snapshot,
        # not bare from_pretrained(repo_id) which can auto-detect an adapter.
        from huggingface_hub import snapshot_download
        from scripts.gpu.phase5_case3_official_sample_smoke import (
            CHECKPOINT_REVISION,
            FULL_WEIGHT_SHA256,
            _prepare_clean_fullft_snapshot,
        )
        from functions.image_classification import infer_image_classification
        snapshot = Path(snapshot_download(
            repo_id=CASE_MODELS["wheat"],
            revision=CHECKPOINT_REVISION,
            local_files_only=True,
        ))
        clean_checkpoint = _prepare_clean_fullft_snapshot(snapshot)
        full_weight = clean_checkpoint / "model.safetensors"
        if sha256(full_weight) != FULL_WEIGHT_SHA256:
            raise RuntimeError("wheat full fine-tuned weight digest drift")
        wheat_checkpoint_provenance = {
            "revision": CHECKPOINT_REVISION,
            "full_weight_sha256": FULL_WEIGHT_SHA256,
            "peft_autodetection_avoided": True,
        }
        outcome = infer_image_classification(
            image_urls=[str(image)], checkpoint=str(clean_checkpoint),
            batch_size=1, device="cuda", output_dir=str(output_dir),
        )
    else:
        from functions.instance_segmentation import infer_instance_segmentation
        outcome = infer_instance_segmentation(
            image_urls=[str(image)], checkpoint=CASE_MODELS[args.case],
            batch_size=1, device="cuda", output_dir=str(output_dir),
        )
    if not isinstance(outcome, str) or outcome.startswith("Error"):
        raise RuntimeError("canonical scientific inference returned an error")
    artifact, count = verify_output(args.case, output_dir, image)
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                         capture_output=True, text=True, check=False)
    evidence = {
        "schema": "phenoguard-gpu-engineering-smoke-v0.1",
        "scope": "GPU_ENGINEERING_SMOKE_NOT_IJCAI_EVALUATION",
        "scientific_outcome": False,
        "approved_phase8_scientific_run": False,
        "case": args.case,
        "model": CASE_MODELS[args.case],
        "input_sha256": info["image_sha256"],
        "gpu": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "git_commit": git.stdout.strip() if git.returncode == 0 else None,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "artifact_type": artifact.name,
        "artifact_sha256": sha256(artifact),
        "record_count": count,
        "checkpoint_sha256": sha256(SAM_CHECKPOINT) if args.case == "potato" else None,
        "wheat_checkpoint_provenance": wheat_checkpoint_provenance,
        "source_sha256": sha256(Path(__file__)),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    evidence_path = output_dir / "engineering_evidence.json"
    evidence_path.write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps({
        "status": "ENGINEERING_SMOKE_OK",
        "evidence": str(evidence_path),
        "case": args.case,
        "record_count": count,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
