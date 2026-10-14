"""Audit the pinned Case 3 full-FT snapshot without loading the full model.

Purpose:
- verify that the 346 MB model.safetensors actually contains the classifier head;
- verify that the classifier output dimension matches the seven published labels;
- record whether PEFT adapter artefacts coexist in the repository;
- preserve a content hash for the exact full-model weight file.

This is a checkpoint-integrity audit, not an accuracy test.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from huggingface_hub import snapshot_download
from safetensors import safe_open


MODEL_ID = (
    "fengchen025/"
    "dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020"
)

REVISION = (
    "89d6b3ca17dba118d7d25c7b8a87ff205dc6235e"
)

OUTPUT_DIR = Path(
    "results/maf_gpu_case3_checkpoint_audit"
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


def main() -> Path:
    snapshot = Path(
        snapshot_download(
            repo_id=MODEL_ID,
            revision=REVISION,
            local_files_only=True,
        )
    )

    config_path = snapshot / "config.json"
    weights_path = snapshot / "model.safetensors"
    adapter_config_path = snapshot / "adapter_config.json"
    adapter_weights_path = snapshot / "adapter_model.safetensors"

    if not config_path.is_file():
        raise FileNotFoundError(config_path)

    if not weights_path.is_file():
        raise FileNotFoundError(weights_path)

    config = json.loads(
        config_path.read_text(
            encoding="utf-8",
        )
    )

    id2label = config.get(
        "id2label",
        {},
    )

    with safe_open(
        weights_path,
        framework="pt",
        device="cpu",
    ) as handle:
        keys = list(
            handle.keys()
        )

        classifier_weight_keys = [
            key
            for key in keys
            if key.endswith(
                "classifier.weight"
            )
        ]

        classifier_bias_keys = [
            key
            for key in keys
            if key.endswith(
                "classifier.bias"
            )
        ]

        classifier_weight_shapes = {
            key: list(
                handle.get_slice(
                    key
                ).get_shape()
            )
            for key in classifier_weight_keys
        }

        classifier_bias_shapes = {
            key: list(
                handle.get_slice(
                    key
                ).get_shape()
            )
            for key in classifier_bias_keys
        }

    label_count = len(
        id2label
    )

    classifier_output_dimensions = sorted(
        {
            shape[0]
            for shape in classifier_weight_shapes.values()
            if shape
        }
        | {
            shape[0]
            for shape in classifier_bias_shapes.values()
            if shape
        }
    )

    classifier_head_present = bool(
        classifier_weight_keys
        and classifier_bias_keys
    )

    classifier_matches_labels = (
        classifier_head_present
        and classifier_output_dimensions
        == [label_count]
    )

    adapter_config = None

    if adapter_config_path.is_file():
        adapter_config = json.loads(
            adapter_config_path.read_text(
                encoding="utf-8",
            )
        )

    payload = {
        "schema_version": "1",
        "purpose": "checkpoint_integrity_audit_only",
        "accuracy_claim_authorized": False,
        "model_id": MODEL_ID,
        "revision": REVISION,
        "snapshot_path": str(
            snapshot
        ),
        "config_architectures": config.get(
            "architectures",
            [],
        ),
        "config_name_or_path": config.get(
            "_name_or_path"
        ),
        "id2label": id2label,
        "label_count": label_count,
        "model_safetensors_path": str(
            weights_path
        ),
        "model_safetensors_size_bytes": (
            weights_path.stat().st_size
        ),
        "model_safetensors_sha256": sha256_file(
            weights_path
        ),
        "state_dict_key_count": len(
            keys
        ),
        "classifier_weight_keys": classifier_weight_keys,
        "classifier_bias_keys": classifier_bias_keys,
        "classifier_weight_shapes": classifier_weight_shapes,
        "classifier_bias_shapes": classifier_bias_shapes,
        "classifier_output_dimensions": classifier_output_dimensions,
        "classifier_head_present": classifier_head_present,
        "classifier_matches_label_count": classifier_matches_labels,
        "adapter_config_present": adapter_config_path.is_file(),
        "adapter_model_present": adapter_weights_path.is_file(),
        "adapter_config": adapter_config,
    }

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / "checkpoint_audit.json"
    )

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "CASE3_AUDIT_MODEL="
        + MODEL_ID
    )
    print(
        "CASE3_AUDIT_REVISION="
        + REVISION
    )
    print(
        "CASE3_AUDIT_FULL_WEIGHT_SHA256="
        + payload["model_safetensors_sha256"]
    )
    print(
        "CASE3_AUDIT_STATE_DICT_KEYS="
        + str(
            payload["state_dict_key_count"]
        )
    )
    print(
        "CASE3_AUDIT_LABEL_COUNT="
        + str(
            label_count
        )
    )
    print(
        "CASE3_AUDIT_CLASSIFIER_WEIGHT_KEYS="
        + json.dumps(
            classifier_weight_keys
        )
    )
    print(
        "CASE3_AUDIT_CLASSIFIER_BIAS_KEYS="
        + json.dumps(
            classifier_bias_keys
        )
    )
    print(
        "CASE3_AUDIT_CLASSIFIER_OUTPUT_DIMS="
        + json.dumps(
            classifier_output_dimensions
        )
    )
    print(
        "CASE3_AUDIT_ADAPTER_CONFIG_PRESENT="
        + str(
            adapter_config_path.is_file()
        ).lower()
    )
    print(
        "CASE3_AUDIT_ADAPTER_MODEL_PRESENT="
        + str(
            adapter_weights_path.is_file()
        ).lower()
    )

    if adapter_config is not None:
        print(
            "CASE3_AUDIT_ADAPTER_BASE_MODEL="
            + str(
                adapter_config.get(
                    "base_model_name_or_path"
                )
            )
        )

    if not classifier_head_present:
        raise RuntimeError(
            "model.safetensors does not contain both classifier weight and bias"
        )

    if label_count != 7:
        raise RuntimeError(
            f"expected seven labels, observed {label_count}"
        )

    if not classifier_matches_labels:
        raise RuntimeError(
            "classifier output dimension does not match the seven-label config"
        )

    print(
        "CASE3_FULLFT_CHECKPOINT_INTEGRITY_PASS=true"
    )
    print(
        "CASE3_FULLFT_CHECKPOINT_AUDIT="
        + str(
            output_path
        )
    )

    return output_path


if __name__ == "__main__":
    main()
