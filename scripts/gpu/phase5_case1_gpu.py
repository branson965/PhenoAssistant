"""Run the real Case 1 instance-segmentation GPU smoke/full path.

This script never overwrites historical Case 1 artefacts. Run from repository root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from functions.compute_phenotypes import compute_phenotypes_from_ins_seg
from functions.instance_segmentation import infer_instance_segmentation


CHECKPOINT = (
    "fengchen025/"
    "arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft"
)
METADATA = Path("data/aracrop_metadata.json")
EXPECTED_IMAGES = 1248


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_images() -> list[str]:
    if not METADATA.is_file():
        raise FileNotFoundError(METADATA)

    payload = json.loads(METADATA.read_text(encoding="utf-8"))
    images = payload.get("file_name")

    if not isinstance(images, list) or not all(
        isinstance(item, str) and item.strip() for item in images
    ):
        raise TypeError(
            "Case 1 metadata must contain a non-empty string list at file_name"
        )

    return images


def main() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("smoke", "sample", "full"),
        default="smoke",
    )
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument(
        "--sample-size",
        type=int,
        default=16,
        help="Number of images for sample mode; ignored for smoke/full.",
    )
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is unavailable in the active Python environment"
        )

    images = _load_images()
    missing = [path for path in images if not Path(path).is_file()]

    if missing:
        raise RuntimeError(
            "Case 1 image set is incomplete: "
            f"{len(images) - len(missing)}/{len(images)} files exist. "
            f"First missing paths: {missing[:5]}"
        )

    if len(images) != EXPECTED_IMAGES:
        raise RuntimeError(
            f"expected {EXPECTED_IMAGES} Case 1 images, found {len(images)}"
        )

    if args.batch_size < 1:
        raise ValueError("batch size must be positive")

    if args.sample_size < 1:
        raise ValueError("sample size must be positive")

    if args.mode == "smoke":
        output_dir = Path("results/maf_gpu_case1_smoke")
        selected_images = [images[0]]
    elif args.mode == "sample":
        output_dir = Path("results/maf_gpu_case1_sample")
        selected_images = images[: min(args.sample_size, len(images))]
    else:
        output_dir = Path("results/maf_gpu_case1")
        selected_images = images

    output_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    result = infer_instance_segmentation(
        image_urls=selected_images,
        checkpoint=CHECKPOINT,
        batch_size=args.batch_size,
        device="cuda",
        output_dir=str(output_dir),
    )
    elapsed = time.perf_counter() - started

    segmentation_path = output_dir / "ins_seg_results.json"
    if not segmentation_path.is_file():
        raise RuntimeError(
            "instance-segmentation call returned without creating "
            f"{segmentation_path}: {result}"
        )

    segmentation = json.loads(
        segmentation_path.read_text(encoding="utf-8")
    )
    image_records = segmentation.get("images", [])
    annotation_records = segmentation.get("annotations", [])

    if not isinstance(image_records, list) or not image_records:
        raise RuntimeError("segmentation output contains no image records")
    if not isinstance(annotation_records, list):
        raise TypeError("segmentation annotations must be a list")

    phenotype_path: Path | None = None
    phenotype_result: str | None = None

    if args.mode == "full":
        phenotype_path = output_dir / "phenotypes.csv"
        phenotype_result = compute_phenotypes_from_ins_seg(
            ins_seg_result_path=str(segmentation_path),
            save_path=str(phenotype_path),
            pixel_to_cm=0.03,
        )
        if not phenotype_path.is_file():
            raise RuntimeError(
                "phenotype extraction returned without creating "
                f"{phenotype_path}: {phenotype_result}"
            )

    evidence = {
        "schema_version": "1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "checkpoint": CHECKPOINT,
        "device": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "torch_cuda_runtime": torch.version.cuda,
        "metadata_path": str(METADATA),
        "metadata_image_count": len(images),
        "executed_image_count": len(selected_images),
        "batch_size": args.batch_size,
        "elapsed_seconds": elapsed,
        "segmentation_result_message": result,
        "segmentation_path": str(segmentation_path),
        "segmentation_sha256": _sha256(segmentation_path),
        "segmentation_image_records": len(image_records),
        "segmentation_annotation_records": len(annotation_records),
        "phenotype_path": str(phenotype_path) if phenotype_path else None,
        "phenotype_sha256": (
            _sha256(phenotype_path) if phenotype_path else None
        ),
        "phenotype_result_message": phenotype_result,
    }

    evidence_path = output_dir / "gpu_execution_evidence.json"
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "mode": args.mode,
                "executed_images": len(selected_images),
                "annotations": len(annotation_records),
                "elapsed_seconds": round(elapsed, 3),
                "evidence": str(evidence_path),
            },
            sort_keys=True,
        )
    )

    return evidence_path


if __name__ == "__main__":
    main()
