"""Tests for production application composition."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import patch

from agent_framework import Agent

from phenoassistant_maf.application import (
    PhenoAssistantApplication,
    build_application,
)
from tests.phenoassistant_maf.fakes import (
    ScriptedToolClient,
)


def calculator(
    a: int,
    b: int,
    operator: str,
) -> int:
    return 12


def anova(
    data_path: str,
    descriptor: str,
    within_subject_factor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    return [{"Source": "Interaction"}]


def tukey(
    data_path: str,
    descriptor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    return [{"A": "control", "B": "treated"}]


def client() -> ScriptedToolClient:
    return ScriptedToolClient(
        "calculator",
        {
            "a": 7,
            "b": 5,
            "operator": "+",
        },
    )


def build_test_application() -> PhenoAssistantApplication:
    return build_application(
        client=client(),
        data_path="/trusted/data.csv",
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )


def test_application_composes_manager_and_registry() -> None:
    application = build_test_application()

    assert isinstance(
        application,
        PhenoAssistantApplication,
    )

    assert isinstance(
        application.manager,
        Agent,
    )

    assert application.registry.names == (
        "calculator",
        "perform_anova",
        "perform_tukey_test",
    )

    manager_tool_names = tuple(
        tool.name
        for tool in application.manager.default_options[
            "tools"
        ]
    )

    assert manager_tool_names == application.registry.names


def test_application_construction_does_not_create_provider() -> None:
    with patch(
        "agent_framework.openai.OpenAIChatCompletionClient",
        side_effect=AssertionError(
            "provider construction is forbidden"
        ),
    ):
        application = build_test_application()

    assert application.manager is not None


def test_application_with_injected_callables_is_import_safe() -> None:
    script = """
import sys

from phenoassistant_maf.application import build_application
from tests.phenoassistant_maf.fakes import ScriptedToolClient


def calculator(a: int, b: int, operator: str) -> int:
    return 12


def anova(
    data_path,
    descriptor,
    within_subject_factor,
    between_subject_factor,
    subject_id,
    save_path=None,
):
    return [{"Source": "Interaction"}]


def tukey(
    data_path,
    descriptor,
    between_subject_factor,
    subject_id,
    save_path=None,
):
    return [{"A": "control", "B": "treated"}]


client = ScriptedToolClient(
    "calculator",
    {"a": 7, "b": 5, "operator": "+"},
)

application = build_application(
    client=client,
    data_path="/trusted/data.csv",
    calculator_callable=calculator,
    anova_callable=anova,
    tukey_callable=tukey,
)

assert application.manager is not None
assert "functions.stat_test" not in sys.modules
assert "functions.generic_tools" not in sys.modules

print("APPLICATION_IMPORT_SAFE")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "APPLICATION_IMPORT_SAFE" in result.stdout
