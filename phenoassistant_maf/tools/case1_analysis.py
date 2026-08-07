"""Deterministic Case 1 CPU analysis tools for production MAF."""

from __future__ import annotations

import inspect
import math
from collections import deque
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Literal, Mapping, Protocol

from agent_framework import FunctionTool
from pydantic import BaseModel, ConfigDict, field_validator

from phenoassistant_maf.tools.statistics import (
    AnovaCallable,
    TukeyCallable,
    resolve_real_anova_callable,
    resolve_real_tukey_callable,
)

CASE1_LONGITUDINAL_PHENOTYPES: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "leaf_count": ("leaf_count", "Leaf count"),
        "projected_leaf_area": ("pla", "Projected leaf area"),
        "diameter": ("plant_diameter", "Plant diameter"),
        "perimeter": ("plant_perimeter", "Plant perimeter"),
    }
)


def _normalise_trusted_path(value: str, label: str) -> str:
    normalised = value.strip()
    if not normalised:
        raise ValueError(f"trusted {label} must not be blank")
    return normalised


def _finite_float(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must be a finite number") from exc
    if not math.isfinite(number):
        raise TypeError(f"{label} must be a finite number")
    return number


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise TypeError(f"{label} must be a positive integer")
    return value


def _normalise_alpha(value: float, label: str) -> float:
    alpha = _finite_float(value, label)
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"{label} must be between 0 and 1")
    return alpha


class LongitudinalPlotInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    phenotypes: list[str]

    @field_validator("phenotypes")
    @classmethod
    def normalise_phenotypes(cls, values: list[str]) -> list[str]:
        normalised = [value.strip() for value in values]
        if not normalised:
            raise ValueError("at least one phenotype is required")
        if any(not value for value in normalised):
            raise ValueError("phenotype names must not be blank")
        if len(normalised) != len(set(normalised)):
            raise ValueError("phenotype names must be unique")
        return normalised


class LongitudinalPlotEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    phenotype: str
    plot_path: str
    stats_path: str
    ecotype_count: int
    time_point_count: int
    grouped_rows: int


class LongitudinalPlotResult(BaseModel):
    schema_version: Literal["1"] = "1"
    tool_name: Literal["plot_longitudinal_phenotypes"] = (
        "plot_longitudinal_phenotypes"
    )
    arguments: LongitudinalPlotInput
    plots: list[LongitudinalPlotEvidence]


class EcotypeRankingInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    phenotype: str

    @field_validator("phenotype")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        normalised = value.strip()
        if not normalised:
            raise ValueError("ranking phenotype must not be blank")
        return normalised


class EcotypeRankEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    rank: int
    ecotype: str
    observation_count: int
    subject_count: int
    observation_mean: float
    subject_mean: float


class EcotypeRankingResult(BaseModel):
    schema_version: Literal["1"] = "1"
    tool_name: Literal["rank_ecotypes_by_phenotype"] = (
        "rank_ecotypes_by_phenotype"
    )
    arguments: EcotypeRankingInput
    rankings: list[EcotypeRankEvidence]


class RepeatedMeasuresPosthocInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    descriptor: str

    @field_validator("descriptor")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        normalised = value.strip()
        if not normalised:
            raise ValueError("analysis descriptor must not be blank")
        return normalised


class InteractionEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    source: str
    df1: float
    df2: float
    f_value: float
    p_value: float
    alpha: float
    significant: bool


class PairwiseEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    group_a: str
    group_b: str
    mean_a: float
    mean_b: float
    difference: float
    p_value: float
    alpha: float
    significant: bool


class OrderedGroupEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    rank: int
    label: str
    members: tuple[str, ...]
    mean: float


class RepeatedMeasuresPosthocResult(BaseModel):
    schema_version: Literal["1"] = "1"
    tool_name: Literal["analyse_repeated_measures_with_posthoc"] = (
        "analyse_repeated_measures_with_posthoc"
    )
    arguments: RepeatedMeasuresPosthocInput
    interaction: InteractionEvidence
    pairwise_comparisons: list[PairwiseEvidence]
    grouping_supported: bool
    grouping_note: str
    ordered_groups: list[OrderedGroupEvidence]


class LongitudinalPlotCallable(Protocol):
    def __call__(
        self,
        data_path: str,
        output_dir: str,
        phenotypes: tuple[str, ...],
    ) -> Mapping[str, Mapping[str, Any]]: ...


