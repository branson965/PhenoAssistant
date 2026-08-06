"""Validate original ANOVA through the production MAF graph."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

# Permit this validation script to be executed directly from any directory.
import sys as _sys
from pathlib import Path as _Path

_PHENOASSISTANT_REPOSITORY_ROOT = (
    _Path(__file__).resolve().parents[2]
)

if str(_PHENOASSISTANT_REPOSITORY_ROOT) not in _sys.path:
    _sys.path.insert(
        0,
        str(_PHENOASSISTANT_REPOSITORY_ROOT),
    )

from functions.stat_test import perform_anova
from phenoassistant_maf import build_application, run_application
from tests.phenoassistant_maf.fakes import ScriptedToolClient

DATA = Path("tests/fixtures/maf/mixed_anova_plants.csv")
ARGS = {
    "descriptor": "height",
    "within_subject_factor": "time",
    "between_subject_factor": "treatment",
    "subject_id": "plant_id",
}


# PHASE6E_EXPLICIT_TOOL_BINDINGS
def phase6e_forbidden_calculator(
    a: int,
    b: int,
    operator: str,
) -> int:
    """Fail if the ANOVA validation selects the calculator."""
    del a, b, operator
    raise AssertionError(
        "calculator must not be selected during ANOVA validation"
    )


def phase6e_forbidden_tukey(
    data_path: str,
    descriptor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    """Fail if the ANOVA validation selects Tukey."""
    del (
        data_path,
        descriptor,
        between_subject_factor,
        subject_id,
        save_path,
    )
    raise AssertionError(
        "Tukey must not be selected during ANOVA validation"
    )


def records(value: object, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise AssertionError(f"{label} did not return non-empty records")
    if not all(isinstance(item, dict) for item in value):
        raise AssertionError(f"{label} returned non-dictionary records")
    return value


async def main() -> None:
    path = DATA.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    direct = records(
        perform_anova(
            str(path),
            ARGS["descriptor"],
            ARGS["within_subject_factor"],
            ARGS["between_subject_factor"],
            ARGS["subject_id"],
            save_path=None,
        ),
        "direct ANOVA",
    )
    print(f"REAL_ANOVA_DIRECT_RECORDS={len(direct)}")
    print("REAL_ANOVA_DIRECT_PASS")

    client = ScriptedToolClient("perform_anova", ARGS)
    app = build_application(
        client=client,
        data_path=str(path),
        calculator_callable=phase6e_forbidden_calculator,
        anova_callable=perform_anova,
        tukey_callable=phase6e_forbidden_tukey,
    )
    response = await run_application(
        app,
        "Run mixed ANOVA for height by time and treatment using plant_id.",
    )

    if client.function_result is None or client.function_result.exception is not None:
        raise AssertionError(
            f"Production graph tool failure: {client.function_result!r}"
        )

    payload = json.loads(client.function_result.result)
    if payload.get("tool_name") != "perform_anova":
        raise AssertionError(payload)

    graph = records(payload.get("records"), "graph ANOVA")
    if len(direct) != len(graph):
        raise AssertionError(
            f"Direct/graph record mismatch: {len(direct)} != {len(graph)}"
        )
    if not response.messages or not response.messages[-1].text.strip():
        raise AssertionError("Production graph returned no final text")

    print(f"REAL_ANOVA_GRAPH_RECORDS={len(graph)}")
    print("REAL_ANOVA_GRAPH_PASS")
    print("REAL_ANOVA_DIRECT_GRAPH_PARITY_PASS")
    print("PHASE6E_REAL_ANOVA_VALIDATION_PASS")


if __name__ == "__main__":
    asyncio.run(main())
