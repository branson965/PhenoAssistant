"""REAL MCP protocol tests, with synthetic approval and FAKE vision inference.

No actual scientific model, CUDA, OpenRouter or gold benchmark is touched.
The synthetic approval lives only under pytest's temporary directory.
"""

from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path

import pytest

from phenoassistant_mcp.client_v2 import McpV2Session
from phenoassistant_mcp.scientific_inference_v1 import (
    ImageAsset,
    ScientificMcpDispatchError,
    build_phase8_scientific_mcp_server,
    file_sha256,
    resolve_image_asset,
    verify_approved_runtime,
    verify_trusted_runtime,
    canonical_inference,
    TRUSTED_APPROVED_RUNTIME_SHA256,
)
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    CASE2_POTATO_SEGMENTATION_MODEL_ID,
    CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
)

TRIAL_ID = "a" * 24


@pytest.fixture
def synthetic_final_record(tmp_path):
    """A TEST-ONLY stand-in, not a supervisor attestation or signed runtime."""
    original = json.loads(
        Path("experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json")
        .read_text(encoding="utf-8")
    )
    original["status"] = "PRE_OUTCOME_RUNTIME_APPROVED_FROZEN"
    original["scientific_execution_permitted"] = True
    original["approval"]["researcher_attested_supervisor_provider_billing_and_models"] = True
    original["http_transport_compatibility"]["scientific_harness_adoption"] = "VERIFIED"
    destination = tmp_path / "SYNTHETIC_APPROVAL_TEST_ONLY.json"
    destination.write_text(json.dumps(original, sort_keys=True), encoding="utf-8")
    return destination, file_sha256(destination)


@pytest.fixture
def tiny_asset(tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"synthetic_test_image_not_for_actual_inference")
    return {"approved_image_1": ImageAsset(path=image, sha256=file_sha256(image))}


def make_server(tmp_path, synthetic_final_record, tiny_asset, delegate):
    path, digest = synthetic_final_record
    return build_phase8_scientific_mcp_server(
        approved_runtime_file=path,
        approved_runtime_sha256=digest,
        frozen_trial_id=TRIAL_ID,
        trusted_images=tiny_asset,
        output_root=tmp_path / "outputs",
        inference_delegate=delegate,
    )


def fake_vision(capability_id, _asset_id, _image_path, output_dir):
    if capability_id in {
        CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
        CASE2_POTATO_SEGMENTATION_MODEL_ID,
    }:
        name = ("leaf_only_sam_results.json"
                if capability_id == CASE2_POTATO_SEGMENTATION_MODEL_ID
                else "ins_seg_results.json")
        (output_dir / name).write_text(
            json.dumps({
                "images": [{"id": 0, "file_name": "approved_image_1"}],
                "annotations": [],
            }),
            encoding="utf-8",
        )
    else:
        with (output_dir / "img_classification_results.csv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=["file_name", "class_ids", "class_labels", "class_scores"],
            )
            writer.writeheader()
            writer.writerow({
                "file_name": "approved_image_1",
                "class_ids": "2",
                "class_labels": "test-label",
                "class_scores": "0.9",
            })
    return "synthetic inference completed"


def test_historic_v03_candidate_cannot_authorize_dispatch():
    candidate = Path("experiments/ijcai2027/runtime/runtime_controls_candidate_v0.3.json")
    with pytest.raises(ScientificMcpDispatchError, match="not been approved"):
        verify_approved_runtime(candidate, file_sha256(candidate))


@pytest.mark.parametrize("alteration", [
    ("scientific_execution_permitted", False),
    ("status", "PRE_OUTCOME_RUNTIME_CANDIDATE_PENDING_SUPERVISOR_PROVIDER_APPROVAL"),
])
def test_unapproved_record_rejected(tmp_path, synthetic_final_record, alteration):
    path, _ = synthetic_final_record
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[alteration[0]] = alteration[1]
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ScientificMcpDispatchError):
        verify_approved_runtime(path, file_sha256(path))


