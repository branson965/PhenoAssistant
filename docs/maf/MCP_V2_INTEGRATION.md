# MCP v2 Integration Contract

**Status:** Phase 6 integration contract — CLOSED 2026-10-10  
**Protocol:** MCP `2026-07-28`  
**SDK:** `mcp==2.3.0`  
**MAF:** `agent-framework-core==1.11.0`, `agent-framework-openai==1.11.0`

## Scope

The Phase 6 MCP v2 integration intentionally covers the three tools with exact
semantic matches across the frozen direct-MAF and MCP boundaries:

- `calculator`;
- `perform_anova`;
- `perform_tukey_test`.

The frozen Vincent MCP v1 baseline remains preserved separately. The v2 work does
not bulk-register the historical tool catalogue and does not overwrite the v1
baseline.

## Manager-facing contract

The MAF Manager sees the same names, descriptions, typed input models, and typed
result envelopes on the direct and MCP-backed paths.

Trusted application data paths are bound by the application layer. They are not
model-controlled arguments and are not exposed in the Manager-facing ANOVA or
Tukey schemas.

## Client lifecycle

Two explicit client modes are supported:

1. one-shot calls through `call_structured_tool(...)`, which create and close one
   MCP client session per call;
2. reusable warm sessions through `McpV2Session`, which keep one client lifecycle
   open for repeated calls and close it deterministically with `async with`.

Using a reusable session before entry, after exit, or attempting to enter the same
session twice fails with `McpV2LifecycleError`.

## Timeout behaviour

Discovery and tool calls accept an optional positive finite `timeout_seconds`.

Timeouts are enforced at the PhenoAssistant client boundary and raise
`McpV2TimeoutError`. A timeout is therefore visible to the orchestration layer and
is not converted into successful scientific evidence.

The current Phase 6 server is exercised in-process for deterministic integration
testing. Remote/network transport timeout behaviour must be evaluated separately
when a remote MCP transport is introduced; this document does not claim network
fault coverage from in-process tests.

## Failure mapping

The boundary fails closed:

- MCP `is_error` results -> `McpV2ToolError`;
- missing/non-dictionary structured content -> `McpV2SchemaError`;
- malformed scientific record envelopes -> `McpV2SchemaError`;
- invalid trusted application path -> `ValueError`;
- expired timeout -> `McpV2TimeoutError`;
- invalid persistent-session lifecycle -> `McpV2LifecycleError`.

Manager-level tests also require an MCP tool failure to be surfaced as failure,
without a false success summary.

## Verified parity evidence

On Plato, the Phase 6 evidence currently includes:

- exact three-tool discovery under protocol `2026-07-28`;
- direct-vs-MCP transport parity;
- real preserved ANOVA direct-vs-MCP record parity;
- real preserved Tukey direct-vs-MCP record parity;
- identical typed MAF result envelopes for direct and MCP scientific paths;
- production-shaped Manager -> FunctionTool -> MCP -> preserved ANOVA execution;
- trusted dataset path hidden from the Manager;
- injected tool, schema, and lifecycle failures fail closed;
- final Phase 6E suite passes 19/19 on Plato;
- explicit timeout and persistent-session lifecycle semantics are verified;
- typed boundary errors survive MCP client cleanup without ExceptionGroup masking.

## Transport overhead probe

`scripts/maf/measure_mcp_v2_transport.py` isolates the interface cost with the
deterministic calculator. It reports direct, one-shot-session, and
persistent-session timing separately and records package/protocol versions.

This microbenchmark is deliberately not presented as end-to-end scientific latency.
The controlled evaluation phase must measure real workflow latency, tokens, cost,
cold/warm behaviour, failures, and scientific-result parity under the frozen
experimental conditions.

## Secrets and configuration

No provider credential is required for the deterministic MCP integration tests.
Credentials remain environment/configuration concerns and must never be embedded in
the MCP server, bridge, tests, benchmark outputs, or documentation.


## Phase 6 closure benchmark

Final Plato transport-only microbenchmark, 10 warmup calls and 100 measured trials:

- direct median: `0.0002445 ms`;
- one-shot MCP median: `1.5335825 ms`;
- persistent-session MCP median: `0.3698135 ms`;
- one-shot median overhead vs direct: `1.533338 ms`;
- persistent median overhead vs direct: `0.369569 ms`;
- result parity: PASS.

The complete closure record is
`docs/maf/evidence/PHASE6_MCP_V2_INTEGRATION_20261010.md`.
