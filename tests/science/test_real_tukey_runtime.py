"""Regression test for the preserved real Tukey scientific runtime."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_real_tukey_runtime_on_deterministic_plant_fixture() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/maf/validate_real_tukey.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "REAL_TUKEY_DIRECT_RECORDS=3" in result.stdout
    assert "REAL_TUKEY_SIGNIFICANT_PAIRS=3" in result.stdout
    assert "REAL_TUKEY_DIRECT_PASS" in result.stdout
    assert "REAL_TUKEY_SCIENTIFIC_FIXTURE_PASS" in result.stdout
