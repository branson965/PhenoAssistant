# Phase 8 provider metering evidence v0.1 (offline implementation)

**Status:** implementation proposed on a feature branch. No live/provider-billed qualification
has been performed and no scientific execution is approved.

## What this captures

For each **non-streaming** OpenRouter `POST /api/v1/chat/completions` response,
`Phase8ProviderMeteringTransport` captures the **raw** response's
`usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`, and
`usage.cost`. The charge is the **provider-reported billed USD amount**, never
inferred from tokens or a posted tariff. It retains the provider generation ID
for prospective reconciliation against OpenRouter's authenticated
`GET /api/v1/generation?id=...` endpoint.

The per-trial JSONL ledger stores only trial ID, sequence, timestamps, model,
provider generation ID, usage, charge, response SHA-256, failure codes and
hash-chain metadata. **No provider response text, tool arguments, prompts,
credentials, image paths or hidden labels are stored.**

Events are `METERED` or `METERING_MISSING`. Unknown or malformed costs,
missing or inconsistent token counts, non-200 HTTP responses and transport
exceptions block subsequent calls. A file lock and a separate nonblocking
session lease prevent simultaneous writers for the same ledger. A new session
cannot quietly resume an existing ledger, and repeated provider generation
IDs fail verification. SHA-256 chaining detects accidental modification and
partial tampering, but is **not a signed, external immutability guarantee**.

A failed or interrupted provider call may still incur a real provider charge.
The unknown-charge state must be reconciled manually before any prospective
trial restarts. Trial-level budget accounting remains in
`phase8_attempt_ledger.py`; its terminal-event metering integration and
independent invoice reconciliation are **not yet certified**.

## Integration

`Phase8MafDecisionClient.create` now accepts both optional parameters:

- `metering_trial_id="<frozen-trial-id>"`
- `metering_ledger_path=Path("<absolute, private per-trial JSONL path>")`

The two values are required together. Non-mock provider transports cannot
initialize without them. The nested order is:

`OpenRouterCompatTransport -> RawNativeToolReplyGuardTransport -> Phase8ProviderMeteringTransport -> upstream`

This records a provider charge before a malformed native tool reply is rejected
by the guard, preserving the billing evidence without allowing a callback.

## Offline test commands on Plato

```bash
cd ~/PhenoAssistant
PY="$HOME/.local/envs/phenoassistant-phase6-mcp/bin/python"

env -u OPENROUTER_API_KEY "$PY" -m pytest -q \
  tests/research/test_phase8_provider_metering_v1.py

env -u OPENROUTER_API_KEY "$PY" -m pytest -q \
  tests/research/test_phase8_native_condition_mediation_v1.py \
  tests/research/test_phase8_raw_tool_reply_guard.py \
  tests/research/test_phase8_native_tool_capture_v1.py \
  tests/research/test_phase8_maf_decision_v1.py \
  tests/research/test_phase8_openrouter_compat.py \
  tests/research/test_phase8_proposal_mcp_bridge_v1.py \
  tests/research/test_phase8_scientific_mcp.py \
  tests/research/test_phase8_image_fixture_registry.py \
  tests/research/test_phase8_provider_metering_v1.py
```

All tests use synthetic replies and `httpx.MockTransport`. They MUST NOT use
live OpenRouter credits, real images, MCP dispatch or GPUs.

## Unresolved qualification gates

1. Run and preserve the Plato offline regression results for this branch.
2. Integrate every trial's metered-call summary with the existing append-only
   qualification attempt ledger, including model/trace binding.
3. Independently reconcile billed `usage.cost` against OpenRouter generation
   records or activity data for an approved, capped pilot.
4. Independently approve real image/checkpoint assets, frozen runtime,
   reviewer sign-off and actual provider spending cap.
5. Reapprove the complete native C3/C4/C8 scientific harness before any
   outcome-bearing inference.

OpenRouter documentation:
- https://openrouter.ai/docs/api/api-reference/generations/get-generation
- https://openrouter.ai/support
- https://openrouter.ai/blog/announcements/smarter-charts-inline-svgs-and-live-usage-accounting/
