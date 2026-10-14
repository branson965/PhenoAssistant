"""Phase 7 v0.2 method-freeze integrity tests."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.research.verify_phenoguard_method_freeze import verify_manifest

ROOT = Path(__file__).resolve().parents[2]

MANIFEST_PATH = (
    ROOT
    / "docs"
    / "research"
    / "IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST.json"
)

ARCHIVED_V01_PATH = (
    ROOT
    / "docs"
    / "research"
    / "IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST_V0.1.json"
)


def load_manifest() -> dict:
    return json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8",
        )
    )


def load_v01() -> dict:
    return json.loads(
        ARCHIVED_V01_PATH.read_text(
            encoding="utf-8",
        )
    )


def test_freeze_manifest_has_expected_v02_identity() -> None:
    payload = load_manifest()

    assert payload["schema"] == (
        "phenoguard-ijcai2027-phase7-method-freeze-v0.2"
    )
    assert payload["venue"] == "IJCAI 2027"
    assert payload["date"] == "2026-10-14"

    source = payload["hash_source_commit"]

    assert len(source) == 40
    assert all(
        char in "0123456789abcdef"
        for char in source
    )


def test_v01_freeze_is_preserved_and_reopen_is_explicit() -> None:
    payload = load_manifest()
    prior = load_v01()

    reopen = payload["reopen"]

    assert prior["schema"] == (
        "phenoguard-ijcai2027-phase7-method-freeze-v0.1"
    )

    assert reopen["prior_schema"] == prior["schema"]
    assert reopen["prior_hash_source_commit"] == (
        prior["hash_source_commit"]
    )
    assert reopen["prior_aggregate_sha256"] == (
        prior["aggregate_sha256"]
    )

    assert (
        reopen["outcome_bearing_work_performed_before_reopen"]
        is False
    )
    assert (
        reopen["hidden_labels_inspected_before_reopen"]
        is False
    )

    assert reopen["record"] == (
        "docs/research/"
        "IJCAI_2027_PHASE7_REOPEN_CASE3_20261014.md"
    )


def test_freeze_manifest_contains_same_22_path_method_scope() -> None:
    payload = load_manifest()
    prior = load_v01()

    paths = set(
        payload["frozen_files"]
    )

    required = {
        "docs/research/SCIENTIFIC_APPLICABILITY_PAPER_PLAN.md",
        "docs/research/IJCAI_2027_PROTOCOL_FREEZE.json",
        "docs/research/IJCAI_2027_PROTOCOL_FREEZE.md",
        "research/phenoguard/contracts.py",
        "research/phenoguard/checker.py",
        "research/phenoguard/provenance.py",
        "research/phenoguard/catalogue.py",
        "research/phenoguard/training.py",
        "research/phenoguard/trace.py",
        "research/phenoguard/benchmark.py",
        "research/phenoguard/post_validation.py",
        "research/phenoguard/experiment_protocol.py",
        "research/phenoguard/pilot_manifest.py",
        "model_zoo.json",
    }

    assert required <= paths
    assert len(paths) == payload["frozen_file_count"] == 22
    assert paths == set(
        prior["frozen_files"]
    )


def test_v02_changes_only_authorised_case3_frozen_paths() -> None:
    payload = load_manifest()
    prior = load_v01()

    changed = {
        path
        for path, digest in payload["frozen_files"].items()
        if digest != prior["frozen_files"][path]
    }

    expected = {
        "docs/research/PHASE7_CATALOGUE_RESOLUTION.md",
        "model_zoo.json",
        "research/phenoguard/__init__.py",
        "research/phenoguard/provenance.py",
    }

    assert changed == expected
    assert set(
        payload["reopen"]["changed_frozen_paths"]
    ) == expected

    assert payload["aggregate_sha256"] != (
        prior["aggregate_sha256"]
    )


def test_freeze_manifest_hashes_match_worktree_exactly() -> None:
    payload = load_manifest()

    count, aggregate = verify_manifest()

    assert count == 22
    assert aggregate == payload["aggregate_sha256"]


def test_freeze_rules_preserve_blinding_and_negative_results() -> None:
    rules = load_manifest()["freeze_rules"]

    assert rules["negative_results_retained"] is True
    assert rules["hidden_labels_available_to_method"] is False
    assert rules["post_unblinding_method_changes_authorized"] is False
    assert rules["phase8_may_modify_frozen_files"] is False


def test_freeze_requires_explicit_reopen_for_scientific_method_changes() -> None:
    policy = load_manifest()["freeze_rules"]["change_policy"]

    assert "Phase 7 reopen" in policy
    assert "new manifest version" in policy
    assert "re-verification" in policy
