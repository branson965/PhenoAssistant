# Phase 7F — IJCAI 2027 Benchmark Contract Freeze

**Date:** 2026-10-10  
**Venue:** IJCAI 2027 stretch target  
**Fallback:** ECAI 2027  
**Status:** schema and scoring contract committed, runtime verification pending

## Authoritative paper direction

Working title:

**Beyond Callability: Scientific Applicability Verification for Tool-Using Agents Under Distribution Shift**

The benchmark tests whether technically callable scientific capabilities are also
scientifically appropriate under distribution shift.

MAF and MCP remain infrastructure and controlled portability variables. They are not
the central novelty claim.

## Scenario/gold separation

Benchmark inputs and gold labels are separate objects.

A benchmark scenario may contain:

- scenario identity;
- split;
- matched-pair identity;
- scientific request context;
- requested capability;
- training-readiness input when relevant;
- shift dimension;
- evidence source;
- fixture references.

It never contains the expected decision.

Gold labels are stored separately and may contain:

- expected PhenoGuard action;
- expected selected capability or acceptable capability set;
- whether expert adjudication is required;
- compact rationale code.

This separation is mandatory for hidden evaluation.

## Paired-case principle

The benchmark must contain minimally different valid/invalid pairs.

A matched pair must:

- share the same pair ID;
- share the same split;
- preserve the same scientific task;
- contain exactly one valid-execution case;
- contain one perturbed case with an explicit shift dimension.

This prevents a trivial always-abstain strategy from appearing successful.

## Shift dimensions

The v0.1 schema supports:

- species;
- modality;
- view;
- environment;
- sensor;
- image quality;
- missing metadata;
- conflicting metadata;
- checkpoint provenance;
- output semantics.

A valid-execution member uses `shift_dimension=none`.

## Evidence hierarchy

Scenarios explicitly distinguish:

1. `real_domain_shift`;
2. `provenance_backed_metadata`;
3. `synthetic_metadata_stress`.

Real-domain-shift scenarios require fixture references. Synthetic metadata
perturbations remain secondary stress tests and must not substitute for real shifts.

## Deterministic core scoring

The first scoring layer records:

- decision correctness;
- selected-capability correctness;
- exact correctness;
- unsafe execution;
- unnecessary abstention.

This layer is deliberately deterministic.

Higher-level IJCAI metrics such as coverage, risk-coverage, clarification/reselection
accuracy, repeated-run reliability, final-answer grounding, latency/cost, calibration,
and failure distributions will aggregate run records in Phase 8.

## Hidden-test discipline

The final hidden benchmark is **not** created or exposed in this commit.

The contract merely permits `split=hidden` while ensuring the system-visible scenario
contains no expected decision or gold label. Expert-authored/adjudicated hidden cases
must be generated and sealed only after method freeze.

## Baseline freeze to carry into Phase 8

The authoritative paper plan requires, at minimum:

1. model without tools;
2. Manager + tool names;
3. Manager + tool descriptions;
4. Manager + tool schemas / MCP metadata;
5. Manager + generic Critic;
6. deterministic structural/schema validation;
7. Scientific Operating Envelope only;
8. envelope + verifier;
9. full verify/reselect/clarify/abstain/post-validation method;
10. expert oracle.

These conditions must use controlled model, prompt, task data, retries, iteration
limits, and scoring where directly comparable.

## Gate to close Phase 7F

Before advancing:

- benchmark schema tests pass;
- matched-pair semantics pass;
- hidden scenario objects remain label-free;
- deterministic scoring tests pass;
- dependency health is clean;
- repository secret scan is clean;
- repository worktree is clean.

The next gate after this is the development/validation benchmark manifest and frozen
baseline-condition specification, still without exposing final hidden labels.
