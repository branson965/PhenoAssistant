"""Phase 8A pre-outcome experiment-branch guardrail tests."""

from __future__ import annotations

import json
from pathlib import Path

from research.phenoguard import ConditionId
from scripts.research.verify_phenoguard_method_freeze import verify_manifest


ROOT = Path(__file__).resolve().parents[2]


def test_experiment_branch_preserves_phase7_freeze() -> None:
    count, aggregate = verify_manifest()

    assert count == 22
    assert aggregate == (
        "337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f"
    )


def test_prompt_contract_covers_all_frozen_conditions() -> None:
    path = (
        ROOT
        / "experiments"
        / "ijcai2027"
        / "condition_prompt_contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert set(payload["conditions"]) == {
        item.value
        for item in ConditionId
    }


def test_prompt_contract_explicitly_blocks_hidden_gold_leakage() -> None:
    path = (
        ROOT
        / "experiments"
        / "ijcai2027"
        / "condition_prompt_contract.json"
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert any(
        "gold labels" in item.lower()
        for item in payload["invariants"]
    )


def test_runtime_capture_source_never_reads_api_key() -> None:
    source = (
        ROOT
        / "scripts"
        / "research"
        / "prepare_ijcai_runtime_controls.py"
    ).read_text(
        encoding="utf-8",
    )

    assert "OPENROUTER_API_KEY" not in source
    assert "api_key_read" in source
    assert '"api_key_read": False' in source
