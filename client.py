import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# This is a standalone MCP client used to prove that a *program* 
# can reach server.py the standard MCP way.
# It doesn't touch PhenoAssistant's manager/agents at all, this is Stage 1
# of the MCP PoC, kept deliberately separate so the connection logic can be
# tested and debugged in isolation before it's wired into the real agent
# system in Stage 2.

# PARAMETERS: tells MCP how to launch the server, not how to find one that's
# already running. We launch fresh each time (same as Command/Arguments
# fields used manually in MCP Inspector) so the client fully owns the
# server's lifecycle.
server_params = StdioServerParameters(
    command="python",
    args=["server.py"],  # must be a list: a command can take multiple args
)

async def main():
    # TRANSPORT: opens the stdio pipe and launches server.py as a subprocess.
    # async with guarantees the server process is shut down cleanly even if
    # something below raises an error.
    async with stdio_client(server_params) as (read, write):

        # SESSION: the actual "conversation" over the pipe. Nothing can be
        # called until this exists, since call_tool needs something to call
        # 'over'.
        async with ClientSession(read, write) as session:

            # Handshake, required by the MCP protocol before any tool calls
            # will be accepted.
            await session.initialize()

            # Sanity check only: confirms the pipe is actually working and
            # that the server is exposing the tools we expect, before we
            # trust it with a real call. Not required for the tool call
            # itself.
            tools = await session.list_tools()
            print("Tools available:", [t.name for t in tools.tools])

            # The actual proof-of-concept call: reaching perform_anova via
            # MCP instead of a direct Python import.
            #
            # Argument keys below must exactly match perform_anova's
            # parameter names in functions/stat_test.py — MCP validates
            # these strictly (stricter than the old in-house registration
            # system), so a typo here fails loudly rather than silently.
            #
            # Column choices come from data_for_eval/aracrop_phenotypes.csv:
            # - ecotype is fixed per plant -> between_subject_factor
            # - days_after_sowing changes across repeated measurements of
            #   the same plant -> within_subject_factor
            # - plant_id identifies a single plant -> subject_id
            result = await session.call_tool(
                "perform_anova",
                arguments={
                    "data_path": "data_for_eval/aracrop_phenotypes.csv",
                    "descriptor": "average_leaf_area",
                    "within_subject_factor": "days_after_sowing",
                    "between_subject_factor": "ecotype",
                    "subject_id": "plant_id",
                },
            )

            # Tool results come back as a list of "content items", not a
            # plain string/dict and each item has a .text field. Printing
            # `result` directly shows a messy wrapper object, so we unwrap
            # it here to get the clean answer.
            print("Result:")
            for item in result.content:
                print(item.text)

asyncio.run(main())