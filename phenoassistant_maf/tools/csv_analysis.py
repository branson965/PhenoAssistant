"""Deterministic CPU tools for analysis of a trusted CSV dataset."""

from __future__ import annotations

import inspect
import math
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Literal, Protocol

from agent_framework import FunctionTool
from pydantic import BaseModel, ConfigDict, field_validator


def _normalise_trusted_path(value: str, label: str) -> str:
    """Trim and validate a trusted application-controlled path."""
    normalised = value.strip()

    if not normalised:
        raise ValueError(f"trusted {label} must not be blank")

    return normalised


def _finite_float(value: object, label: str) -> float:
    """Convert one numeric result while rejecting booleans and non-finite values."""
    if isinstance(value, bool):
        raise TypeError(f"{label} must be a finite number")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must be a finite number") from exc

    if not math.isfinite(number):
        raise TypeError(f"{label} must be a finite number")

    return number


class RegressionComparisonInput(BaseModel):
    """Model-controlled columns for two linear relationships."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    first_x_column: str
    second_x_column: str
    y_column: str

    @field_validator("*")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        stripped = value.strip()

        if not stripped:
            raise ValueError("regression column names must not be blank")

        return stripped


class RegressionLineResult(BaseModel):
    """Evidence for one fitted linear relationship."""

    model_config = ConfigDict(frozen=True)

    x_column: str
    y_column: str
    slope: float
    intercept: float
    r_value: float
    plot_path: str


class RegressionComparisonResult(BaseModel):
    """Stable evidence envelope for the two regression analyses."""

    schema_version: Literal["1"] = "1"
    tool_name: Literal[
        "compare_linear_relationships"
    ] = "compare_linear_relationships"
    arguments: RegressionComparisonInput
    analyses: list[RegressionLineResult]


class CsvAggregateInput(BaseModel):
    """Model-controlled grouped aggregate request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation: Literal["maximum", "mean"]
    value_column: str
    filter_column: str
    filter_value: str

    @field_validator(
        "value_column",
        "filter_column",
        "filter_value",
    )
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        stripped = value.strip()

        if not stripped:
            raise ValueError("CSV aggregate arguments must not be blank")

        return stripped


class CsvAggregateResult(BaseModel):
    """Stable evidence envelope for a grouped CSV aggregate."""

    schema_version: Literal["1"] = "1"
    tool_name: Literal[
        "query_csv_statistic"
    ] = "query_csv_statistic"
    arguments: CsvAggregateInput
    matching_rows: int
    result: float


class RegressionCallable(Protocol):
    """Boundary for one deterministic regression-and-plot execution."""

    def __call__(
        self,
        data_path: str,
        x_column: str,
        y_column: str,
        save_path: str,
    ) -> Mapping[str, Any]: ...


class AggregateCallable(Protocol):
    """Boundary for one deterministic grouped aggregate execution."""

    def __call__(
        self,
        data_path: str,
        operation: str,
        value_column: str,
        filter_column: str,
        filter_value: str,
    ) -> Mapping[str, Any]: ...


RegressionComparisonHandler = Callable[
    [str, str, str],
    RegressionComparisonResult,
]

CsvAggregateHandler = Callable[
    [str, str, str, str],
    CsvAggregateResult,
]


