"""Verify Feng's public Case 3 checkpoints without downloading model weights.

This is login-node safe: it requests Hugging Face metadata plus the small config.json
for the collaborator-provided fully fine-tuned checkpoint. It does not load Torch,
download weight files, or execute inference.
"""

from __future__ import annotations

import json

from huggingface_hub import (
    dataset_info,
    hf_hub_download,
    model_info,
)
from huggingface_hub.utils import HfHubHTTPError


FULLFT = (
    "fengchen025/"
    "dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020"
)

LORA = (
    "fengchen025/"
    "winter-wheat_nutri-defi-identify_dndww20_dino2b_lora"
)

DATASET = (
    "fengchen025/"
    "winter-wheat_nutri-defi-identify_dndww20"
)


def probe_model(repo_id: str) -> dict[str, object]:
    try:
        info = model_info(repo_id)
    except HfHubHTTPError as exc:
        return {
            "repo_id": repo_id,
            "reachable": False,
            "status_code": getattr(
                exc.response,
                "status_code",
                None,
            ),
            "error_type": type(exc).__name__,
        }

    return {
        "repo_id": repo_id,
        "reachable": True,
        "private": bool(info.private),
        "gated": info.gated,
        "sha": info.sha,
        "pipeline_tag": info.pipeline_tag,
    }


def probe_dataset(repo_id: str) -> dict[str, object]:
    try:
        info = dataset_info(repo_id)
    except HfHubHTTPError as exc:
        return {
            "repo_id": repo_id,
            "reachable": False,
            "status_code": getattr(
                exc.response,
                "status_code",
                None,
            ),
            "error_type": type(exc).__name__,
        }

    return {
        "repo_id": repo_id,
        "reachable": True,
        "private": bool(info.private),
        "gated": info.gated,
        "sha": info.sha,
    }


def main() -> None:
    fullft = probe_model(FULLFT)
    lora = probe_model(LORA)
    dataset = probe_dataset(DATASET)

    if fullft["reachable"] is not True:
        raise RuntimeError(
            "collaborator-provided full-FT checkpoint is not reachable: "
            + json.dumps(
                fullft,
                sort_keys=True,
            )
        )

    if fullft.get("private") is not False:
        raise RuntimeError(
            "full-FT checkpoint is reachable but not public"
        )

    if not fullft.get("sha"):
        raise RuntimeError(
            "full-FT checkpoint has no immutable Hub SHA"
        )

    config_path = hf_hub_download(
        repo_id=FULLFT,
        revision=str(
            fullft["sha"]
        ),
        filename="config.json",
    )

    with open(
        config_path,
        encoding="utf-8",
    ) as handle:
        config = json.load(handle)

    print(
        "CASE3_FULLFT_REACHABLE="
        + str(
            fullft["reachable"]
        ).lower()
    )
    print(
        "CASE3_FULLFT_PRIVATE="
        + str(
            fullft.get("private")
        ).lower()
    )
    print(
        "CASE3_FULLFT_GATED="
        + str(
            fullft.get("gated")
        )
    )
    print(
        "CASE3_FULLFT_SHA="
        + str(
            fullft.get("sha")
        )
    )
    print(
        "CASE3_FULLFT_PIPELINE_TAG="
        + str(
            fullft.get("pipeline_tag")
        )
    )
    print(
        "CASE3_FULLFT_ARCHITECTURES="
        + json.dumps(
            config.get(
                "architectures",
                [],
            )
        )
    )
    print(
        "CASE3_FULLFT_NUM_LABELS="
        + str(
            config.get(
                "num_labels"
            )
        )
    )
    print(
        "CASE3_FULLFT_ID2LABEL="
        + json.dumps(
            config.get(
                "id2label",
                {},
            ),
            sort_keys=True,
        )
    )

    print(
        "CASE3_LORA_REACHABLE="
        + str(
            lora["reachable"]
        ).lower()
    )
    print(
        "CASE3_LORA_PRIVATE="
        + str(
            lora.get("private")
        ).lower()
    )
    print(
        "CASE3_LORA_SHA="
        + str(
            lora.get("sha")
        )
    )

    print(
        "CASE3_HISTORICAL_DATASET_REACHABLE="
        + str(
            dataset["reachable"]
        ).lower()
    )
    print(
        "CASE3_HISTORICAL_DATASET_PRIVATE="
        + str(
            dataset.get("private")
        ).lower()
    )
    print(
        "CASE3_HISTORICAL_DATASET_SHA="
        + str(
            dataset.get("sha")
        )
    )

    print(
        "CASE3_PUBLIC_MODEL_METADATA_PASS=true"
    )


if __name__ == "__main__":
    main()