class RankingCallable(Protocol):
    def __call__(
        self,
        data_path: str,
        phenotype: str,
        group_column: str,
        subject_id_column: str,
    ) -> Mapping[str, Any]: ...


LongitudinalPlotHandler = Callable[[tuple[str, ...]], LongitudinalPlotResult]
EcotypeRankingHandler = Callable[[str], EcotypeRankingResult]
RepeatedMeasuresPosthocHandler = Callable[[str], RepeatedMeasuresPosthocResult]


def run_longitudinal_plots(
    data_path: str,
    output_dir: str,
    phenotypes: tuple[str, ...],
) -> Mapping[str, Mapping[str, Any]]:
    import matplotlib

    matplotlib.use("Agg", force=True)

    import matplotlib.pyplot as plt
    import pandas as pd

    data = pd.read_csv(data_path)
    required_columns = {"ecotype", "days_after_sowing", *phenotypes}
    missing = sorted(required_columns.difference(data.columns))
    if missing:
        raise ValueError(
            "trusted CSV is missing required columns: " + ", ".join(missing)
        )

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    results: dict[str, Mapping[str, Any]] = {}

    for phenotype in phenotypes:
        output_stem, display_name = CASE1_LONGITUDINAL_PHENOTYPES[phenotype]
        grouped = (
            data.groupby(["ecotype", "days_after_sowing"], as_index=False)[
                phenotype
            ]
            .agg(["mean", "std"])
        )
        grouped["std"] = grouped["std"].fillna(0.0)

        stats_path = destination / f"{output_stem}_stats.csv"
        plot_path = destination / f"{output_stem}_plot.png"
        grouped.to_csv(stats_path, index=False)

        figure, axis = plt.subplots()
        for ecotype in sorted(grouped["ecotype"].astype(str).unique()):
            ecotype_data = grouped[
                grouped["ecotype"].astype(str) == ecotype
            ].sort_values("days_after_sowing")
            x_values = ecotype_data["days_after_sowing"].to_numpy(dtype=float)
            means = ecotype_data["mean"].to_numpy(dtype=float)
            deviations = ecotype_data["std"].to_numpy(dtype=float)
            axis.plot(x_values, means, label=ecotype)
            axis.fill_between(
                x_values,
                means - deviations,
                means + deviations,
                alpha=0.2,
            )

        axis.set_title(
            f"Mean and STD of {display_name} for each ecotype over time"
        )
        axis.set_xlabel("Days after sowing")
        axis.set_ylabel(display_name)
        axis.legend(title="Ecotype")
        axis.grid(False)
        figure.tight_layout()
        figure.savefig(plot_path)
        plt.close(figure)

        results[phenotype] = {
            "plot_path": str(plot_path),
            "stats_path": str(stats_path),
            "ecotype_count": int(grouped["ecotype"].nunique()),
            "time_point_count": int(grouped["days_after_sowing"].nunique()),
            "grouped_rows": int(len(grouped)),
        }

    return results


def run_ecotype_ranking(
    data_path: str,
    phenotype: str,
    group_column: str,
    subject_id_column: str,
) -> Mapping[str, Any]:
    import pandas as pd

    data = pd.read_csv(data_path)
    required_columns = {phenotype, group_column, subject_id_column}
    missing = sorted(required_columns.difference(data.columns))
    if missing:
        raise ValueError(
            "trusted CSV is missing required columns: " + ", ".join(missing)
        )

    subject_means = data.groupby(
        [group_column, subject_id_column], as_index=False
    )[phenotype].mean()
    observation_summary = (
        data.groupby(group_column)[phenotype]
        .agg(["count", "mean"])
        .rename(
            columns={
                "count": "observation_count",
                "mean": "observation_mean",
            }
        )
    )
    subject_summary = (
        subject_means.groupby(group_column)[phenotype]
        .agg(["count", "mean"])
        .rename(columns={"count": "subject_count", "mean": "subject_mean"})
    )
    summary = observation_summary.join(subject_summary, how="inner").reset_index()
    summary[group_column] = summary[group_column].astype(str)
    summary = summary.sort_values(
        ["subject_mean", group_column], ascending=[False, True]
    ).reset_index(drop=True)

    return {
        "rankings": [
            {
                "rank": index + 1,
                "ecotype": row[group_column],
                "observation_count": int(row["observation_count"]),
                "subject_count": int(row["subject_count"]),
                "observation_mean": float(row["observation_mean"]),
                "subject_mean": float(row["subject_mean"]),
            }
            for index, row in summary.iterrows()
        ]
    }