def test_modified_final_record_hash_fails_closed(synthetic_final_record):
    path, original_sha = synthetic_final_record
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ScientificMcpDispatchError, match="checksum changed"):
        verify_approved_runtime(path, original_sha)


def test_only_trusted_image_sha_is_accepted(tiny_asset, tmp_path):
    image = tiny_asset["approved_image_1"].path
    assert resolve_image_asset("approved_image_1", trusted_assets=tiny_asset) == image.resolve()
    with pytest.raises(ScientificMcpDispatchError):
        resolve_image_asset("../etc/passwd", trusted_assets=tiny_asset)
    with pytest.raises(ScientificMcpDispatchError):
        resolve_image_asset("unknown", trusted_assets=tiny_asset)
    image.write_bytes(b"modified_without_authorization")
    with pytest.raises(ScientificMcpDispatchError, match="changed"):
        resolve_image_asset("approved_image_1", trusted_assets=tiny_asset)


def test_no_unbounded_scientific_paths_or_gpu_settings_in_mcp_schema(
    tmp_path, synthetic_final_record, tiny_asset,
):
    calls = []
    def record_delegate(model_id, image_id, image_path, output_dir):
        calls.append((model_id, image_id, image_path, output_dir))
        return fake_vision(model_id, image_id, image_path, output_dir)

    server = make_server(
        tmp_path, synthetic_final_record, tiny_asset, record_delegate
    )

    async def run():
        async with McpV2Session(server) as session:
            names = await session.discover_tool_names(timeout_seconds=10.0)
            assert names == ("run_scientific_model",)
            result = await session.call_structured_tool(
                "run_scientific_model",
                {
                    "capability_id": CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
                    "image_asset_id": "approved_image_1",
                },
                timeout_seconds=10.0,
            )
            return result
    result = asyncio.run(run())
    assert result["schema_version"] == "1"
    assert result["capability_id"] == CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
    assert result["image_asset_id"] == "approved_image_1"
    assert result["tool_executed"] is True
    assert result["artifact_format"] == "coco_json"
    artifact = Path(result["artifact_path"])
    assert artifact.is_file()
    assert result["artifact_sha256"] == file_sha256(artifact)
    assert result["record_count"] == 1
    assert len(calls) == 1
    assert calls[0][0] == CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID
    assert calls[0][2] == tiny_asset["approved_image_1"].path.resolve()

    # A second invocation must return a real MCP tool-error envelope
    # and must not execute the model again.
    from phenoassistant_mcp.client_v2 import McpV2ToolError

    async def duplicate():
        async with McpV2Session(server) as session:
            return await session.call_structured_tool(
                "run_scientific_model",
                {
                    "capability_id": CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
                    "image_asset_id": "approved_image_1",
                },
                timeout_seconds=10,
            )

    with pytest.raises(McpV2ToolError):
        asyncio.run(duplicate())
    assert len(calls) == 1


def test_mcp_classification_boundary_returns_verified_artifact(
    tmp_path, synthetic_final_record, tiny_asset,
):
    server = make_server(tmp_path, synthetic_final_record, tiny_asset, fake_vision)
    async def run():
        async with McpV2Session(server) as session:
            return await session.call_structured_tool(
                "run_scientific_model",
                {
                    "capability_id": CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
                    "image_asset_id": "approved_image_1",
                },
                timeout_seconds=10,
            )
    result = asyncio.run(run())
    assert result["artifact_format"] == "classification_csv"
    assert result["record_count"] == 1
    assert result["tool_executed"] is True


def test_rejects_unregistered_checkpoint_at_protocol_boundary(
    tmp_path, synthetic_final_record, tiny_asset,
):
    server = make_server(tmp_path, synthetic_final_record, tiny_asset, fake_vision)
    async def run():
        async with McpV2Session(server) as session:
            await session.call_structured_tool(
                "run_scientific_model",
                {
                    "capability_id": "unregistered/unsafe_model",
                    "image_asset_id": "approved_image_1",
                },
                timeout_seconds=10,
            )
    from phenoassistant_mcp.client_v2 import McpV2ToolError
    with pytest.raises(McpV2ToolError):
        asyncio.run(run())


