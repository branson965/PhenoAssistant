"""Bounded REAL MCP boundary for repository scientific-vision inference.

Unlike the Phase 8 simulated condition rehearsal, this MCPServer exposes an
actual callable tool whose production delegate is PhenoAssistant's canonical
inference functions, imported lazily. The public tool arguments are ONLY an
approved capability ID and an opaque approved image-asset ID.

This module does not itself run a model. An invocation requires a genuinely
approved, SHA-pinned final runtime record, trusted image bindings, and a
single frozen trial ID. No raw paths, checkpoint URIs, HTTP URLs, GPU settings
or output paths are accepted from an LLM.

The production runner MUST additionally enforce a trial ledger, real
pre/post-condition distinctions, one-call budget gate and upstream key cap.
Do not count fake-delegate MCP tests as scientific inference.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from mcp.server import MCPServer

from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    CASE2_POTATO_SEGMENTATION_MODEL_ID,
    CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
)

SEGMENTATION = frozenset((
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    CASE2_POTATO_SEGMENTATION_MODEL_ID,
))
CLASSIFICATION = frozenset((CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,))
ALLOWED_MODELS = SEGMENTATION | CLASSIFICATION
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
TRIAL_RE = re.compile(r"^[a-f0-9]{24}$")
ASSET_RE = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,95}$")
IMAGE_SUFFIXES = frozenset((".png", ".jpg", ".jpeg", ".tif", ".tiff"))


class ScientificMcpDispatchError(ValueError):
    """Fail closed at the scientific MCP execution boundary."""


@dataclass(frozen=True)
class ImageAsset:
    """Opaque, application-controlled image binding, never a model-supplied path."""

    path: Path
    sha256: str


# Canonical PhenoAssistant inference signatures use checkpoint, image_urls,
# batch_size, device, and output_dir. Testing injects a fake delegate while
# using the REAL MCP client/server protocol and response parsing.
InferenceDelegate = Callable[[str, str, Path, Path], str]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_approved_runtime(runtime_file: Path, expected_sha256: str) -> dict:
    """SHA-bound authorization; the historic v0.3 candidate always fails."""
    if not SHA256_RE.fullmatch(expected_sha256):
        raise ScientificMcpDispatchError("invalid approved-runtime checksum")
    if not runtime_file.is_file() or file_sha256(runtime_file) != expected_sha256:
        raise ScientificMcpDispatchError("final runtime file absent or checksum changed")
    try:
        record = json.loads(runtime_file.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ScientificMcpDispatchError("invalid final runtime JSON") from exc
    if not isinstance(record, dict):
        raise ScientificMcpDispatchError("final runtime must be a JSON object")
    if record.get("status") != "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN":
        raise ScientificMcpDispatchError("final runtime has not been approved and frozen")
    if record.get("scientific_execution_permitted") is not True:
        raise ScientificMcpDispatchError("scientific execution is not permitted")
    if (
        record.get("approval", {}).get(
            "researcher_attested_supervisor_provider_billing_and_models"
        )
        is not True
    ):
        raise ScientificMcpDispatchError("provider/billing/model approval absent")
    compatibility = record.get("http_transport_compatibility", {})
    if (
        compatibility.get("scientific_harness_adoption") != "VERIFIED"
        or compatibility.get("upstream_provider") != "openai"
        or compatibility.get("no_provider_fallbacks") is not True
        or compatibility.get("provider_require_parameters") is not True
        or compatibility.get("application_side_max_function_calls") != 1
    ):
        raise ScientificMcpDispatchError("final transport or tool-limit controls differ")
    return record


def resolve_image_asset(
    asset_id: str,
    *,
    trusted_assets: Mapping[str, ImageAsset],
) -> Path:
    if not isinstance(asset_id, str) or not ASSET_RE.fullmatch(asset_id):
        raise ScientificMcpDispatchError("invalid opaque image asset ID")
    asset = trusted_assets.get(asset_id)
    if asset is None:
        raise ScientificMcpDispatchError("image asset absent from approved manifest")
    if not isinstance(asset, ImageAsset):
        raise ScientificMcpDispatchError("invalid trusted asset binding")
    path = asset.path
    if path.is_symlink() or not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
        raise ScientificMcpDispatchError("trusted image is missing or unsafe")
    if not SHA256_RE.fullmatch(asset.sha256):
        raise ScientificMcpDispatchError("invalid expected image checksum")
    if file_sha256(path) != asset.sha256:
        raise ScientificMcpDispatchError("trusted image changed after binding")
    return path.resolve(strict=True)


def canonical_inference(
    capability_id: str,
    _asset_id: str,
    image_path: Path,
    output_dir: Path,
) -> str:
    """Invoke repository inference; no paths/checkpoints come from LLM text."""
    if capability_id in SEGMENTATION:
        from functions.instance_segmentation import infer_instance_segmentation
        return infer_instance_segmentation(
            image_urls=[str(image_path)],
            checkpoint=capability_id,
            batch_size=1,
            device="cuda",
            output_dir=str(output_dir),
        )
    if capability_id in CLASSIFICATION:
        from functions.image_classification import infer_image_classification
        return infer_image_classification(
            image_urls=[str(image_path)],
            checkpoint=capability_id,
            batch_size=1,
            device="cuda",
            output_dir=str(output_dir),
        )
    raise ScientificMcpDispatchError("unregistered scientific model")


def verified_artifact(
    capability_id: str, output_dir: Path, invocation_message: str,
) -> tuple[Path, str, int]:
    """Check that success corresponds to a real structured scientific artifact."""
    if not isinstance(invocation_message, str) or invocation_message.startswith("Error"):
        raise ScientificMcpDispatchError("canonical inference reported an error")
    if capability_id in SEGMENTATION:
        artifact = output_dir / "ins_seg_results.json"
        kind = "coco_json"
        if not artifact.is_file() or artifact.is_symlink():
            raise ScientificMcpDispatchError("COCO result file missing")
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ScientificMcpDispatchError("COCO artifact malformed") from exc
        if (
            not isinstance(payload, dict)
            or not isinstance(payload.get("images"), list)
            or len(payload["images"]) != 1
            or not isinstance(payload.get("annotations"), list)
        ):
            raise ScientificMcpDispatchError("COCO artifact lacks expected image/annotation records")
        record_count = len(payload["images"])
    elif capability_id in CLASSIFICATION:
        artifact = output_dir / "img_classification_results.csv"
        kind = "classification_csv"
        if not artifact.is_file() or artifact.is_symlink():
            raise ScientificMcpDispatchError("classification CSV missing")
        with artifact.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            expected = {"file_name", "class_ids", "class_labels", "class_scores"}
            if not expected.issubset(reader.fieldnames or []):
                raise ScientificMcpDispatchError("classification CSV missing required columns")
            records = list(reader)
        if len(records) != 1:
            raise ScientificMcpDispatchError("classification artifact must contain one image row")
        record_count = len(records)
    else:
        raise ScientificMcpDispatchError("unknown capability artifact format")
    return artifact, kind, record_count


def build_phase8_scientific_mcp_server(
    *,
    approved_runtime_file: Path,
    approved_runtime_sha256: str,
    frozen_trial_id: str,
    trusted_images: Mapping[str, ImageAsset],
    output_root: Path,
    inference_delegate: InferenceDelegate | None = None,
) -> MCPServer:
    """Bound a per-trial MCP server to approved runtime and physical assets.

    The caller supplies a SHA-pinned final approved runtime, never the
    historical unapproved v0.3 candidate. The same server/real tool schema
    must be used for C3, C4 and C8. C8 applicability is a SEPARATE policy
    layer that gates whether this tool is invoked.
    """
    verify_approved_runtime(approved_runtime_file, approved_runtime_sha256)
    if not isinstance(frozen_trial_id, str) or not TRIAL_RE.fullmatch(frozen_trial_id):
        raise ScientificMcpDispatchError("invalid frozen trial ID")
    if not trusted_images:
        raise ScientificMcpDispatchError("approved image manifest is empty")
    if output_root.is_symlink():
        raise ScientificMcpDispatchError("output root must not be a symlink")
    root = output_root.resolve()
    if root.exists() and not root.is_dir():
        raise ScientificMcpDispatchError("unsafe output-root directory")
    implement = inference_delegate or canonical_inference
    server = MCPServer("phenoguard-phase8-scientific-inference-v1")

    def run_scientific_model(
        capability_id: str,
        image_asset_id: str,
    ) -> dict[str, str | int | bool]:
        """Run one approved scientific vision model on one trusted image asset."""
        if capability_id not in ALLOWED_MODELS:
            raise ScientificMcpDispatchError("model checkpoint is not in provenance catalogue")
        image_path = resolve_image_asset(image_asset_id, trusted_assets=trusted_images)
        # Capability ID and asset ID cannot introduce path segments.
        call_label = hashlib.sha256(
            (capability_id + "\t" + image_asset_id).encode("utf-8")
        ).hexdigest()[:24]
        directory = root / frozen_trial_id / call_label
        if directory.exists():
            raise ScientificMcpDispatchError("scientific result directory already exists: no re-run")
        directory.mkdir(parents=True, exist_ok=False)
        message = implement(capability_id, image_asset_id, image_path, directory)
        artifact, kind, count = verified_artifact(capability_id, directory, message)
        return {
            "schema_version": "1",
            "capability_id": capability_id,
            "image_asset_id": image_asset_id,
            "tool_executed": True,
            "artifact_format": kind,
            "artifact_path": str(artifact),
            "artifact_sha256": file_sha256(artifact),
            "record_count": count,
        }

    server.add_tool(
        run_scientific_model,
        name="run_scientific_model",
        description=(
            "Run one registered scientific vision model on an application-bound "
            "image asset. capability_id is a registered model identifier; "
            "image_asset_id is an opaque approved asset ID. No paths are accepted."
        ),
        structured_output=True,
    )
    return server