def _build_ordered_groups(
    comparisons: list[PairwiseEvidence],
) -> tuple[bool, str, list[OrderedGroupEvidence]]:
    means: dict[str, float] = {}
    significance: dict[frozenset[str], bool] = {}

    for comparison in comparisons:
        means[comparison.group_a] = comparison.mean_a
        means[comparison.group_b] = comparison.mean_b
        key = frozenset((comparison.group_a, comparison.group_b))
        if len(key) != 2:
            return False, "A self-comparison prevented deterministic grouping.", []
        significance[key] = comparison.significant

    names = sorted(means)
    if not names:
        return False, "No pairwise comparisons were returned.", []

    expected_pairs = len(names) * (len(names) - 1) // 2
    if len(significance) != expected_pairs:
        return (
            False,
            "Pairwise evidence was incomplete, so groups were not inferred.",
            [],
        )

    neighbours = {name: set() for name in names}
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            if not significance[frozenset((left, right))]:
                neighbours[left].add(right)
                neighbours[right].add(left)

    components: list[tuple[str, ...]] = []
    remaining = set(names)
    while remaining:
        queue = deque([min(remaining)])
        component = set()
        while queue:
            current = queue.popleft()
            if current in component:
                continue
            component.add(current)
            queue.extend(sorted(neighbours[current] - component))
        remaining.difference_update(component)
        components.append(tuple(sorted(component)))

    for component in components:
        for left_index, left in enumerate(component):
            for right in component[left_index + 1 :]:
                if significance[frozenset((left, right))]:
                    return (
                        False,
                        "Non-significance was not transitive; groups were not inferred.",
                        [],
                    )

    for left_index, left_component in enumerate(components):
        for right_component in components[left_index + 1 :]:
            for left in left_component:
                for right in right_component:
                    if not significance[frozenset((left, right))]:
                        return (
                            False,
                            "At least one cross-group comparison was not significant.",
                            [],
                        )

    components.sort(
        key=lambda component: (
            -sum(means[name] for name in component) / len(component),
            component,
        )
    )
    labels = (
        ("large", "medium", "small")
        if len(components) == 3
        else tuple(f"rank_{index}" for index in range(1, len(components) + 1))
    )
    groups = [
        OrderedGroupEvidence(
            rank=index,
            label=labels[index - 1],
            members=component,
            mean=sum(means[name] for name in component) / len(component),
        )
        for index, component in enumerate(components, start=1)
    ]
    return (
        True,
        "Pairwise non-significance formed disjoint cliques and every "
        "cross-group comparison was significant.",
        groups,
    )


def build_longitudinal_plot_handler(
    data_path: str,
    output_dir: str,
    plot_callable: LongitudinalPlotCallable | None = None,
) -> LongitudinalPlotHandler:
    trusted_data_path = _normalise_trusted_path(data_path, "data_path")
    trusted_output_dir = _normalise_trusted_path(output_dir, "output_dir")
    implementation = run_longitudinal_plots if plot_callable is None else plot_callable

    def plot_longitudinal_phenotypes(
        phenotypes: list[str],
    ) -> LongitudinalPlotResult:
        arguments = LongitudinalPlotInput(phenotypes=phenotypes)
        unsupported = sorted(
            set(arguments.phenotypes).difference(CASE1_LONGITUDINAL_PHENOTYPES)
        )
        if unsupported:
            raise ValueError(
                "unsupported Case 1 phenotypes: " + ", ".join(unsupported)
            )

        evidence = implementation(
            trusted_data_path,
            trusted_output_dir,
            tuple(arguments.phenotypes),
        )
        if not isinstance(evidence, Mapping):
            raise TypeError("plot implementation must return a mapping")

        plots = []
        for phenotype in arguments.phenotypes:
            record = evidence.get(phenotype)
            if not isinstance(record, Mapping):
                raise TypeError(f"plot evidence for {phenotype} must be a mapping")
            plot_path = str(record.get("plot_path", "")).strip()
            stats_path = str(record.get("stats_path", "")).strip()
            if not plot_path or not stats_path:
                raise TypeError("plot and stats paths must not be blank")
            plots.append(
                LongitudinalPlotEvidence(
                    phenotype=phenotype,
                    plot_path=plot_path,
                    stats_path=stats_path,
                    ecotype_count=_positive_int(
                        record.get("ecotype_count"), "ecotype_count"
                    ),
                    time_point_count=_positive_int(
                        record.get("time_point_count"), "time_point_count"
                    ),
                    grouped_rows=_positive_int(
                        record.get("grouped_rows"), "grouped_rows"
                    ),
                )
            )

        return LongitudinalPlotResult(arguments=arguments, plots=plots)

    if tuple(inspect.signature(plot_longitudinal_phenotypes).parameters) != (
        "phenotypes",
    ):
        raise RuntimeError("longitudinal plot handler exposes an unexpected signature")
    return plot_longitudinal_phenotypes


