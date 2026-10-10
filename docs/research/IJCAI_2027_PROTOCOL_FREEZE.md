# Phase 7H — Prospective IJCAI 2027 Experiment Protocol Freeze

**Date:** 2026-10-10  
**Venue:** IJCAI 2027 stretch target  
**Internal go/no-go:** 2026-11-30  
**Fallback:** ECAI 2027  
**Status:** protocol structure committed, runtime verification pending

## Purpose

Phase 7H prospectively freezes the experiment structure before the Phase 8 pilot and
before any hidden-test outcome is available.

The research question remains scientific applicability under distribution shift. MAF
and MCP are infrastructure and controlled execution variables rather than the novelty
claim.

## Frozen condition catalogue

The main condition identities are:

| ID | Condition |
|---|---|
| C0 | model without tools |
| C1 | Manager + tool names |
| C2 | Manager + tool descriptions |
| C3 | Manager + tool schemas / MCP metadata |
| C4 | Manager + generic LLM Critic |
| C5 | Manager + deterministic structural/schema validator |
| C6 | Scientific Operating Envelope only |
| C7 | Scientific Operating Envelope + pre-execution verifier |
| C8 | full PhenoGuard |
| C9 | expert oracle |

The full PhenoGuard condition includes:

- Scientific Operating Envelope;
- pre-execution scientific-applicability resolution;
- EXECUTE / RESELECT / CLARIFY / ABSTAIN / RECOMMEND_TRAINING policy;
- deterministic decision trace;
- bounded post-execution scientific validation.

The primary tool-using comparison interface is MCP. Portability is evaluated
separately by repeating C3 and C8 under both direct Python and MCP-backed execution.

## Controlled-variable contract

Before any directly compared run set is executed, the run manifest must freeze:

- provider;
- model identifier;
- model revision/version where identifiable;
- temperature;
- maximum output tokens;
- prompt-bundle SHA-256;
- tool-catalogue SHA-256;
- task-manifest SHA-256;
- retry policy;
- iteration limit;
- session-reset policy;
- package-lock SHA-256;
- hardware class.

The schema rejects blank identities and invalid numeric controls.

Concrete provider/model values are intentionally **not** guessed in Phase 7H. They
must be filled and hashed before the first outcome-bearing Phase 8 pilot run, and may
not be changed after pilot freeze merely because another configuration looks better.

## Required metrics

The protocol retains every metric in the authoritative scientific-applicability plan:

- valid-execution accuracy;
- unsafe-execution rate;
- correct-abstention rate;
- unnecessary-abstention rate;
- clarification accuracy;
- re-selection accuracy;
- coverage;
- risk-coverage;
- repeated-run reliability;
- final-answer grounding;
- latency;
- cost;
- failure-category distribution.

## Development/validation qualification manifest

A 12-case mechanically adjudicable manifest is frozen for harness qualification:

- 8 development cases;
- 4 validation cases;
- 5 matched valid/shifted pairs;
- 2 additional training-policy cases.

The matched pairs cover:

- valid Arabidopsis execution versus potato re-selection;
- valid Arabidopsis execution versus missing-species clarification;
- valid potato execution versus unsupported-maize abstention;
- valid potato execution versus Arabidopsis re-selection;
- valid potato execution versus missing-species clarification.

The two unpaired development cases exercise RECOMMEND_TRAINING and missing-training-
data CLARIFY behaviour.

These cases are **not** the final benchmark and must not be presented as evidence of
real-world distribution-shift performance. They qualify the harness, scoring, and
condition plumbing only.

## Prospective claim boundary

### Claim 1 — callability is insufficient

Authorised only if one or more callable/schema-valid baseline conditions execute a
scientifically invalid capability on a gold-labelled invalid case.

If no such failures are observed, the paper may discuss the theoretical distinction
but must not claim that the evaluated baseline empirically demonstrates the failure.

### Claim 2 — explicit applicability grounding helps

A strong improvement claim is authorised only if full PhenoGuard reduces unsafe
execution relative to the Manager + schemas baseline and the generic-Critic baseline
without reducing valid-execution accuracy below both comparison baselines.

If unsafe execution improves but valid execution falls, only a safety/coverage
trade-off claim is authorised.

If unsafe execution does not improve, no reliability-improvement claim is authorised.

### Claim 3 — portability across direct and MCP execution

A deterministic portability claim requires exact semantic decision parity for the
frozen deterministic qualification cases under direct and MCP-backed execution.

For stochastic main runs, paired differences and uncertainty must be reported. No
equivalence claim is authorised without a predeclared equivalence margin.

### Optional Claim 4 — distribution shift changes failure signatures

This claim is authorised only if failure-category distributions differ across
predeclared shift categories on real or independently justified benchmark cases.

Synthetic metadata stress tests may support mechanism analysis but cannot by
themselves establish a real distribution-shift claim.

## Hidden-test discipline

- hidden labels are unavailable to the method;
- final hidden cases are not authored from observed method failures;
- negative results are retained;
- method changes after hidden-label unblinding are prohibited;
- hidden expert adjudication remains outside the qualification manifest.

## What is still not frozen

Phase 7H does not invent:

- a final hidden benchmark;
- domain-expert labels;
- the concrete LLM/provider/model revision;
- a statistical equivalence margin;
- real-domain-shift fixtures that have not yet been sourced.

Those are frozen only when evidence exists and before their corresponding outcomes are
inspected.

## Gate to close Phase 7H

- full Phase 7A-H test suite passes;
- all ten condition IDs are present exactly once;
- C8 structurally requires post-execution validation;
- all authoritative metrics are retained;
- development/validation manifest has unique IDs and no hidden cases;
- five matched pairs satisfy the pair contract;
- all 12 mechanical qualification cases score exactly under the frozen method;
- dependency health is clean;
- bounded secret scan is clean;
- worktree is clean.

After this gate, the method branch is ready for the final Phase 7 freeze package and
then the separate `experiments/ijcai2027` branch.
