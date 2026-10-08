"""Run secret-safe Phase 5 data and repository preflight checks.

This script does not import heavyweight ML libraries and does not execute any model.
Run it from the repository root before GPU smoke tests.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASE1_METADATA = ROOT / "data" / "aracrop_metadata.json"
CASE1_IMAGE_ROOT = ROOT / "data" / "AraCropData"
CASE3_ROOT = ROOT / "data" / "winter-wheat_nutri-defi-identify_dndww20"


def _git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _case1_status() -> dict[str, object]:
    if not CASE1_METADATA.is_file():
        return {
            "metadata_exists": False,
            "metadata_images": 0,
            "existing_images": 0,
            "missing_images": 0,
            "first_missing": [],
        }

    payload = json.loads(CASE1_METADATA.read_text(encoding="utf-8"))
    images = payload.get("file_name")

    if not isinstance(images, list):
        raise TypeError("Case 1 metadata file_name must be a list")

    paths = [ROOT / str(item).removeprefix("./") for item in images]
    missing = [path for path in paths if not path.is_file()]

    return {
        "metadata_exists": True,
        "image_root_exists": CASE1_IMAGE_ROOT.is_dir(),
        "metadata_images": len(paths),
        "existing_images": len(paths) - len(missing),
        "missing_images": len(missing),
        "first_missing": [
            str(path.relative_to(ROOT)) for path in missing[:5]
        ],
        "ready_for_gpu_smoke": len(paths) == 1248 and not missing,
    }


def _case3_status() -> dict[str, object]:
    required = {
        "dataset_root": CASE3_ROOT,
        "train_dir": CASE3_ROOT / "train",
        "train_metadata": CASE3_ROOT / "train" / "metadata.csv",
        "label2id": CASE3_ROOT / "label2id.json",
    }

    image_count = 0
    for suffix in ("*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff"):
        image_count += sum(
            1 for _ in CASE3_ROOT.glob(f"**/{suffix}")
        ) if CASE3_ROOT.exists() else 0

    return {
        "paths": {
            name: path.exists() for name, path in required.items()
        },
        "local_image_count": image_count,
        "ready_for_inference_smoke": image_count > 0,
        "training_dataset_layout_present": all(
            path.exists() for path in required.values()
        ),
    }


def main() -> None:
    result = {
        "schema_version": "1",
        "git": {
            "head": _git(["rev-parse", "HEAD"]),
            "branch": _git(["branch", "--show-current"]),
            "status_short": _git(
                ["status", "--short", "--untracked-files=all"]
            ),
        },
        "credentials_present": {
            "HF_USER": bool(os.environ.get("HF_USER")),
            "HF_TOKEN": bool(os.environ.get("HF_TOKEN")),
            "OPENROUTER_API_KEY": bool(
                os.environ.get("OPENROUTER_API_KEY")
            ),
        },
        "case1": _case1_status(),
        "case3": _case3_status(),
    }

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
