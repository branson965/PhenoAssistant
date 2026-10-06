"""Generic MCP server: loops over TOOL_REGISTRY instead of one add_tool line per tool.

stdout guard: MCP speaks JSON-RPC over stdout, so ANY print() inside a tool
corrupts the protocol channel. Tools that run nested AutoGen chats print their
whole transcript. We wrap every tool so its stdout is redirected to stderr for
the duration of the call - applied once here, so no individual tool has to
remember to be quiet.
"""
import contextlib
import functools
import inspect
import sys

import logging
logging.getLogger("autogen").setLevel(logging.ERROR)
logging.getLogger("autogen.oai.client").setLevel(logging.ERROR)
from mcp.server.fastmcp import FastMCP
from tool_registry import TOOL_REGISTRY

mcp = FastMCP("phenoassistant")


def _quiet(func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def aw(*args, **kwargs):
            with contextlib.redirect_stdout(sys.stderr):
                return await func(*args, **kwargs)
        wrapper = aw
    else:
        @functools.wraps(func)
        def sw(*args, **kwargs):
            with contextlib.redirect_stdout(sys.stderr):
                return func(*args, **kwargs)
        wrapper = sw
    wrapper.__signature__ = inspect.signature(func)
    return wrapper


for func, name, description in TOOL_REGISTRY:
    mcp.add_tool(_quiet(func), name=name, description=description)

if __name__ == "__main__":
    mcp.run()
