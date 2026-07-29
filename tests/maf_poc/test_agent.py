"""Offline execution tests for the single mixed-ANOVA MAF Agent."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from agent_framework import Agent

from maf_poc.agent import build_mixed_anova_agent, run_mixed_anova_agent
from maf_poc.tool_adapter import create_mixed_anova_tool
from tests.maf_poc.fakes import ScriptedMixedAnovaClient

VALID_ARGUMENTS = {
    "descriptor": "height",
    "within_subject_factor": "time",
    "between_subject_factor": "treatment",
    "subject_id": "plant_id",
}
RECORDS = [{"Source": "time", "F": 4.25, "p-unc": 0.03}]


def _build_run(
    arguments: dict[str, object] | None = None,
) -> tuple[Agent, ScriptedMixedAnovaClient, Mock]:
    implementation = Mock(return_value=RECORDS)
    tool = create_mixed_anova_tool("/trusted/approved.csv", implementation)
    client = ScriptedMixedAnovaClient(arguments or VALID_ARGUMENTS)
    return build_mixed_anova_agent(client, tool), client, implementation


@pytest.mark.asyncio
async def test_complete_maf_execution_sequence(tmp_path: Path) -> None:
    agent, client, implementation = _build_run()

    with patch(
        "agent_framework.openai.OpenAIChatCompletionClient",
        side_effect=AssertionError("provider construction is forbidden"),
    ), patch(
        "socket.create_connection",
        side_effect=AssertionError("network access is forbidden"),
    ):
        response = await run_mixed_anova_agent(
            agent,
            "Analyse height by time and treatment for each plant.",
        )

    assert isinstance(agent, Agent)
    tools = agent.default_options["tools"]
    assert len(tools) == 1
    assert tools[0].name == "perform_mixed_anova"

    first_response = client.received_messages[1][-2]
    assert first_response.contents[0].type == "text"
    assert first_response.contents[0].text.startswith("Plan:")
    assert first_response.contents[1].type == "function_call"
    assert first_response.contents[1].name == "perform_mixed_anova"
    assert first_response.contents[1].parse_arguments() == VALID_ARGUMENTS

    implementation.assert_called_once()
    assert client.function_result is not None
    assert client.function_result.exception is None
    evidence = json.loads(client.function_result.result)
    assert evidence["records"] == RECORDS
    assert response.messages[-1].text == (
        "Mixed ANOVA completed from tool evidence: "
        "1 record(s); descriptor=height."
    )
    assert response.text.endswith(response.messages[-1].text)
    assert client.stream_values == [False, False]
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_independent_runs_do_not_share_history() -> None:
    first_agent, first_client, _ = _build_run()
    second_agent, second_client, _ = _build_run()

    await run_mixed_anova_agent(first_agent, "first run")
    await run_mixed_anova_agent(second_agent, "second run")

    assert first_agent is not second_agent
    assert len(first_client.received_messages[0]) == 1
    assert len(second_client.received_messages[0]) == 1
    assert first_client.received_messages[0][-1].text == "first run"
    assert second_client.received_messages[0][-1].text == "second run"


@pytest.mark.asyncio
async def test_invalid_tool_arguments_are_visible_as_failure() -> None:
    invalid = VALID_ARGUMENTS | {"descriptor": "   "}
    agent, client, implementation = _build_run(invalid)

    response = await run_mixed_anova_agent(agent, "invalid run")

    implementation.assert_not_called()
    assert client.function_result is not None
    assert client.function_result.exception is not None
    assert "MixedAnovaInput" in client.function_result.exception
    assert response.messages[-1].text.startswith("Mixed ANOVA failed:")
    assert "completed" not in response.messages[-1].text


def test_importing_agent_is_side_effect_free() -> None:
    sys.modules.pop("maf_poc.agent", None)

    with patch(
        "agent_framework.openai.OpenAIChatCompletionClient"
    ) as provider_constructor:
        imported = importlib.import_module("maf_poc.agent")

    provider_constructor.assert_not_called()
    assert imported.MIXED_ANOVA_INSTRUCTIONS_VERSION == "mixed-anova-agent-v1"
