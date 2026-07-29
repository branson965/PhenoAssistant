"""Single-agent, non-streaming mixed-ANOVA execution path."""

from __future__ import annotations

from agent_framework import Agent, AgentResponse, FunctionTool, SupportsChatGetResponse

MIXED_ANOVA_INSTRUCTIONS_VERSION = "mixed-anova-agent-v1"
MIXED_ANOVA_INSTRUCTIONS = """\
You are the PhenoAssistant mixed-ANOVA agent.
First state a concise plan. Then call perform_mixed_anova exactly once with the
four requested column names. Finally summarise only the returned tool evidence.
Do not invent statistical values or request a data path.
"""


def build_mixed_anova_agent(
    client: SupportsChatGetResponse,
    tool: FunctionTool,
) -> Agent:
    """Build one native MAF Agent with one injected mixed-ANOVA tool."""
    if tool.name != "perform_mixed_anova":
        raise ValueError("the agent requires the perform_mixed_anova tool")
    return Agent(
        client=client,
        name="phenoassistant-mixed-anova",
        description="Runs one mixed-design repeated-measures ANOVA.",
        instructions=MIXED_ANOVA_INSTRUCTIONS,
        tools=[tool],
        default_options={"allow_multiple_tool_calls": False},
        additional_properties={
            "instructions_version": MIXED_ANOVA_INSTRUCTIONS_VERSION
        },
    )


async def run_mixed_anova_agent(
    agent: Agent,
    prompt: str,
) -> AgentResponse:
    """Run the mixed-ANOVA agent without streaming or retained session state."""
    return await agent.run(prompt, stream=False, session=None)
