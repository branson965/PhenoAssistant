"""High-level MCP v2 client boundary for Phase 6 parity experiments."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mcp import Client
from mcp.server import MCPServer

MCP_PROTOCOL_VERSION = "2026-07-28"


class McpV2Error(RuntimeError):
    """Base error for the local Phase 6 MCP client boundary."""


class McpV2ToolError(McpV2Error):
    """Raised when the MCP server reports a tool execution failure."""


class McpV2SchemaError(McpV2Error):
    """Raised when an MCP result is missing the required structured payload."""


async def discover_tool_names(server: MCPServer) -> tuple[str, ...]:
    """Return advertised tool names through the first-class MCP v2 Client."""
    async with Client(
        server,
        mode=MCP_PROTOCOL_VERSION,
    ) as client:
        result = await client.list_tools()

    return tuple(tool.name for tool in result.tools)


async def call_structured_tool(
    server: MCPServer,
    tool_name: str,
    arguments: Mapping[str, Any],
) -> dict[str, Any]:
    """Call one MCP tool and fail closed unless structured content is returned."""
    async with Client(
        server,
        mode=MCP_PROTOCOL_VERSION,
    ) as client:
        result = await client.call_tool(
            tool_name,
            dict(arguments),
        )

    if result.is_error:
        raise McpV2ToolError(
            f"MCP tool {tool_name!r} reported an execution error"
        )

    structured = result.structured_content
    if not isinstance(structured, dict):
        raise McpV2SchemaError(
            f"MCP tool {tool_name!r} did not return structured content"
        )

    return dict(structured)
