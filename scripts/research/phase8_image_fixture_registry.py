"""Offline reviewed-image fixture binding for Phase 8 C3/C4/C8.

Qualification cases encode scientific request metadata, NOT approved images.
This module keeps any image path, dataset provenance, actual species and
internal scenario IDs in a private application-side registry. Such fields
must NEVER be sent to either Manager or Critic.

This does not select labels or outcomes, run a provider, instantiate an MCP
server, or claim supervisor approval. A structurally complete registry is
STILL NOT AUTHORISED: a separately reviewed SHA pin is required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phenoassistant_mcp.scientific_inference_v1 import (  # noqa: E402
    IMAGE_SUFFIXES, ASSET_RE, SHA256_RE, ImageAsset, file_sha256,
)
from research.phenoguard.pilot_manifest import build_development_validation_manifest  # noqa: E402
from scripts.research.phase8_attempt_ledger import load_verified_controls  # noqa: E402
from scripts.research.prepare_phase8_qualification_matrix import model_visible_view, sha256_value  # noqa: E402

SCHEMA = "phase8-image-fixture-registry-v0.1"
# This is intentionally under data/_staging/, already ignored in .gitignore.
# Real filesystem paths and access/reviewer records MUST NOT be committed.
DEFAULT_TEMPLATE = (
    ROOT / "data" / "_staging"
    / "phase8_image_fixture_binding_template_v0.1.json"
)
MAX_IMAGE_BYTES = 64 * 1024 * 1024
# Independent approval, intentionally unset. NEVER infer it from user input.
TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256: str | None = None
FIELDS = {
    "scenario_id_internal_only", "model_visible_view_sha256",
    "image_asset_id_internal_only", "image_path_internal_only",
    "image_sha256", "source_dataset", "source_image_id",
    "reviewed_species", "license_or_access_evidence", "reviewer_evidence_id",
}
LEAKAGE_FIELDS = frozenset(FIELDS - {"model_visible_view_sha256"})


class FixtureGateError(ValueError):
    """Image provenance, integrity or approval gate is not satisfied."""


def fixture_template() -> dict[str, Any]:
    matrix, _ = load_verified_controls()
    scenarios = build_development_validation_manifest()
    if len(scenarios) != 12 or matrix["trial_count"] != 108:
        raise FixtureGateError("qualification manifest/matrix count drift")
    expected = {
        row["scenario_id_internal_only"]: row["model_visible_view_sha256"]
        for row in matrix["trials"]
    }
    if len(expected) != 12:
        raise FixtureGateError("trial matrix lost unique scenario identity")
    entries = []
    for scenario in scenarios:
        view_hash = sha256_value(model_visible_view(scenario))
        if expected.get(scenario.scenario_id) != view_hash:
            raise FixtureGateError("scenario view hash does not match frozen 108-trial matrix")
        entries.append({
            "scenario_id_internal_only": scenario.scenario_id,
            "model_visible_view_sha256": view_hash,
            "image_asset_id_internal_only": None,
            "image_path_internal_only": None,
            "image_sha256": None,
            "source_dataset": None,
            "source_image_id": None,
            "reviewed_species": None,
            "license_or_access_evidence": None,
            "reviewer_evidence_id": None,
        })
    return {
        "schema": SCHEMA,
        "status": "PENDING_REAL_IMAGES_AND_INDEPENDENT_REVIEW",
        "qualification_matrix_sha256": "8a9688aa464564bf99121656430ea09fc93bbf2b1d262a73a9b2276944876692",
        "purpose": "private asset mapping only; never model-visible; never scientific outcomes",
        "entries": entries,
    }


def _checked_path(raw: str, trusted_root: Path) -> Path:
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise FixtureGateError("invalid image path")
    path = Path(raw)
    if not path.is_absolute() or ".." in path.parts or path.suffix.lower() not in IMAGE_SUFFIXES:
        raise FixtureGateError("image path must be absolute, clean and a permitted image type")
    root = trusted_root.resolve(strict=True)
    if not root.is_dir() or trusted_root.is_symlink():
        raise FixtureGateError("invalid trusted image root")
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise FixtureGateError("image path is outside the trusted image root") from exc
    if not relative.parts:
        raise FixtureGateError("image path cannot be the root")
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise FixtureGateError("image path traverses an untrusted symlink")
    if not path.is_file():
        raise FixtureGateError("image file is missing")
    size = path.stat().st_size
    if not (0 < size <= MAX_IMAGE_BYTES):
        raise FixtureGateError("image file is empty or exceeds single-image limit")
    # Recognised image extensions alone are not proof of readable image bytes.
    try:
        from PIL import Image
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        raise FixtureGateError("image file is not a decodable image") from exc
    return path


def audit_fixtures(registry: dict[str, Any], *, trusted_root: Path) -> dict[str, ImageAsset]:
    """Verify image identity across all 12 cases; does NOT grant approval.

    A valid, internally consistent registry may still have fabricated
    source/reviewer strings. Independent review and SHA pin remain separate.
    """
    template = fixture_template()
    if not isinstance(registry, dict) or set(registry) != set(template):
        raise FixtureGateError("registry top-level schema changed")
    if any(registry[key] != template[key] for key in template if key != "entries"):
        raise FixtureGateError("registry metadata or status differs from approved template contract")
    rows = registry["entries"]
    if not isinstance(rows, list) or len(rows) != 12:
        raise FixtureGateError("exactly 12 case bindings required")
    expected = {row["scenario_id_internal_only"]: row for row in template["entries"]}
    reviewed_species = {
        scenario.scenario_id: scenario.request.species
        for scenario in build_development_validation_manifest()
    }
    assets = {}
    observed_ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise FixtureGateError("image binding entry has missing/extra fields")
        scenario_id = row["scenario_id_internal_only"]
        if not isinstance(scenario_id, str) or scenario_id not in expected or scenario_id in observed_ids:
            raise FixtureGateError("unknown or duplicate private scenario identifier")
        observed_ids.add(scenario_id)
        if row["model_visible_view_sha256"] != expected[scenario_id]["model_visible_view_sha256"]:
            raise FixtureGateError("paired scientific request hash changed")
        asset_id = row["image_asset_id_internal_only"]
        if not isinstance(asset_id, str) or not ASSET_RE.fullmatch(asset_id):
            raise FixtureGateError("missing or invalid application-bound image asset ID")
        path = _checked_path(row["image_path_internal_only"], trusted_root)
        checksum = row["image_sha256"]
        if not isinstance(checksum, str) or not SHA256_RE.fullmatch(checksum):
            raise FixtureGateError("image digest must be a full SHA-256")
        if file_sha256(path) != checksum:
            raise FixtureGateError("image checksum changed after review")
        for field in ("source_dataset", "source_image_id",
                      "license_or_access_evidence", "reviewer_evidence_id"):
            value = row[field]
            if not isinstance(value, str) or not value.strip() or len(value) > 1024:
                raise FixtureGateError("source, access and reviewer evidence are required")
        declared_species = reviewed_species[scenario_id]
        image_species = row["reviewed_species"]
        if not isinstance(image_species, str) or not image_species.strip():
            raise FixtureGateError("reviewed image species is missing")
        if declared_species is not None and image_species.casefold() != declared_species.casefold():
            raise FixtureGateError("image species contradicts declared case request")
        if asset_id in assets and assets[asset_id] != ImageAsset(path, checksum):
            raise FixtureGateError("one image asset ID refers to conflicting files")
        assets[asset_id] = ImageAsset(path=path, sha256=checksum)
    if observed_ids != set(expected):
        raise FixtureGateError("qualification scenario missing from image registry")
    return assets


def verify_trusted_fixture_registry(
    *, file: Path, trusted_root: Path,
) -> dict[str, ImageAsset]:
    """Independently approved file pin is mandatory, not caller-supplied."""
    if TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256 is None:
        raise FixtureGateError("no independently reviewed image-registry SHA pinned")
    if not file.is_file() or file_sha256(file) != TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256:
        raise FixtureGateError("image-registry SHA does not match independent reviewer pin")
    return audit_fixtures(json.loads(file.read_text(encoding="utf-8")), trusted_root=trusted_root)


def model_visible_fields_must_exclude_fixture_data(prompt_object: dict[str, Any]) -> None:
    """Defence in depth for accidental fixture metadata injection."""
    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if LEAKAGE_FIELDS.intersection(value):
                raise FixtureGateError("private fixture/provenance data leaked into model context")
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    visit(prompt_object)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-template", action="store_true")
    args = parser.parse_args()
    try:
        template = fixture_template()
        if args.write_template:
            if DEFAULT_TEMPLATE.exists():
                raise FixtureGateError("template exists; refuse overwrite")
            DEFAULT_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
            DEFAULT_TEMPLATE.write_text(
                json.dumps(template, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            print("PHASE8_FIXTURE_TEMPLATE=" + DEFAULT_TEMPLATE.relative_to(ROOT).as_posix())
            print("PHASE8_FIXTURE_TEMPLATE_SHA256=" + file_sha256(DEFAULT_TEMPLATE))
    except (OSError, ValueError, KeyError) as exc:
        print("PHASE8_FIXTURE_PREFLIGHT_PASS=false")
        print("PHASE8_FIXTURE_REASON=" + str(exc))
        return 2
    print("PHASE8_FIXTURE_CASES=" + str(len(template["entries"])))
    print("PHASE8_FIXTURE_REAL_IMAGES_BOUND=0")
    print("PHASE8_FIXTURE_PRIVATE_SOURCE_FIELDS_MODEL_VISIBLE=false")
    print("PHASE8_FIXTURE_INDEPENDENT_REVIEW_APPROVED=false")
    print("PHASE8_FIXTURE_PROVIDER_CALLS=0")
    print("PHASE8_FIXTURE_SCIENTIFIC_EXECUTION=0")
    print("PHASE8_FIXTURE_READY_FOR_SCIENCE=false")
    print("PHASE8_FIXTURE_PREFLIGHT_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
