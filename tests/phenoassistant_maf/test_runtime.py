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



@pytest.mark.asyncio
async def test_regression_comparison_executes_through_application_graph() -> None:
    implementation = Mock(
        side_effect=[
            {
                "slope": 0.0019823477915018924,
                "intercept": 0.04262671903070531,
                "r_value": 0.8910860678113759,
            },
            {
                "slope": 0.0003433802936082736,
                "intercept": 0.06349718502926727,
                "r_value": 0.7598824217936114,
            },
        ]
    )

    client = ScriptedToolClient(
        "compare_linear_relationships",
        {
            "first_x_column": "manual_leaf_area",
            "second_x_column": "projected_leaf_area",
            "y_column": "manual_dried_weight",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/potatoes.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
        first_plot_path="/trusted/manual.png",
        second_plot_path="/trusted/algorithm.png",
        regression_callable=implementation,
    )

    response = await run_application(
        application,
        "Compare manual and algorithm-derived leaf area.",
    )

    assert implementation.call_count == 2
    assert implementation.call_args_list[0].args == (
        "/trusted/potatoes.csv",
        "manual_leaf_area",
        "manual_dried_weight",
        "/trusted/manual.png",
    )
    assert implementation.call_args_list[1].args == (
        "/trusted/potatoes.csv",
        "projected_leaf_area",
        "manual_dried_weight",
        "/trusted/algorithm.png",
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(client.function_result.result)

    assert evidence["tool_name"] == "compare_linear_relationships"
    assert len(evidence["analyses"]) == 2
    assert evidence["analyses"][0]["r_value"] == 0.8910860678113759
    assert evidence["analyses"][1]["r_value"] == 0.7598824217936114
    assert response.messages[-1].text == (
        "compare_linear_relationships completed from tool evidence."
    )


@pytest.mark.asyncio
async def test_csv_statistic_executes_through_application_graph() -> None:
    implementation = Mock(
        return_value={
            "matching_rows": 22,
            "result": 649.69,
        }
    )

    client = ScriptedToolClient(
        "query_csv_statistic",
        {
            "operation": "maximum",
            "value_column": "manual_leaf_area",
            "filter_column": "Variety",
            "filter_value": "Desiree",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/potatoes.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
        aggregate_callable=implementation,
    )

    response = await run_application(
        application,
        "Find the maximum manual leaf area for Desiree.",
    )

    implementation.assert_called_once_with(
        "/trusted/potatoes.csv",
        "maximum",
        "manual_leaf_area",
        "Variety",
        "Desiree",
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(client.function_result.result)

    assert evidence["tool_name"] == "query_csv_statistic"
    assert evidence["matching_rows"] == 22
    assert evidence["result"] == 649.69
    assert response.messages[-1].text == (
        "query_csv_statistic completed from tool evidence."
    )



@pytest.mark.asyncio
async def test_case1_longitudinal_plot_executes_through_application_graph() -> None:
    implementation = Mock(
        return_value={
            "leaf_count": {
                "plot_path": "/trusted/case1/leaf_count_plot.png",
                "stats_path": "/trusted/case1/leaf_count_stats.csv",
                "ecotype_count": 5,
                "time_point_count": 52,
                "grouped_rows": 260,
            },
            "projected_leaf_area": {
                "plot_path": "/trusted/case1/pla_plot.png",
                "stats_path": "/trusted/case1/pla_stats.csv",
                "ecotype_count": 5,
                "time_point_count": 52,
                "grouped_rows": 260,
            },
        }
    )

    client = ScriptedToolClient(
        "plot_longitudinal_phenotypes",
        {
            "phenotypes": [
                "leaf_count",
                "projected_leaf_area",
            ],
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/potatoes.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
        case1_data_path="/trusted/aracrop.csv",
        case1_output_dir="/trusted/case1",
        case1_plot_callable=implementation,
        case1_anova_callable=unused_anova,
        case1_tukey_callable=unused_tukey,
    )

    response = await run_application(
        application,
        "Plot Arabidopsis phenotype growth over time.",
    )

    implementation.assert_called_once_with(
        "/trusted/aracrop.csv",
        "/trusted/case1",
        (
            "leaf_count",
            "projected_leaf_area",
        ),
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(client.function_result.result)

    assert evidence["tool_name"] == "plot_longitudinal_phenotypes"
    assert len(evidence["plots"]) == 2

    assert response.messages[-1].text == (
        "plot_longitudinal_phenotypes completed from tool evidence."
    )


@pytest.mark.asyncio
async def test_case1_ecotype_ranking_executes_through_application_graph() -> None:
    implementation = Mock(
        return_value={
            "rankings": [
                {
                    "rank": 1,
                    "ecotype": "ein2",
                    "observation_count": 260,
                    "subject_count": 5,
                    "observation_mean": 8.94815653846154,
                    "subject_mean": 8.948156538461538,
                },
                {
                    "rank": 2,
                    "ecotype": "col0",
                    "observation_count": 260,
                    "subject_count": 5,
                    "observation_mean": 7.563658846153847,
                    "subject_mean": 7.563658846153847,
                },
            ],
        }
    )

    client = ScriptedToolClient(
        "rank_ecotypes_by_phenotype",
        {
            "phenotype": "projected_leaf_area",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/potatoes.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
        case1_data_path="/trusted/aracrop.csv",
        case1_ranking_callable=implementation,
        case1_anova_callable=unused_anova,
        case1_tukey_callable=unused_tukey,
    )

    response = await run_application(
        application,
        "Rank the Arabidopsis ecotypes by PLA.",
    )

    implementation.assert_called_once_with(
        "/trusted/aracrop.csv",
        "projected_leaf_area",
        "ecotype",
        "plant_id",
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(client.function_result.result)

    assert evidence["tool_name"] == "rank_ecotypes_by_phenotype"
    assert evidence["rankings"][0]["ecotype"] == "ein2"

    assert response.messages[-1].text == (
        "rank_ecotypes_by_phenotype completed from tool evidence."
    )


@pytest.mark.asyncio
async def test_case1_repeated_measures_executes_through_application_graph() -> None:
    anova_implementation = Mock(
        return_value=[
            {
                "Source": "Interaction",
                "DF1": 2,
                "DF2": 20,
                "F": 9.5,
                "p-unc": 0.001,
            },
        ]
    )

    tukey_implementation = Mock(
        return_value=[
            {
                "A": "high",
                "B": "low",
                "mean(A)": 8.0,
                "mean(B)": 2.0,
                "diff": 6.0,
                "p-tukey": 0.001,
            },
        ]
    )

    client = ScriptedToolClient(
        "analyse_repeated_measures_with_posthoc",
        {
            "descriptor": "projected_leaf_area",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/potatoes.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
        case1_data_path="/trusted/aracrop.csv",
        case1_anova_callable=anova_implementation,
        case1_tukey_callable=tukey_implementation,
        case1_interaction_alpha=0.01,
        case1_posthoc_alpha=0.05,
    )

    response = await run_application(
        application,
        "Analyse repeated measures and post-hoc differences in PLA.",
    )

    anova_implementation.assert_called_once_with(
        "/trusted/aracrop.csv",
        "projected_leaf_area",
        "days_after_sowing",
        "ecotype",
        "plant_id",
        save_path=None,
    )

    tukey_implementation.assert_called_once_with(
        "/trusted/aracrop.csv",
        "projected_leaf_area",
        "ecotype",
        "plant_id",
        save_path=None,
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(client.function_result.result)

    assert evidence["tool_name"] == "analyse_repeated_measures_with_posthoc"
    assert evidence["interaction"]["significant"] is True
    assert evidence["interaction"]["alpha"] == 0.01
    assert len(evidence["pairwise_comparisons"]) == 1

    assert response.messages[-1].text == (
        "analyse_repeated_measures_with_posthoc "
        "completed from tool evidence."
    )
