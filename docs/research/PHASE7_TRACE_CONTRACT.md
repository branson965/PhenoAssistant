# Phase 7E — Deterministic Decision Trace Contract

**Date:** 2026-10-10  
**Branch:** research/phenoguard  
**Status:** implementation committed, runtime verification pending

## Purpose

PhenoGuard must produce machine-readable evidence that can later support the frozen
AAMAS benchmark, failure analysis, and reproducible scoring. A final decision label
alone is insufficient: the experiment must retain the scientific request, catalogue
state, per-capability assessments, training-readiness evidence when relevant, selected
capability, and a stable reason for the final action.

Phase 7E therefore freezes a deterministic **pre-execution decision trace**.

## Trace contents

Each trace contains:

- schema version;
- method version;
- scenario identifier supplied by the benchmark;
- full structured scientific request context;
- explicitly requested capability, if any;
- ordered capability catalogue identifiers;
- complete catalogue resolution, including all per-capability applicability
  assessments and optional training-readiness evidence;
- final selected capability, when one exists;
- final PhenoGuard decision;
- one deterministic reason code.

## Stable reason codes

The v0.1 trace contract supports:

- requested capability executable;
- unique capability executable;
- unique alternative executable;
- multiple capabilities executable;
- missing applicability context;
- training ready;
- training requirements missing;
- no applicable capability.

These codes are intended for later failure stratification and confusion analysis. They
are not free-form LLM explanations.

## Reproducibility

Trace serialisation uses canonical JSON with sorted keys and compact separators.
A SHA-256 digest can therefore be computed reproducibly from the semantic trace.

The trace intentionally contains no wall-clock timestamp, duration, token count, or
cost field. Runtime measurements are condition/run metadata and can vary while the
same scientific decision remains semantically identical. Those systems metrics belong
in the experiment-run envelope, not the deterministic decision record.

## Separation from hidden labels

The trace contains the system's inputs and decision evidence only. It does not contain
expert gold labels, hidden-test adjudication, or outcome-derived corrections.

This separation is required so hidden labels can remain inaccessible to the method
during execution and so raw traces can later be scored independently.

## Phase boundary

Passing Phase 7E establishes a reproducible evidence object for all five decision
actions:

- EXECUTE;
- RESELECT;
- CLARIFY;
- ABSTAIN;
- RECOMMEND_TRAINING.

It does not freeze the benchmark itself. The next gate is the benchmark/gold-label
contract: scenario schema, matched valid/invalid pairs, hard negatives, split policy,
expert annotation fields, scoring rules, and the predeclared experimental conditions.
