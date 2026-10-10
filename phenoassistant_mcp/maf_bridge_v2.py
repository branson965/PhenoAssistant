"""MAF-facing adapters for the bounded Phase 6 MCP v2 parity slice.

The Manager-facing contracts intentionally match the existing direct MAF tools.
Trusted application-controlled paths are bound inside this bridge and are never
exposed as model-controlled arguments.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Awaitable

from agent_framework import FunctionTool
from mcp.server import MCPServer

from phenoassistant_maf.registry import ProductionToolRegistry
from phenoassistant_maf.tools import (
    CalculatorInput,
    CalculatorResult,
    MixedAnovaInput,
    MixedAnovaResult,
    TukeyInput,
    TukeyResult,
)
from phenoassistant_mcp.client_v2 import (
    McpV2SchemaError,
    call_structured_tool,
)


CalculatorMcpHandler = Callable[
    [int, int, str],
    Awaitable[CalculatorResult],
]

AnovaMcpHandler = Callable[
    [str, str, str, str],
    Awaitable[MixedAnovaResult],
]

TukeyMcpHandler = Callable[
    [str, str, str],
    Awaitable[TukeyResult],
]


def _normalise_trusted_data_path(data_path: str) -> str:
    """Trim and reject a blank application-controlled dataset path."""
    normalised = data_path.strip()

    if not normalised:
        raise ValueError("trusted data_path must not be blank")

    return normalised


def _validated_records(
    payload: dict[str, Any],
    *,
    tool_name: str,
) -> list[dict[str, Any]]:
    """Fail closed unless one MCP result contains list[dict] records."""
    records = payload.get("records")

    if not isinstance(records, list):
        raise McpV2SchemaError(
            f"MCP tool {tool_name!r} returned invalid records"
        )

    if any(not isinstance(record, dict) for record in records):
        raise McpV2SchemaError(
            f"MCP tool {tool_name!r} returned non-dictionary records"
        )

    return records


def build_mcp_calculator_handler(
    server: MCPServer,
) -> CalculatorMcpHandler:
    """Build the MAF-facing calculator handler backed by MCP v2."""

    async def calculate(
        a: int,
        b: int,
        operator: str,
    ) -> CalculatorResult:
        arguments = CalculatorInput(
            a=a,
            b=b,
            operator=operator,
        )

        payload = await call_structured_tool(
            server,
            "calculator",
            arguments.model_dump(mode="json"),
        )

        result = payload.get("result")

        if isinstance(result, bool) or not isinstance(result, int):
            raise McpV2SchemaError(
                "MCP calculator result must be an integer"
            )

        return CalculatorResult(
            arguments=arguments,
            result=result,
        )

    return calculate


def build_mcp_anova_handler(
    server: MCPServer,
    data_path: str,
) -> AnovaMcpHandler:
    """Bind the trusted dataset behind the direct MAF ANOVA contract."""
    trusted_data_path = _normalise_trusted_data_path(data_path)

    async def perform_anova(
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
    ) -> MixedAnovaResult:
        arguments = MixedAnovaInput(
            descriptor=descriptor,
            within_subject_factor=within_subject_factor,
            between_subject_factor=between_subject_factor,
            subject_id=subject_id,
        )

        payload = await call_structured_tool(
            server,
            "perform_anova",
            {
                "data_path": trusted_data_path,
                **arguments.model_dump(mode="json"),
            },
        )

        return MixedAnovaResult(
            arguments=arguments,
            records=_validated_records(
                payload,
                tool_name="perform_anova",
            ),
        )

    return perform_anova


def build_mcp_tukey_handler(
    server: MCPServer,
    data_path: str,
) -> TukeyMcpHandler:
    """Bind the trusted dataset behind the direct MAF Tukey contract."""
    trusted_data_path = _normalise_trusted_data_path(data_path)

    async def perform_tukey_test(
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
    ) -> TukeyResult:
        arguments = TukeyInput(
            descriptor=descriptor,
            between_subject_factor=between_subject_factor,
            subject_id=subject_id,
        )

        payload = await call_structured_tool(
            server,
            "perform_tukey_test",
            {
                "data_path": trusted_data_path,
                **arguments.model_dump(mode="json"),
            },
        )

        return TukeyResult(
            arguments=arguments,
            records=_validated_records(
                payload,
                tool_name="perform_tukey_test",
            ),
        )

    return perform_tukey_test


def create_mcp_calculator_tool(
    server: MCPServer,
) -> FunctionTool:
    """Expose MCP calculator through the same contract as direct MAF."""
    return FunctionTool(
        name="calculator",
        description=(
            "Perform integer arithmetic using one of +, -, *, or /. "
            "Division preserves the original calculator's integer result."
        ),
        func=build_mcp_calculator_handler(server),
        input_model=CalculatorInput,
    )


def create_mcp_anova_tool(
    server: MCPServer,
    data_path: str,
) -> FunctionTool:
    """Expose MCP ANOVA while keeping data_path application-controlled."""
    return FunctionTool(
        name="perform_anova",
        description=(
            "Perform a mixed-design repeated-measures ANOVA using the "
            "trusted application dataset and supplied column names."
        ),
        func=build_mcp_anova_handler(
            server,
            data_path,
        ),
        input_model=MixedAnovaInput,
    )


def create_mcp_tukey_tool(
    server: MCPServer,
    data_path: str,
) -> FunctionTool:
    """Expose MCP Tukey while keeping data_path application-controlled."""
    return FunctionTool(
        name="perform_tukey_test",
        description=(
            "Perform a Tukey-Kramer post-hoc test using the trusted "
            "application dataset and supplied column names."
        ),
        func=build_mcp_tukey_handler(
            server,
            data_path,
        ),
        input_model=TukeyInput,
    )


def replace_first_parity_slice_with_mcp(
    registry: ProductionToolRegistry,
    *,
    server: MCPServer,
    data_path: str,
) -> ProductionToolRegistry:
    """Replace only the frozen three-tool direct slice with MCP-backed tools."""
    required = {
        "calculator",
        "perform_anova",
        "perform_tukey_test",
    }
    present = set(registry.names)
    missing = required - present

    if missing:
        raise ValueError(
            "registry is missing MCP parity tools: "
            + ", ".join(sorted(missing))
        )

    replacements = {
        "calculator": create_mcp_calculator_tool(server),
        "perform_anova": create_mcp_anova_tool(
            server,
            data_path,
        ),
        "perform_tukey_test": create_mcp_tukey_tool(
            server,
            data_path,
        ),
    }

    return ProductionToolRegistry(
        tools=tuple(
            replacements.get(tool.name, tool)
            for tool in registry.tools
        )
    )
