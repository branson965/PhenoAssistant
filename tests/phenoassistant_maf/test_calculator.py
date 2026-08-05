"""Tests for the production calculator adapter."""

from __future__ import annotations

import inspect

import pytest
from pydantic import ValidationError

from phenoassistant_maf.tools.calculator import (
    build_calculator_handler,
    create_calculator_tool,
)


class RecordingCalculator:
    def __init__(self, result: object = 12) -> None:
        self.result = result
        self.calls: list[tuple[int, int, str]] = []

    def __call__(self, a: int, b: int, operator: str) -> object:
        self.calls.append((a, b, operator))
        return self.result


def test_calculator_handler_delegates_once() -> None:
    implementation = RecordingCalculator(result=12)
    handler = build_calculator_handler(implementation)

    result = handler(7, 5, "+")

    assert implementation.calls == [(7, 5, "+")]
    assert result.tool_name == "calculator"
    assert result.arguments.a == 7
    assert result.arguments.b == 5
    assert result.arguments.operator == "+"
    assert result.result == 12


def test_calculator_handler_rejects_invalid_operator() -> None:
    implementation = RecordingCalculator()
    handler = build_calculator_handler(implementation)

    with pytest.raises(ValidationError):
        handler(7, 5, "%")

    assert implementation.calls == []


def test_calculator_handler_rejects_non_integer_result() -> None:
    implementation = RecordingCalculator(result="12")
    handler = build_calculator_handler(implementation)

    with pytest.raises(TypeError, match="must return an integer"):
        handler(7, 5, "+")


def test_calculator_handler_exposes_only_model_arguments() -> None:
    handler = build_calculator_handler(RecordingCalculator())

    assert tuple(inspect.signature(handler).parameters) == (
        "a",
        "b",
        "operator",
    )


def test_calculator_tool_preserves_published_name() -> None:
    tool = create_calculator_tool(RecordingCalculator())

    assert tool.name == "calculator"
