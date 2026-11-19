"""Offline, no-network regression checks for the Phase 8 budget gate."""

from __future__ import annotations

from decimal import Decimal

import pytest

from scripts.research import check_phase8_openrouter_budget as budget


def sample_prices():
    # USD per token, as if catalogue reports $0.10/$0.60 and $5/$30 per M.
    return {
        budget.LUNA: (Decimal("0.0000001"), Decimal("0.0000006")),
        budget.SOL: (Decimal("0.000005"), Decimal("0.00003")),
    }


def test_catalogue_prices_are_exact_model_slugs():
    payload = {
        "data": [
            {"id": budget.LUNA, "pricing": {"prompt": "0.0000001", "completion": "0.0000006"}},
            {"id": budget.SOL, "pricing": {"prompt": "0.000005", "completion": "0.00003"}},
            {"id": "openrouter/free", "pricing": {"prompt": "0", "completion": "0"}},
        ]
    }
    assert budget.extract_prices(payload) == sample_prices()


def test_missing_or_unpriced_model_fails_closed():
    with pytest.raises(ValueError, match="absent"):
        budget.extract_prices({
            "data": [{"id": budget.LUNA, "pricing": {"prompt": "0.01", "completion": "0.02"}}]
        })
    with pytest.raises(ValueError, match="unusable"):
        budget.extract_prices({
            "data": [
                {"id": budget.LUNA, "pricing": {"prompt": "-1", "completion": "0"}},
                {"id": budget.SOL, "pricing": {"prompt": "1", "completion": "1"}},
            ]
        })


def test_nine_dollar_plan_preserves_one_dollar_buffer():
    plan = budget.budget_plan(sample_prices(), available_usd=Decimal("9"))
    assert plan["luna_usd"] == Decimal("1.0550304")
    assert plan["sol_usd"] == Decimal("5.86464")
    assert plan["total_usd"] == Decimal("6.9196704")
    assert plan["ceiling_usd"] == Decimal("8.00")
    assert plan["headroom_usd"] == Decimal("1.0803296")


def test_breadth_expansion_without_budget_fails_headroom_check():
    plan = budget.budget_plan(
        sample_prices(), available_usd=Decimal("9"), sol_cases=12
    )
    assert plan["headroom_usd"] < 0


def test_key_probe_has_no_inference_endpoint_or_secret_printing():
    source = budget.__file__
    with open(source, encoding="utf-8") as handle:
        text = handle.read()
    assert "OPENROUTER_API_KEY" in text
    assert "print(key)" not in text
    assert "chat/completions" not in text
    assert "responses/create" not in text
    assert "PHASE8_OUTCOME_BEARING=false" in text
