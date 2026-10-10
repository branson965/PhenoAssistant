# IJCAI 2027 Pre-Outcome Model Selection

**Frozen:** 2026-10-10  
**Status:** provisional pre-outcome, pending supervisor confirmation  
**Provisional primary:** `openai/gpt-5.6-luna`  
**Provisional breadth:** `openai/gpt-5.6-sol`

## Why the historical model is not reused

The migration live tests used `openrouter/free`.

That was appropriate for proving that the migrated Manager could make a real provider
call, but it is not suitable for a controlled paper experiment because the free router
does not identify one fixed underlying model across runs.

The IJCAI experiment therefore uses fixed OpenRouter model slugs.

## Primary model

`openai/gpt-5.6-luna` is frozen as the primary model.

Selection was made before any Phase 8 scientific outcome was observed.

Reasons:

- explicit tool-calling support;
- a fixed model slug;
- contemporary GPT-5.6 family;
- low enough cost for repeated C0-C8 trials;
- suitable for high-volume agentic/tool-selection evaluation.

The public OpenRouter catalogue records a 2026-07-09 release date. OpenRouter does
not expose an immutable model-weight revision for this slug, so the experiment records
the release date as provenance rather than pretending that it is a byte-identical
checkpoint identifier.

## Breadth model

`openai/gpt-5.6-sol` is predeclared as a stronger same-generation breadth model.

It is not a replacement selected after seeing Luna outcomes.

The breadth evaluation is restricted to the most informative comparison subset:

- C3 Manager + schemas/MCP metadata;
- C4 Manager + generic LLM Critic;
- C8 full PhenoGuard.

This gives a stronger-model robustness check without multiplying the cost of every
ablation condition.

## Provider control

OpenRouter can normally route one model slug across multiple upstream providers.

For the paper, the route is pinned to the OpenAI upstream provider with:

```json
{
  "order": ["openai"],
  "allow_fallbacks": false,
  "require_parameters": true
}
```

A provider outage therefore becomes a recorded failed attempt rather than silently
moving one condition to a different provider implementation.

## Sampling control

The GPT-5.6 Luna OpenRouter parameter surface used for this freeze does not expose a
temperature parameter.

Therefore:

- temperature is not transmitted;
- the frozen Phase 7 numeric temperature field is populated with `0.0` only as an
  explicit schema sentinel;
- every artifact also records `temperature_parameter_sent=false`;
- reasoning effort is frozen to `medium`;
- matched condition runs use the same predeclared seed schedule:
  `2026, 2027, 2028`.

This avoids falsely claiming that a temperature value was applied when it was not.

## Tool-loop control

The primary tool-using conditions use:

- at most 2 model roundtrips;
- at most 1 local function execution;
- no concurrent function invocation;
- terminate on unknown calls;
- fresh client, agent, and session for every scenario replicate.

Transport failures may be retried at most twice. Semantic/model failures are never
retried away.

## Response identity drift

Every live run should retain:

- requested model slug;
- returned model identity;
- system fingerprint when the provider exposes one;
- seed;
- condition ID;
- attempt number.

A change in returned model identity or system fingerprint is flagged before
aggregation. Results with mismatched identities must not be silently pooled.

## Claim boundary

The primary result remains a method comparison, not a claim that GPT-5.6 Luna or Sol
is intrinsically better than another model family.

The breadth model is evidence about whether the observed PhenoGuard effect survives a
stronger same-family model, not evidence of universal cross-model generality.


## Supervisor gate

Before the first authenticated provider call or scientific Phase 8 run, Valerio must
confirm the credential/provider route and whether this provisional Luna/Sol model
selection should remain the study configuration.

No scientific outcomes have been observed under this model plan, so changing the
provider or models in response to supervisor guidance would remain a pre-outcome
design decision rather than outcome-driven tuning.
