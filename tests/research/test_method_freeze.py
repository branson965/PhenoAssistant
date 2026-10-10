"""Phase 7I final method-freeze integrity tests."""

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


def load_manifest() -> dict:
    return json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8",
        )
    )


def test_freeze_manifest_has_expected_identity_and_parent_commit() -> None:
    payload = load_manifest()

    assert payload["schema"] == (
        "phenoguard-ijcai2027-phase7-method-freeze-v0.1"
    )
    assert payload["venue"] == "IJCAI 2027"
    assert payload["date"] == "2026-10-10"
    assert payload["hash_source_commit"] == (
        "c58741bb9b0bcc8ebef68755e3d8528de9533312"
    )


def test_freeze_manifest_contains_complete_method_snapshot() -> None:
    payload = load_manifest()
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


def test_freeze_manifest_hashes_match_worktree_exactly() -> None:
    count, aggregate = verify_manifest()

    assert count == 22
    assert aggregate == (
        "337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f"
    )


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
