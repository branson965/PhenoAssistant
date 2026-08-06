"""Explicit construction of the production PhenoAssistant MAF tool registry."""

from __future__ import annotations

from dataclasses import dataclass

from agent_framework import FunctionTool

from phenoassistant_maf.tools import (
    AggregateCallable,
    AnovaCallable,
    CalculatorCallable,
    RegressionCallable,
    TukeyCallable,
    create_anova_tool,
    create_calculator_tool,
    create_csv_aggregate_tool,
    create_regression_comparison_tool,
    create_tukey_tool,
)


@dataclass(frozen=True)
class ProductionToolRegistry:
    """Immutable collection of explicitly constructed MAF tools."""

    tools: tuple[FunctionTool, ...]

    @property
    def names(self) -> tuple[str, ...]:
        """Return tool names in deterministic registration order."""
        return tuple(tool.name for tool in self.tools)

    def get(self, name: str) -> FunctionTool:
        """Resolve one registered tool by exact published name."""
        for tool in self.tools:
            if tool.name == name:
                return tool

        raise KeyError(f"tool is not registered: {name}")

    def as_list(self) -> list[FunctionTool]:
        """Return a new list suitable for MAF Agent construction."""
        return list(self.tools)


def build_production_tool_registry(
    data_path: str,
    calculator_callable: CalculatorCallable | None = None,
    anova_callable: AnovaCallable | None = None,
    tukey_callable: TukeyCallable | None = None,
    first_plot_path: str = "./results/maf_demo/potato_manual.png",
    second_plot_path: str = "./results/maf_demo/potato_algorithm.png",
    regression_callable: RegressionCallable | None = None,
    aggregate_callable: AggregateCallable | None = None,
) -> ProductionToolRegistry:
    """Construct the initial calculator, ANOVA, and Tukey registry."""
    tools = (
        create_calculator_tool(calculator_callable),
        create_anova_tool(data_path, anova_callable),
        create_tukey_tool(data_path, tukey_callable),
        create_regression_comparison_tool(
            data_path=data_path,
            first_plot_path=first_plot_path,
            second_plot_path=second_plot_path,
            regression_callable=regression_callable,
        ),
        create_csv_aggregate_tool(
            data_path=data_path,
            aggregate_callable=aggregate_callable,
        ),
    )

    names = tuple(tool.name for tool in tools)

    if len(names) != len(set(names)):
        raise ValueError("production tool names must be unique")

    return ProductionToolRegistry(tools=tools)
