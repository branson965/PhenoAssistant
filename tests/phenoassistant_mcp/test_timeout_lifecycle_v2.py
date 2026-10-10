"""Phase 6E timeout and explicit MCP client lifecycle tests."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("mcp")

import phenoassistant_mcp.client_v2 as client_v2
from phenoassistant_mcp.client_v2 import (
    McpV2LifecycleError,
    McpV2Session,
    McpV2TimeoutError,
    call_structured_tool,
)
from phenoassistant_mcp.server_v2 import build_phase6_mcp_server


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


def anova(
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
    return [{"Source": "Interaction"}]


def tukey(
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
    return [{"A": "control", "B": "treated"}]


def build_server(calculator: RecordingCalculator | None = None):
    return build_phase6_mcp_server(
        calculator_callable=(
            RecordingCalculator()
            if calculator is None
            else calculator
        ),
        anova_callable=anova,
        tukey_callable=tukey,
    )


@pytest.mark.asyncio
async def test_persistent_session_reuses_one_client_for_multiple_calls() -> None:
    calculator = RecordingCalculator()
    server = build_server(calculator)

    async with McpV2Session(server) as session:
        first = await session.call_structured_tool(
            "calculator",
            {
                "a": 7,
                "b": 5,
                "operator": "+",
            },
        )
        second = await session.call_structured_tool(
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
async def test_session_rejects_call_before_enter_and_after_exit() -> None:
    server = build_server()
    session = McpV2Session(server)

    with pytest.raises(
        McpV2LifecycleError,
        match="not active",
    ):
        await session.call_structured_tool(
            "calculator",
            {
                "a": 1,
                "b": 1,
                "operator": "+",
            },
        )

    async with session:
        result = await session.call_structured_tool(
            "calculator",
            {
                "a": 1,
                "b": 1,
                "operator": "+",
            },
        )
        assert result == {"result": 2}

    with pytest.raises(
        McpV2LifecycleError,
        match="not active",
    ):
        await session.discover_tool_names()


@pytest.mark.asyncio
async def test_session_rejects_double_enter() -> None:
    server = build_server()
    session = McpV2Session(server)

    async with session:
        with pytest.raises(
            McpV2LifecycleError,
            match="already active",
        ):
            await session.__aenter__()


@pytest.mark.asyncio
async def test_one_shot_call_timeout_is_visible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SlowClient:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            del exc_type, exc, traceback
            return None

        async def call_tool(self, tool_name, arguments):
            del tool_name, arguments
            await asyncio.sleep(0.05)
            return SimpleNamespace(
                is_error=False,
                structured_content={"result": 12},
            )

    monkeypatch.setattr(
        client_v2,
        "Client",
        SlowClient,
    )

    with pytest.raises(
        McpV2TimeoutError,
        match="timed out",
    ):
        await call_structured_tool(
            build_server(),
            "calculator",
            {
                "a": 7,
                "b": 5,
                "operator": "+",
            },
            timeout_seconds=0.001,
        )


@pytest.mark.asyncio
async def test_timeout_argument_must_be_positive_and_finite() -> None:
    server = build_server()

    for value in (
        0,
        -1,
        float("inf"),
        float("nan"),
    ):
        with pytest.raises(
            ValueError,
            match="positive finite",
        ):
            await call_structured_tool(
                server,
                "calculator",
                {
                    "a": 7,
                    "b": 5,
                    "operator": "+",
                },
                timeout_seconds=value,
            )

    with pytest.raises(
        TypeError,
        match="positive finite",
    ):
        await call_structured_tool(
            server,
            "calculator",
            {
                "a": 7,
                "b": 5,
                "operator": "+",
            },
            timeout_seconds=True,
        )
