"""Probe Hugging Face access for Phase 5 checkpoints/datasets without downloading weights.

Run from repository root in the Phase 5 Python environment. No credential values are
printed. This is safe to run on the Plato login node because it performs metadata
requests only and does not load a model or GPU library state beyond importing the
Hugging Face client.
"""

from __future__ import annotations

import json
import os

from huggingface_hub import dataset_info, model_info
from huggingface_hub.utils import HfHubHTTPError


RESOURCES = (
    (
        "case1_model",
        "model",
        "fengchen025/arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft",
    ),
    (
        "case3_model",
        "model",
        "fengchen025/winter-wheat_nutri-defi-identify_dndww20_dino2b_lora",
    ),
    (
        "case3_dataset",
        "dataset",
        "fengchen025/winter-wheat_nutri-defi-identify_dndww20",
    ),
)


def _probe(kind: str, repo_id: str) -> dict[str, object]:
    try:
        if kind == "model":
            info = model_info(repo_id)
        elif kind == "dataset":
            info = dataset_info(repo_id)
        else:
            raise ValueError(kind)
    except HfHubHTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        return {
            "repo_id": repo_id,
            "kind": kind,
            "reachable": False,
            "status_code": status_code,
            "error_type": type(exc).__name__,
        }
    except Exception as exc:
        return {
            "repo_id": repo_id,
            "kind": kind,
            "reachable": False,
            "status_code": None,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    return {
        "repo_id": repo_id,
        "kind": kind,
        "reachable": True,
        "private": bool(getattr(info, "private", False)),
        "gated": getattr(info, "gated", None),
        "sha": getattr(info, "sha", None),
    }


def main() -> None:
    results = {
        "schema_version": "1",
        "hf_token_present": bool(os.environ.get("HF_TOKEN")),
        "resources": {
            label: _probe(kind, repo_id)
            for label, kind, repo_id in RESOURCES
        },
    }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
