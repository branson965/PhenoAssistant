"""Validate deterministic CSV analysis against the tracked potato demo data."""

from __future__ import annotations

from pathlib import Path

from phenoassistant_maf.tools.csv_analysis import (
    build_csv_aggregate_handler,
    build_regression_comparison_handler,
)

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "results/demo/potato_phenotypes.csv"


def test_real_potato_regression_comparison(
    tmp_path: Path,
) -> None:
    assert DATASET.is_file()

    manual_plot = tmp_path / "potato_manual.png"
    algorithm_plot = tmp_path / "potato_algorithm.png"

    handler = build_regression_comparison_handler(
        data_path=str(DATASET),
        first_plot_path=str(manual_plot),
        second_plot_path=str(algorithm_plot),
    )

    result = handler(
        "manual_leaf_area",
        "projected_leaf_area",
        "manual_dried_weight",
    )

    assert result.tool_name == "compare_linear_relationships"
    assert len(result.analyses) == 2

    manual = result.analyses[0]
    algorithm = result.analyses[1]

    assert manual.x_column == "manual_leaf_area"
    assert abs(manual.slope - 0.0019823477915018924) < 1e-15
    assert abs(manual.intercept - 0.04262671903070531) < 1e-15
    assert abs(manual.r_value - 0.8910860678113759) < 1e-15

    assert algorithm.x_column == "projected_leaf_area"
    assert abs(algorithm.slope - 0.0003433802936082736) < 1e-15
    assert abs(algorithm.intercept - 0.06349718502926727) < 1e-15
    assert abs(algorithm.r_value - 0.7598824217936114) < 1e-15

    assert manual_plot.is_file()
    assert manual_plot.stat().st_size > 0
    assert algorithm_plot.is_file()
    assert algorithm_plot.stat().st_size > 0


def test_real_desiree_grouped_statistics() -> None:
    assert DATASET.is_file()

    handler = build_csv_aggregate_handler(
        str(DATASET),
    )

    maximum = handler(
        "maximum",
        "manual_leaf_area",
        "Variety",
        "Desiree",
    )

    mean = handler(
        "mean",
        "manual_leaf_area",
        "Variety",
        "desiree",
    )

    assert maximum.tool_name == "query_csv_statistic"
    assert maximum.matching_rows == 22
    assert maximum.result == 649.69

    assert mean.matching_rows == 22
    assert abs(mean.result - 225.65568181818182) < 1e-12
