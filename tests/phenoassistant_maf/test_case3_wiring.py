"""Production profile tests for the CPU-safe Case 3 capabilities."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from phenoassistant_maf.application import (
    build_application,
)
from phenoassistant_maf.manager import (
    CASE1_CASE3_MANAGER_TOOLS,
    CASE1_MANAGER_TOOLS,
    CASE1_PIPELINE_MANAGER_TOOLS,
    CASE3_MANAGER_TOOLS,
    FULL_CPU_MANAGER_TOOLS,
    INITIAL_MANAGER_TOOLS,
    MANAGER_INSTRUCTIONS,
    MANAGER_INSTRUCTIONS_VERSION,
)
from phenoassistant_maf.registry import (
    build_production_tool_registry,
)
from tests.phenoassistant_maf.fakes import (
    ScriptedToolClient,
)


ROOT = Path(__file__).resolve().parents[2]

MODEL_ZOO = ROOT / "model_zoo.json"
PIPELINE_ZOO = ROOT / "pipeline_zoo.json"

CASE3_DATASET = (
    ROOT
    / "data"
    / "winter-wheat_nutri-defi-identify_dndww20"
)


def calculator(
    a: int,
    b: int,
    operator: str,
) -> int:
    return 0


def anova(
    data_path: str,
    descriptor: str,
    within_subject_factor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    return []


def tukey(
    data_path: str,
    descriptor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    return []


def base_kwargs() -> dict[str, object]:
    return {
        "data_path": "/trusted/base.csv",
        "calculator_callable": calculator,
        "anova_callable": anova,
        "tukey_callable": tukey,
    }


def test_manager_v5_profiles_have_expected_sizes() -> None:
    assert len(INITIAL_MANAGER_TOOLS) == 5
    assert len(CASE3_MANAGER_TOOLS) == 7
    assert len(CASE1_MANAGER_TOOLS) == 8
    assert len(CASE1_PIPELINE_MANAGER_TOOLS) == 9
    assert len(CASE1_CASE3_MANAGER_TOOLS) == 10
    assert len(FULL_CPU_MANAGER_TOOLS) == 11


def test_case3_profile_appends_two_exact_tools() -> None:
    assert (
        CASE3_MANAGER_TOOLS[:5]
        == INITIAL_MANAGER_TOOLS
    )

    assert CASE3_MANAGER_TOOLS[-2:] == (
        "get_model_catalogue",
        "assess_case3_readiness",
    )


def test_manager_v5_describes_case3_read_only_boundaries() -> None:
    assert MANAGER_INSTRUCTIONS_VERSION == "phenoassistant-manager-v5"

    assert "get_model_catalogue" in MANAGER_INSTRUCTIONS
    assert "assess_case3_readiness" in MANAGER_INSTRUCTIONS
    assert "without loading or executing a model" in MANAGER_INSTRUCTIONS
    assert "without" in MANAGER_INSTRUCTIONS
    assert "training" in MANAGER_INSTRUCTIONS
    assert "inference" in MANAGER_INSTRUCTIONS


def test_registry_builds_independent_case3_profile() -> None:
    kwargs = base_kwargs()

    kwargs.update(
        {
            "model_zoo_path": str(MODEL_ZOO),
            "case3_dataset_path": str(CASE3_DATASET),
        }
    )

    registry = build_production_tool_registry(
        **kwargs
    )

    assert registry.names == CASE3_MANAGER_TOOLS

    assert (
        registry.get("get_model_catalogue").name
        == "get_model_catalogue"
    )

    assert (
        registry.get("assess_case3_readiness").name
        == "assess_case3_readiness"
    )


def test_registry_builds_full_cpu_profile() -> None:
    kwargs = base_kwargs()

    kwargs.update(
        {
            "case1_data_path": "/trusted/aracrop.csv",
            "case1_anova_callable": anova,
            "case1_tukey_callable": tukey,
            "pipeline_zoo_path": str(PIPELINE_ZOO),
            "model_zoo_path": str(MODEL_ZOO),
            "case3_dataset_path": str(CASE3_DATASET),
        }
    )

    registry = build_production_tool_registry(
        **kwargs
    )

    assert registry.names == FULL_CPU_MANAGER_TOOLS


@pytest.mark.parametrize(
    (
        "model_zoo_path",
        "case3_dataset_path",
    ),
    [
        (str(MODEL_ZOO), None),
        (None, str(CASE3_DATASET)),
    ],
)
def test_partial_case3_profile_fails_before_tool_construction(
    model_zoo_path: str | None,
    case3_dataset_path: str | None,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Case 3 profile requires both model_zoo_path "
            "and case3_dataset_path"
        ),
    ):
        build_production_tool_registry(
            data_path="/trusted/base.csv",
            model_zoo_path=model_zoo_path,
            case3_dataset_path=case3_dataset_path,
        )

    assert "functions.generic_tools" not in sys.modules
    assert "functions.image_classification" not in sys.modules


def test_application_accepts_independent_case3_profile() -> None:
    application = build_application(
        client=ScriptedToolClient(
            "get_model_catalogue",
            {
                "task": "image-classification",
            },
        ),
        data_path="/trusted/base.csv",
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
        model_zoo_path=str(MODEL_ZOO),
        case3_dataset_path=str(CASE3_DATASET),
    )

    assert application.registry.names == CASE3_MANAGER_TOOLS

    manager_tools = tuple(
        tool.name
        for tool in application.manager.default_options[
            "tools"
        ]
    )

    assert manager_tools == CASE3_MANAGER_TOOLS
