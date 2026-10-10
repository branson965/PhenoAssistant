# Phase 7G — Bounded Post-Execution Scientific Validation

**Date:** 2026-10-10  
**Venue:** IJCAI 2027 stretch target  
**Fallback:** ECAI 2027  
**Status:** implementation committed, runtime verification pending

## Why this phase exists

The authoritative IJCAI paper plan defines the strongest method condition as
pre-execution applicability verification plus post-execution scientific validation.

The method therefore cannot be considered frozen while it only decides whether a
tool should run. It must also catch bounded cases in which a technically successful
tool execution produces evidence that should not be reported as scientifically valid.

## v0.1 validator scope

Phase 7G adds three deterministic validators grounded in existing PhenoAssistant
workflows.

### Phenotype invariants

For records containing leaf count and projected leaf area:

- leaf count must exist;
- projected leaf area must exist;
- both must be numeric and finite;
- leaf count must be integer-valued;
- leaf count must be non-negative;
- projected leaf area must be non-negative.

### Statistical-claim grounding

For a reported significance claim:

- tool and reported p-values must be finite and within [0, 1];
- alpha must be finite and strictly within (0, 1);
- reported p-value must match the tool evidence within the declared numeric tolerance;
- reported significance must equal `tool_p_value < alpha`.

### Identifier preservation

For output artifacts that must preserve sample identity:

- expected IDs must be unique;
- observed IDs must be unique;
- observed IDs must match the expected ordered identity sequence.

## Failure policy

Any hard validation issue sets `safe_to_report=false`.

The validator does not silently repair scientific output and does not reinterpret tool
results. It returns structured evidence so a higher-level policy can stop, clarify,
or surface the failure explicitly.

## Scope boundary

These validators do **not** establish scientific truth and do not replace domain
expert adjudication.

They are intentionally bounded to invariants that can be mechanically checked without
an LLM judge. Additional tool-specific validators may be added only when their
scientific semantics and scoring role are predeclared.

## Relationship to the IJCAI experiment

The full-method condition in Phase 8 will combine:

1. Scientific Operating Envelope;
2. pre-execution applicability resolution;
3. controlled clarification/reselection/abstention/training recommendation;
4. deterministic decision traces;
5. bounded post-execution scientific validation.

This closes an implementation gap before the baseline/condition protocol is frozen.
