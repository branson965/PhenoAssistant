"""Read-only readiness report for private Phase 8 qualification image bindings.

Shows exactly which source/reviewer fields are missing per frozen
development/validation scenario. Does not fill fields, print private image
paths, inspect hidden gold labels, approve any review or run inference.

If all 12 private entries are complete, executes existing *structural*
fixture audit against a caller-supplied trusted root. This is not the
independent reviewer SHA approval required for real Phase 8 execution.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.phenoguard.pilot_manifest import build_development_validation_manifest
from scripts.research.phase8_image_fixture_registry import (
    DEFAULT_TEMPLATE,
    FIELDS,
    FixtureGateError,
    audit_fixtures,
    fixture_template,
)


def missing_fields(row: dict[str, Any]) -> list[str]:
    fields = FIELDS - {"scenario_id_internal_only", "model_visible_view_sha256"}
    return sorted(
        key for key in fields
        if not isinstance(row.get(key), str) or not row[key].strip()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", type=Path, default=DEFAULT_TEMPLATE,
        help="Private fixture registry or template, never a public Git file",
    )
    parser.add_argument(
        "--trusted-root", type=Path, default=ROOT / "data",
        help="Root for read-only structural asset audit once all bindings exist",
    )
    args = parser.parse_args()
    expected = fixture_template()
    scenarios = build_development_validation_manifest()
    print("PHASE8_FIXTURE_REGISTERED_SCENARIOS=" + str(len(scenarios)))
    print("PHASE8_FIXTURE_INDEPENDENT_APPROVAL_GRANTED=false")
    print("PHASE8_FIXTURE_SCIENTIFIC_EXECUTION_PERMITTED=false")
    print("PHASE8_FIXTURE_NO_PROVIDER_OR_GPU_CALLS=true")

    if not args.file.is_file():
        print("PHASE8_FIXTURE_FILE_PRESENT=false")
        print("PHASE8_FIXTURE_READINESS=NEEDS_PRIVATE_REGISTRY")
        return 2
    if args.file.is_symlink():
        print("PHASE8_FIXTURE_READINESS=REJECTED_SYMLINK")
        return 2
    try:
        registry = json.loads(args.file.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        print("PHASE8_FIXTURE_READINESS=INVALID_JSON")
        print("PHASE8_FIXTURE_ERROR=" + type(exc).__name__)
        return 2
    if not isinstance(registry, dict) or not isinstance(registry.get("entries"), list):
        print("PHASE8_FIXTURE_READINESS=INVALID_SCHEMA")
        return 2
    expected_by_id = {
        row["scenario_id_internal_only"]: row
        for row in expected["entries"]
    }
    rows = registry["entries"]
    by_id: dict[str, dict[str, Any]] = {}
    unexpected = 0
    for row in rows:
        if not isinstance(row, dict):
            unexpected += 1
            continue
        ident = row.get("scenario_id_internal_only")
        if not isinstance(ident, str) or ident not in expected_by_id or ident in by_id:
            unexpected += 1
            continue
        by_id[ident] = row

    missing_counts: Counter[str] = Counter()
    fully_bound = 0
    print("PHASE8_FIXTURE_FILE_PRESENT=true")
    print("PHASE8_FIXTURE_ENTRY_COUNT=" + str(len(rows)))
    print("PHASE8_FIXTURE_INVALID_OR_DUPLICATE_ENTRIES=" + str(unexpected))
    print("CASE_ID | SPECIES_IN_REQUEST | FIELD_READINESS")
    for scenario in scenarios:
        ident = scenario.scenario_id
        row = by_id.get(ident)
        required = sorted(FIELDS - {
            "scenario_id_internal_only", "model_visible_view_sha256"
        }) if row is None else missing_fields(row)
        if row is not None:
            if set(row) != FIELDS or (
                row.get("model_visible_view_sha256")
                != expected_by_id[ident]["model_visible_view_sha256"]
            ):
                required = sorted(set(required) | {"INVALID_SCHEMA_OR_VIEW_HASH"})
        missing_counts.update(required)
        if not required:
            fully_bound += 1
        species = scenario.request.species or "UNSPECIFIED"
        print(f"{ident} | {species} | " + (
            "FIELDS_PRESENT_NOT_YET_REVIEWED"
            if not required else ",".join(required)
        ))
    print("PHASE8_FIXTURE_FIELDS_PRESENT=" + str(fully_bound) + "/" + str(len(scenarios)))
    print("PHASE8_FIXTURE_MISSING_FIELD_COUNTS=" + json.dumps(dict(sorted(missing_counts.items()))))
    if (len(rows) != len(scenarios) or unexpected
            or fully_bound != len(scenarios)):
        print("PHASE8_FIXTURE_STRUCTURAL_AUDIT=NOT_RUN_INCOMPLETE")
        return 0

    try:
        assets = audit_fixtures(registry, trusted_root=args.trusted_root)
    except (FixtureGateError, OSError, ValueError, KeyError) as exc:
        print("PHASE8_FIXTURE_STRUCTURAL_AUDIT=FAILED")
        print("PHASE8_FIXTURE_AUDIT_REASON=" + str(exc))
        return 2
    print("PHASE8_FIXTURE_STRUCTURAL_AUDIT=PASSED_NOT_APPROVED")
    print("PHASE8_FIXTURE_UNIQUE_ASSETS=" + str(len(assets)))
    print("PHASE8_FIXTURE_REVIEW_NEXT=INDEPENDENT_REAL_SOURCE_AND_SPECIES_CHECK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
