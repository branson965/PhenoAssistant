"""Verify the exact Plato-generated Phase 8 qualification matrix offline.

Never reads OpenRouter credentials, benchmark gold labels or hidden test data.
This verifies a PLANNING artifact, not a completed experimental run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research import prepare_phase8_qualification_matrix as plan  # noqa: E402

EXPECTED_MATRIX_SHA256 = "8a9688aa464564bf99121656430ea09fc93bbf2b1d262a73a9b2276944876692"


def audit(matrix: dict, expected: dict) -> None:
    """Fail closed if any trial, label barrier, control or cost flag drifts."""
    if matrix != expected:
        raise ValueError("matrix differs from deterministic frozen-input re-derivation")
    if matrix["case_count"] != 12 or matrix["trial_count"] != 108:
        raise ValueError("qualification counts changed")
    if matrix["conditions"] != [
        "C3_MANAGER_TOOL_SCHEMAS",
        "C4_MANAGER_GENERIC_CRITIC",
        "C8_FULL_PHENOGUARD",
    ]:
        raise ValueError("condition set/order changed")
    if matrix["seeds"] != [2026, 2027, 2028]:
        raise ValueError("seed schedule changed")
    if matrix["scientific_execution_permitted"] is not False:
        raise ValueError("scientific execution authorization appeared")
    if matrix["api_key_read"] is not False:
        raise ValueError("credential-read flag appeared")
    if matrix["outcome_bearing_work_performed"] is not False:
        raise ValueError("matrix claims scientific outcomes")
    if any(trial["status"] != "PLANNED_NO_MODEL_CALL" for trial in matrix["trials"]):
        raise ValueError("trial status changed")
    banned_fields = {
        "expected_decision",
        "expected_selected_capability_id",
        "rationale_code",
        "expert_adjudication_required",
        "gold",
    }
    def visit(item):
        if isinstance(item, dict):
            if banned_fields.intersection(item):
                raise ValueError("gold label field leaked into matrix")
            for value in item.values():
                visit(value)
        elif isinstance(item, list):
            for value in item:
                visit(value)
    visit(matrix)


def main() -> int:
    if not plan.OUTPUT.is_file():
        print("PHASE8_QUALIFICATION_VERIFY_PASS=false")
        print("PHASE8_QUALIFICATION_VERIFY_REASON=matrix-not-found")
        return 2
    try:
        actual = plan.hash_file(plan.OUTPUT)
        if actual != EXPECTED_MATRIX_SHA256:
            raise ValueError("matrix SHA-256 differs from Plato-verified result")
        matrix = plan.read_json(plan.OUTPUT)
        candidate = plan.read_json(plan.CANDIDATE)
        runtime = plan.read_json(plan.RUNTIME_PLAN)
        protocol = plan.read_json(plan.PROTOCOL)
        prompts = plan.read_json(plan.CONDITION_PROMPTS)
        expected = plan.build_matrix(
            candidate=candidate,
            runtime=runtime,
            protocol=protocol,
            prompt_contract=prompts,
        )
        audit(matrix, expected)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("PHASE8_QUALIFICATION_VERIFY_PASS=false")
        print("PHASE8_QUALIFICATION_VERIFY_REASON=" + str(exc))
        return 3

    print("PHASE8_QUALIFICATION_VERIFY_SHA256=" + EXPECTED_MATRIX_SHA256)
    print("PHASE8_QUALIFICATION_VERIFY_TRIALS=108")
    print("PHASE8_QUALIFICATION_VERIFY_GOLD_LABELS_READ=false")
    print("PHASE8_QUALIFICATION_VERIFY_API_CALLS=0")
    print("PHASE8_QUALIFICATION_VERIFY_OUTCOME_BEARING=false")
    print("PHASE8_QUALIFICATION_VERIFY_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
