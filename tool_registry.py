"""tool_registry.py — single source of truth for which functions become MCP tools."""

from functions.stat_test import perform_anova, perform_tukey_test
from functions.generic_tools import calculator, make_dir

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
    (
        calculator,
        "calculator",
        "Perform basic arithmetic operations between two integers.",
    ),
    (
        make_dir,
        "make_dir",
        "Check if a directory exists, and create it if it does not. Call it whenever you need to save files to a directory.",
    ),
]
