"""tool_registry.py — the single source of truth for which functions become MCP tools."""
from functions.stat_test import perform_anova, perform_tukey_test

TOOL_REGISTRY = [
    (
        perform_anova,
        "perform_anova",
        "Perform Mixed-design Repeated Measures ANOVA on given data "
        "(Greenhouse-Geisser correction will be automatically applied if needed)",
    ),
    (
        perform_tukey_test,
        "perform_tukey_test",
        "Perform Post-hoc Tukey-Kramer test on given data",
    ),
]