def run_linear_regression(
    data_path: str,
    x_column: str,
    y_column: str,
    save_path: str,
) -> Mapping[str, Any]:
    """Fit and plot one linear relationship using local CPU libraries."""
    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    import pandas as pd
    from scipy.stats import linregress

    data = pd.read_csv(data_path)

    missing = [
        column
        for column in (x_column, y_column)
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            "CSV is missing required columns: "
            + ", ".join(missing)
        )

    values = data[[x_column, y_column]].dropna()

    if len(values) < 2:
        raise ValueError(
            "linear regression requires at least two complete rows"
        )

    fitted = linregress(
        values[x_column],
        values[y_column],
    )

    target = Path(save_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    ordered = values.sort_values(x_column)

    figure, axes = plt.subplots()
    axes.scatter(
        values[x_column],
        values[y_column],
    )
    axes.plot(
        ordered[x_column],
        fitted.intercept
        + fitted.slope * ordered[x_column],
    )
    axes.set_xlabel(x_column)
    axes.set_ylabel(y_column)
    axes.set_title("Linear fit")
    figure.tight_layout()
    figure.savefig(target, dpi=150)
    plt.close(figure)

    return {
        "slope": fitted.slope,
        "intercept": fitted.intercept,
        "r_value": fitted.rvalue,
    }


def run_csv_aggregate(
    data_path: str,
    operation: str,
    value_column: str,
    filter_column: str,
    filter_value: str,
) -> Mapping[str, Any]:
    """Compute a case-insensitive grouped maximum or mean."""
    import pandas as pd

    data = pd.read_csv(data_path)

    missing = [
        column
        for column in (value_column, filter_column)
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            "CSV is missing required columns: "
            + ", ".join(missing)
        )

    selected = data.loc[
        data[filter_column]
        .astype(str)
        .str.casefold()
        == filter_value.casefold(),
        value_column,
    ].dropna()

    if selected.empty:
        raise ValueError(
            "no rows matched the requested filter"
        )

    if operation == "maximum":
        result = selected.max()
    elif operation == "mean":
        result = selected.mean()
    else:
        raise ValueError(
            "operation must be maximum or mean"
        )

    return {
        "matching_rows": int(len(selected)),
        "result": float(result),
    }


def build_regression_comparison_handler(
    data_path: str,
    first_plot_path: str,
    second_plot_path: str,
    regression_callable: RegressionCallable | None = None,
) -> RegressionComparisonHandler:
    """Bind trusted data and output paths behind three model arguments."""
    trusted_data_path = _normalise_trusted_path(
        data_path,
        "data_path",
    )
    trusted_first_plot_path = _normalise_trusted_path(
        first_plot_path,
        "first_plot_path",
    )
    trusted_second_plot_path = _normalise_trusted_path(
        second_plot_path,
        "second_plot_path",
    )

    implementation = (
        run_linear_regression
        if regression_callable is None
        else regression_callable
    )

    def compare_linear_relationships(
        first_x_column: str,
        second_x_column: str,
        y_column: str,
    ) -> RegressionComparisonResult:
        arguments = RegressionComparisonInput(
            first_x_column=first_x_column,
            second_x_column=second_x_column,
            y_column=y_column,
        )

        first = implementation(
            trusted_data_path,
            arguments.first_x_column,
            arguments.y_column,
            trusted_first_plot_path,
        )
        second = implementation(
            trusted_data_path,
            arguments.second_x_column,
            arguments.y_column,
            trusted_second_plot_path,
        )

        if not isinstance(first, Mapping) or not isinstance(
            second,
            Mapping,
        ):
            raise TypeError(
                "regression implementation must return mappings"
            )

        analyses = [
            RegressionLineResult(
                x_column=arguments.first_x_column,
                y_column=arguments.y_column,
                slope=_finite_float(first.get("slope"), "slope"),
                intercept=_finite_float(
                    first.get("intercept"),
                    "intercept",
                ),
                r_value=_finite_float(
                    first.get("r_value"),
                    "r_value",
                ),
                plot_path=trusted_first_plot_path,
            ),
            RegressionLineResult(
                x_column=arguments.second_x_column,
                y_column=arguments.y_column,
                slope=_finite_float(second.get("slope"), "slope"),
                intercept=_finite_float(
                    second.get("intercept"),
                    "intercept",
                ),
                r_value=_finite_float(
                    second.get("r_value"),
                    "r_value",
                ),
                plot_path=trusted_second_plot_path,
            ),
        ]

        return RegressionComparisonResult(
            arguments=arguments,
            analyses=analyses,
        )

    expected_parameters = (
        "first_x_column",
        "second_x_column",
        "y_column",
    )

    if (
        tuple(
            inspect.signature(
                compare_linear_relationships
            ).parameters
        )
        != expected_parameters
    ):
        raise RuntimeError(
            "regression handler exposes an unexpected signature"
        )

    return compare_linear_relationships


def build_csv_aggregate_handler(
    data_path: str,
    aggregate_callable: AggregateCallable | None = None,
) -> CsvAggregateHandler:
    """Bind the trusted CSV path behind four model arguments."""
    trusted_data_path = _normalise_trusted_path(
        data_path,
        "data_path",
    )

    implementation = (
        run_csv_aggregate
        if aggregate_callable is None
        else aggregate_callable
    )

    def query_csv_statistic(
        operation: str,
        value_column: str,
        filter_column: str,
        filter_value: str,
    ) -> CsvAggregateResult:
        arguments = CsvAggregateInput(
            operation=operation,
            value_column=value_column,
            filter_column=filter_column,
            filter_value=filter_value,
        )

        evidence = implementation(
            trusted_data_path,
            arguments.operation,
            arguments.value_column,
            arguments.filter_column,
            arguments.filter_value,
        )

        if not isinstance(evidence, Mapping):
            raise TypeError(
                "aggregate implementation must return a mapping"
            )

        matching_rows = evidence.get("matching_rows")

        if isinstance(matching_rows, bool) or not isinstance(
            matching_rows,
            int,
        ):
            raise TypeError(
                "matching_rows must be an integer"
            )

        return CsvAggregateResult(
            arguments=arguments,
            matching_rows=matching_rows,
            result=_finite_float(
                evidence.get("result"),
                "aggregate result",
            ),
        )

    expected_parameters = (
        "operation",
        "value_column",
        "filter_column",
        "filter_value",
    )

    if (
        tuple(
            inspect.signature(
                query_csv_statistic
            ).parameters
        )
        != expected_parameters
    ):
        raise RuntimeError(
            "CSV aggregate handler exposes an unexpected signature"
        )

    return query_csv_statistic


def create_regression_comparison_tool(
    data_path: str,
    first_plot_path: str,
    second_plot_path: str,
    regression_callable: RegressionCallable | None = None,
) -> FunctionTool:
    """Expose deterministic two-model regression comparison through MAF."""
    return FunctionTool(
        name="compare_linear_relationships",
        description=(
            "Fit two linear relationships against one response column, "
            "report both equations and Pearson correlations, and save "
            "plots to trusted application-controlled paths."
        ),
        func=build_regression_comparison_handler(
            data_path=data_path,
            first_plot_path=first_plot_path,
            second_plot_path=second_plot_path,
            regression_callable=regression_callable,
        ),
        input_model=RegressionComparisonInput,
    )


def create_csv_aggregate_tool(
    data_path: str,
    aggregate_callable: AggregateCallable | None = None,
) -> FunctionTool:
    """Expose a deterministic filtered maximum or mean through MAF."""
    return FunctionTool(
        name="query_csv_statistic",
        description=(
            "Compute a maximum or mean from a trusted CSV after applying "
            "one case-insensitive equality filter."
        ),
        func=build_csv_aggregate_handler(
            data_path=data_path,
            aggregate_callable=aggregate_callable,
        ),
        input_model=CsvAggregateInput,
    )
