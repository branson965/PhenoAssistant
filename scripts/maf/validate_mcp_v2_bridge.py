#!/usr/bin/env python3
"""Validate real MAF -> MCP v2 -> PhenoAssistant scientific execution."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )

from functions.stat_test import (
    perform_anova,
    perform_tukey_test,
)
from phenoassistant_maf.application import PhenoAssistantApplication
from phenoassistant_maf.manager import build_manager_agent
from phenoassistant_maf.registry import build_production_tool_registry
from phenoassistant_maf.runtime import run_application
from phenoassistant_maf.tools.statistics import (
    build_anova_handler,
    build_tukey_handler,
)
from phenoassistant_mcp.maf_bridge_v2 import (
    build_mcp_anova_handler,
    build_mcp_tukey_handler,
    replace_first_parity_slice_with_mcp,
)
from phenoassistant_mcp.server_v2 import build_phase6_mcp_server
from tests.phenoassistant_maf.fakes import ScriptedToolClient


FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "maf"
    / "mixed_anova_plants.csv"
).resolve()


def transport_control_calculator(
    a: int,
    b: int,
    operator: str,
) -> int:
    operations = {
        "+": a + b,
        "-": a - b,
        "*": a * b,
        "/": int(a / b),
    }
    return operations[operator]


async def validate_handler_parity(server) -> None:
    direct_anova = build_anova_handler(
        str(FIXTURE),
        perform_anova,
    )
    mcp_anova = build_mcp_anova_handler(
        server,
        str(FIXTURE),
    )

    anova_args = {
        "descriptor": "height",
        "within_subject_factor": "time",
        "between_subject_factor": "treatment",
        "subject_id": "plant_id",
    }

    direct_anova_result = direct_anova(**anova_args)
    mcp_anova_result = await mcp_anova(**anova_args)

    assert (
        direct_anova_result.model_dump(mode="json")
        == mcp_anova_result.model_dump(mode="json")
    )

    print("PHASE6C_DIRECT_MCP_MAF_ANOVA_ENVELOPE_PARITY_PASS=true")

    direct_tukey = build_tukey_handler(
        str(FIXTURE),
        perform_tukey_test,
    )
    mcp_tukey = build_mcp_tukey_handler(
        server,
        str(FIXTURE),
    )

    tukey_args = {
        "descriptor": "height",
        "between_subject_factor": "treatment",
        "subject_id": "plant_id",
    }

    direct_tukey_result = direct_tukey(**tukey_args)
    mcp_tukey_result = await mcp_tukey(**tukey_args)

    assert (
        direct_tukey_result.model_dump(mode="json")
        == mcp_tukey_result.model_dump(mode="json")
    )

    print("PHASE6C_DIRECT_MCP_MAF_TUKEY_ENVELOPE_PARITY_PASS=true")


async def validate_manager_path(server) -> None:
    direct_registry = build_production_tool_registry(
        data_path=str(FIXTURE),
        calculator_callable=transport_control_calculator,
        anova_callable=perform_anova,
        tukey_callable=perform_tukey_test,
    )

    bridged_registry = replace_first_parity_slice_with_mcp(
        direct_registry,
        server=server,
        data_path=str(FIXTURE),
    )

    assert bridged_registry.names == direct_registry.names

    for name in (
        "calculator",
        "perform_anova",
        "perform_tukey_test",
    ):
        assert (
            bridged_registry.get(name).description
            == direct_registry.get(name).description
        )

    client = ScriptedToolClient(
        "perform_anova",
        {
            "descriptor": "height",
            "within_subject_factor": "time",
            "between_subject_factor": "treatment",
            "subject_id": "plant_id",
        },
    )

    application = PhenoAssistantApplication(
        manager=build_manager_agent(
            client=client,
            registry=bridged_registry,
        ),
        registry=bridged_registry,
    )

    response = await run_application(
        application,
        "Run mixed ANOVA for height by time and treatment using plant_id.",
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    payload = json.loads(
        client.function_result.result
    )

    assert payload["tool_name"] == "perform_anova"
    assert len(payload["records"]) == 3
    assert "data_path" not in payload["arguments"]
    assert response.messages
    assert response.messages[-1].text.strip()

    print("PHASE6C_MANAGER_MCP_ANOVA_RECORDS=3")
    print("PHASE6C_MANAGER_TRUSTED_PATH_HIDDEN=true")
    print("PHASE6C_MAF_TO_MCP_MANAGER_PATH_PASS=true")


async def main() -> None:
    if not FIXTURE.is_file():
        raise FileNotFoundError(FIXTURE)

    server = build_phase6_mcp_server(
        calculator_callable=transport_control_calculator,
        anova_callable=perform_anova,
        tukey_callable=perform_tukey_test,
    )

    await validate_handler_parity(server)
    await validate_manager_path(server)

    print("PHASE6C_REAL_MAF_MCP_INTEGRATION_PASS=true")


if __name__ == "__main__":
    asyncio.run(main())
