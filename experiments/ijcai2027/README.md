# IJCAI 2027 Experiments

This branch begins from the runtime-verified Phase 7 closure.

## Frozen scientific method

Do not modify the 22 files listed in:

`docs/research/IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST.json`

The frozen method aggregate is:

`337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f`

Any required scientific-method change after outcome inspection must reopen Phase 7,
version the freeze manifest, rerun the complete research suite, and preserve every
pre-change result.

## Phase 8A objective

Before any outcome-bearing pilot:

1. verify the Phase 7 freeze;
2. pin provider, model ID, model revision, temperature, output-token limit, retry
   policy, iteration limit, session-reset policy, package lock, and hardware class;
3. hash the prompt bundle, tool catalogue inputs, and qualification task manifest;
4. write the runtime-control candidate without calling an LLM or executing a
   scientific benchmark;
5. review the candidate and only then mark the runtime controls frozen.

The preparation script is:

`scripts/research/prepare_ijcai_runtime_controls.py`

It intentionally fails if required runtime identity is missing. It never reads or
prints API keys.

## Experiment order

- qualify the harness on development/validation contract cases;
- run the predeclared pilot on development/validation only;
- freeze any non-scientific harness fixes and scoring analysis;
- only then prepare expert hidden evaluation;
- retain every run, including failures and negative results.

The primary venue is IJCAI 2027 with the 2026-11-30 internal go/no-go.
