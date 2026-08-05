"""Typed MAF adapter for the existing PhenoAssistant calculator."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Literal, Protocol, cast

from agent_framework import FunctionTool
from pydantic import BaseModel, ConfigDict


class CalculatorInput(BaseModel):
    """Model-controlled calculator arguments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    a: int
    b: int
    operator: Literal["+", "-", "*", "/"]


class CalculatorResult(BaseModel):
    """Stable result envelope for calculator execution."""

    schema_version: Literal["1"] = "1"
    tool_name: Literal["calculator"] = "calculator"
    arguments: CalculatorInput
    result: int


class CalculatorCallable(Protocol):
    """Callable boundary matching the existing calculator."""

    def __call__(
        self,
        a: int,
        b: int,
        operator: str,
    ) -> int: ...


CalculatorHandler = Callable[[int, int, str], CalculatorResult]


def resolve_real_calculator_callable() -> CalculatorCallable:
    """Import the original implementation only when explicitly requested."""
    from functions.generic_tools import calculator

    return cast(CalculatorCallable, calculator)


def build_calculator_handler(
    calculator_callable: CalculatorCallable | None = None,
) -> CalculatorHandler:
    """Create a typed handler that delegates to the original calculator."""
    implementation = (
        resolve_real_calculator_callable()
        if calculator_callable is None
        else calculator_callable
    )

    def calculate(
        a: int,
        b: int,
        operator: str,
    ) -> CalculatorResult:
        arguments = CalculatorInput(
            a=a,
            b=b,
            operator=operator,
        )

        result = implementation(
            arguments.a,
            arguments.b,
            arguments.operator,
        )

        if isinstance(result, bool) or not isinstance(result, int):
            raise TypeError(
                "calculator implementation must return an integer"
            )

        return CalculatorResult(
            arguments=arguments,
            result=result,
        )

    expected_parameters = ("a", "b", "operator")
    actual_parameters = tuple(
        inspect.signature(calculate).parameters
    )

    if actual_parameters != expected_parameters:
        raise RuntimeError(
            "calculator handler exposes an unexpected signature"
        )

    return calculate


def create_calculator_tool(
    calculator_callable: CalculatorCallable | None = None,
) -> FunctionTool:
    """Expose the original calculator through a typed MAF FunctionTool."""
    handler = build_calculator_handler(calculator_callable)

    return FunctionTool(
        name="calculator",
        description=(
            "Perform integer arithmetic using one of +, -, *, or /. "
            "Division preserves the original calculator's integer result."
        ),
        func=handler,
        input_model=CalculatorInput,
    )
