import asyncio
from typing import Annotated, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Same "how to start the server" info as client.py — unchanged.
server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)


async def _call_anova_via_mcp(data_path, descriptor, within_subject_factor,
                               between_subject_factor, subject_id, save_path=None):
    """The actual MCP round-trip — same steps as client.py, packaged into a
    reusable function instead of a one-off script."""
    # Build arguments dict first, and only include save_path when it's
    # actually provided. MCP validates types strictly (stricter than the old
    # in-house registration), so passing save_path=None into a string-typed
    # field can be rejected — we omit it rather than send a None.
    arguments = {
        "data_path": data_path,
        "descriptor": descriptor,
        "within_subject_factor": within_subject_factor,
        "between_subject_factor": between_subject_factor,
        "subject_id": subject_id,
    }
    if save_path is not None:
        arguments["save_path"] = save_path

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("perform_anova", arguments=arguments)
            # Collapse MCP content items back into plain text, same
            # unwrapping client.py did.
            return "\n".join(item.text for item in result.content)


def perform_anova_via_mcp(
    data_path: Annotated[str, "Path to the input CSV file"],
    descriptor: Annotated[str, "The name of the descriptor column to analyse"],
    within_subject_factor: Annotated[str, "The name of the within-subjects factor"],
    between_subject_factor: Annotated[str, "The name of the between-subjects factor"],
    subject_id: Annotated[str, "The name of the subject identifier"],
    save_path: Annotated[Optional[str], "Path to save the ANOVA results CSV"] = None,
) -> str:
    """
    Perform Mixed-design Repeated Measures ANOVA on a given descriptor,
    reaching perform_anova via an MCP server instead of a direct import
    (proof-of-concept for MCP-based tool registration).

    Returns the ANOVA results as text.
    """
    # register_function expects a plain synchronous callable (same shape as
    # every other tool in agents.py), but MCP calls are async. asyncio.run()
    # is the sync "front door" that runs the async logic and returns a plain
    # result — so from the manager's side this behaves like any normal tool.
    return asyncio.run(_call_anova_via_mcp(
        data_path, descriptor, within_subject_factor,
        between_subject_factor, subject_id, save_path,
    ))