import asyncio, sys, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
sp = StdioServerParameters(command=sys.executable, args=['server.py'])
async def main():
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    async with stdio_client(sp) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool(sys.argv[1], arguments=args)
            print('=== RESULT ===')
            print(chr(10).join(i.text for i in res.content))
asyncio.run(main())
