"""Regression test for real ANOVA through the production MAF graph."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_real_anova_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/maf/validate_real_anova.py"],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    for marker in (
        "REAL_ANOVA_DIRECT_PASS",
        "REAL_ANOVA_GRAPH_PASS",
        "REAL_ANOVA_DIRECT_GRAPH_PARITY_PASS",
        "PHASE6E_REAL_ANOVA_VALIDATION_PASS",
    ):
        assert marker in result.stdout