def test_no_credential_read_or_direct_paid_inference():
    source = Path("phenoassistant_mcp/scientific_inference_v1.py").read_text("utf-8")
    assert "OPENROUTER_API_KEY" not in source
    assert "AsyncOpenAI" not in source
    assert "OpenAIChatCompletionClient" not in source
    assert "build_development_validation_gold" not in source
    assert "image_urls=[str(image_path)]" in source
    assert "checkpoint=capability_id" in source


def test_real_mcp_input_schema_exposes_only_capability_and_asset(
    tmp_path, synthetic_final_record, tiny_asset,
):
    from mcp import Client
    from phenoassistant_mcp.client_v2 import MCP_PROTOCOL_VERSION
    server = make_server(tmp_path, synthetic_final_record, tiny_asset, fake_vision)
    async def inspect():
        async with Client(server, mode=MCP_PROTOCOL_VERSION) as client:
            listing = await client.list_tools()
            assert len(listing.tools) == 1
            tool = listing.tools[0]
            wire = tool.model_dump(by_alias=True)
            schema = wire.get("inputSchema", wire.get("input_schema"))
            assert isinstance(schema, dict)
            return schema
    schema = asyncio.run(inspect())
    assert set(schema["properties"]) == {"capability_id", "image_asset_id"}
    assert set(schema.get("required", [])) == {"capability_id", "image_asset_id"}
    for forbidden in ("image_urls", "file_path", "checkpoint", "device",
                      "output_dir", "batch_size", "scientific_operating_envelope"):
        assert forbidden not in schema["properties"]


def test_potato_sam_uses_canonical_leaf_only_sam_output_filename(
    tmp_path, synthetic_final_record, tiny_asset,
):
    server = make_server(tmp_path, synthetic_final_record, tiny_asset, fake_vision)

    async def run():
        async with McpV2Session(server) as session:
            return await session.call_structured_tool(
                "run_scientific_model",
                {
                    "capability_id": CASE2_POTATO_SEGMENTATION_MODEL_ID,
                    "image_asset_id": "approved_image_1",
                },
                timeout_seconds=10,
            )

    result = asyncio.run(run())
    assert Path(result["artifact_path"]).name == "leaf_only_sam_results.json"
    assert result["artifact_format"] == "coco_json"
    assert Path(result["artifact_path"]).is_file()


def test_second_different_model_is_still_blocked_within_same_trial(
    tmp_path, synthetic_final_record, tiny_asset,
):
    from phenoassistant_mcp.client_v2 import McpV2ToolError
    calls = []

    def recording_delegate(model_id, image_id, image_path, output_dir):
        calls.append(model_id)
        return fake_vision(model_id, image_id, image_path, output_dir)

    server = make_server(tmp_path, synthetic_final_record, tiny_asset, recording_delegate)

    async def run():
        async with McpV2Session(server) as session:
            first = await session.call_structured_tool(
                "run_scientific_model",
                {
                    "capability_id": CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
                    "image_asset_id": "approved_image_1",
                },
                timeout_seconds=10,
            )
            assert first["tool_executed"] is True
            with pytest.raises(McpV2ToolError):
                await session.call_structured_tool(
                    "run_scientific_model",
                    {
                        "capability_id": CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
                        "image_asset_id": "approved_image_1",
                    },
                    timeout_seconds=10,
                )

    asyncio.run(run())
    assert calls == [CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID]


