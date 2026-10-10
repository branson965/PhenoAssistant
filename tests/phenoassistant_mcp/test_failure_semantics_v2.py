"""Phase 6D fail-closed and lifecycle tests for the MCP v2 boundary."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("mcp")

import phenoassistant_mcp.maf_bridge_v2 as bridge
from phenoassistant_maf.application import PhenoAssistantApplication
from phenoassistant_maf.manager import build_manager_agent
from phenoassistant_maf.registry import build_production_tool_registry
from phenoassistant_maf.runtime import run_application
from phenoassistant_mcp.client_v2 import (
    McpV2SchemaError,
    McpV2ToolError,
    call_structured_tool,
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
    def __call__(
        self,
        data_path: str,
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]:
        del (
            data_path,
            descriptor,
            between_subject_factor,
            subject_id,
            save_path,
        )
        return [
            {
                "A": "control",
                "B": "treated",
                "p-tukey": 0.01,
            }
        ]


class FailingCalculator:
    def __call__(self, a: int, b: int, operator: str) -> int:
        del a, b, operator
        raise RuntimeError("injected calculator failure")


class InvalidCalculator:
    def __call__(self, a: int, b: int, operator: str) -> int:
        del a, b, operator
        return True  # type: ignore[return-value]


class FailingAnova:
    def __call__(
        self,
        data_path: str,
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]:
        del (
            data_path,
            descriptor,
            within_subject_factor,
            between_subject_factor,
            subject_id,
            save_path,
        )
        raise RuntimeError("injected ANOVA failure")


def build_server(
    *,
    calculator=None,
    anova=None,
):
    return build_phase6_mcp_server(
        calculator_callable=(
            RecordingCalculator()
            if calculator is None
            else calculator
        ),
        anova_callable=(
            RecordingAnova()
            if anova is None
            else anova
        ),
        tukey_callable=RecordingTukey(),
    )


@pytest.mark.asyncio
async def test_client_converts_server_tool_exception_to_mcp_error() -> None:
    server = build_server(
        calculator=FailingCalculator(),
    )

    with pytest.raises(
        McpV2ToolError,
        match="reported an execution error",
    ):
        await call_structured_tool(
            server,
            "calculator",
            {
                "a": 7,
                "b": 5,
                "operator": "+",
            },
        )


@pytest.mark.asyncio
async def test_server_return_contract_violation_fails_closed() -> None:
    server = build_server(
        calculator=InvalidCalculator(),
    )

    with pytest.raises(
        McpV2ToolError,
        match="reported an execution error",
    ):
        await call_structured_tool(
            server,
            "calculator",
            {
                "a": 7,
                "b": 5,
                "operator": "+",
            },
        )


@pytest.mark.asyncio
async def test_bridge_rejects_missing_records_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = build_server()

    async def malformed_call(*args, **kwargs):
        del args, kwargs
        return {}

    monkeypatch.setattr(
        bridge,
        "call_structured_tool",
        malformed_call,
    )

    handler = build_mcp_anova_handler(
        server,
        "/trusted/data.csv",
    )

    with pytest.raises(
        McpV2SchemaError,
        match="invalid records",
    ):
        await handler(
            "height",
            "time",
            "treatment",
            "plant_id",
        )


@pytest.mark.asyncio
async def test_bridge_rejects_non_dictionary_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = build_server()

    async def malformed_call(*args, **kwargs):
        del args, kwargs
        return {
            "records": [
                {
                    "Source": "Interaction",
                },
                7,
            ]
        }

    monkeypatch.setattr(
        bridge,
        "call_structured_tool",
        malformed_call,
    )

    handler = build_mcp_anova_handler(
        server,
        "/trusted/data.csv",
    )

    with pytest.raises(
        McpV2SchemaError,
        match="non-dictionary records",
    ):
        await handler(
            "height",
            "time",
            "treatment",
            "plant_id",
        )


def test_bridge_rejects_blank_trusted_data_path() -> None:
    server = build_server()

    with pytest.raises(
        ValueError,
        match="trusted data_path must not be blank",
    ):
        build_mcp_anova_handler(
            server,
            "   ",
        )


@pytest.mark.asyncio
async def test_repeated_client_sessions_are_stateless_and_repeatable() -> None:
    calculator = RecordingCalculator()
    server = build_server(
        calculator=calculator,
    )

    first = await call_structured_tool(
        server,
        "calculator",
        {
            "a": 7,
            "b": 5,
            "operator": "+",
        },
    )
    second = await call_structured_tool(
        server,
        "calculator",
        {
            "a": 9,
            "b": 4,
            "operator": "-",
        },
    )

    assert first == {"result": 12}
    assert second == {"result": 5}
    assert calculator.calls == [
        (7, 5, "+"),
        (9, 4, "-"),
    ]


@pytest.mark.asyncio
async def test_manager_surfaces_mcp_failure_without_success_claim() -> None:
    calculator = RecordingCalculator()
    anova = FailingAnova()
    tukey = RecordingTukey()

    server = build_phase6_mcp_server(
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )

    direct_registry = build_production_tool_registry(
        data_path="/trusted/data.csv",
        calculator_callable=calculator,
        anova_callable=anova,
        tukey_callable=tukey,
    )

    bridged_registry = replace_first_parity_slice_with_mcp(
        direct_registry,
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
            registry=bridged_registry,
        ),
        registry=bridged_registry,
    )

    response = await run_application(
        application,
        "Run mixed ANOVA for height by time and treatment using plant_id.",
    )

    assert client.function_result is not None
    assert client.function_result.exception is not None
    assert response.messages
    final_text = response.messages[-1].text
    assert "failed" in final_text
    assert "completed from tool evidence" not in final_text
