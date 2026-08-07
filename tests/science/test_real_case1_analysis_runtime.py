"""Scientific regression tests for Case 1 against the tracked Arabidopsis data."""

from __future__ import annotations

import math
from pathlib import Path

from phenoassistant_maf.tools.case1_analysis import (
    build_ecotype_ranking_handler,
    build_longitudinal_plot_handler,
    build_repeated_measures_posthoc_handler,
)

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "results/Case1/aracrop_phenotypes.csv"


def test_real_case1_longitudinal_outputs(tmp_path: Path) -> None:
    assert DATASET.is_file()

    handler = build_longitudinal_plot_handler(
        data_path=str(DATASET),
        output_dir=str(tmp_path),
    )

    result = handler(
        [
            "leaf_count",
            "projected_leaf_area",
            "diameter",
            "perimeter",
        ]
    )

    assert result.tool_name == "plot_longitudinal_phenotypes"
    assert [item.phenotype for item in result.plots] == [
        "leaf_count",
        "projected_leaf_area",
        "diameter",
        "perimeter",
    ]

    expected_stems = {
        "leaf_count": "leaf_count",
        "projected_leaf_area": "pla",
        "diameter": "plant_diameter",
        "perimeter": "plant_perimeter",
    }

    for item in result.plots:
        stem = expected_stems[item.phenotype]
        plot_path = Path(item.plot_path)
        stats_path = Path(item.stats_path)

        assert plot_path.name == f"{stem}_plot.png"
        assert stats_path.name == f"{stem}_stats.csv"
        assert plot_path.is_file()
        assert plot_path.stat().st_size > 0
        assert stats_path.is_file()
        assert stats_path.stat().st_size > 0
        assert item.ecotype_count == 5
        assert item.time_point_count == 52
        assert item.grouped_rows == 260


def test_real_case1_ecotype_ranking() -> None:
    assert DATASET.is_file()

    handler = build_ecotype_ranking_handler(
        data_path=str(DATASET),
    )

    result = handler("projected_leaf_area")

    assert result.tool_name == "rank_ecotypes_by_phenotype"
    assert [item.ecotype for item in result.rankings] == [
        "ein2",
        "col0",
        "adh1",
        "pgm",
        "ctr",
    ]

    assert [item.subject_count for item in result.rankings] == [
        5,
        5,
        4,
        5,
        5,
    ]

    assert math.isclose(
        result.rankings[0].subject_mean,
        8.948156538461538,
        rel_tol=1e-12,
    )
    assert math.isclose(
        result.rankings[-1].subject_mean,
        0.38613461538461535,
        rel_tol=1e-12,
    )


def test_real_case1_repeated_measures_and_posthoc() -> None:
    assert DATASET.is_file()

    handler = build_repeated_measures_posthoc_handler(
        data_path=str(DATASET),
        interaction_alpha=0.01,
        posthoc_alpha=0.05,
    )

    result = handler("projected_leaf_area")

    assert result.tool_name == "analyse_repeated_measures_with_posthoc"
    assert result.interaction.source == "Interaction"
    assert result.interaction.alpha == 0.01
    assert result.interaction.significant is True
    assert math.isclose(
        result.interaction.f_value,
        22.6669360372141,
        rel_tol=1e-12,
    )
    assert math.isclose(
        result.interaction.p_value,
        2.3834021910781097e-262,
        rel_tol=1e-12,
    )

    assert len(result.pairwise_comparisons) == 10
    assert all(
        comparison.alpha == 0.05
        for comparison in result.pairwise_comparisons
    )

    nonsignificant_pairs = {
        frozenset((comparison.group_a, comparison.group_b))
        for comparison in result.pairwise_comparisons
        if not comparison.significant
    }

    assert nonsignificant_pairs == {
        frozenset(("adh1", "pgm")),
        frozenset(("col0", "ein2")),
    }

    assert result.grouping_supported is True
    assert [group.label for group in result.ordered_groups] == [
        "large",
        "medium",
        "small",
    ]
    assert [list(group.members) for group in result.ordered_groups] == [
        ["col0", "ein2"],
        ["adh1", "pgm"],
        ["ctr"],
    ]
