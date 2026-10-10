# Phase 7I — Final IJCAI 2027 Method Freeze Package

**Date:** 2026-10-10  
**Venue:** IJCAI 2027 stretch target  
**Fallback:** ECAI 2027  
**Status:** freeze package committed, runtime verification pending

## Purpose

Phase 7I converts the accumulated scientific-applicability method into an immutable
pre-outcome research snapshot before Phase 8 begins.

The freeze is content-addressed. Scientific-method source files, core research
contracts, benchmark/protocol documents, and the registered model catalogue are
listed in:

`docs/research/IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST.json`

Each file is pinned by SHA-256 and the sorted path/hash list has its own aggregate
SHA-256 digest.

## Frozen snapshot

The manifest pins 22 files, including:

- the authoritative scientific-applicability paper plan;
- Scientific Operating Envelope and request/decision contracts;
- single-capability checking;
- provenance-backed capability envelopes;
- catalogue resolution;
- training-readiness policy;
- deterministic trace contract;
- benchmark scenario/gold/scoring contracts;
- post-execution scientific validation;
- frozen C0-C9 condition protocol;
- development/validation qualification manifest;
- machine-readable IJCAI protocol freeze;
- `model_zoo.json`.

The content snapshot is taken from commit:

`c58741bb9b0bcc8ebef68755e3d8528de9533312`

Aggregate frozen-content digest:

`337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f`

## Freeze policy

Phase 8 may import and execute this method but must not silently alter the frozen
scientific-method files.

If a scientific-method change is genuinely required after Phase 8 outcome inspection,
the project must:

1. explicitly reopen Phase 7;
2. document why the frozen method was inadequate;
3. increment the freeze-manifest version;
4. recompute every affected hash;
5. rerun the complete research regression suite;
6. distinguish all pre-change and post-change outcomes;
7. never overwrite or discard an unfavourable pre-change result.

Hidden labels remain unavailable to the method, negative results are retained, and
post-unblinding method changes are not authorised under the frozen protocol.

## Runtime verification

`scripts/research/verify_phenoguard_method_freeze.py` independently hashes the local
worktree and verifies:

- every frozen path exists;
- each SHA-256 matches exactly;
- the file count is 22;
- the aggregate digest matches.

The final Phase 7I test module additionally locks the venue identity, source commit,
required frozen components, blinding rules, and explicit reopen policy.

## Phase transition

After the Phase 7I runtime gate passes on Plato:

- create preservation ref
  `baseline/phenoguard-method-freeze-20261010` at the verified Phase 7 closure
  commit;
- mark Phase 7 complete;
- create `experiments/ijcai2027` from that preservation point;
- populate concrete provider/model/runtime controls before the first outcome-bearing
  pilot;
- run only development/validation pilot cases until the harness and scoring analysis
  are frozen;
- keep the final expert hidden benchmark sealed from method tuning.

The first outcome-bearing Phase 8 run must therefore be traceable to an immutable
Phase 7 method snapshot.
