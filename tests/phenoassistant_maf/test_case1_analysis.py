from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError

from phenoassistant_maf.tools.case1_analysis import (
    EcotypeRankingInput,
    LongitudinalPlotInput,
    RepeatedMeasuresPosthocInput,
    build_ecotype_ranking_handler,
    build_longitudinal_plot_handler,
    build_repeated_measures_posthoc_handler,
    create_ecotype_ranking_tool,
    create_longitudinal_plot_tool,
    create_repeated_measures_posthoc_tool,
)


def test_model_inputs_are_strict_and_trimmed() -> None:
    plots = LongitudinalPlotInput(
        phenotypes=(" leaf_count ", "projected_leaf_area"),
    )
    ranking = EcotypeRankingInput(phenotype=" projected_leaf_area ")
    repeated = RepeatedMeasuresPosthocInput(
        descriptor=" projected_leaf_area "
    )

    assert plots.phenotypes == ["leaf_count", "projected_leaf_area"]
    assert ranking.phenotype == "projected_leaf_area"
    assert repeated.descriptor == "projected_leaf_area"

    with pytest.raises(ValidationError):
        LongitudinalPlotInput(phenotypes=())

    with pytest.raises(ValidationError):
        EcotypeRankingInput(phenotype="   ")

    with pytest.raises(ValidationError):
        RepeatedMeasuresPosthocInput(descriptor="   ")

    with pytest.raises(ValidationError):
        EcotypeRankingInput(
            phenotype="projected_leaf_area",
            data_path="model-controlled.csv",
        )


def test_longitudinal_handler_binds_trusted_paths() -> None:
    calls: list[tuple[str, str, tuple[str, ...]]] = []

    def fake_plot(
        data_path: str,
        output_dir: str,
        phenotypes: tuple[str, ...],
    ):
        calls.append((data_path, output_dir, phenotypes))
        return {
            phenotype: {
                "plot_path": f"{output_dir}/{phenotype}_plot.png",
                "stats_path": f"{output_dir}/{phenotype}_stats.csv",
                "ecotype_count": 5,
                "time_point_count": 52,
                "grouped_rows": 260,
            }
            for phenotype in phenotypes
        }

    handler = build_longitudinal_plot_handler(
        data_path=" trusted.csv ",
        output_dir=" output-dir ",
        plot_callable=fake_plot,
    )

    assert tuple(inspect.signature(handler).parameters) == ("phenotypes",)

    result = handler(("leaf_count", "projected_leaf_area"))

    assert calls == [
        (
            "trusted.csv",
            "output-dir",
            ("leaf_count", "projected_leaf_area"),
        )
    ]
    assert result.tool_name == "plot_longitudinal_phenotypes"
    assert [item.phenotype for item in result.plots] == [
        "leaf_count",
        "projected_leaf_area",
    ]
    assert all(item.ecotype_count == 5 for item in result.plots)


def test_ranking_handler_binds_case1_grouping_columns() -> None:
    calls: list[tuple[str, str, str, str]] = []

    def fake_ranking(
        data_path: str,
        phenotype: str,
        group_column: str,
        subject_id_column: str,
    ):
        calls.append(
            (data_path, phenotype, group_column, subject_id_column)
        )
        return {
            "rankings": [
                {
                    "rank": 1,
                    "ecotype": "ein2",
                    "observation_count": 260,
                    "subject_count": 5,
                    "observation_mean": 8.9,
                    "subject_mean": 8.8,
                },
                {
                    "rank": 2,
                    "ecotype": "ctr",
                    "observation_count": 260,
                    "subject_count": 5,
                    "observation_mean": 0.4,
                    "subject_mean": 0.4,
                },
            ]
        }

    handler = build_ecotype_ranking_handler(
        data_path=" trusted.csv ",
        ranking_callable=fake_ranking,
    )

    assert tuple(inspect.signature(handler).parameters) == ("phenotype",)

    result = handler("projected_leaf_area")

    assert calls == [
        (
            "trusted.csv",
            "projected_leaf_area",
            "ecotype",
            "plant_id",
        )
    ]
    assert result.tool_name == "rank_ecotypes_by_phenotype"
    assert [item.ecotype for item in result.rankings] == ["ein2", "ctr"]


