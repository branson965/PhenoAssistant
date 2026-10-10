# Phase 6 MCP v2 + MAF Integration Closure Evidence

**Date:** 2026-10-10  
**Branch:** `feature/maf-mcp-v2-integration`  
**Evaluated commit:** `514b0a9a36b1bfb75c24aeb29e33c1aaf096d012`  
**Decision:** **PHASE 6 CLOSED**

## Scope

Phase 6 migrated the bounded exact-semantic MCP slice to the modern MCP Python SDK,
integrated that slice behind the production-shaped MAF Manager contract, and verified
direct/MCP scientific parity, fail-closed behaviour, explicit lifecycle handling, and
transport overhead.

The bounded slice is intentionally:

- `calculator`;
- `perform_anova`;
- `perform_tukey_test`.

The preserved Vincent MCP v1 baseline was not overwritten.

## Frozen environment

- Python: `3.11.17`
- MCP SDK: `mcp==2.3.0`
- protocol: `2026-07-28`
- `agent-framework-core==1.11.0`
- `agent-framework-openai==1.11.0`
- `pydantic==2.13.4`
- `pytest==8.4.2`
- `pytest-asyncio==0.26.0`

`pip check` was clean at the final Phase 6E checkpoint.

## Evidence chain

### A. MCP v2 transport contract

The runtime import contract was verified on Plato and the MCP v2 discovery/direct
parity suite passed. Tool discovery is bounded to the three approved parity tools.

### B. Real scientific direct-versus-MCP parity

Using the preserved repository statistical implementations and the frozen
`mixed_anova_plants.csv` fixture:

- ANOVA direct path: 3 records;
- ANOVA MCP path: 3 records;
- direct and MCP records matched exactly after deterministic normalisation;
- Tukey direct path: 3 records;
- Tukey MCP path: 3 records;
- direct and MCP records matched exactly after deterministic normalisation.

### C. Production-shaped MAF -> MCP execution

The MAF-facing bridge preserves the direct MAF tool names, descriptions, typed input
models, and typed result envelopes.

The production-shaped path was executed successfully:

```text
MAF Manager
-> FunctionTool
-> MCP v2 Client
-> MCP Server
-> preserved scientific implementation
-> typed evidence
```

The application-controlled dataset path remains hidden from the Manager-facing schema.

### D. Fail-closed behaviour

The combined Phase 6D suite passed 14/14 on Plato. It covered:

- injected tool implementation failure;
- server return-contract violation;
- malformed structured payload;
- non-dictionary scientific records;
- invalid trusted data path;
- repeated one-shot client sessions;
- Manager-level failure propagation without a false success claim.

### E. Explicit lifecycle and timeout contract

The final Phase 6E suite passed **19/19** on Plato after fixing an MCP SDK cleanup
interaction that wrapped already-classified boundary exceptions inside an
`ExceptionGroup`.

The final contract verifies:

- reusable persistent MCP client sessions;
- rejection of calls outside an active session;
- rejection of double entry;
- visible caller-controlled timeout failure;
- positive finite timeout validation;
- preservation of typed PhenoAssistant boundary errors across MCP client cleanup.

## Transport microbenchmark

The final transport-only calculator microbenchmark used 10 warmup calls and 100
measured trials.

| Path | Median (ms) | Mean (ms) | p95 (ms) |
|---|---:|---:|---:|
| Direct Python | 0.0002445 | 0.00025253 | 0.000263 |
| MCP one-shot session | 1.5335825 | 1.55223348 | 1.696495 |
| MCP persistent session | 0.3698135 | 0.37902302 | 0.433335 |

Median interface overhead relative to direct execution:

- one-shot MCP: **1.533338 ms**;
- persistent-session MCP: **0.369569 ms**.

All paths returned the same expected result.

These measurements are an **in-process interface microbenchmark**, not end-to-end
scientific workflow latency and not a claim about remote/network MCP performance.

Machine-readable evidence is preserved in
`docs/maf/evidence/PHASE6E_MCP_TRANSPORT_BENCHMARK_20261010.json`.

## Repository hygiene

At the final checkpoint:

- dependency health was clean;
- a basic repository secret-pattern scan returned no matches;
- generated benchmark outputs are ignored;
- tracked Python bytecode was removed and remains ignored.

The secret-pattern scan is a bounded hygiene check, not a claim that every possible
credential format has been exhaustively detected.

## Phase gate assessment

The migration-plan MCP integration gate is satisfied:

| Gate requirement | Evidence |
|---|---|
| Same target tool invoked direct and through MCP | PASS |
| Arguments/results match | PASS |
| Failures visible | PASS |
| No credentials embedded in the integration | PASS under bounded repository checks |
| Vincent MCP baseline not overwritten | PASS |

Additional Phase 6 evidence exceeds the minimum gate through real statistical parity,
production-shaped MAF integration, typed failure semantics, timeout handling, explicit
warm-session lifecycle, and measured cold/warm interface overhead.

## Carry-forward limitations

Phase 6 closure does **not** close the independent Phase 5 Case 3 blocker. Historical
private Case 3 resources remain inaccessible to the current account, and no retraining
or substitute checkpoint is authorised without explicit provenance approval.

Remote/network MCP transport behaviour also remains outside the deterministic
in-process Phase 6 claim boundary and should be evaluated only if a remote transport
becomes part of the frozen experiment.

## Transition

The MCP/MAF interface is now stable enough to serve as infrastructure for the next
research phase. Scientific-applicability method work must remain separate from the
migration branch and should consume this frozen interface through explicit adapters.
