"""No-network tests for the independently verified 108-trial plan."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from scripts.research import prepare_phase8_qualification_matrix as planner
from scripts.research import verify_phase8_qualification_matrix as verifier


def reference_plan():
    return planner.build_matrix(
        candidate=planner.read_json(planner.CANDIDATE),
        runtime=planner.read_json(planner.RUNTIME_PLAN),
        protocol=planner.read_json(planner.PROTOCOL),
        prompt_contract=planner.read_json(planner.CONDITION_PROMPTS),
    )


def test_recomputed_matrix_matches_frozen_sha_when_serialized():
    plan = reference_plan()
    encoded = __import__("json").dumps(plan, indent=2, sort_keys=True) + "\n"
    digest = __import__("hashlib").sha256(encoded.encode("utf-8")).hexdigest()
    assert digest == verifier.EXPECTED_MATRIX_SHA256
    verifier.audit(plan, reference_plan())


@pytest.mark.parametrize("field,value", [
    ("trial_count", 107),
    ("api_key_read", True),
    ("scientific_execution_permitted", True),
    ("outcome_bearing_work_performed", True),
])
def test_bad_matrix_metadata_fails_closed(field, value):
    plan = reference_plan()
    bad = deepcopy(plan)
    bad[field] = value
    with pytest.raises(ValueError):
        verifier.audit(bad, plan)


def test_gold_field_leakage_fails_closed():
    plan = reference_plan()
    altered = deepcopy(plan)
    altered["trials"][0]["expected_decision"] = "EXECUTE"
    with pytest.raises(ValueError):
        verifier.audit(altered, altered)


def test_trial_status_drift_fails_closed():
    plan = reference_plan()
    changed = deepcopy(plan)
    changed["trials"][0]["status"] = "SUCCEEDED"
    with pytest.raises(ValueError):
        verifier.audit(changed, changed)


def test_script_does_not_access_key_or_gold():
    content = Path(verifier.__file__).read_text("utf-8")
    assert "OPENROUTER_API_KEY" not in content
    assert "build_development_validation_gold" not in content
    assert "AsyncOpenAI" not in content
    assert "OpenAIChatCompletionClient" not in content
    assert "PHASE8_QUALIFICATION_VERIFY_OUTCOME_BEARING=false" in content