def test_potato_artifact_filename_is_derived_from_repository_implementation():
    """Pin adapter to canonical Leaf-only SAM output naming, not test fiction."""
    from pathlib import Path
    script = Path("functions/leaf_only_sam.py").read_text(encoding="utf-8")
    assert 'f"leaf_only_{sam_version}_results.json"' in script
    adapter = Path("phenoassistant_mcp/scientific_inference_v1.py").read_text(
        encoding="utf-8"
    )
    assert '"leaf_only_sam_results.json"' in adapter


def test_self_declared_synthetic_approval_cannot_authorize_real_gpu(
    tmp_path, synthetic_final_record, tiny_asset,
):
    """A caller-produced JSON and its hash cannot unlock canonical inference."""
    path, digest = synthetic_final_record
    assert TRUSTED_APPROVED_RUNTIME_SHA256 is None
    with pytest.raises(ScientificMcpDispatchError, match="independently approved"):
        verify_trusted_runtime(path, digest)
    with pytest.raises(ScientificMcpDispatchError, match="independently approved"):
        build_phase8_scientific_mcp_server(
            approved_runtime_file=path,
            approved_runtime_sha256=digest,
            frozen_trial_id=TRIAL_ID,
            trusted_images=tiny_asset,
            output_root=tmp_path / "no-gpu-output",
            inference_delegate=None,
        )
    assert not (tmp_path / "no-gpu-output").exists()


def test_canonical_delegate_explicitly_injected_cannot_bypass_trust(
    tmp_path, synthetic_final_record, tiny_asset,
):
    """Passing the real canonical function as the 'fake' is also blocked."""
    path, digest = synthetic_final_record
    with pytest.raises(ScientificMcpDispatchError, match="independently approved"):
        build_phase8_scientific_mcp_server(
            approved_runtime_file=path,
            approved_runtime_sha256=digest,
            frozen_trial_id=TRIAL_ID,
            trusted_images=tiny_asset,
            output_root=tmp_path / "blocked-real-output",
            inference_delegate=canonical_inference,
        )


def test_canonical_wheat_route_uses_local_pinned_fullft_snapshot(tmp_path, monkeypatch):
    """Routing regression only; no real checkpoint load or GPU inference."""
    import sys
    from types import SimpleNamespace

    weight = tmp_path / "model.safetensors"
    weight.write_bytes(b"synthetic-routing-test-only")
    digest = file_sha256(weight)
    revision = "89d6b3ca17dba118d7d25c7b8a87ff205dc6235e"
    calls = []
    def snapshot_download(**kwargs):
        calls.append(("snapshot", kwargs))
        return str(tmp_path)
    def clean_snapshot(path):
        calls.append(("clean", path))
        return tmp_path
    def classify(**kwargs):
        calls.append(("classify", kwargs))
        return "synthetic routing test"
    monkeypatch.setitem(sys.modules, "huggingface_hub",
                        SimpleNamespace(snapshot_download=snapshot_download))
    monkeypatch.setitem(sys.modules, "scripts.gpu.phase5_case3_official_sample_smoke",
                        SimpleNamespace(CHECKPOINT_REVISION=revision, FULL_WEIGHT_SHA256=digest,
                                        _prepare_clean_fullft_snapshot=clean_snapshot))
    monkeypatch.setitem(sys.modules, "functions.image_classification",
                        SimpleNamespace(infer_image_classification=classify))
    image = tmp_path / "image.png"
    output = tmp_path / "output"
    assert canonical_inference(CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
                               "asset_1", image, output) == "synthetic routing test"
    assert calls == [
        ("snapshot", {"repo_id": CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
                      "revision": revision, "local_files_only": True}),
        ("clean", tmp_path),
        ("classify", {"image_urls": [str(image)], "checkpoint": str(tmp_path),
                      "batch_size": 1, "device": "cuda", "output_dir": str(output)}),
    ]
    weight.write_bytes(b"changed")
    with pytest.raises(ScientificMcpDispatchError, match="weight digest drift"):
        canonical_inference(CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
                            "asset_1", image, output)
    assert len([c for c in calls if c[0] == "classify"]) == 1
