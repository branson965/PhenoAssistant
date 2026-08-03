"""smoke_test.py — connect to the server and list every tool + its schema."""
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(command=sys.executable, args=["server.py"])


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"{len(tools.tools)} tool(s) mounted:\n")
            for t in tools.tools:
                params = list(t.inputSchema.get("properties", {}).keys())
                required = t.inputSchema.get("required", [])
                print(f"  - {t.name}")
                print(f"      params  : {params}")
                print(f"      required: {required}")
                print(f"      desc    : {t.description[:60]}...")
                print()


asyncio.run(main())