"""Actual artifact-structure invariants, no LLM/GPU/gold data.

The source files here are synthetic *formats* using the real canonical
output schema, not purported biological measurements.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from phenoassistant_mcp.scientific_inference_v1 import ImageAsset, file_sha256
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID as CASE1,
    CASE2_POTATO_SEGMENTATION_MODEL_ID as CASE2,
    CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID as CASE3,
)
from scripts.research.phase8_scientific_artifact_validator import (
    make_c8_artifact_validator, validate_scientific_mcp_artifact,
)


@pytest.fixture
def bound(tmp_path):
    image = tmp_path / "trusted_image.png"
    image.write_bytes(b"synthetic_image_for_structural_postvalidation")
    asset = ImageAsset(image, file_sha256(image))
    return "approved_image_001", asset, image.resolve()


def write_result(tmp_path, bound, capability=CASE1, *, empty=False):
    asset_id, asset, actual_image = bound
    root = tmp_path / "result_root"
    target = root / ("b" * 24) / ("c" * 24)
    target.mkdir(parents=True)
    if capability in (CASE1, CASE2):
        artifact = target / (
            "leaf_only_sam_results.json" if capability == CASE2
            else "ins_seg_results.json"
        )
        annotations = [] if empty else [{
            "id": 0, "image_id": 0, "category_id": 0,
            "segmentation": {"size": [32, 64], "counts": "fake_compressed_rle"},
            "area": 15.0, "score": 0.92, "iscrowd": 0,
        }]
        artifact.write_text(json.dumps({
            "images": [{"id": 0, "width": 64, "height": 32,
                        "file_name": str(actual_image)}],
            "annotations": annotations,
            "categories": [{"id": 0, "name": "leaf"}],
        }), encoding="utf-8")
        fmt = "coco_json"
    else:
        artifact = target / "img_classification_results.csv"
        with artifact.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "file_name", "class_ids", "class_labels", "class_scores"
            ])
            writer.writeheader()
            writer.writerow({
                "file_name": str(actual_image),
                "class_ids": 2,
                "class_labels": "N_KCa",
                "class_scores": 0.83,
            })
        fmt = "classification_csv"
    data = {
        "tool_executed": True,
        "capability_id": capability,
        "image_asset_id": asset_id,
        "artifact_path": str(artifact),
        "artifact_format": fmt,
        "artifact_sha256": file_sha256(artifact),
        "record_count": 1,
    }
    return data, root, artifact


def check(data, bound, root):
    return validate_scientific_mcp_artifact(
        data, bound_asset_id=bound[0],
        bound_asset=bound[1], output_root=root,
    )


@pytest.mark.parametrize("capability", [CASE1, CASE2, CASE3])
def test_scientific_artifacts_validated_by_actual_output_type(tmp_path, bound, capability):
    payload, root, _ = write_result(tmp_path, bound, capability)
    finding = check(payload, bound, root)
    assert finding.safe_to_report is True
    assert finding.issues == ()
    assert "actual-scientific-artifact" in finding.validator_id


def test_zero_segmentation_predictions_are_valid_not_a_blanket_refusal(tmp_path, bound):
    payload, root, _ = write_result(tmp_path, bound, CASE2, empty=True)
    finding = check(payload, bound, root)
    assert finding.safe_to_report is True
    assert not finding.issues


@pytest.mark.parametrize("change", [
    ("image_id", 99),
    ("category_id", 77),
    ("area", -1),
    ("area", 1e9),
    ("score", -0.02),
    ("score", 1.5),
    ("segmentation", {"size": [64, 32], "counts": "bad"}),
    ("segmentation", {"size": [32, 64], "counts": ""}),
])
def test_invalid_coco_instances_fail_closed(tmp_path, bound, change):
    payload, root, artifact = write_result(tmp_path, bound)
    coco = json.loads(artifact.read_text(encoding="utf-8"))
    coco["annotations"][0][change[0]] = change[1]
    artifact.write_text(json.dumps(coco), encoding="utf-8")
    payload["artifact_sha256"] = file_sha256(artifact)
    assert check(payload, bound, root).safe_to_report is False


def test_coco_mismatched_image_path_or_category_fails(tmp_path, bound):
    payload, root, artifact = write_result(tmp_path, bound)
    coco = json.loads(artifact.read_text(encoding="utf-8"))
    coco["images"][0]["file_name"] = "../untrusted-image.png"
    artifact.write_text(json.dumps(coco), encoding="utf-8")
    payload["artifact_sha256"] = file_sha256(artifact)
    assert check(payload, bound, root).safe_to_report is False


def test_classification_invalid_probability_blocks_reporting(tmp_path, bound):
    payload, root, artifact = write_result(tmp_path, bound, CASE3)
    text = artifact.read_text(encoding="utf-8")
    artifact.write_text(text.replace("0.83", "1.8"), encoding="utf-8")
    payload["artifact_sha256"] = file_sha256(artifact)
    finding = check(payload, bound, root)
    assert finding.safe_to_report is False
    assert any("confidence" in i.message for i in finding.issues)


def test_classification_invalid_class_id_blocks_reporting(tmp_path, bound):
    payload, root, artifact = write_result(tmp_path, bound, CASE3)
    artifact.write_text(artifact.read_text(encoding="utf-8").replace(",2,", ",20,"),
                        encoding="utf-8")
    payload["artifact_sha256"] = file_sha256(artifact)
    assert check(payload, bound, root).safe_to_report is False


def test_mismatched_record_hash_never_confers_validity(tmp_path, bound):
    payload, root, artifact = write_result(tmp_path, bound)
    artifact.write_text(artifact.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert check(payload, bound, root).safe_to_report is False


def test_path_outside_bound_output_root_fails(tmp_path, bound):
    payload, root, _ = write_result(tmp_path, bound)
    assert check(payload, bound, tmp_path / "different_root").safe_to_report is False


def test_untrusted_image_hash_change_fails(tmp_path, bound):
    payload, root, _ = write_result(tmp_path, bound)
    bound[1].path.write_bytes(b"tampered")
    assert check(payload, bound, root).safe_to_report is False


def test_invalid_tool_identity_fails(tmp_path, bound):
    payload, root, _ = write_result(tmp_path, bound)
    payload["capability_id"] = "unregistered/non-model"
    assert check(payload, bound, root).safe_to_report is False


def test_actual_artifact_post_validator_is_async_and_no_network(tmp_path, bound):
    import asyncio
    payload, root, _ = write_result(tmp_path, bound, CASE2)
    callback = make_c8_artifact_validator(
        bound_asset_id=bound[0],
        bound_asset=bound[1], output_root=root,
    )
    finding = asyncio.run(callback(payload))
    assert finding.safe_to_report is True


def test_canonical_filename_not_interchangeable_across_potato_and_arabidopsis(tmp_path, bound):
    payload, root, artifact = write_result(tmp_path, bound, CASE1)
    payload["capability_id"] = CASE2
    assert check(payload, bound, root).safe_to_report is False


def test_validator_reads_neither_approval_flags_nor_gold_labels():
    source = Path(
        "scripts/research/phase8_scientific_artifact_validator.py"
    ).read_text(encoding="utf-8")
    assert "build_development_validation_gold" not in source
    assert "OPENROUTER_API_KEY" not in source
    assert "AsyncOpenAI" not in source
    assert "ChatCompletionClient" not in source
