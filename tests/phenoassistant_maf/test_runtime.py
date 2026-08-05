"""Offline end-to-end tests for the production MAF application."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

import pytest
from agent_framework import Agent

from phenoassistant_maf.application import (
    build_application,
)
from phenoassistant_maf.runtime import (
    run_application,
)
from tests.phenoassistant_maf.fakes import (
    ScriptedToolClient,
)


def unused_calculator(
    a: int,
    b: int,
    operator: str,
) -> int:
    return 0


def unused_anova(
    data_path: str,
    descriptor: str,
    within_subject_factor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    return []


def unused_tukey(
    data_path: str,
    descriptor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, object]]:
    return []


@pytest.mark.asyncio
async def test_calculator_executes_through_application_graph() -> None:
    implementation = Mock(return_value=12)

    client = ScriptedToolClient(
        "calculator",
        {
            "a": 7,
            "b": 5,
            "operator": "+",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/data.csv",
        calculator_callable=implementation,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
    )

    with patch(
        "agent_framework.openai.OpenAIChatCompletionClient",
        side_effect=AssertionError(
            "provider construction is forbidden"
        ),
    ):
        response = await run_application(
            application,
            "Calculate seven plus five.",
        )

    assert isinstance(
        application.manager,
        Agent,
    )

    implementation.assert_called_once_with(
        7,
        5,
        "+",
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(
        client.function_result.result
    )

    assert evidence["tool_name"] == "calculator"
    assert evidence["result"] == 12

    first_response = client.received_messages[1][-2]

    assert first_response.contents[0].type == "text"
    assert first_response.contents[0].text.startswith(
        "Plan:"
    )
    assert first_response.contents[1].type == "function_call"
    assert (
        first_response.contents[1].name
        == "calculator"
    )

    assert response.messages[-1].text == (
        "calculator completed from tool evidence."
    )

    assert client.stream_values == [
        False,
        False,
    ]


@pytest.mark.asyncio
async def test_anova_executes_through_application_graph() -> None:
    records = [
        {
            "Source": "Interaction",
            "F": 4.25,
            "p-unc": 0.03,
        }
    ]

    implementation = Mock(
        return_value=records
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

    application = build_application(
        client=client,
        data_path="/trusted/approved.csv",
        calculator_callable=unused_calculator,
        anova_callable=implementation,
        tukey_callable=unused_tukey,
    )

    response = await run_application(
        application,
        (
            "Analyse height by time and treatment "
            "for each plant."
        ),
    )

    implementation.assert_called_once_with(
        "/trusted/approved.csv",
        "height",
        "time",
        "treatment",
        "plant_id",
        save_path=None,
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(
        client.function_result.result
    )

    assert evidence["tool_name"] == "perform_anova"
    assert evidence["records"] == records

    assert response.messages[-1].text == (
        "perform_anova completed from tool evidence."
    )


@pytest.mark.asyncio
async def test_invalid_tool_arguments_are_visible() -> None:
    implementation = Mock(
        return_value=12
    )

    client = ScriptedToolClient(
        "calculator",
        {
            "a": 7,
            "b": 5,
            "operator": "%",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/data.csv",
        calculator_callable=implementation,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
    )

    response = await run_application(
        application,
        "Use an invalid calculator operator.",
    )

    implementation.assert_not_called()

    assert client.function_result is not None
    assert client.function_result.exception is not None

    assert response.messages[-1].text.startswith(
        "calculator failed:"
    )

    assert "completed" not in response.messages[-1].text


@pytest.mark.asyncio
async def test_blank_prompt_is_rejected_before_client_call() -> None:
    client = ScriptedToolClient(
        "calculator",
        {
            "a": 1,
            "b": 1,
            "operator": "+",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/data.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
    )

    with pytest.raises(
        ValueError,
        match="prompt must not be blank",
    ):
        await run_application(
            application,
            "   ",
        )

    assert client.received_messages == []


@pytest.mark.asyncio
async def test_independent_applications_do_not_share_history() -> None:
    first_client = ScriptedToolClient(
        "calculator",
        {
            "a": 2,
            "b": 3,
            "operator": "+",
        },
    )

    second_client = ScriptedToolClient(
        "calculator",
        {
            "a": 4,
            "b": 5,
            "operator": "+",
        },
    )

    first_application = build_application(
        client=first_client,
        data_path="/trusted/data.csv",
        calculator_callable=lambda a, b, operator: a + b,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
    )

    second_application = build_application(
        client=second_client,
        data_path="/trusted/data.csv",
        calculator_callable=lambda a, b, operator: a + b,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
    )

    await run_application(
        first_application,
        "first run",
    )

    await run_application(
        second_application,
        "second run",
    )

    assert first_application is not second_application
    assert (
        first_application.manager
        is not second_application.manager
    )

    assert len(
        first_client.received_messages[0]
    ) == 1

    assert len(
        second_client.received_messages[0]
    ) == 1

    assert (
        first_client.received_messages[0][-1].text
        == "first run"
    )

    assert (
        second_client.received_messages[0][-1].text
        == "second run"
    )
