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


@pytest.mark.asyncio
async def test_pipeline_catalogue_executes_through_application_graph() -> None:
    """Read pipeline evidence through the full production MAF graph."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    pipeline_zoo = root / "pipeline_zoo.json"

    client = ScriptedToolClient(
        "get_pipeline_catalogue",
        {
            "family": "arabidopsis_phenotype_extraction",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/potatoes.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
        case1_data_path="/trusted/aracrop.csv",
        case1_anova_callable=unused_anova,
        case1_tukey_callable=unused_tukey,
        pipeline_zoo_path=str(pipeline_zoo),
    )

    response = await run_application(
        application,
        (
            "Inspect the reusable Arabidopsis phenotype-extraction "
            "pipeline capability."
        ),
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(
        client.function_result.result
    )

    assert evidence["tool_name"] == "get_pipeline_catalogue"
    assert evidence["schema_version"] == "1"

    assert evidence["arguments"] == {
        "family": "arabidopsis_phenotype_extraction",
    }

    assert evidence["capability_count"] == 1

    capability = evidence["capabilities"][0]

    assert (
        capability["family_id"]
        == "arabidopsis_phenotype_extraction"
    )
    assert capability["variant_count"] == 5
    assert capability["requires_gpu"] is True
    assert capability["execution_status"] == "gpu_deferred"
    assert capability["maf_replacement"] is None

    assert (
        capability["legacy_dynamic_execution_allowed"]
        is False
    )

    assert len(
        capability["legacy_variants"]
    ) == 5

    variant_names = {
        item["registry_key"]
        for item in capability["legacy_variants"]
    }

    assert variant_names == {
        "ara_crop_pipeline",
        "ara_crop_pipeline_2",
        "ara_crop_pipeline_3",
        "ara_crop_pipeline_4",
        "ara_crop_pipeline_5",
    }

    assert len(client.received_messages) == 2

    first_response = client.received_messages[1][-2]

    assert first_response.contents[0].type == "text"
    assert first_response.contents[0].text.startswith(
        "Plan:"
    )

    assert first_response.contents[1].type == "function_call"
    assert (
        first_response.contents[1].name
        == "get_pipeline_catalogue"
    )

    assert response.messages[-1].text == (
        "get_pipeline_catalogue completed from tool evidence."
    )


@pytest.mark.asyncio
async def test_case3_model_catalogue_executes_through_application_graph() -> None:
    """Discover the current Case 3 classifier through production MAF."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]

    client = ScriptedToolClient(
        "get_model_catalogue",
        {
            "task": "image-classification",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/base.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
        model_zoo_path=str(
            root / "model_zoo.json"
        ),
        case3_dataset_path=str(
            root
            / "data"
            / "winter-wheat_nutri-defi-identify_dndww20"
        ),
    )

    response = await run_application(
        application,
        "What image-classification models are registered?",
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(
        client.function_result.result
    )

    assert evidence["tool_name"] == "get_model_catalogue"
    assert evidence["arguments"] == {
        "task": "image-classification",
    }

    assert evidence["task_count"] == 1
    assert evidence["total_model_count"] == 1

    task = evidence["tasks"][0]

    assert task["task"] == "image-classification"
    assert task["model_count"] == 1

    assert task["models"] == [
        {
            "checkpoint": (
                "fengchen025/"
                "winter-wheat_nutri-defi-identify_"
                "dndww20_dino2b_lora"
            )
        }
    ]

    first_response = client.received_messages[1][-2]

    assert first_response.contents[1].type == "function_call"
    assert (
        first_response.contents[1].name
        == "get_model_catalogue"
    )

    assert response.messages[-1].text == (
        "get_model_catalogue completed from tool evidence."
    )


@pytest.mark.asyncio
async def test_case3_training_readiness_executes_through_application_graph() -> None:
    """Expose the real missing-dataset/GPU boundary through production MAF."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]

    client = ScriptedToolClient(
        "assess_case3_readiness",
        {
            "operation": "training",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/base.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
        model_zoo_path=str(
            root / "model_zoo.json"
        ),
        case3_dataset_path=str(
            root
            / "data"
            / "winter-wheat_nutri-defi-identify_dndww20"
        ),
    )

    response = await run_application(
        application,
        "Check whether Case 3 training can begin.",
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(
        client.function_result.result
    )

    assert evidence["tool_name"] == "assess_case3_readiness"
    assert evidence["arguments"] == {
        "operation": "training",
    }

    assert evidence["checkpoint_registered"] is True

    assert evidence["dataset"]["root_exists"] is False
    assert (
        evidence["dataset"]["ready_for_prepare_dataset"]
        is False
    )

    assert (
        evidence["operation_preconditions_satisfied"]
        is False
    )

    assert evidence["requires_gpu"] is True
    assert evidence["execution_status"] == "gpu_deferred"
    assert (
        evidence["execution_allowed_in_cpu_phase"]
        is False
    )

    assert (
        "local Case 3 dataset directory is missing"
        in evidence["blockers"]
    )

    assert any(
        "GPU execution is deferred"
        in blocker
        for blocker in evidence["blockers"]
    )

    first_response = client.received_messages[1][-2]

    assert first_response.contents[1].type == "function_call"
    assert (
        first_response.contents[1].name
        == "assess_case3_readiness"
    )

    assert response.messages[-1].text == (
        "assess_case3_readiness completed from tool evidence."
    )


@pytest.mark.asyncio
async def test_case3_inference_readiness_executes_through_application_graph() -> None:
    """Expose registered-model readiness while preserving the GPU stop."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]

    client = ScriptedToolClient(
        "assess_case3_readiness",
        {
            "operation": "inference",
        },
    )

    application = build_application(
        client=client,
        data_path="/trusted/base.csv",
        calculator_callable=unused_calculator,
        anova_callable=unused_anova,
        tukey_callable=unused_tukey,
        model_zoo_path=str(
            root / "model_zoo.json"
        ),
        case3_dataset_path=str(
            root
            / "data"
            / "winter-wheat_nutri-defi-identify_dndww20"
        ),
    )

    response = await run_application(
        application,
        "Check whether Case 3 inference can proceed.",
    )

    assert client.function_result is not None
    assert client.function_result.exception is None

    evidence = json.loads(
        client.function_result.result
    )

    assert evidence["tool_name"] == "assess_case3_readiness"
    assert evidence["arguments"] == {
        "operation": "inference",
    }

    assert evidence["checkpoint_registered"] is True

    assert (
        evidence["expected_checkpoint"]
        == (
            "fengchen025/"
            "winter-wheat_nutri-defi-identify_"
            "dndww20_dino2b_lora"
        )
    )

    assert (
        evidence["operation_preconditions_satisfied"]
        is True
    )

    assert evidence["requires_gpu"] is True
    assert evidence["execution_status"] == "gpu_deferred"
    assert (
        evidence["execution_allowed_in_cpu_phase"]
        is False
    )

    assert evidence["blockers"] == [
        (
            "GPU execution is deferred until the canonical "
            "Nottingham GPU environment is available"
        )
    ]

    first_response = client.received_messages[1][-2]

    assert first_response.contents[1].type == "function_call"
    assert (
        first_response.contents[1].name
        == "assess_case3_readiness"
    )

    assert response.messages[-1].text == (
        "assess_case3_readiness completed from tool evidence."
    )
