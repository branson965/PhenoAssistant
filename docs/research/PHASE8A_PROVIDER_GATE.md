# Phase 8A Provider Gate

**Date:** 2026-10-14  
**Status:** LIVE_MAF_PREFLIGHT_PASSED_PENDING_SUPERVISOR_ROUTE_ATTESTATION_AND_V0.3_RUNTIME_PRESERVATION

## Current preserved state

The offline Phase 8A runtime candidate is preserved at:

`baseline/phase8a-runtime-candidate-20261014`

Candidate commit:

`2c9717acf479191935fc0f19a980b66d813edfa5`

The candidate is explicitly pre-outcome:

- API key read: false;
- outcome-bearing scientific work performed: false;
- provider candidate: `OpenRouter->openai`;
- primary model candidate: `openai/gpt-5.6-luna`;
- breadth model candidate: `openai/gpt-5.6-sol`;
- Phase 7 v0.2 aggregate:
  `25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294`.

## Supervisor decision required

Before any authenticated provider call, confirm:

1. the approved credential ownership/access route;
2. the approved provider/billing route;
3. whether the provisional Luna primary and Sol breadth models should remain the
   study models.

A provider/model change made at this gate remains a pre-outcome design change and must
be preserved as a new runtime-candidate version rather than overwriting the existing
candidate.

## Immediate next gate after confirmation

Run only the committed non-scientific infrastructure preflight:

`scripts/research/validate_ijcai_openrouter_preflight.py`

The preflight is allowed to verify:

- authenticated provider access;
- requested model identity;
- OpenAI upstream provider pin;
- no provider fallbacks;
- seed/request parameter acceptance;
- one-tool-call MAF loop;
- response model identity;
- system fingerprint when available.

The preflight must not execute a scientific benchmark case and must emit:

`PHASE8A_LIVE_PREFLIGHT_OUTCOME_BEARING=false`

## Scientific execution prohibition

Do not execute development, validation, or hidden IJCAI scientific scenarios until:

- supervisor/provider confirmation is recorded;
- the live non-scientific provider preflight passes;
- the final provider/model/runtime candidate is frozen and content-addressed.

The hidden expert benchmark remains sealed.


## Live qualification update — 2026-11-19

The authenticated Luna/MAF echo-tool preflight **passed** on Plato.
Observed model `openai/gpt-5.6-luna`, exactly one tool call,
OpenAI upstream pinned, no fallbacks, seed 2026, temperature not sent,
compatibility adapter enabled, and
`PHASE8A_LIVE_OPENROUTER_MAF_PREFLIGHT_PASS=true`.
No system fingerprint was returned. The run was non-scientific.

The historical October runtime candidate remains unchanged.
The new live evidence is preserved in
`experiments/ijcai2027/runtime/live_preflight_evidence_20261119.json`.
Before outcome-bearing experiments, the approved provider route must
be attested explicitly and the v0.3 runtime candidate must be verified
and content-addressed. Scientific pilot integration must use the same
validated HTTP compatibility transport, not silently bypass it.

The key's successful use does not independently establish billing/credential
ownership approval, Sol endpoint compatibility or any scientific claim.
