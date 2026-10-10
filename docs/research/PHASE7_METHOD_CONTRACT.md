# Phase 7A Method Contract — Scientific Operating Envelope v0.1

**Date:** 2026-10-10  
**Branch:** research/phenoguard  
**Status:** implementation committed, empirical claims not yet validated

## Research boundary

The migration/MCP work is infrastructure. The Phase 7 research question is whether a
tool-using scientific agent can distinguish **technical callability** from
**scientific applicability** under distribution shift.

The v0.1 primitive is the **Scientific Operating Envelope**.

## Contract

Each capability declares:

- stable capability identifier;
- scientific task;
- context constraints over species, modality, view, and environment;
- hard versus soft severity for each constraint;
- required request-context fields;
- required metadata keys;
- output semantics;
- assumptions;
- limitations;
- known failure conditions;
- provenance;
- version/checkpoint identity.

Each proposed execution supplies a ScientificRequestContext.

The deterministic checker evaluates the request **before tool execution** and returns
a structured ScientificApplicabilityAssessment.

## Decision semantics

The global method retains five allowed decisions:

- EXECUTE
- RESELECT
- CLARIFY
- ABSTAIN
- RECOMMEND_TRAINING

The v0.1 single-capability deterministic checker intentionally emits only:

- EXECUTE when the scientific task matches, no hard constraint is violated, and
  required context/metadata are present;
- CLARIFY when required context or metadata are missing;
- ABSTAIN when the scientific task mismatches or a hard applicability constraint
  is violated.

RESELECT requires evidence from a multi-capability catalogue.  
RECOMMEND_TRAINING requires an explicit training-readiness policy.

Neither is inferred by the local checker because doing so without those additional
inputs would create unsupported autonomy.

## Hard and soft constraints

A hard mismatch blocks execution.

A soft mismatch is retained as a structured warning but does not independently block
execution in v0.1. This is a deliberately testable design choice, not a scientific
claim. Later pilot evidence may justify changing the policy only **before** the frozen
evaluation protocol.

## Current unit fixture

The initial tests use a synthetic-but-domain-shaped Arabidopsis top-view segmentation
envelope to exercise:

- exact valid execution;
- missing acquisition view;
- side-view hard mismatch;
- field-environment soft mismatch;
- scientific-task mismatch;
- missing required metadata;
- case-insensitive matching with evidence preservation;
- duplicate constraint rejection.

These tests validate contract mechanics only. They do **not** establish that the
chosen constraints are scientifically correct for any production checkpoint. Real
operating envelopes must be sourced from repository/model provenance and reviewed
against domain evidence before benchmark labels are frozen.

## Next method gate

Before Phase 7 can be frozen, the project still needs:

1. provenance-backed envelopes for the selected real scientific capabilities;
2. a catalogue-level resolver that can emit RESELECT;
3. an explicit RECOMMEND_TRAINING policy boundary;
4. deterministic trace schema for pre-execution checks and final decisions;
5. paired valid/invalid benchmark cases with hard-negative controls;
6. expert review of non-mechanical applicability labels;
7. baseline definitions and scoring frozen before hidden evaluation.

No superiority or safety-improvement claim is authorised by this v0.1 implementation.
