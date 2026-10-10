"""High-level MCP v2 client boundary for Phase 6 parity experiments."""

from __future__ import annotations

import asyncio
import math
from collections.abc import Awaitable, Mapping
from typing import Any, TypeVar

from mcp import Client
from mcp.server import MCPServer

MCP_PROTOCOL_VERSION = "2026-07-28"

_ResultT = TypeVar("_ResultT")


class McpV2Error(RuntimeError):
    """Base error for the local Phase 6 MCP client boundary."""


class McpV2ToolError(McpV2Error):
    """Raised when the MCP server reports a tool execution failure."""


class McpV2SchemaError(McpV2Error):
    """Raised when an MCP result is missing the required structured payload."""


class McpV2TimeoutError(McpV2Error):
    """Raised when an MCP operation exceeds the caller-controlled timeout."""


class McpV2LifecycleError(McpV2Error):
    """Raised when a persistent MCP session is used outside its lifecycle."""


def _validated_timeout(
    timeout_seconds: float | None,
) -> float | None:
    """Validate an optional positive finite timeout."""
    if timeout_seconds is None:
        return None

    if isinstance(timeout_seconds, bool) or not isinstance(
        timeout_seconds,
        (int, float),
    ):
        raise TypeError("timeout_seconds must be a positive finite number")

    timeout = float(timeout_seconds)

    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout_seconds must be a positive finite number")

    return timeout


async def _await_with_timeout(
    awaitable: Awaitable[_ResultT],
    *,
    timeout_seconds: float | None,
    operation: str,
) -> _ResultT:
    """Await one operation with an explicit fail-closed timeout."""
    if timeout_seconds is None:
        return await awaitable

    try:
        return await asyncio.wait_for(
            awaitable,
            timeout=timeout_seconds,
        )
    except TimeoutError as exc:
        raise McpV2TimeoutError(
            f"{operation} timed out after {timeout_seconds:.6g} seconds"
        ) from exc


def _structured_payload(
    result: Any,
    *,
    tool_name: str,
) -> dict[str, Any]:
    """Validate the MCP call result and return structured content."""
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


class McpV2Session:
    """Explicit reusable MCP v2 client lifecycle for warm-call execution."""

    def __init__(self, server: MCPServer) -> None:
        self._server = server
        self._client: Client | None = None

    async def __aenter__(self) -> "McpV2Session":
        if self._client is not None:
            raise McpV2LifecycleError(
                "MCP session is already active"
            )

        client = Client(
            self._server,
            mode=MCP_PROTOCOL_VERSION,
        )
        await client.__aenter__()
        self._client = client

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: Any,
    ) -> bool | None:
        client = self._client

        if client is None:
            return None

        self._client = None

        return await client.__aexit__(
            exc_type,
            exc,
            traceback,
        )

    def _require_client(self) -> Client:
        client = self._client

        if client is None:
            raise McpV2LifecycleError(
                "MCP session is not active"
            )

        return client

    async def discover_tool_names(
        self,
        *,
        timeout_seconds: float | None = None,
    ) -> tuple[str, ...]:
        """Return advertised tool names on the active client session."""
        timeout = _validated_timeout(timeout_seconds)
        client = self._require_client()

        result = await _await_with_timeout(
            client.list_tools(),
            timeout_seconds=timeout,
            operation="MCP list_tools",
        )

        return tuple(
            tool.name
            for tool in result.tools
        )

    async def call_structured_tool(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Call one tool on the active session and validate its result."""
        timeout = _validated_timeout(timeout_seconds)
        client = self._require_client()

        result = await _await_with_timeout(
            client.call_tool(
                tool_name,
                dict(arguments),
            ),
            timeout_seconds=timeout,
            operation=f"MCP tool {tool_name!r}",
        )

        return _structured_payload(
            result,
            tool_name=tool_name,
        )


async def discover_tool_names(
    server: MCPServer,
    *,
    timeout_seconds: float | None = None,
) -> tuple[str, ...]:
    """Return advertised tool names through a one-shot MCP v2 session."""
    async with McpV2Session(server) as session:
        return await session.discover_tool_names(
            timeout_seconds=timeout_seconds,
        )


async def call_structured_tool(
    server: MCPServer,
    tool_name: str,
    arguments: Mapping[str, Any],
    *,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Call one MCP tool through a one-shot session with fail-closed validation."""
    async with McpV2Session(server) as session:
        return await session.call_structured_tool(
            tool_name,
            arguments,
            timeout_seconds=timeout_seconds,
        )
