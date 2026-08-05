"""Tests for production Manager construction."""

from __future__ import annotations

import subprocess
import sys

import pytest
from agent_framework import Agent

from phenoassistant_maf.manager import (
    INITIAL_MANAGER_TOOLS,
    MANAGER_INSTRUCTIONS_VERSION,
    build_manager_agent,
)
from phenoassistant_maf.registry import (
    ProductionToolRegistry,
    build_production_tool_registry,
)
from tests.phenoassistant_maf.fakes import (
    ScriptedToolClient,
)


def calculator(
    a: int,
    b: int,
    operator: str,
) -> int:
    operations = {
        "+": a + b,
        "-": a - b,
        "*": a * b,
        "/": int(a / b),
    }

    return operations[operator]


def anova(
    data_path: str,
    descriptor: str,
    within_subject_factor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    return [
        {
            "Source": "Interaction",
            "p-unc": 0.001,
        }
    ]


def tukey(
    data_path: str,
    descriptor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    return [
        {
            "A": "control",
            "B": "treated",
            "p-tukey": 0.001,
        }
    ]


def build_registry() -> ProductionToolRegistry:
    return build_production_tool_registry(
        data_path="/trusted/data.csv",
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )


def test_manager_registers_exact_initial_tool_set() -> None:
    client = ScriptedToolClient(
        "calculator",
        {
            "a": 7,
            "b": 5,
            "operator": "+",
        },
    )

    manager = build_manager_agent(
        client,
        build_registry(),
    )

    assert isinstance(manager, Agent)

    tools = manager.default_options["tools"]

    assert tuple(
        tool.name
        for tool in tools
    ) == INITIAL_MANAGER_TOOLS

    assert (
        manager.default_options[
            "allow_multiple_tool_calls"
        ]
        is False
    )

    assert (
        manager.additional_properties[
            "instructions_version"
        ]
        == MANAGER_INSTRUCTIONS_VERSION
    )


def test_manager_rejects_incomplete_registry() -> None:
    full_registry = build_registry()

    incomplete_registry = ProductionToolRegistry(
        tools=full_registry.tools[:2]
    )

    client = ScriptedToolClient(
        "calculator",
        {
            "a": 1,
            "b": 1,
            "operator": "+",
        },
    )

    with pytest.raises(
        ValueError,
        match="initial Manager requires exactly",
    ):
        build_manager_agent(
            client,
            incomplete_registry,
        )


def test_importing_manager_does_not_load_scientific_modules() -> None:
    script = """
import sys
import phenoassistant_maf.manager

assert "functions.stat_test" not in sys.modules
assert "functions.generic_tools" not in sys.modules

print("MANAGER_IMPORT_SAFE")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "MANAGER_IMPORT_SAFE" in result.stdout
