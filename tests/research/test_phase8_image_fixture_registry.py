"""No-provider/zero-GPU fixture registry tests; no benchmark gold opened."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from PIL import Image

from phenoassistant_mcp.scientific_inference_v1 import file_sha256
from scripts.research import phase8_image_fixture_registry as registry
from scripts.research.prepare_phase8_qualification_matrix import model_visible_view
from research.phenoguard.pilot_manifest import build_development_validation_manifest


@pytest.fixture
def complete_registry(tmp_path):
    template = registry.fixture_template()
    root = tmp_path / "trusted_images"
    root.mkdir()
    images = {}
    # Separate real, decodable synthetic-image fixtures with no scientific labels.
    for idx, row in enumerate(template["entries"]):
        asset_id = f"approved_asset_{idx:02d}"
        path = root / f"{asset_id}.png"
        Image.new("RGB", (16, 16), (idx * 10, 15, 30)).save(path)
        scenario = build_development_validation_manifest()[idx]
        row["image_asset_id_internal_only"] = asset_id
        row["image_path_internal_only"] = str(path)
        row["image_sha256"] = file_sha256(path)
        row["source_dataset"] = "SYNTHETIC_TEST_ONLY"
        row["source_image_id"] = f"synthetic-image-{idx}"
        row["reviewed_species"] = scenario.request.species or "unknown_test_species"
        row["license_or_access_evidence"] = "TEST_ONLY_IMAGE_GENERATED_INSIDE_PYTEST"
        row["reviewer_evidence_id"] = "TEST_ONLY_NOT_REAL_REVIEW"
        images[asset_id] = path
    return template, root, images


def test_template_is_exactly_frozen_cases_and_has_no_image_claims():
    model = registry.fixture_template()
    assert len(model["entries"]) == 12
    assert model["schema"] == registry.SCHEMA
    assert model["status"] == "PENDING_REAL_IMAGES_AND_INDEPENDENT_REVIEW"
    assert {entry["scenario_id_internal_only"] for entry in model["entries"]} == {
        s.scenario_id for s in build_development_validation_manifest()
    }
    assert all(row["image_path_internal_only"] is None for row in model["entries"])
    assert all(row["reviewer_evidence_id"] is None for row in model["entries"])
    assert registry.TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256 is None


def test_decodable_images_hash_and_source_metadata_validate_structurally(complete_registry):
    manifest, root, paths = complete_registry
    bindings = registry.audit_fixtures(manifest, trusted_root=root)
    assert set(bindings) == set(paths)
    assert len(bindings) == 12
    assert all(bindings[key].path == image for key, image in paths.items())


def test_self_proclaimed_approval_is_never_independent_approval(complete_registry, tmp_path):
    manifest, root, _ = complete_registry
    path = tmp_path / "self_approved.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(registry.FixtureGateError, match="no independently reviewed"):
        registry.verify_trusted_fixture_registry(file=path, trusted_root=root)
    assert file_sha256(path) != registry.TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256


@pytest.mark.parametrize("change,message", [
    ("image_sha256", "checksum"),
    ("source_dataset", "source"),
    ("source_image_id", "source"),
    ("reviewer_evidence_id", "source"),
    ("license_or_access_evidence", "source"),
    ("image_asset_id_internal_only", "asset ID"),
    ("reviewed_species", "contradicts"),
    ("model_visible_view_sha256", "hash"),
])
def test_missing_or_tampered_provenance_fails(complete_registry, change, message):
    manifest, root, _ = complete_registry
    bad = deepcopy(manifest)
    bad["entries"][0][change] = (
        "Solanum tuberosum" if change == "reviewed_species"
        else ("0" * 64 if change in {"image_sha256", "model_visible_view_sha256"}
              else None)
    )
    with pytest.raises(registry.FixtureGateError, match=message):
        registry.audit_fixtures(bad, trusted_root=root)


def test_no_path_escape_or_symlink_in_any_parent(complete_registry, tmp_path):
    manifest, root, _ = complete_registry
    outside = tmp_path / "outside.png"
    Image.new("RGB", (16, 16), "red").save(outside)
    bad = deepcopy(manifest)
    bad["entries"][0]["image_path_internal_only"] = str(outside)
    bad["entries"][0]["image_sha256"] = file_sha256(outside)
    with pytest.raises(registry.FixtureGateError, match="outside"):
        registry.audit_fixtures(bad, trusted_root=root)

    alias = root / "alias.png"
    alias.symlink_to(outside)
    bad["entries"][0]["image_path_internal_only"] = str(alias)
    with pytest.raises(registry.FixtureGateError, match="symlink"):
        registry.audit_fixtures(bad, trusted_root=root)


def test_fake_png_bytes_rejected_even_if_sha_matches(complete_registry):
    manifest, root, paths = complete_registry
    broken = paths["approved_asset_00"]
    broken.write_bytes(b"not actually a png")
    manifest["entries"][0]["image_sha256"] = file_sha256(broken)
    with pytest.raises(registry.FixtureGateError, match="decodable"):
        registry.audit_fixtures(manifest, trusted_root=root)


def test_conflicting_alias_asset_id_is_rejected(complete_registry):
    manifest, root, _ = complete_registry
    manifest["entries"][1]["image_asset_id_internal_only"] = "approved_asset_00"
    with pytest.raises(registry.FixtureGateError, match="conflicting"):
        registry.audit_fixtures(manifest, trusted_root=root)


def test_duplicate_or_missing_scenario_is_rejected(complete_registry):
    manifest, root, _ = complete_registry
    manifest["entries"][1]["scenario_id_internal_only"] = (
        manifest["entries"][0]["scenario_id_internal_only"]
    )
    with pytest.raises(registry.FixtureGateError, match="duplicate"):
        registry.audit_fixtures(manifest, trusted_root=root)


def test_private_paths_source_review_species_and_case_ids_never_go_to_llm(complete_registry):
    manifest, root, _ = complete_registry
    registry.audit_fixtures(manifest, trusted_root=root)
    scenario = build_development_validation_manifest()[0]
    safe = model_visible_view(scenario)
    registry.model_visible_fields_must_exclude_fixture_data(safe)
    unsafe = {"request": safe, "image_path_internal_only": manifest["entries"][0]["image_path_internal_only"]}
    with pytest.raises(registry.FixtureGateError, match="leaked"):
        registry.model_visible_fields_must_exclude_fixture_data(unsafe)
    for internal in (
        "scenario_id_internal_only", "source_dataset", "reviewer_evidence_id",
        "image_asset_id_internal_only", "reviewed_species",
        "image_asset_id", "fixture_refs", "image_path",
    ):
        with pytest.raises(registry.FixtureGateError, match="leaked"):
            registry.model_visible_fields_must_exclude_fixture_data({"private": {internal: "secret"}})


def test_template_cli_is_no_network_no_real_image_no_approval(capsys):
    assert registry.main.__name__ == "main"
    source = Path(registry.__file__).read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY" not in source
    assert "build_development_validation_gold" not in source
    assert "PHASE8_FIXTURE_PROVIDER_CALLS=0" in source
    assert "PHASE8_FIXTURE_REAL_IMAGES_BOUND=0" in source
    assert "TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256: str | None = None" in source


def test_template_location_is_already_git_ignored_and_never_a_public_runtime_artifact():
    ignore_text = Path(".gitignore").read_text(encoding="utf-8")
    assert "data/_staging/" in ignore_text
    assert registry.DEFAULT_TEMPLATE.relative_to(registry.ROOT).parts[:2] == (
        "data", "_staging"
    )
    assert registry.DEFAULT_TEMPLATE.name.endswith("_template_v0.1.json")
