"""
MCP server for PhenoAssistant.

Exposes existing functions from functions/ as MCP tools, so external
apps can call them through the standard MCP interface. This is a thin
adapter — the actual logic lives in functions/, untouched.

Run for local testing:  mcp dev server.py
"""
from mcp.server.fastmcp import FastMCP
from functions.stat_test import perform_anova, perform_tukey_test

mcp = FastMCP("phenoassistant")

mcp.add_tool(perform_anova)
mcp.add_tool(perform_tukey_test)

if __name__ == "__main__":
    mcp.run()