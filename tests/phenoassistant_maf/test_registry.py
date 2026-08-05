"""Tests for the initial production MAF tool registry."""

from __future__ import annotations

import pytest

from phenoassistant_maf.registry import (
    build_production_tool_registry,
)


def calculator(a: int, b: int, operator: str) -> int:
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
    return [{"Source": "Interaction", "p-unc": 0.001}]


def tukey(
    data_path: str,
    descriptor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    return [{"A": "col0", "B": "ctr1", "p-tukey": 0.001}]


def build_registry():
    return build_production_tool_registry(
        data_path="/trusted/data.csv",
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )


def test_registry_has_deterministic_original_tool_names() -> None:
    registry = build_registry()

    assert registry.names == (
        "calculator",
        "perform_anova",
        "perform_tukey_test",
    )


def test_registry_resolves_tools_by_exact_name() -> None:
    registry = build_registry()

    assert registry.get("calculator").name == "calculator"
    assert registry.get("perform_anova").name == "perform_anova"
    assert (
        registry.get("perform_tukey_test").name
        == "perform_tukey_test"
    )


def test_registry_missing_name_is_visible() -> None:
    registry = build_registry()

    with pytest.raises(
        KeyError,
        match="tool is not registered",
    ):
        registry.get("missing_tool")


def test_registry_returns_a_new_agent_tool_list() -> None:
    registry = build_registry()

    first = registry.as_list()
    second = registry.as_list()

    assert first == second
    assert first is not second
