"""Production wiring tests for safe pipeline catalogue discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from phenoassistant_maf.manager import (
    CASE1_MANAGER_TOOLS,
    CASE1_PIPELINE_MANAGER_TOOLS,
    INITIAL_MANAGER_TOOLS,
    MANAGER_INSTRUCTIONS,
    MANAGER_INSTRUCTIONS_VERSION,
)
from phenoassistant_maf.registry import (
    build_production_tool_registry,
)


ROOT = Path(__file__).resolve().parents[2]
BASE_DATA = ROOT / "results/demo/potato_phenotypes.csv"
CASE1_DATA = ROOT / "results/Case1/aracrop_phenotypes.csv"
PIPELINE_ZOO = ROOT / "pipeline_zoo.json"


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
            "DF1": 1,
            "DF2": 1,
            "F": 1.0,
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
            "mean(A)": 1.0,
            "mean(B)": 2.0,
            "diff": -1.0,
            "p-tukey": 0.001,
        }
    ]


def build_registry(
    *,
    case1: bool = False,
    catalogue: bool = False,
):
    kwargs = {
        "data_path": str(BASE_DATA),
        "calculator_callable": calculator,
        "anova_callable": anova,
        "tukey_callable": tukey,
    }

    if case1:
        kwargs.update(
            {
                "case1_data_path": str(CASE1_DATA),
                "case1_anova_callable": anova,
                "case1_tukey_callable": tukey,
            }
        )

    if catalogue:
        kwargs["pipeline_zoo_path"] = str(
            PIPELINE_ZOO
        )

    return build_production_tool_registry(
        **kwargs
    )


def test_existing_manager_profiles_are_preserved() -> None:
    assert len(INITIAL_MANAGER_TOOLS) == 5
    assert len(CASE1_MANAGER_TOOLS) == 8
    assert INITIAL_MANAGER_TOOLS == CASE1_MANAGER_TOOLS[:5]


def test_pipeline_manager_profile_appends_exactly_one_safe_tool() -> None:
    assert len(CASE1_PIPELINE_MANAGER_TOOLS) == 9
    assert (
        CASE1_PIPELINE_MANAGER_TOOLS[:-1]
        == CASE1_MANAGER_TOOLS
    )
    assert (
        CASE1_PIPELINE_MANAGER_TOOLS[-1]
        == "get_pipeline_catalogue"
    )


def test_manager_v5_preserves_read_only_pipeline_catalogue() -> None:
    assert MANAGER_INSTRUCTIONS_VERSION == "phenoassistant-manager-v5"
    assert "get_pipeline_catalogue" in MANAGER_INSTRUCTIONS
    assert "without importing or executing" in MANAGER_INSTRUCTIONS


def test_registry_preserves_base_profile() -> None:
    registry = build_registry()

    assert registry.names == INITIAL_MANAGER_TOOLS


def test_registry_preserves_case1_profile_without_catalogue() -> None:
    registry = build_registry(
        case1=True,
    )

    assert registry.names == CASE1_MANAGER_TOOLS


def test_registry_builds_case1_plus_catalogue_profile() -> None:
    registry = build_registry(
        case1=True,
        catalogue=True,
    )

    assert registry.names == CASE1_PIPELINE_MANAGER_TOOLS

    tool = registry.get(
        "get_pipeline_catalogue"
    )

    assert tool.name == "get_pipeline_catalogue"


def test_catalogue_without_case1_profile_fails_closed() -> None:
    with pytest.raises(
        ValueError,
        match="pipeline catalogue requires the Case 1 tool profile",
    ):
        build_production_tool_registry(
            data_path=str(BASE_DATA),
            pipeline_zoo_path=str(PIPELINE_ZOO),
        )
