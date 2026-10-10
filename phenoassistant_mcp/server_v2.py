"""Canonical MCP v2 server surface for the first Phase 6 parity slice.

This module intentionally exposes only the three exact semantic matches frozen in
the Phase 4 integration contract: calculator, mixed ANOVA, and Tukey-Kramer.
The broader Vincent MCP v1 registry remains preserved as historical evidence and
is not bulk-registered into MAF.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from mcp.server import MCPServer


class CalculatorCallable(Protocol):
    def __call__(self, a: int, b: int, operator: str) -> int: ...


class AnovaCallable(Protocol):
    def __call__(
        self,
        data_path: str,
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]: ...


class TukeyCallable(Protocol):
    def __call__(
        self,
        data_path: str,
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]: ...


def _resolve_real_calculator() -> CalculatorCallable:
    from functions.generic_tools import calculator

    return calculator


def _resolve_real_anova() -> AnovaCallable:
    from functions.stat_test import perform_anova

    return perform_anova


def _resolve_real_tukey() -> TukeyCallable:
    from functions.stat_test import perform_tukey_test

    return perform_tukey_test


def build_phase6_mcp_server(
    *,
    calculator_callable: CalculatorCallable | None = None,
    anova_callable: AnovaCallable | None = None,
    tukey_callable: TukeyCallable | None = None,
) -> MCPServer:
    """Build the bounded MCP v2 server used for direct↔MCP parity work."""
    calculator_impl = (
        _resolve_real_calculator()
        if calculator_callable is None
        else calculator_callable
    )
    anova_impl = (
        _resolve_real_anova()
        if anova_callable is None
        else anova_callable
    )
    tukey_impl = (
        _resolve_real_tukey()
        if tukey_callable is None
        else tukey_callable
    )

    server = MCPServer("phenoassistant-phase6-v2")

    def calculator(
        a: int,
        b: int,
        operator: str,
    ) -> dict[str, int]:
        """Perform integer arithmetic using the canonical PhenoAssistant implementation."""
        result = calculator_impl(a, b, operator)
        if isinstance(result, bool) or not isinstance(result, int):
            raise TypeError("calculator implementation must return an integer")
        return {"result": result}

    def perform_anova(
        data_path: str,
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """Run the canonical mixed repeated-measures ANOVA implementation."""
        records = anova_impl(
            data_path,
            descriptor,
            within_subject_factor,
            between_subject_factor,
            subject_id,
            save_path=None,
        )
        if not isinstance(records, list):
            raise TypeError("ANOVA implementation must return list[dict]")
        if any(not isinstance(record, dict) for record in records):
            raise TypeError("ANOVA records must be dictionaries")
        return {"records": records}

    def perform_tukey_test(
        data_path: str,
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """Run the canonical Tukey-Kramer implementation."""
        records = tukey_impl(
            data_path,
            descriptor,
            between_subject_factor,
            subject_id,
            save_path=None,
        )
        if not isinstance(records, list):
            raise TypeError("Tukey implementation must return list[dict]")
        if any(not isinstance(record, dict) for record in records):
            raise TypeError("Tukey records must be dictionaries")
        return {"records": records}

    server.add_tool(
        calculator,
        name="calculator",
        description="Perform basic arithmetic operations between two integers.",
        structured_output=True,
    )
    server.add_tool(
        perform_anova,
        name="perform_anova",
        description=(
            "Perform mixed-design repeated-measures ANOVA using a trusted "
            "application-bound dataset path."
        ),
        structured_output=True,
    )
    server.add_tool(
        perform_tukey_test,
        name="perform_tukey_test",
        description=(
            "Perform Tukey-Kramer post-hoc analysis using a trusted "
            "application-bound dataset path."
        ),
        structured_output=True,
    )

    return server


def build_real_phase6_mcp_server() -> MCPServer:
    """Build the Phase 6 server against the canonical repository implementations."""
    return build_phase6_mcp_server()
