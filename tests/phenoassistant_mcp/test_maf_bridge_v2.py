"""MAF -> MCP v2 bridge tests for the bounded Phase 6 parity slice."""

from __future__ import annotations

import json
from typing import Any

import pytest

pytest.importorskip("mcp")

from phenoassistant_maf.application import PhenoAssistantApplication
from phenoassistant_maf.manager import build_manager_agent
from phenoassistant_maf.registry import build_production_tool_registry
from phenoassistant_maf.runtime import run_application
from phenoassistant_maf.tools import (
    CalculatorInput,
    MixedAnovaInput,
    TukeyInput,
)
from phenoassistant_mcp.maf_bridge_v2 import (
    build_mcp_anova_handler,
    replace_first_parity_slice_with_mcp,
)
from phenoassistant_mcp.server_v2 import build_phase6_mcp_server
from tests.phenoassistant_maf.fakes import ScriptedToolClient


class RecordingCalculator:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int, str]] = []

    def __call__(self, a: int, b: int, operator: str) -> int:
        self.calls.append((a, b, operator))
        operations = {
            "+": a + b,
            "-": a - b,
            "*": a * b,
            "/": int(a / b),
        }
        return operations[operator]


class RecordingAnova:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def __call__(
        self,
        data_path: str,
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            (
                data_path,
                descriptor,
                within_subject_factor,
                between_subject_factor,
                subject_id,
                save_path,
            )
        )
        return [
            {
                "Source": "Interaction",
                "F": 9.5,
                "p-unc": 0.001,
            }
        ]


class RecordingTukey:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def __call__(
        self,
        data_path: str,
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            (
                data_path,
                descriptor,
                between_subject_factor,
                subject_id,
                save_path,
            )
        )
        return [
            {
                "A": "control",
                "B": "treated",
                "p-tukey": 0.01,
            }
        ]


def build_direct_registry(
    calculator: RecordingCalculator,
    anova: RecordingAnova,
    tukey: RecordingTukey,
):
    return build_production_tool_registry(
        data_path="/trusted/data.csv",
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )


@pytest.mark.asyncio
async def test_mcp_anova_handler_binds_trusted_data_path() -> None:
    calculator = RecordingCalculator()
    anova = RecordingAnova()
    tukey = RecordingTukey()

    server = build_phase6_mcp_server(
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )

    handler = build_mcp_anova_handler(
        server,
        "  /trusted/data.csv  ",
    )

    result = await handler(
        "height",
        "time",
        "treatment",
        "plant_id",
    )

    assert result.tool_name == "perform_anova"
    assert result.arguments == MixedAnovaInput(
        descriptor="height",
        within_subject_factor="time",
        between_subject_factor="treatment",
        subject_id="plant_id",
    )
    assert result.records == [
        {
            "Source": "Interaction",
            "F": 9.5,
            "p-unc": 0.001,
        }
    ]
    assert anova.calls == [
        (
            "/trusted/data.csv",
            "height",
            "time",
            "treatment",
            "plant_id",
            None,
        )
    ]


def test_bridge_preserves_manager_facing_contracts() -> None:
    calculator = RecordingCalculator()
    anova = RecordingAnova()
    tukey = RecordingTukey()

    server = build_phase6_mcp_server(
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )

    direct = build_direct_registry(
        calculator,
        anova,
        tukey,
    )
    bridged = replace_first_parity_slice_with_mcp(
        direct,
        server=server,
        data_path="/trusted/data.csv",
    )

    assert bridged.names == direct.names

    expected_models = {
        "calculator": CalculatorInput,
        "perform_anova": MixedAnovaInput,
        "perform_tukey_test": TukeyInput,
    }

    for name, input_model in expected_models.items():
        assert bridged.get(name).description == direct.get(name).description
        assert bridged.get(name).input_model is input_model
        assert (
            "data_path"
            not in input_model.model_fields
        )


@pytest.mark.asyncio
async def test_manager_executes_anova_through_mcp_without_path_argument() -> None:
    calculator = RecordingCalculator()
    anova = RecordingAnova()
    tukey = RecordingTukey()

    server = build_phase6_mcp_server(
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )

    direct = build_direct_registry(
        calculator,
        anova,
        tukey,
    )
    bridged = replace_first_parity_slice_with_mcp(
        direct,
        server=server,
        data_path="/trusted/data.csv",
    )

    client = ScriptedToolClient(
        "perform_anova",
        {
            "descriptor": "height",
            "within_subject_factor": "time",
            "between_subject_factor": "treatment",
            "subject_id": "plant_id",
        },
    )

    application = PhenoAssistantApplication(
        manager=build_manager_agent(
            client=client,
            registry=bridged,
        ),
        registry=bridged,
    )

    response = await run_application(
        application,
        "Run mixed ANOVA for height by time and treatment using plant_id.",
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    payload = json.loads(
        client.function_result.result
    )

    assert payload == {
        "schema_version": "1",
        "tool_name": "perform_anova",
        "arguments": {
            "descriptor": "height",
            "within_subject_factor": "time",
            "between_subject_factor": "treatment",
            "subject_id": "plant_id",
        },
        "records": [
            {
                "Source": "Interaction",
                "F": 9.5,
                "p-unc": 0.001,
            }
        ],
    }

    assert anova.calls == [
        (
            "/trusted/data.csv",
            "height",
            "time",
            "treatment",
            "plant_id",
            None,
        )
    ]

    assert response.messages
    assert response.messages[-1].text.strip()
