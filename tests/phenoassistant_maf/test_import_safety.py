"""Import-safety tests for the production MAF package."""

from __future__ import annotations

import subprocess
import sys

from phenoassistant_maf.config import OpenRouterSettings


def test_package_import_does_not_import_scientific_modules() -> None:
    script = """
import sys
import phenoassistant_maf

assert "functions.stat_test" not in sys.modules
assert "functions.generic_tools" not in sys.modules
print("PRODUCTION_IMPORT_SAFE")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PRODUCTION_IMPORT_SAFE" in result.stdout


def test_production_settings_redact_api_key() -> None:
    secret = "unit-test-secret-value"

    settings = OpenRouterSettings(
        api_key=secret,
        model="provider/model",
    )

    assert secret not in repr(settings)
    assert secret not in str(settings)
