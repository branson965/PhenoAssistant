"""bridge_factory.py — one factory that builds an MCP bridge for ANY tool."""
import asyncio
import functools
import inspect
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command=sys.executable,
    args=["server.py"],
)


async def _call_tool_via_mcp(tool_name, arguments):
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return "\n".join(item.text for item in result.content)


def make_mcp_bridge(func, tool_name):
    """Return a sync wrapper that calls `tool_name` over MCP, carrying func's real signature."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound = inspect.signature(func).bind(*args, **kwargs)
        bound.apply_defaults()
        arguments = {k: v for k, v in bound.arguments.items() if v is not None}
        return asyncio.run(_call_tool_via_mcp(tool_name, arguments))

    wrapper.__signature__ = inspect.signature(func)
    return wrapper