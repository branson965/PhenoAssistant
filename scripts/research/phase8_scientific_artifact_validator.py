"""Output-format-aware post-execution checks for actual PhenoAssistant artifacts.

The canonical image segmentation tools emit COCO JSON, not phenotype records.
Case 1 Mask2Former: ins_seg_results.json.
Case 2 Leaf-only SAM: leaf_only_sam_results.json.
Case 3 DINOv2 classifier: img_classification_results.csv.

This adapter checks only independently supportable structural scientific
invariants and file/data provenance; it does not assess model accuracy, gold
labels, model calibration, visual correctness or mask-RLE decodability. For
segmentation, leaf count and summed predicted mask areas are derived from
COCO annotations and passed through the frozen Phase 7 phenotype invariant
validator. For classification, finite confidence and bounded class IDs are
checked without assuming a label-to-index mapping not yet frozen.

No GPU calls, API keys, OpenRouter clients, benchmark gold or hidden data.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Awaitable, Callable

from phenoassistant_mcp.scientific_inference_v1 import (
    ALLOWED_MODELS,
    CLASSIFICATION,
    SEGMENTATION,
    ImageAsset,
    ScientificMcpDispatchError,
    file_sha256,
    resolve_image_asset,
)
from research.phenoguard.post_validation import (
    PostExecutionValidation,
    PostValidationIssue,
    ValidationIssueCode,
    ValidationSeverity,
    validate_phenotype_records,
)
from research.phenoguard.provenance import CASE2_POTATO_SEGMENTATION_MODEL_ID

MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
VALIDATOR = "phase8-actual-scientific-artifact-invariants-v0.1"


def issue(code: ValidationIssueCode, message: str, field: str = "") -> PostValidationIssue:
    return PostValidationIssue(
        code=code,
        severity=ValidationSeverity.HARD,
        field=field or None,
        message=message,
    )


def result_of(issues: list[PostValidationIssue]) -> PostExecutionValidation:
    return PostExecutionValidation(
        validator_id=VALIDATOR,
        safe_to_report=not bool(issues),
        issues=tuple(issues),
    )


def fail(message: str, field: str = "artifact") -> PostExecutionValidation:
    return result_of([issue(ValidationIssueCode.IDENTIFIER_MISMATCH, message, field)])


def _number(value: Any, *, integer: bool = False) -> bool:
    if isinstance(value, bool):
        return False
    if integer:
        return isinstance(value, int)
    return isinstance(value, (int, float)) and math.isfinite(value)


def _expected_name(capability_id: str) -> str:
    if capability_id == CASE2_POTATO_SEGMENTATION_MODEL_ID:
        return "leaf_only_sam_results.json"
    if capability_id in SEGMENTATION:
        return "ins_seg_results.json"
    if capability_id in CLASSIFICATION:
        return "img_classification_results.csv"
    raise ValueError("unknown scientific capability")


def validate_coco(
    path: Path, *, expected_image_path: Path
) -> PostExecutionValidation:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return fail("COCO artifact is unreadable or malformed", "COCO")
    if not isinstance(data, dict):
        return fail("COCO result must be an object", "COCO")
    images = data.get("images")
    annotations = data.get("annotations")
    categories = data.get("categories")
    if not (isinstance(images, list) and len(images) == 1
            and isinstance(annotations, list) and isinstance(categories, list)
            and len(categories) > 0):
        return fail("COCO must contain exactly one image, annotation list and categories", "COCO")

    im = images[0]
    if not isinstance(im, dict):
        return fail("COCO image record missing", "images")
    if im.get("file_name") != str(expected_image_path):
        return fail("COCO file_name does not match trusted input image", "file_name")
    width, height = im.get("width"), im.get("height")
    if not (_number(width, integer=True) and width > 0
            and _number(height, integer=True) and height > 0):
        return fail("image dimensions must be positive integer pixels", "images")
    image_id = im.get("id")
    if not _number(image_id, integer=True):
        return fail("COCO image ID must be an integer", "images")

    category_ids: set[int] = set()
    for category in categories:
        if (not isinstance(category, dict)
            or not _number(category.get("id"), integer=True)
            or not isinstance(category.get("name"), str)
            or not category["name"].strip()
            or category["id"] in category_ids):
            return fail("invalid or duplicate category ID/name", "categories")
        category_ids.add(category["id"])

    annotation_ids: set[int] = set()
    total_predicted_area = 0.0
    for ann in annotations:
        if not isinstance(ann, dict):
            return fail("COCO annotation is not an object", "annotations")
        ident = ann.get("id")
        if not _number(ident, integer=True) or ident in annotation_ids:
            return fail("invalid or duplicate annotation ID", "annotations")
        annotation_ids.add(ident)
        if ann.get("image_id") != image_id or ann.get("category_id") not in category_ids:
            return fail("annotation references incorrect image or category", "annotations")
        area, score = ann.get("area"), ann.get("score")
        if not (_number(area) and 0 <= area <= width * height):
            return fail("predicted segmentation area outside physical image bounds", "area")
        if not (_number(score) and 0 <= score <= 1):
            return fail("non-finite or out-of-range model confidence", "score")
        if ann.get("iscrowd") not in (0, False):
            return fail("unexpected crowd/instance encoding", "iscrowd")
        mask = ann.get("segmentation")
        if (not isinstance(mask, dict)
            or mask.get("size") != [height, width]
            or not isinstance(mask.get("counts"), str)
            or not mask["counts"]):
            return fail("COCO mask RLE shape or counts missing/mismatched", "segmentation")
        total_predicted_area += float(area)

    # Frozen Phase 7 scientific invariants applied to actual, derived
    # output rather than an invented test-only phenotype record.
    phenotype = validate_phenotype_records((
        {"leaf_count": len(annotations), "projected_leaf_area": total_predicted_area},
    ))
    return result_of(list(phenotype.issues))


def validate_classification(
    path: Path, *, expected_image_path: Path
) -> PostExecutionValidation:
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or not {
                "file_name", "class_ids", "class_labels", "class_scores"
            }.issubset(reader.fieldnames):
                return fail("classification CSV missing expected columns", "CSV")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error):
        return fail("classification CSV unreadable", "CSV")
    if len(rows) != 1:
        return fail("classification CSV must contain exactly one image", "CSV")
    row = rows[0]
    if row["file_name"] != str(expected_image_path):
        return fail("classification file_name differs from trusted image", "file_name")
    try:
        class_id = int(row["class_ids"])
        score = float(row["class_scores"])
    except (ValueError, TypeError):
        return fail("classification ID or confidence is non-numeric", "class_scores")
    if not (row["class_ids"].strip() == str(class_id) and 0 <= class_id < 7):
        return fail("classification ID outside declared seven-class scope", "class_ids")
    if not (math.isfinite(score) and 0 <= score <= 1):
        return fail("classification confidence must be finite and within [0,1]", "class_scores")
    if not isinstance(row["class_labels"], str) or not row["class_labels"].strip():
        return fail("classification label missing", "class_labels")
    # The exact label-to-ID mapping is not yet independently pinned:
    # do NOT fabricate such a mapping or claim top-1 accuracy.
    return result_of([])


def validate_scientific_mcp_artifact(
    payload: dict[str, Any],
    *,
    bound_asset_id: str,
    bound_asset: ImageAsset,
    output_root: Path,
) -> PostExecutionValidation:
    """Read the *actual* hashed output from the trusted MCP result envelope.

    Returns a typed hard failure rather than treating absent/invalid model
    evidence as safe. No model or benchmark input is generated here.
    """
    if not isinstance(payload, dict) or payload.get("tool_executed") is not True:
        return fail("MCP scientific tool did not confirm execution", "tool_executed")
    capability = payload.get("capability_id")
    if capability not in ALLOWED_MODELS:
        return fail("MCP returned unregistered scientific capability", "capability_id")
    if payload.get("image_asset_id") != bound_asset_id:
        return fail("MCP returned an unbound image identifier", "image_asset_id")
    try:
        expected_image = resolve_image_asset(
            bound_asset_id, trusted_assets={bound_asset_id: bound_asset},
        )
    except (ValueError, OSError, ScientificMcpDispatchError):
        return fail("trusted input image is missing or checksum changed", "image_asset_id")
    try:
        root = output_root.resolve(strict=True)
        artifact = Path(payload["artifact_path"])
        if output_root.is_symlink() or artifact.is_symlink() or not artifact.is_file():
            return fail("output artifact is a symlink or does not exist")
        absolute = artifact.resolve(strict=True)
        relative = absolute.relative_to(root)
        if len(relative.parts) != 3:
            return fail("unexpected scientific trial artifact directory layout")
        if relative.name != _expected_name(capability):
            return fail("scientific artifact filename disagrees with canonical tool")
        expected_format = "coco_json" if capability in SEGMENTATION else "classification_csv"
        if payload.get("artifact_format") != expected_format:
            return fail("declared artifact format differs from capability")
        if type(payload.get("record_count")) is not int or payload["record_count"] != 1:
            return fail("MCP record count must confirm one input image")
        if not (0 < absolute.stat().st_size <= MAX_ARTIFACT_BYTES):
            return fail("artifact size outside bounded single-image range")
        calculated_hash = file_sha256(absolute)
        if payload.get("artifact_sha256") != calculated_hash:
            return fail("MCP artifact hash does not match disk content")
    except (KeyError, OSError, ValueError, TypeError):
        return fail("invalid or untrusted scientific artifact path")

    if capability in SEGMENTATION:
        return validate_coco(absolute, expected_image_path=expected_image)
    return validate_classification(absolute, expected_image_path=expected_image)


def make_c8_artifact_validator(
    *, bound_asset_id: str, bound_asset: ImageAsset, output_root: Path,
) -> Callable[[dict[str, Any]], Awaitable[PostExecutionValidation]]:
    """Bind reviewed assets at the application boundary, not in the LLM."""
    async def validate(payload: dict[str, Any]) -> PostExecutionValidation:
        return validate_scientific_mcp_artifact(
            payload, bound_asset_id=bound_asset_id,
            bound_asset=bound_asset, output_root=output_root,
        )
    return validate
