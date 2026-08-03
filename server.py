"""Generic MCP server: loops over TOOL_REGISTRY instead of one add_tool line per tool."""
from mcp.server.fastmcp import FastMCP
from tool_registry import TOOL_REGISTRY

mcp = FastMCP("phenoassistant")

for func, name, description in TOOL_REGISTRY:
    mcp.add_tool(func, name=name, description=description)

if __name__ == "__main__":
    mcp.run()