def build_ecotype_ranking_handler(
    data_path: str,
    ranking_callable: RankingCallable | None = None,
) -> EcotypeRankingHandler:
    trusted_data_path = _normalise_trusted_path(data_path, "data_path")
    implementation = run_ecotype_ranking if ranking_callable is None else ranking_callable

    def rank_ecotypes_by_phenotype(phenotype: str) -> EcotypeRankingResult:
        arguments = EcotypeRankingInput(phenotype=phenotype)
        if arguments.phenotype not in CASE1_LONGITUDINAL_PHENOTYPES:
            raise ValueError("unsupported Case 1 phenotype: " + arguments.phenotype)

        evidence = implementation(
            trusted_data_path, arguments.phenotype, "ecotype", "plant_id"
        )
        if not isinstance(evidence, Mapping):
            raise TypeError("ranking implementation must return a mapping")
        raw_rankings = evidence.get("rankings")
        if not isinstance(raw_rankings, list) or not raw_rankings:
            raise TypeError("ranking implementation must return non-empty rankings")

        rankings = []
        for raw_record in raw_rankings:
            if not isinstance(raw_record, Mapping):
                raise TypeError("each ranking record must be a mapping")
            ecotype = str(raw_record.get("ecotype", "")).strip()
            if not ecotype:
                raise TypeError("ranking ecotype must not be blank")
            rankings.append(
                EcotypeRankEvidence(
                    rank=_positive_int(raw_record.get("rank"), "rank"),
                    ecotype=ecotype,
                    observation_count=_positive_int(
                        raw_record.get("observation_count"), "observation_count"
                    ),
                    subject_count=_positive_int(
                        raw_record.get("subject_count"), "subject_count"
                    ),
                    observation_mean=_finite_float(
                        raw_record.get("observation_mean"), "observation_mean"
                    ),
                    subject_mean=_finite_float(
                        raw_record.get("subject_mean"), "subject_mean"
                    ),
                )
            )

        if [record.rank for record in rankings] != list(
            range(1, len(rankings) + 1)
        ):
            raise TypeError("ranking records must have contiguous ordered ranks")
        return EcotypeRankingResult(arguments=arguments, rankings=rankings)

    if tuple(inspect.signature(rank_ecotypes_by_phenotype).parameters) != (
        "phenotype",
    ):
        raise RuntimeError("ecotype ranking handler exposes an unexpected signature")
    return rank_ecotypes_by_phenotype


