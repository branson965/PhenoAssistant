"""Tests for deterministic trusted-CSV analysis adapters."""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from typing import Any

import pytest
from pydantic import ValidationError

from phenoassistant_maf.tools.csv_analysis import (
    CsvAggregateInput,
    RegressionComparisonInput,
    build_csv_aggregate_handler,
    build_regression_comparison_handler,
    create_csv_aggregate_tool,
    create_regression_comparison_tool,
)


class RecordingRegression:
    def __init__(self, result: Mapping[str, Any] | object | None = None) -> None:
        self.result = (
            {
                "slope": 0.1,
                "intercept": 0.2,
                "r_value": 0.9,
            }
            if result is None
            else result
        )
        self.calls: list[tuple[str, str, str, str]] = []

    def __call__(
        self,
        data_path: str,
        x_column: str,
        y_column: str,
        save_path: str,
    ) -> object:
        self.calls.append(
            (data_path, x_column, y_column, save_path)
        )
        return self.result


class RecordingAggregate:
    def __init__(self, result: Mapping[str, Any] | object | None = None) -> None:
        self.result = (
            {
                "matching_rows": 22,
                "result": 649.69,
            }
            if result is None
            else result
        )
        self.calls: list[tuple[str, str, str, str, str]] = []

    def __call__(
        self,
        data_path: str,
        operation: str,
        value_column: str,
        filter_column: str,
        filter_value: str,
    ) -> object:
        self.calls.append(
            (
                data_path,
                operation,
                value_column,
                filter_column,
                filter_value,
            )
        )
        return self.result


def test_regression_input_trims_columns() -> None:
    arguments = RegressionComparisonInput(
        first_x_column=" manual_leaf_area ",
        second_x_column=" projected_leaf_area ",
        y_column=" manual_dried_weight ",
    )

    assert arguments.first_x_column == "manual_leaf_area"
    assert arguments.second_x_column == "projected_leaf_area"
    assert arguments.y_column == "manual_dried_weight"


def test_regression_input_rejects_blank_column() -> None:
    with pytest.raises(ValidationError):
        RegressionComparisonInput(
            first_x_column=" ",
            second_x_column="projected_leaf_area",
            y_column="manual_dried_weight",
        )


def test_aggregate_input_validates_and_trims_arguments() -> None:
    arguments = CsvAggregateInput(
        operation="maximum",
        value_column=" manual_leaf_area ",
        filter_column=" Variety ",
        filter_value=" Desiree ",
    )

    assert arguments.value_column == "manual_leaf_area"
    assert arguments.filter_column == "Variety"
    assert arguments.filter_value == "Desiree"

    with pytest.raises(ValidationError):
        CsvAggregateInput(
            operation="median",
            value_column="manual_leaf_area",
            filter_column="Variety",
            filter_value="Desiree",
        )


def test_regression_handler_binds_trusted_paths_and_delegates_twice() -> None:
    implementation = RecordingRegression()

    handler = build_regression_comparison_handler(
        data_path="/trusted/potatoes.csv",
        first_plot_path="/trusted/manual.png",
        second_plot_path="/trusted/algorithm.png",
        regression_callable=implementation,
    )

    result = handler(
        "manual_leaf_area",
        "projected_leaf_area",
        "manual_dried_weight",
    )

    assert implementation.calls == [
        (
            "/trusted/potatoes.csv",
            "manual_leaf_area",
            "manual_dried_weight",
            "/trusted/manual.png",
        ),
        (
            "/trusted/potatoes.csv",
            "projected_leaf_area",
            "manual_dried_weight",
            "/trusted/algorithm.png",
        ),
    ]

    assert result.tool_name == "compare_linear_relationships"
    assert len(result.analyses) == 2
    assert result.analyses[0].r_value == 0.9
    assert result.analyses[1].plot_path == "/trusted/algorithm.png"


def test_aggregate_handler_binds_trusted_path_and_delegates_once() -> None:
    implementation = RecordingAggregate()

    handler = build_csv_aggregate_handler(
        "/trusted/potatoes.csv",
        implementation,
    )

    result = handler(
        "maximum",
        "manual_leaf_area",
        "Variety",
        "Desiree",
    )

    assert implementation.calls == [
        (
            "/trusted/potatoes.csv",
            "maximum",
            "manual_leaf_area",
            "Variety",
            "Desiree",
        )
    ]

    assert result.tool_name == "query_csv_statistic"
    assert result.matching_rows == 22
    assert result.result == 649.69


def test_handlers_expose_only_model_controlled_arguments() -> None:
    regression = build_regression_comparison_handler(
        "/trusted/data.csv",
        "/trusted/first.png",
        "/trusted/second.png",
        RecordingRegression(),
    )
    aggregate = build_csv_aggregate_handler(
        "/trusted/data.csv",
        RecordingAggregate(),
    )

    assert tuple(inspect.signature(regression).parameters) == (
        "first_x_column",
        "second_x_column",
        "y_column",
    )
    assert tuple(inspect.signature(aggregate).parameters) == (
        "operation",
        "value_column",
        "filter_column",
        "filter_value",
    )


def test_handlers_reject_invalid_implementation_results() -> None:
    regression = build_regression_comparison_handler(
        "/trusted/data.csv",
        "/trusted/first.png",
        "/trusted/second.png",
        RecordingRegression(result="invalid"),
    )

    with pytest.raises(
        TypeError,
        match="must return mappings",
    ):
        regression("first", "second", "response")

    aggregate = build_csv_aggregate_handler(
        "/trusted/data.csv",
        RecordingAggregate(
            result={
                "matching_rows": "22",
                "result": 649.69,
            }
        ),
    )

    with pytest.raises(
        TypeError,
        match="matching_rows must be an integer",
    ):
        aggregate(
            "maximum",
            "manual_leaf_area",
            "Variety",
            "Desiree",
        )


def test_tool_names_preserve_published_contract() -> None:
    regression = create_regression_comparison_tool(
        "/trusted/data.csv",
        "/trusted/first.png",
        "/trusted/second.png",
        RecordingRegression(),
    )
    aggregate = create_csv_aggregate_tool(
        "/trusted/data.csv",
        RecordingAggregate(),
    )

    assert regression.name == "compare_linear_relationships"
    assert aggregate.name == "query_csv_statistic"


def test_handlers_reject_blank_trusted_paths() -> None:
    with pytest.raises(
        ValueError,
        match="trusted data_path must not be blank",
    ):
        build_csv_aggregate_handler(
            " ",
            RecordingAggregate(),
        )

    with pytest.raises(
        ValueError,
        match="trusted first_plot_path must not be blank",
    ):
        build_regression_comparison_handler(
            "/trusted/data.csv",
            " ",
            "/trusted/second.png",
            RecordingRegression(),
        )
