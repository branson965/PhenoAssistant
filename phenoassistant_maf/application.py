"""Explicit composition of the production PhenoAssistant MAF application."""

from __future__ import annotations

from dataclasses import dataclass

from agent_framework import Agent, SupportsChatGetResponse

from phenoassistant_maf.manager import build_manager_agent
from phenoassistant_maf.registry import (
    ProductionToolRegistry,
    build_production_tool_registry,
)
from phenoassistant_maf.tools import (
    AnovaCallable,
    CalculatorCallable,
    TukeyCallable,
)


@dataclass(frozen=True)
class PhenoAssistantApplication:
    """Immutable initial production application graph."""

    manager: Agent
    registry: ProductionToolRegistry


def build_application(
    client: SupportsChatGetResponse,
    data_path: str,
    calculator_callable: CalculatorCallable | None = None,
    anova_callable: AnovaCallable | None = None,
    tukey_callable: TukeyCallable | None = None,
) -> PhenoAssistantApplication:
    """Build the production registry and Manager without global state."""
    registry = build_production_tool_registry(
        data_path=data_path,
        calculator_callable=calculator_callable,
        anova_callable=anova_callable,
        tukey_callable=tukey_callable,
    )

    manager = build_manager_agent(
        client=client,
        registry=registry,
    )

    return PhenoAssistantApplication(
        manager=manager,
        registry=registry,
    )
