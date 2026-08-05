"""Production PhenoAssistant Manager construction."""

from __future__ import annotations

from agent_framework import Agent, SupportsChatGetResponse

from phenoassistant_maf.registry import ProductionToolRegistry

MANAGER_INSTRUCTIONS_VERSION = "phenoassistant-manager-v1"

INITIAL_MANAGER_TOOLS = (
    "calculator",
    "perform_anova",
    "perform_tukey_test",
)

MANAGER_INSTRUCTIONS = """\
You are the PhenoAssistant Manager for the initial production MAF migration.

For every supported request:
1. State a concise plan.
2. Select exactly one appropriate registered tool.
3. Call that tool no more than once.
4. Summarise only evidence returned by the tool.

Available responsibilities:
- calculator: integer arithmetic;
- perform_anova: mixed-design repeated-measures ANOVA;
- perform_tukey_test: Tukey-Kramer post-hoc analysis.

Never invent statistical values.
Never ask the model to provide data_path or save_path.
Do not claim that a tool succeeded unless its returned evidence confirms success.
"""


def build_manager_agent(
    client: SupportsChatGetResponse,
    registry: ProductionToolRegistry,
) -> Agent:
    """Construct the initial production MAF Manager explicitly."""
    if registry.names != INITIAL_MANAGER_TOOLS:
        raise ValueError(
            "the initial Manager requires exactly: "
            + ", ".join(INITIAL_MANAGER_TOOLS)
        )

    return Agent(
        client=client,
        name="phenoassistant-manager",
        description=(
            "Selects and executes validated PhenoAssistant tools."
        ),
        instructions=MANAGER_INSTRUCTIONS,
        tools=registry.as_list(),
        default_options={
            "allow_multiple_tool_calls": False,
        },
        additional_properties={
            "instructions_version": MANAGER_INSTRUCTIONS_VERSION,
        },
    )