def test_repeated_measures_handler_binds_case1_factors_and_thresholds() -> None:
    anova_calls: list[tuple[object, ...]] = []
    tukey_calls: list[tuple[object, ...]] = []

    def fake_anova(
        data_path: str,
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ):
        anova_calls.append(
            (
                data_path,
                descriptor,
                within_subject_factor,
                between_subject_factor,
                subject_id,
                save_path,
            )
        )
        return [
            {
                "Source": "Interaction",
                "DF1": 204,
                "DF2": 969,
                "F": 22.6669360372141,
                "p-unc": 2.3834021910781097e-262,
            }
        ]

    means = {
        "ein2": 8.948156538461538,
        "col0": 7.563658846153847,
        "adh1": 4.403085576923077,
        "pgm": 2.8698542307692305,
        "ctr": 0.38613461538461535,
    }

    nonsignificant = {
        frozenset(("ein2", "col0")): 0.3553311998316586,
        frozenset(("adh1", "pgm")): 0.31523009195993934,
    }

    def fake_tukey(
        data_path: str,
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ):
        tukey_calls.append(
            (
                data_path,
                descriptor,
                between_subject_factor,
                subject_id,
                save_path,
            )
        )

        records = []
        groups = ("adh1", "col0", "ctr", "ein2", "pgm")

        for index, group_a in enumerate(groups):
            for group_b in groups[index + 1:]:
                p_value = nonsignificant.get(
                    frozenset((group_a, group_b)),
                    0.001,
                )
                records.append(
                    {
                        "A": group_a,
                        "B": group_b,
                        "mean(A)": means[group_a],
                        "mean(B)": means[group_b],
                        "diff": means[group_a] - means[group_b],
                        "p-tukey": p_value,
                    }
                )

        return records

    handler = build_repeated_measures_posthoc_handler(
        data_path=" trusted.csv ",
        anova_callable=fake_anova,
        tukey_callable=fake_tukey,
        interaction_alpha=0.01,
        posthoc_alpha=0.05,
    )

    assert tuple(inspect.signature(handler).parameters) == ("descriptor",)

    result = handler("projected_leaf_area")

    assert anova_calls == [
        (
            "trusted.csv",
            "projected_leaf_area",
            "days_after_sowing",
            "ecotype",
            "plant_id",
            None,
        )
    ]
    assert tukey_calls == [
        (
            "trusted.csv",
            "projected_leaf_area",
            "ecotype",
            "plant_id",
            None,
        )
    ]

    assert result.interaction.significant is True
    assert result.interaction.alpha == 0.01
    assert result.interaction.p_value == pytest.approx(
        2.3834021910781097e-262
    )
    assert len(result.pairwise_comparisons) == 10
    assert result.grouping_supported is True
    assert [tuple(group.members) for group in result.ordered_groups] == [
        ("col0", "ein2"),
        ("adh1", "pgm"),
        ("ctr",),
    ]
    assert [group.label for group in result.ordered_groups] == [
        "large",
        "medium",
        "small",
    ]


def test_tool_factories_publish_expected_names(tmp_path: Path) -> None:
    def fake_plot(data_path: str, output_dir: str, phenotypes: tuple[str, ...]):
        return {
            phenotype: {
                "plot_path": f"{output_dir}/{phenotype}.png",
                "stats_path": f"{output_dir}/{phenotype}.csv",
                "ecotype_count": 1,
                "time_point_count": 1,
                "grouped_rows": 1,
            }
            for phenotype in phenotypes
        }

    def fake_ranking(
        data_path: str,
        phenotype: str,
        group_column: str,
        subject_id_column: str,
    ):
        return {
            "rankings": [
                {
                    "rank": 1,
                    "ecotype": "ein2",
                    "observation_count": 1,
                    "subject_count": 1,
                    "observation_mean": 1.0,
                    "subject_mean": 1.0,
                }
            ]
        }

    def fake_anova(
        data_path: str,
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ):
        return [
            {
                "Source": "Interaction",
                "DF1": 1,
                "DF2": 1,
                "F": 1.0,
                "p-unc": 0.001,
            }
        ]

    def fake_tukey(
        data_path: str,
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ):
        return [
            {
                "A": "a",
                "B": "b",
                "mean(A)": 2.0,
                "mean(B)": 1.0,
                "diff": 1.0,
                "p-tukey": 0.001,
            }
        ]

    assert create_longitudinal_plot_tool(
        data_path="trusted.csv",
        output_dir=str(tmp_path),
        plot_callable=fake_plot,
    ).name == "plot_longitudinal_phenotypes"

    assert create_ecotype_ranking_tool(
        data_path="trusted.csv",
        ranking_callable=fake_ranking,
    ).name == "rank_ecotypes_by_phenotype"

    assert create_repeated_measures_posthoc_tool(
        data_path="trusted.csv",
        anova_callable=fake_anova,
        tukey_callable=fake_tukey,
    ).name == "analyse_repeated_measures_with_posthoc"


@pytest.mark.parametrize(
    ("builder", "kwargs"),
    [
        (
            build_longitudinal_plot_handler,
            {"data_path": " ", "output_dir": "out"},
        ),
        (
            build_longitudinal_plot_handler,
            {"data_path": "data.csv", "output_dir": " "},
        ),
        (
            build_ecotype_ranking_handler,
            {"data_path": " "},
        ),
        (
            build_repeated_measures_posthoc_handler,
            {"data_path": " "},
        ),
    ],
)
def test_blank_trusted_paths_are_rejected(builder, kwargs) -> None:
    with pytest.raises(ValueError):
        builder(**kwargs)
