"""GPU Case 3 compatibility smoke using the official DND-Diko-WWWR example image.

This validates that Feng's collaborator-approved fully fine-tuned checkpoint can be
loaded and can execute one bounded inference in the historical PhenoAssistant
classification function. The input is the official example montage linked from the
DND-Diko-WWWR repository README. Because it is a montage rather than an individually
labelled WW2020 test image, this is compatibility evidence only, not accuracy evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests
import torch
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from functions.image_classification import infer_image_classification


CHECKPOINT = (
    "fengchen025/"
    "dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020"
)

CHECKPOINT_REVISION = (
    "89d6b3ca17dba118d7d25c7b8a87ff205dc6235e"
)

FULL_WEIGHT_SHA256 = (
    "4a29f8b73438a6d16cbc80287c40002af40029fd529146f0be73d7825befbbf5"
)

SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "image-hosting/ImageHosting/main/img/202306200458172.png"
)

OUTPUT_DIR = Path(
    "results/maf_gpu_case3_fullft_official_sample"
)

INPUT_PATH = (
    OUTPUT_DIR
    / "dnd_diko_wwwr_official_example_montage.png"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def download_input() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if INPUT_PATH.is_file():
        return

    response = requests.get(
        SOURCE_URL,
        timeout=60,
    )

    response.raise_for_status()

    INPUT_PATH.write_bytes(
        response.content
    )


def _prepare_clean_fullft_snapshot(
    source_snapshot: Path,
) -> Path:
    """Expose only the full-FT files so Transformers cannot auto-detect PEFT."""

    hf_home = Path(
        os.environ.get(
            "HF_HOME",
            Path.home() / ".cache" / "huggingface",
        )
    )

    clean_snapshot = (
        hf_home
        / "phenoassistant_case3_fullft_clean"
        / CHECKPOINT_REVISION
    )

    clean_snapshot.mkdir(
        parents=True,
        exist_ok=True,
    )

    required = (
        "config.json",
        "preprocessor_config.json",
        "model.safetensors",
    )

    for name in required:
        source = source_snapshot / name
        target = clean_snapshot / name

        if not source.is_file():
            raise FileNotFoundError(source)

        source_real = source.resolve(
            strict=True,
        )

        if target.exists() or target.is_symlink():
            target.unlink()

        try:
            os.link(
                source_real,
                target,
            )
        except OSError:
            shutil.copy2(
                source_real,
                target,
            )

        if not target.is_file():
            raise RuntimeError(
                "clean full-FT runtime file was not materialized: "
                + str(target)
            )

        if target.is_symlink():
            raise RuntimeError(
                "clean full-FT runtime file must be a regular file, not a symlink: "
                + str(target)
            )

    for forbidden in (
        "adapter_config.json",
        "adapter_model.safetensors",
    ):
        path = clean_snapshot / forbidden

        if path.exists() or path.is_symlink():
            path.unlink()

    if (
        sha256_file(
            clean_snapshot / "model.safetensors"
        )
        != FULL_WEIGHT_SHA256
    ):
        raise RuntimeError(
            "clean full-FT model.safetensors hash does not match "
            "the audited collaborator checkpoint"
        )

    return clean_snapshot


def main() -> Path:
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is unavailable; run this script inside a GPU allocation"
        )

    download_input()

    source_snapshot = Path(
        snapshot_download(
            repo_id=CHECKPOINT,
            revision=CHECKPOINT_REVISION,
            local_files_only=True,
        )
    )

    resolved_checkpoint = _prepare_clean_fullft_snapshot(
        source_snapshot
    )

    started = time.perf_counter()

    result = infer_image_classification(
        image_urls=[
            str(INPUT_PATH),
        ],
        checkpoint=str(
            resolved_checkpoint
        ),
        batch_size=1,
        device="cuda",
        output_dir=str(
            OUTPUT_DIR
        ),
    )

    elapsed = time.perf_counter() - started

    result_path = (
        OUTPUT_DIR
        / "img_classification_results.csv"
    )

    if not result_path.is_file():
        raise RuntimeError(
            "classification returned without an output CSV: "
            + str(result)
        )

    frame = pd.read_csv(
        result_path
    )

    if len(frame) != 1:
        raise RuntimeError(
            f"expected one result row, observed {len(frame)}"
        )

    row = frame.iloc[0]

    score = float(
        row["class_scores"]
    )

    if not (
        0.0
        <= score
        <= 1.0
    ):
        raise RuntimeError(
            f"classification confidence outside [0,1]: {score}"
        )

    evidence = {
        "schema_version": "1",
        "captured_at_utc": datetime.now(
            UTC
        ).isoformat(),
        "purpose": (
            "checkpoint_load_and_inference_compatibility_only"
        ),
        "accuracy_claim_authorized": False,
        "input_scope": (
            "official DND-Diko-WWWR README example montage; "
            "not an individually labelled WW2020 evaluation image"
        ),
        "input_source_url": SOURCE_URL,
        "input_path": str(
            INPUT_PATH
        ),
        "input_sha256": sha256_file(
            INPUT_PATH
        ),
        "checkpoint": CHECKPOINT,
        "checkpoint_revision": CHECKPOINT_REVISION,
        "source_snapshot_path": str(source_snapshot),
        "resolved_checkpoint_path": str(resolved_checkpoint),
        "checkpoint_resolution": (
            "audited_fullft_only_snapshot_without_peft_autodetection"
        ),
        "full_weight_sha256": FULL_WEIGHT_SHA256,
        "adapter_files_excluded_from_runtime": True,
        "device": torch.cuda.get_device_name(
            0
        ),
        "torch_version": torch.__version__,
        "torch_cuda_runtime": torch.version.cuda,
        "elapsed_seconds": elapsed,
        "result_path": str(
            result_path
        ),
        "result_sha256": sha256_file(
            result_path
        ),
        "prediction": {
            "class_id": int(
                row["class_ids"]
            ),
            "class_label": str(
                row["class_labels"]
            ),
            "class_score": score,
        },
    }

    evidence_path = (
        OUTPUT_DIR
        / "gpu_execution_evidence.json"
    )

    evidence_path.write_text(
        json.dumps(
            evidence,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "CASE3_FULLFT_CHECKPOINT="
        + CHECKPOINT
    )
    print(
        "CASE3_FULLFT_REVISION="
        + CHECKPOINT_REVISION
    )
    print(
        "CASE3_FULLFT_RESOLVED_SNAPSHOT="
        + str(resolved_checkpoint)
    )
    print(
        "CASE3_FULLFT_DEVICE="
        + evidence["device"]
    )
    print(
        "CASE3_FULLFT_INPUT_SHA256="
        + evidence["input_sha256"]
    )
    print(
        "CASE3_FULLFT_PREDICTED_CLASS="
        + evidence["prediction"]["class_label"]
    )
    print(
        "CASE3_FULLFT_PREDICTED_SCORE="
        + str(
            evidence["prediction"]["class_score"]
        )
    )
    print(
        "CASE3_FULLFT_ACCURACY_CLAIM_AUTHORIZED=false"
    )
    print(
        "CASE3_FULLFT_GPU_COMPATIBILITY_PASS=true"
    )
    print(
        "CASE3_FULLFT_EVIDENCE="
        + str(
            evidence_path
        )
    )

    return evidence_path


if __name__ == "__main__":
    main()
