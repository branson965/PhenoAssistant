"""No-network, non-scientific condition isolation tests for C3/C4/C8."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from research.phenoguard.contracts import ApplicabilityDecision
from research.phenoguard.pilot_manifest import build_development_validation_manifest
from research.phenoguard.post_validation import validate_phenotype_records
from scripts.research.prepare_phase8_qualification_matrix import model_visible_view
from scripts.research.phase8_condition_rehearsal import (
    C3, C4, C8, Proposal, rehearse_one,
)


def cases():
    return build_development_validation_manifest()


async def good_post_validator(result):
    return validate_phenotype_records((result,))


async def fake_executor(_selected, _request):
    return {"leaf_count": 3, "projected_leaf_area": 17.2}


async def fake_manager(view):
    return Proposal(
        decision=ApplicabilityDecision.EXECUTE,
        capability_id=view["requested_capability_id"],
    )


def test_schema_baseline_executes_mock_on_wrong_species_while_c8_reselects():
    # This is a deliberately scripted unit fixture, NOT empirical evidence of
    # an unsafe baseline LLM decision.
    scenario = cases()[1]  # potato request, Arabidopsis model requested
    visible = model_visible_view(scenario)
    called = []

    async def record_executor(capability, request):
        called.append(capability)
        return await fake_executor(capability, request)

    async def run():
        c3 = await rehearse_one(
            condition=C3, visible_view=visible, manager=fake_manager,
            critic=None, mock_executor=record_executor, post_validator=None,
        )
        c8 = await rehearse_one(
            condition=C8, visible_view=visible, manager=fake_manager,
            critic=None, mock_executor=record_executor,
            post_validator=good_post_validator,
        )
        return c3, c8

    c3, c8 = asyncio.run(run())
    assert c3.decision == ApplicabilityDecision.EXECUTE
    assert c3.selected_capability_id == scenario.requested_capability_id
    assert c3.soe_pre_verifier_used is False
    assert c3.post_validator_used is False
    assert c8.decision == ApplicabilityDecision.RESELECT
    assert c8.selected_capability_id != scenario.requested_capability_id
    assert c8.soe_pre_verifier_used is True
    assert c8.post_validator_used is True
    assert c3.model_visible_sha256 == c8.model_visible_sha256
    assert len(called) == 2
    assert c3.report_scope == "SIMULATED_OFFLINE_NOT_SCIENTIFIC_EVIDENCE"
    assert c8.report_scope == "SIMULATED_OFFLINE_NOT_SCIENTIFIC_EVIDENCE"


def test_c4_calls_separate_generic_critic_and_does_not_use_soe():
    scenario = cases()[0]
    visible = model_visible_view(scenario)
    seen = []

    async def critic(view, action):
        assert set(view) == {"scientific_request", "requested_capability_id", "training_readiness"}
        assert "catalogue" not in json.dumps(view).lower()
        seen.append(action)
        return Proposal(decision=ApplicabilityDecision.CLARIFY, capability_id=None)

    async def fail_if_executor_called(_capability, _request):
        raise AssertionError("critic rejected proposed call")

    async def run():
        return await rehearse_one(
            condition=C4, visible_view=visible, manager=fake_manager,
            critic=critic, mock_executor=fail_if_executor_called,
            post_validator=None,
        )

    result = asyncio.run(run())
    assert len(seen) == 1
    assert result.critic_used is True
    assert result.soe_pre_verifier_used is False
    assert result.tool_attempted_in_mock is False
    assert result.decision == ApplicabilityDecision.CLARIFY


@pytest.mark.parametrize("condition", [C3, C4, C8])
def test_missing_required_condition_stage_fails_closed(condition):
    visible = model_visible_view(cases()[0])
    async def run():
        return await rehearse_one(
            condition=condition,
            visible_view=visible,
            manager=fake_manager,
            critic=None,
            mock_executor=fake_executor,
            post_validator=None,
        )
    if condition == C3:
        result = asyncio.run(run())
        assert result.critic_used is False
    else:
        with pytest.raises(ValueError, match="requires"):
            asyncio.run(run())


@pytest.mark.parametrize("condition", [C3, C4])
def test_no_pheno_post_validation_in_baselines(condition):
    visible = model_visible_view(cases()[0])
    async def critic(_view, action):
        return action
    async def run():
        return await rehearse_one(
            condition=condition,
            visible_view=visible,
            manager=fake_manager,
            critic=critic if condition == C4 else None,
            mock_executor=fake_executor,
            post_validator=good_post_validator,
        )
    with pytest.raises(ValueError, match="must not receive"):
        asyncio.run(run())


def test_rejects_gold_and_split_metadata_as_model_input():
    view = model_visible_view(cases()[0])
    for key in ("expected_decision", "scenario_id", "category", "shift_dimension", "split"):
        altered = dict(view)
        altered[key] = "invalid"
        async def run():
            return await rehearse_one(
                condition=C3, visible_view=altered,
                manager=fake_manager, critic=None,
                mock_executor=fake_executor, post_validator=None,
            )
        with pytest.raises(ValueError, match="unexpected fields"):
            asyncio.run(run())


def test_c8_blocks_reporting_invalid_mock_phenotype():
    view = model_visible_view(cases()[0])
    async def bad_executor(_capability, _request):
        return {"leaf_count": -1, "projected_leaf_area": -5.0}
    async def run():
        return await rehearse_one(
            condition=C8, visible_view=view,
            manager=fake_manager, critic=None,
            mock_executor=bad_executor, post_validator=good_post_validator,
        )
    observation = asyncio.run(run())
    assert observation.decision == ApplicabilityDecision.EXECUTE
    assert observation.tool_attempted_in_mock is True
    assert observation.post_validator_used is True
    assert observation.safe_to_report is False


def test_unknown_condition_fails_closed():
    view = model_visible_view(cases()[0])
    async def run():
        return await rehearse_one(
            condition="C2_MANAGER_TOOL_DESCRIPTIONS",
            visible_view=view, manager=fake_manager,
            critic=None, mock_executor=fake_executor,
            post_validator=None,
        )
    with pytest.raises(ValueError, match="unregistered"):
        asyncio.run(run())


def test_offline_script_has_no_openrouter_or_gold_access():
    from scripts.research import phase8_condition_rehearsal as module
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY" not in source
    assert "AsyncOpenAI" not in source
    assert "OpenAIChatCompletionClient" not in source
    assert "build_development_validation_gold" not in source
    assert "PHASE8_CONDITION_REHEARSAL_PROVIDER_CALLS=0" in source
    assert "PHASE8_CONDITION_REHEARSAL_REAL_GENERIC_LLM_CRITIC=false" in source
    assert "PHASE8_CONDITION_REHEARSAL_REAL_SCIENTIFIC_DISPATCH=false" in source


def test_soe_exposure_only_in_c8_manager_input():
    scenario = cases()[0]
    view = model_visible_view(scenario)
    seen = {}

    async def manager3(received):
        seen["c3"] = received
        return await fake_manager(received)

    async def manager4(received):
        seen["c4"] = received
        return await fake_manager(received)

    async def manager8(received):
        seen["c8"] = received
        return await fake_manager(received)

    async def critic(received, proposal):
        assert "scientific_operating_envelopes" not in received
        return proposal

    async def run():
        for condition, manager in ((C3, manager3), (C4, manager4), (C8, manager8)):
            await rehearse_one(
                condition=condition,
                visible_view=view,
                manager=manager,
                critic=critic if condition == C4 else None,
                mock_executor=fake_executor,
                post_validator=good_post_validator if condition == C8 else None,
            )
    asyncio.run(run())
    assert "scientific_operating_envelopes" not in seen["c3"]
    assert "scientific_operating_envelopes" not in seen["c4"]
    assert len(seen["c8"]["scientific_operating_envelopes"]) == 3
    assert seen["c3"] == seen["c4"]
    for key in ("expected_decision", "category", "shift_dimension", "scenario_id"):
        assert key not in json.dumps(seen["c8"])


def test_c8_manager_cannot_mutate_original_shared_request():
    visible = model_visible_view(cases()[0])
    unchanged = json.dumps(visible, sort_keys=True)
    async def manager(received):
        received["scientific_request"]["species"] = "edited"
        return Proposal(
            decision=ApplicabilityDecision.EXECUTE,
            capability_id=visible["requested_capability_id"],
        )
    async def run():
        return await rehearse_one(
            condition=C8, visible_view=visible, manager=manager,
            critic=None, mock_executor=fake_executor,
            post_validator=good_post_validator,
        )
    result = asyncio.run(run())
    assert result.decision == ApplicabilityDecision.EXECUTE
    assert json.dumps(visible, sort_keys=True) == unchanged
