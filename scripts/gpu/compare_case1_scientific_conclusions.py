"""Compare scientific Case 1 conclusions on regenerated vs tracked phenotypes.

This is the final scientific-parity gate after GPU regeneration. It compares the
mixed-ANOVA interaction decision and the Tukey-Kramer grouping for projected leaf
area using the historical PhenoAssistant statistical implementation.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from functions.stat_test import perform_anova, perform_tukey_test


REGENERATED = Path("results/maf_gpu_case1/aracrop_phenotypes.csv")
REFERENCE = Path("results/Case1/aracrop_phenotypes.csv")
OUTPUT = Path("results/maf_gpu_case1/scientific_conclusion_comparison.json")
DESCRIPTOR = "projected_leaf_area"
INTERACTION_ALPHA = 0.01
POSTHOC_ALPHA = 0.05


def _interaction(path: Path) -> dict[str, object]:
    rows = perform_anova(
        str(path),
        DESCRIPTOR,
        "days_after_sowing",
        "ecotype",
        "plant_id",
        save_path=None,
    )
    row = next(
        record
        for record in rows
        if str(record.get("Source", "")).strip().lower() == "interaction"
    )
    p_value = float(row["p-unc"])
    return {
        "f_value": float(row["F"]),
        "p_value": p_value,
        "alpha": INTERACTION_ALPHA,
        "significant": p_value < INTERACTION_ALPHA,
    }


def _pairwise(path: Path) -> tuple[dict[str, dict[str, object]], list[list[str]]]:
    rows = perform_tukey_test(
        str(path),
        DESCRIPTOR,
        "ecotype",
        "plant_id",
        save_path=None,
    )

    decisions: dict[str, dict[str, object]] = {}
    means: dict[str, float] = {}
    nonsig_edges: dict[str, set[str]] = {}

    for row in rows:
        left = str(row["A"])
        right = str(row["B"])
        p_value = float(row["p-tukey"])
        significant = p_value < POSTHOC_ALPHA
        key = "::".join(sorted((left, right)))
        decisions[key] = {
            "p_value": p_value,
            "alpha": POSTHOC_ALPHA,
            "significant": significant,
        }
        means[left] = float(row["mean(A)"])
        means[right] = float(row["mean(B)"])
        nonsig_edges.setdefault(left, set())
        nonsig_edges.setdefault(right, set())
        if not significant:
            nonsig_edges[left].add(right)
            nonsig_edges[right].add(left)

    # The historical Case 1 result forms disjoint non-significance cliques.
    remaining = set(means)
    groups: list[list[str]] = []
    while remaining:
        seed = min(remaining)
        stack = [seed]
        component: set[str] = set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            stack.extend(sorted(nonsig_edges.get(current, set()) - component))
        remaining.difference_update(component)
        groups.append(sorted(component))

    groups.sort(
        key=lambda members: (
            -sum(means[name] for name in members) / len(members),
            tuple(members),
        )
    )
    return decisions, groups


def main() -> Path:
    for path in (REGENERATED, REFERENCE):
        if not path.is_file():
            raise FileNotFoundError(path)

    regenerated_rows = len(pd.read_csv(REGENERATED))
    reference_rows = len(pd.read_csv(REFERENCE))

    regenerated_interaction = _interaction(REGENERATED)
    reference_interaction = _interaction(REFERENCE)
    regenerated_pairs, regenerated_groups = _pairwise(REGENERATED)
    reference_pairs, reference_groups = _pairwise(REFERENCE)

    pairwise_decisions_match = (
        set(regenerated_pairs) == set(reference_pairs)
        and all(
            regenerated_pairs[key]["significant"]
            == reference_pairs[key]["significant"]
            for key in reference_pairs
        )
    )
    interaction_decision_match = (
        regenerated_interaction["significant"]
        == reference_interaction["significant"]
    )
    grouping_match = regenerated_groups == reference_groups

    report = {
        "schema_version": "1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "descriptor": DESCRIPTOR,
        "rows": {
            "regenerated": regenerated_rows,
            "reference": reference_rows,
        },
        "interaction": {
            "regenerated": regenerated_interaction,
            "reference": reference_interaction,
            "decision_match": interaction_decision_match,
        },
        "tukey": {
            "regenerated_groups": regenerated_groups,
            "reference_groups": reference_groups,
            "pairwise_decisions_match": pairwise_decisions_match,
            "grouping_match": grouping_match,
            "regenerated": regenerated_pairs,
            "reference": reference_pairs,
        },
        "scientific_conclusion_match": (
            interaction_decision_match
            and pairwise_decisions_match
            and grouping_match
        ),
    }

    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(OUTPUT)
    print(
        json.dumps(
            {
                "interaction_decision_match": interaction_decision_match,
                "pairwise_decisions_match": pairwise_decisions_match,
                "grouping_match": grouping_match,
                "scientific_conclusion_match": report[
                    "scientific_conclusion_match"
                ],
                "regenerated_groups": regenerated_groups,
                "reference_groups": reference_groups,
            },
            sort_keys=True,
        )
    )

    if not report["scientific_conclusion_match"]:
        raise RuntimeError(
            "GPU-regenerated Case 1 scientific conclusions do not match "
            "the tracked reference"
        )

    return OUTPUT


if __name__ == "__main__":
    main()
