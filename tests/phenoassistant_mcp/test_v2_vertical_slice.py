"""Phase 6 MCP v2 discovery and exact-semantic parity tests."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("mcp")

from phenoassistant_mcp.client_v2 import (
    MCP_PROTOCOL_VERSION,
    call_structured_tool,
    discover_tool_names,
)
from phenoassistant_mcp.server_v2 import build_phase6_mcp_server


class RecordingCalculator:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int, str]] = []

    def __call__(self, a: int, b: int, operator: str) -> int:
        self.calls.append((a, b, operator))
        if operator == "+":
            return a + b
        if operator == "-":
            return a - b
        if operator == "*":
            return a * b
        if operator == "/":
            return int(a / b)
        raise ValueError("Invalid operator")


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
                "DF1": 4.0,
                "DF2": 20.0,
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
                "A": "a",
                "B": "b",
                "mean(A)": 1.0,
                "mean(B)": 2.0,
                "p-tukey": 0.01,
            }
        ]


@pytest.mark.asyncio
async def test_mcp_v2_discovery_is_bounded_to_first_parity_slice() -> None:
    server = build_phase6_mcp_server(
        calculator_callable=RecordingCalculator(),
        anova_callable=RecordingAnova(),
        tukey_callable=RecordingTukey(),
    )

    assert MCP_PROTOCOL_VERSION == "2026-07-28"
    assert await discover_tool_names(server) == (
        "calculator",
        "perform_anova",
        "perform_tukey_test",
    )


@pytest.mark.asyncio
async def test_calculator_direct_and_mcp_results_match() -> None:
    direct = RecordingCalculator()
    server = build_phase6_mcp_server(
        calculator_callable=direct,
        anova_callable=RecordingAnova(),
        tukey_callable=RecordingTukey(),
    )

    expected = direct(7, 5, "+")
    result = await call_structured_tool(
        server,
        "calculator",
        {"a": 7, "b": 5, "operator": "+"},
    )

    assert result == {"result": expected}
    assert direct.calls == [(7, 5, "+"), (7, 5, "+")]


@pytest.mark.asyncio
async def test_anova_direct_and_mcp_records_match() -> None:
    direct = RecordingAnova()
    server = build_phase6_mcp_server(
        calculator_callable=RecordingCalculator(),
        anova_callable=direct,
        tukey_callable=RecordingTukey(),
    )
    arguments = {
        "data_path": "trusted.csv",
        "descriptor": "projected_leaf_area",
        "within_subject_factor": "days_after_sowing",
        "between_subject_factor": "ecotype",
        "subject_id": "plant_id",
    }

    expected = direct(**arguments)
    result = await call_structured_tool(
        server,
        "perform_anova",
        arguments,
    )

    assert result == {"records": expected}
    assert len(direct.calls) == 2
    assert direct.calls[0] == direct.calls[1]


@pytest.mark.asyncio
async def test_tukey_direct_and_mcp_records_match() -> None:
    direct = RecordingTukey()
    server = build_phase6_mcp_server(
        calculator_callable=RecordingCalculator(),
        anova_callable=RecordingAnova(),
        tukey_callable=direct,
    )
    arguments = {
        "data_path": "trusted.csv",
        "descriptor": "projected_leaf_area",
        "between_subject_factor": "ecotype",
        "subject_id": "plant_id",
    }

    expected = direct(**arguments)
    result = await call_structured_tool(
        server,
        "perform_tukey_test",
        arguments,
    )

    assert result == {"records": expected}
    assert len(direct.calls) == 2
    assert direct.calls[0] == direct.calls[1]
