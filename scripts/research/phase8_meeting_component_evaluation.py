"""Meeting-only offline component evaluation, NOT the registered agent trial matrix.

Run the frozen deterministic catalogue on existing mechanically adjudicated
development/validation cases. Compare with an explicitly naive requested-tool
pass-through reference (not C3 or C4). Also exercise the actual COCO validator
on a preserved genuine GPU artifact and independently altered temporary copies.

No API, GPU, MCP dispatch, private fixture approval, hidden gold, or scientific
qualification trial. No changes to the frozen method. The deliberately aligned
development contracts and targeted output faults are diagnostics, not evidence
of generalisation, visual accuracy, or superiority over a generic LLM critic.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.phenoguard.catalogue import resolve_capability_catalogue
from research.phenoguard.contracts import ApplicabilityDecision as D
from research.phenoguard.pilot_manifest import (
    build_development_validation_manifest, build_development_validation_gold,
)
from research.phenoguard.provenance import build_default_provenance_catalogue
from scripts.research.verify_phenoguard_method_freeze import verify_manifest
from scripts.research.phase8_attempt_ledger import load_verified_controls
from scripts.research.phase8_scientific_artifact_validator import validate_coco

EXECUTABLE = {D.EXECUTE, D.RESELECT}
ARTIFACT = ROOT / "results/phase8_gpu_engineering_smoke/potato/20261122T114432Z_447299/leaf_only_sam_results.json"
IMAGE = ROOT / "data/PotatoLeaf/IMG_8064.JPG"
ARTIFACT_SHA = "5f4aaa3c68e0c0f1035e15bbd79c70a80b84cd998339e6ae448609f62f846180"
IMAGE_SHA = "9ceeae5973237712727240469a3bbb98d66a87265cbafcc2bc2b90449a4dca8e"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def evaluate_decisions():
    scenarios = build_development_validation_manifest()
    if len(scenarios) != 12 or any(s.split.value not in {"development", "validation"} for s in scenarios):
        raise ValueError("unexpected development/validation case set")
    envelopes = build_default_provenance_catalogue()
    predicted = {}
    for s in scenarios:
        result = resolve_capability_catalogue(
            envelopes, s.request,
            requested_capability_id=s.requested_capability_id,
            training_readiness=s.training_readiness,
        )
        # Baseline is explicitly naive: call the named tool if supplied,
        # otherwise ask for clarification. It is not a learned agent.
        naive = (D.EXECUTE, s.requested_capability_id) if s.requested_capability_id else (D.CLARIFY, None)
        predicted[s.scenario_id] = {
            "request_passthrough_reference": naive,
            "frozen_resolver_component": (result.decision, result.selected_capability_id),
        }

    # Mechanical DEV/VAL labels are consulted only AFTER all decisions.
    # No hidden benchmark or external expert adjudication is accessed.
    gold = {g.scenario_id: g for g in build_development_validation_gold()}
    if set(gold) != set(predicted):
        raise ValueError("mechanical scoring label set differs")
    counts = {name: Counter() for name in next(iter(predicted.values()))}
    details = []
    for ident, observations in predicted.items():
        g = gold[ident]
        row = {"scenario": ident, "mechanical_expected_action": g.expected_decision.value}
        for name, (decision, selected) in observations.items():
            selection_ok = (
                selected == g.expected_selected_capability_id
                if not g.acceptable_selected_capability_ids
                else selected in g.acceptable_selected_capability_ids
            )
            c = counts[name]
            c["n"] += 1
            c["exact_correct"] += int(decision == g.expected_decision and selection_ok)
            c["decision_correct"] += int(decision == g.expected_decision)
            c["execution_proposed"] += int(decision in EXECUTABLE)
            c["execution_on_nonexecution_case"] += int(decision in EXECUTABLE and g.expected_decision not in EXECUTABLE)
            c["wrong_model_on_executable_case"] += int(decision in EXECUTABLE and g.expected_decision in EXECUTABLE and not selection_ok)
            c["correct_model_on_executable_case"] += int(decision in EXECUTABLE and g.expected_decision in EXECUTABLE and selection_ok)
            c["unnecessary_abstention"] += int(decision == D.ABSTAIN and g.expected_decision != D.ABSTAIN)
            row[name] = {"decision": decision.value, "selected": selected}
        details.append(row)
    return {
        "scope": "DEVELOPMENT_VALIDATION_MECHANICAL_COMPONENT_CHECK_NOT_AGENT_TRIAL",
        "summary": {name: dict(count) for name, count in counts.items()},
        "case_details": details,
    }


def evaluate_coco():
    if sha(ARTIFACT) != ARTIFACT_SHA or sha(IMAGE) != IMAGE_SHA:
        raise ValueError("preserved GPU input/output digest mismatch")
    original = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    if len(original["images"]) != 1 or len(original["annotations"]) != 13:
        raise ValueError("preserved potato artifact unexpected shape")
    im = original["images"][0]
    w, h = im["width"], im["height"]
    bad_image_id = im["id"] + 1
    bad_category = max(x["id"] for x in original["categories"]) + 1

    def set_annotation(key, value):
        def mutate(obj):
            obj["annotations"][0][key] = value
        return mutate

    def set_image(key, value):
        def mutate(obj):
            obj["images"][0][key] = value
        return mutate

    def set_mask(key, value):
        def mutate(obj):
            obj["annotations"][0]["segmentation"][key] = value
        return mutate

    faults = [
        ("incorrect_input_filename", set_image("file_name", "wrong-input.jpg")),
        ("negative_predicted_area", set_annotation("area", -1)),
        ("area_larger_than_image", set_annotation("area", w * h + 1)),
        ("confidence_out_of_range", set_annotation("score", 1.01)),
        ("wrong_image_reference", set_annotation("image_id", bad_image_id)),
        ("unknown_category", set_annotation("category_id", bad_category)),
        ("duplicate_annotation_id", set_annotation("id", original["annotations"][1]["id"])),
        ("incorrect_rle_dimensions", set_mask("size", [h + 1, w])),
        ("empty_rle_counts", set_mask("counts", "")),
    ]
    rows = []
    clean = validate_coco(ARTIFACT, expected_image_path=IMAGE.resolve())
    rows.append({"case": "unmodified_gpu_artifact", "json_parse_accepts": True,
                 "validator_accepts": clean.safe_to_report, "issues": [x.model_dump(mode="json") for x in clean.issues]})
    with tempfile.TemporaryDirectory(prefix="phenoguard_component_faults_") as td:
        for i, (name, mutate) in enumerate(faults):
            variant = copy.deepcopy(original)
            mutate(variant)
            p = Path(td) / f"fault_{i}.json"
            p.write_text(json.dumps(variant, allow_nan=False), encoding="utf-8")
            json.loads(p.read_text(encoding="utf-8"))
            checked = validate_coco(p, expected_image_path=IMAGE.resolve())
            rows.append({"case": name, "json_parse_accepts": True,
                         "validator_accepts": checked.safe_to_report,
                         "issues": [x.model_dump(mode="json") for x in checked.issues]})
        # An explicitly disclosed structural limitation: the validator
        # checks nonempty RLE strings and shape but does not decode masks.
        variant = copy.deepcopy(original)
        variant["annotations"][0]["segmentation"]["counts"] = "!"
        p = Path(td) / "rle_limit_probe.json"
        p.write_text(json.dumps(variant, allow_nan=False), encoding="utf-8")
        checked = validate_coco(p, expected_image_path=IMAGE.resolve())
        limitation = {"case": "nonempty_unchecked_rle_string",
                      "validator_accepts": checked.safe_to_report,
                      "scope": "mask RLE decodability not independently tested; excluded from targeted fault denominator"}
    if sha(ARTIFACT) != ARTIFACT_SHA or sha(IMAGE) != IMAGE_SHA:
        raise ValueError("original input/output changed during evaluation")
    return {
        "scope": "ONE_REAL_ARTIFACT_SYNTHETIC_TARGETED_FAULTS_NOT_ACCURACY_BENCHMARK",
        "clean_artifact_accepted": clean.safe_to_report,
        "targeted_faults": len(faults),
        "json_parser_faults_rejected": sum(not r["json_parse_accepts"] for r in rows[1:]),
        "validator_faults_rejected": sum(not r["validator_accepts"] for r in rows[1:]),
        "details": rows,
        "limitation_probe": limitation,
    }


def main():
    count, aggregate = verify_manifest()
    matrix, candidate = load_verified_controls()
    if candidate["scientific_execution_permitted"] is not False:
        raise ValueError("historical candidate changed")
    print("METHOD_FREEZE_VERIFIED", count, aggregate)
    print("REGISTERED_AGENT_TRIALS_EXECUTED_BY_THIS_SCRIPT=0")
    print("PROVIDER_CALLS=0 GPU_CALLS=0 HIDDEN_GOLD_READ=false")
    decisions = evaluate_decisions()
    print("=== OFFLINE APPLICABILITY COMPONENT ===")
    print(json.dumps(decisions, indent=2, sort_keys=True))
    coco = evaluate_coco()
    print("=== REAL ARTIFACT TARGETED CORRUPTION CHECK ===")
    print(json.dumps(coco, indent=2, sort_keys=True))
    print("COMPONENT_EVALUATION_COMPLETED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
