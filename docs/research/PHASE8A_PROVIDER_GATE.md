# Phase 8A Provider Gate

**Date:** 2026-10-14  
**Status:** BLOCKED_ON_SUPERVISOR_PROVIDER_CONFIRMATION

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
