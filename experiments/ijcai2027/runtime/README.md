# Phase 8A Runtime Evidence

This directory stores pre-outcome runtime-control evidence for the IJCAI 2027
scientific-applicability evaluation.

The first candidate was captured on Nottingham Plato after the verified Phase 7 v0.2
re-freeze and before any outcome-bearing scientific LLM run.

## Current candidate

Expected files:

- `runtime_controls_candidate.json`
- `requirements_phase8_pilot.lock`

Expected runtime-controls candidate SHA-256:

`85acd6efd5ae880051548977355f05d6bdd5e048c365a945a512378023355ce1`

Expected package-lock SHA-256:

`2c67b0b895b81a482c148512ee5ab0de23e333bd21a4d44c31061e2fb19a6391`

The candidate status must remain:

`CANDIDATE_PRE_OUTCOME_PENDING_SUPERVISOR_CONFIRMATION`

until the supervisor/provider route is confirmed.

## Scientific boundary

Committing these files records the exact pre-outcome runtime state. It does not
authorise a live scientific benchmark, does not convert the provisional model plan
into a final plan, and does not imply access to or use of an API key.

If supervisor guidance changes the provider or model before the first scientific
outcome, preserve this candidate and generate a new version rather than overwriting
the historical record.
