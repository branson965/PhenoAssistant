"""Run a bounded Case 3 image-classification inference smoke on GPU.

Uses the already-registered winter-wheat LoRA checkpoint. It does not train,
upload datasets, mutate the model zoo, or expose credential values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import torch

from functions.image_classification import infer_image_classification


CHECKPOINT = (
    "fengchen025/"
    "winter-wheat_nutri-defi-identify_dndww20_dino2b_lora"
)
DATASET_ROOT = Path(
    "data/winter-wheat_nutri-defi-identify_dndww20"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _discover_image() -> Path | None:
    for split in ("test", "train"):
        metadata = DATASET_ROOT / split / "metadata.csv"
        if not metadata.is_file():
            continue

        with metadata.open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                raw = (row.get("file_name") or "").strip()
                if not raw:
                    continue
                path = Path(raw)
                if not path.is_absolute():
                    path = DATASET_ROOT / split / path
                if path.is_file():
                    return path
    return None


def main() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image",
        default=None,
        help=(
            "Approved local winter-wheat image. When omitted, the script "
            "tries test/metadata.csv then train/metadata.csv."
        ),
    )
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is unavailable in the active Python environment"
        )

    image_path = (
        Path(args.image)
        if args.image is not None
        else _discover_image()
    )

    if image_path is None:
        raise RuntimeError(
            "No Case 3 image was supplied and no local image could be "
            "discovered from the winter-wheat metadata."
        )

    if not image_path.is_file():
        raise FileNotFoundError(image_path)

    output_dir = Path("results/maf_gpu_case3_smoke")
    output_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    result = infer_image_classification(
        image_urls=[str(image_path)],
        checkpoint=CHECKPOINT,
        batch_size=1,
        device="cuda",
        output_dir=str(output_dir),
    )
    elapsed = time.perf_counter() - started

    result_path = output_dir / "img_classification_results.csv"
    if not result_path.is_file():
        raise RuntimeError(
            "classification call returned without creating "
            f"{result_path}: {result}"
        )

    frame = pd.read_csv(result_path)
    required = {
        "file_name",
        "class_ids",
        "class_labels",
        "class_scores",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise RuntimeError(
            "Case 3 inference output is missing columns: "
            + ", ".join(missing)
        )

    if len(frame) != 1:
        raise RuntimeError(
            f"Case 3 smoke expected one output row, found {len(frame)}"
        )

    row = frame.iloc[0]
    score = float(row["class_scores"])
    if not (0.0 <= score <= 1.0):
        raise RuntimeError(
            f"classification confidence is outside [0, 1]: {score}"
        )

    evidence = {
        "schema_version": "1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint": CHECKPOINT,
        "input_image": str(image_path),
        "input_sha256": _sha256(image_path),
        "device": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "torch_cuda_runtime": torch.version.cuda,
        "elapsed_seconds": elapsed,
        "result_message": result,
        "result_path": str(result_path),
        "result_sha256": _sha256(result_path),
        "prediction": {
            "class_id": int(row["class_ids"]),
            "class_label": str(row["class_labels"]),
            "class_score": score,
        },
    }

    evidence_path = output_dir / "gpu_execution_evidence.json"
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "class_label": evidence["prediction"]["class_label"],
                "class_score": score,
                "elapsed_seconds": round(elapsed, 3),
                "evidence": str(evidence_path),
            },
            sort_keys=True,
        )
    )

    return evidence_path


if __name__ == "__main__":
    main()
