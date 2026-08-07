"""Production PhenoAssistant Manager construction."""

from __future__ import annotations

from agent_framework import Agent, SupportsChatGetResponse

from phenoassistant_maf.registry import ProductionToolRegistry

MANAGER_INSTRUCTIONS_VERSION = "phenoassistant-manager-v4"

INITIAL_MANAGER_TOOLS = (
    "calculator",
    "perform_anova",
    "perform_tukey_test",
    "compare_linear_relationships",
    "query_csv_statistic",
)

CASE1_MANAGER_TOOLS = INITIAL_MANAGER_TOOLS + (
    "plot_longitudinal_phenotypes",
    "rank_ecotypes_by_phenotype",
    "analyse_repeated_measures_with_posthoc",
)

CASE1_PIPELINE_MANAGER_TOOLS = CASE1_MANAGER_TOOLS + (
    "get_pipeline_catalogue",
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
- perform_tukey_test: Tukey-Kramer post-hoc analysis;
- compare_linear_relationships: compare two linear fits and correlations;
- query_csv_statistic: compute a filtered maximum or mean;
- plot_longitudinal_phenotypes: generate longitudinal ecotype mean/STD plots;
- rank_ecotypes_by_phenotype: rank ecotypes directly from trusted phenotype data;
- analyse_repeated_measures_with_posthoc: run the Case 1 ANOVA and Tukey analysis
  with explicit significance thresholds and evidence-backed grouping;
- get_pipeline_catalogue: inspect canonical reusable pipeline families and their
  legacy variants without importing or executing legacy pipeline Python code.

Never invent statistical values.
Never ask the model to provide data paths or output paths.
Do not claim that a tool succeeded unless its returned evidence confirms success.
"""


def build_manager_agent(
    client: SupportsChatGetResponse,
    registry: ProductionToolRegistry,
) -> Agent:
    """Construct the initial production MAF Manager explicitly."""
    supported_profiles = (
        INITIAL_MANAGER_TOOLS,
        CASE1_MANAGER_TOOLS,
        CASE1_PIPELINE_MANAGER_TOOLS,
    )

    if registry.names not in supported_profiles:
        raise ValueError(
            "the initial Manager requires exactly one supported "
            "deterministic tool profile"
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