def build_repeated_measures_posthoc_handler(
    data_path: str,
    anova_callable: AnovaCallable | None = None,
    tukey_callable: TukeyCallable | None = None,
    interaction_alpha: float = 0.01,
    posthoc_alpha: float = 0.05,
) -> RepeatedMeasuresPosthocHandler:
    trusted_data_path = _normalise_trusted_path(data_path, "data_path")
    trusted_interaction_alpha = _normalise_alpha(
        interaction_alpha, "interaction_alpha"
    )
    trusted_posthoc_alpha = _normalise_alpha(posthoc_alpha, "posthoc_alpha")
    anova_implementation = (
        resolve_real_anova_callable() if anova_callable is None else anova_callable
    )
    tukey_implementation = (
        resolve_real_tukey_callable() if tukey_callable is None else tukey_callable
    )

    def analyse_repeated_measures_with_posthoc(
        descriptor: str,
    ) -> RepeatedMeasuresPosthocResult:
        arguments = RepeatedMeasuresPosthocInput(descriptor=descriptor)
        anova_records = anova_implementation(
            trusted_data_path,
            arguments.descriptor,
            "days_after_sowing",
            "ecotype",
            "plant_id",
            save_path=None,
        )
        tukey_records = tukey_implementation(
            trusted_data_path,
            arguments.descriptor,
            "ecotype",
            "plant_id",
            save_path=None,
        )
        if not isinstance(anova_records, list):
            raise TypeError("ANOVA implementation must return list[dict]")
        if not isinstance(tukey_records, list):
            raise TypeError("Tukey implementation must return list[dict]")

        interaction_record = next(
            (
                record
                for record in anova_records
                if isinstance(record, Mapping)
                and str(record.get("Source", "")).strip().lower() == "interaction"
            ),
            None,
        )
        if interaction_record is None:
            raise ValueError("ANOVA results did not contain an Interaction row")
        interaction_p = _finite_float(
            interaction_record.get("p-unc"), "interaction p-value"
        )
        interaction = InteractionEvidence(
            source=str(interaction_record.get("Source", "")).strip(),
            df1=_finite_float(interaction_record.get("DF1"), "interaction DF1"),
            df2=_finite_float(interaction_record.get("DF2"), "interaction DF2"),
            f_value=_finite_float(interaction_record.get("F"), "interaction F"),
            p_value=interaction_p,
            alpha=trusted_interaction_alpha,
            significant=interaction_p < trusted_interaction_alpha,
        )

        comparisons = []
        for record in tukey_records:
            if not isinstance(record, Mapping):
                raise TypeError("each Tukey record must be a mapping")
            group_a = str(record.get("A", "")).strip()
            group_b = str(record.get("B", "")).strip()
            if not group_a or not group_b:
                raise TypeError("Tukey group names must not be blank")
            p_value = _finite_float(record.get("p-tukey"), "Tukey p-value")
            comparisons.append(
                PairwiseEvidence(
                    group_a=group_a,
                    group_b=group_b,
                    mean_a=_finite_float(record.get("mean(A)"), "Tukey mean(A)"),
                    mean_b=_finite_float(record.get("mean(B)"), "Tukey mean(B)"),
                    difference=_finite_float(
                        record.get("diff"), "Tukey difference"
                    ),
                    p_value=p_value,
                    alpha=trusted_posthoc_alpha,
                    significant=p_value < trusted_posthoc_alpha,
                )
            )

        grouping_supported, grouping_note, ordered_groups = _build_ordered_groups(
            comparisons
        )
        return RepeatedMeasuresPosthocResult(
            arguments=arguments,
            interaction=interaction,
            pairwise_comparisons=comparisons,
            grouping_supported=grouping_supported,
            grouping_note=grouping_note,
            ordered_groups=ordered_groups,
        )

    if tuple(
        inspect.signature(analyse_repeated_measures_with_posthoc).parameters
    ) != ("descriptor",):
        raise RuntimeError(
            "combined statistics handler exposes an unexpected signature"
        )
    return analyse_repeated_measures_with_posthoc


def create_longitudinal_plot_tool(
    data_path: str,
    output_dir: str,
    plot_callable: LongitudinalPlotCallable | None = None,
) -> FunctionTool:
    return FunctionTool(
        name="plot_longitudinal_phenotypes",
        description=(
            "Plot mean and standard deviation over time for selected trusted "
            "Case 1 phenotypes, grouped by ecotype."
        ),
        func=build_longitudinal_plot_handler(
            data_path=data_path,
            output_dir=output_dir,
            plot_callable=plot_callable,
        ),
        input_model=LongitudinalPlotInput,
    )


def create_ecotype_ranking_tool(
    data_path: str,
    ranking_callable: RankingCallable | None = None,
) -> FunctionTool:
    return FunctionTool(
        name="rank_ecotypes_by_phenotype",
        description=(
            "Rank Case 1 ecotypes from trusted CSV values using raw-observation "
            "and subject-level means."
        ),
        func=build_ecotype_ranking_handler(
            data_path=data_path, ranking_callable=ranking_callable
        ),
        input_model=EcotypeRankingInput,
    )


def create_repeated_measures_posthoc_tool(
    data_path: str,
    anova_callable: AnovaCallable | None = None,
    tukey_callable: TukeyCallable | None = None,
    interaction_alpha: float = 0.01,
    posthoc_alpha: float = 0.05,
) -> FunctionTool:
    return FunctionTool(
        name="analyse_repeated_measures_with_posthoc",
        description=(
            "Run the trusted Case 1 repeated-measures ANOVA and Tukey-Kramer "
            "workflow, report the interaction, and derive significance groups "
            "only when complete pairwise evidence supports them."
        ),
        func=build_repeated_measures_posthoc_handler(
            data_path=data_path,
            anova_callable=anova_callable,
            tukey_callable=tukey_callable,
            interaction_alpha=interaction_alpha,
            posthoc_alpha=posthoc_alpha,
        ),
        input_model=RepeatedMeasuresPosthocInput,
    )
