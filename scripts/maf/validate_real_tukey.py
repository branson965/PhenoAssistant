#!/usr/bin/env python3
"""Validate the preserved Tukey implementation on the canonical CPU fixture."""

from __future__ import annotations

import json
import math
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from functions.stat_test import perform_tukey_test

FIXTURE = ROOT / "tests/fixtures/maf/mixed_anova_plants.csv"


def normalise(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalise(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalise(item) for item in value]
    if hasattr(value, "item"):
        try:
            return normalise(value.item())
        except Exception:
            pass
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def canonical_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean = normalise(records)
    return sorted(
        clean,
        key=lambda record: (
            str(record.get("A", "")),
            str(record.get("B", "")),
        ),
    )


def main() -> None:
    if not FIXTURE.is_file():
        raise RuntimeError(f"Fixture not found: {FIXTURE}")

    records = perform_tukey_test(
        data_path=str(FIXTURE),
        descriptor="height",
        between_subject_factor="treatment",
        subject_id="plant_id",
        save_path=None,
    )

    if not isinstance(records, list):
        raise TypeError(f"Expected list result, found {type(records).__name__}")

    records = canonical_records(records)

    if len(records) != 3:
        raise AssertionError(f"Expected 3 pairwise records, found {len(records)}")

    expected_pairs = {
        frozenset(pair)
        for pair in combinations(("control", "low", "high"), 2)
    }
    observed_pairs = {
        frozenset((str(record["A"]), str(record["B"])))
        for record in records
    }

    if observed_pairs != expected_pairs:
        raise AssertionError(
            f"Unexpected Tukey pairs: {sorted(map(sorted, observed_pairs))}"
        )

    p_values = [float(record["p-tukey"]) for record in records]
    if not all(0.0 <= value <= 1.0 for value in p_values):
        raise AssertionError(f"Invalid Tukey p-values: {p_values}")

    significant = [value < 0.05 for value in p_values]
    if not all(significant):
        raise AssertionError(
            "The deterministic fixture should separate all three treatments at alpha 0.05"
        )

    print(f"REAL_TUKEY_DIRECT_RECORDS={len(records)}")
    print("REAL_TUKEY_GROUPS=control,high,low")
    print("REAL_TUKEY_SIGNIFICANT_PAIRS=3")
    print("REAL_TUKEY_DIRECT_PASS")
    print("REAL_TUKEY_SCIENTIFIC_FIXTURE_PASS")
    print("REAL_TUKEY_CANONICAL_JSON=" + json.dumps(records, sort_keys=True))


if __name__ == "__main__":
    main()
