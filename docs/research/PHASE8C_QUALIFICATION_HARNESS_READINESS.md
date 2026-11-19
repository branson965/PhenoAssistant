# Phase 8C: First C3/C4/C8 qualification matrix, no scientific runs yet

**Date:** 2026-11-19  
**Venue:** IJCAI 2027 stretch, November 30 internal evidence-based go/no-go  
**Status:** offline planning available; supervisor approval and scientific harness not yet complete

## Achievements and boundaries

- The exact SHA-256 v0.3 runtime candidate was generated on Plato
  (`e3a8826b8942f2b0951775b557ce3530b2a54ed7666e827e3687443974718c12`),
  committed and pushed as `09ebaec`.
- Authenticated Luna MAF single-tool echo passed. This is *infrastructure only*.
- Frozen 22-file Phase 7 v0.2 method aggregate remains
  `25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294`.
- Runtime-v0.3 candidate explicitly says approval not attested and scientific
  execution not permitted. These are live gates, not a paperwork formality.
- No scientific effectiveness results exist.

## Offline qualification planning command

After pulling `experiments/ijcai2027` on Plato:

```bash
cd ~/PhenoAssistant
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_qualification_matrix.py \
  tests/research/test_phase8_runtime_v03.py \
  tests/research/test_phase8_preflight.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/prepare_phase8_qualification_matrix.py
```

Expected results: 12 scenarios, exactly 108 planned trials (3
predeclared conditions x 3 seeds), `PHASE8_QUALIFICATION_PLAN_PASS=true`,
`PHASE8_QUALIFICATION_SCIENTIFIC_EXECUTION_PERMITTED=false`,
`PHASE8_QUALIFICATION_API_KEY_READ=false`,
`PHASE8_QUALIFICATION_OUTCOME_BEARING=false`.

The script is deterministic and refuses to overwrite an existing output.
Preserve its printed SHA-256, commit only the generated matrix file,
and push as a separate Git interaction with its SSH passphrase handled.

The prospective Luna **manager-roundtrip-only** call-cost estimate
is around $0.70 for the 108 planned trials **if** each uses at most
two model rounds with 4,000 input and 2,048 output tokens per round,
at the November 19 catalogue price. This is a preliminary planning
floor, **not a valid all-in budget for C4**: additional generic-Critic
LLM calls, retries, larger prompts, variable reasoning, and scientific
tool/GPU costs are not included. Nothing in the offline plan authorises
model calls or represents measured spending.

## Separation of benchmark metadata from model prompt

The frozen `BenchmarkScenario` structure has fields such as
`category` and `shift_dimension` that can encode the expected
outcome. The original qualification `scenario_id` also sometimes
contains words such as `valid` or `missing`. These must never become
manager-visible prompt context. The planner therefore *only* permits:

- `scientific_request`, containing the actual scientific context;
- `requested_capability_id`;
- `training_readiness`, when relevant.

The trial list contains internal-only scenario IDs, split, seed, trial ID,
and a hash of the shared model-visible case facts. It does **not** contain
the full prompt or gold label. The upcoming live runner must reconstruct
prompts from the allowlisted view and refuse to inject
internal bookkeeping or expert labels.

## Scope and expected scientific paper value

These 12 frozen development/validation cases are only to qualify the
experiment runner, condition isolation, retry/session/cost accounting,
decision logging and deterministic scorer. They must not be described as
the final real-domain-shift benchmark or presented as empirical IJCAI
effectiveness claims.

The outcome-bearing pilot should prioritise `C3_MANAGER_TOOL_SCHEMAS`,
`C4_MANAGER_GENERIC_CRITIC` and `C8_FULL_PHENOGUARD`. The complete
C0-C8 set, expert C9 adjudication, real/provenance-grounded shift cases,
MCP vs direct portability, stronger-model subset and hidden evaluation
remain required for a defensible full submission.

## Before any paid scientific trial

1. Record genuine supervisor/provider/credential/billing and Luna/Sol model approval.
2. Preserve the final approved runtime, with source hashes and the exact
   `OpenRouterCompatTransport` used for every relevant model call.
3. Build isolated runnable **real** C3, C4 and C8 conditions; do not
   substitute a shared identical policy or a rule-based simulation for a
   generic LLM critic.
4. Verify the MCP scientific-tool dispatch is the same implementation in
   comparable conditions; apply pre-execution safety guard and post-execution
   validation only where the frozen condition calls for them.
5. Check that prompts contain no scenario category, shift label, internal
   scenario name or gold target. Preserve the hidden set sealed.
6. Use append-only raw attempts, exact model/provider identity, measured
   token usage, bounded retries, measured dollar cost, and failure records.
7. Pass offline integration tests and a tiny live *non-scientific* runner
   capability test before authorizing the first outcome-bearing task.

Do not increase the paper progress percentage just because the planning
matrix was generated. Scientific evaluation evidence is the critical
outstanding contribution.


## Plato matrix generation passed — 2026-11-19

The researcher pulled commit `b511bea`, executed the three targeted
offline suites, and received **27/27 passed**. The qualification
planner emitted exactly 12 development/validation cases and 108
planned C3/C4/C8 × three-seed trials:

```text
PHASE8_QUALIFICATION_MATRIX=experiments/ijcai2027/runtime/phase8_c3_c4_c8_qualification_matrix_v0.1.json
PHASE8_QUALIFICATION_MATRIX_SHA256=8a9688aa464564bf99121656430ea09fc93bbf2b1d262a73a9b2276944876692
PHASE8_QUALIFICATION_CASE_COUNT=12
PHASE8_QUALIFICATION_TRIAL_COUNT=108
PHASE8_QUALIFICATION_ESTIMATED_USD=0.7036416
PHASE8_QUALIFICATION_SCIENTIFIC_EXECUTION_PERMITTED=false
PHASE8_QUALIFICATION_API_KEY_READ=false
PHASE8_QUALIFICATION_OUTCOME_BEARING=false
PHASE8_QUALIFICATION_PLAN_PASS=true
```

The matrix was still untracked in the user's local worktree when the
output was reported. It must be committed *as is*, without
regeneration, and pushed. This is not evidence of scientific
effectiveness.

The independent verifier is now committed as
`scripts/research/verify_phase8_qualification_matrix.py`,
with `tests/research/test_phase8_qualification_matrix_verify.py`.
It pins the exact reported SHA-256 and re-derives every planned
trial and controlled setting from frozen inputs, rejecting altered
trial status, leaked labels, fake outputs and drifting seeds.

After pulling the updated experiment branch, run the offline
verification before committing the generated matrix:

```bash
cd ~/PhenoAssistant
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_qualification_matrix_verify.py \
  tests/research/test_phase8_qualification_matrix.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/verify_phase8_qualification_matrix.py
sha256sum experiments/ijcai2027/runtime/phase8_c3_c4_c8_qualification_matrix_v0.1.json
git status --short
```

Only if the verifier prints `PHASE8_QUALIFICATION_VERIFY_PASS=true`,
commit and push that **single** generated JSON file. No other
experiment outcome or method file is to be added to that commit.

### Scientific-runner implementation gap

The current `phenoassistant_mcp/maf_bridge_v2.py` proves parity for
calculator, ANOVA and Tukey tools; it is not itself the complete
capability-selection / scientific-vision-model MCP dispatcher tested
by this paper. The full C3 schemas, C4 genuine generic LLM critic,
and C8 SOE pre/post execution policies need their own isolated,
matched pilot implementations. Until that is true, running paid
messages and calling them the C3/C4/C8 paper comparison would be
scientifically misleading.

A successful planning verifier is **not** approval to spend credits.
Provider/model approval and final runtime freeze remain separate.


## Immutable matrix pushed and science-run ledger gate staged — 2026-11-19

The researcher pulled the independent matrix verifier and ran **18/18
passing tests**. The verifier re-derived all 108 trial records,
reported no gold-label reads or provider calls, and reproduced SHA-256
`8a9688aa464564bf99121656430ea09fc93bbf2b1d262a73a9b2276944876692`.
They then committed only the matrix as `97c8db2` and pushed
`experiments/ijcai2027`. The remote branch and matrix were checked
independently after the push; `git status --short` showed no output.

The next implementation step is not another planning matrix, but
controlled run-record integrity. Committed:
- `scripts/research/phase8_attempt_ledger.py`
- `tests/research/test_phase8_attempt_ledger.py`

The standard-library ledger provides:
- exact pinned v0.3 candidate and 108-trial matrix checks;
- a fail-closed scientific-run approval gate, currently **blocked**;
- append-only JSONL STARTED/terminal records with POSIX locking/fsync;
- no duplicate trial starts or overlapping trial runs;
- explicit input/output token counts and provider-reported billable cost;
- missing metering marked as a terminal error which blocks future calls;
- conservative next-call software budget reserve checks;
- no prompts, hidden labels, credential values, tool outputs or raw
  response content in its narrow accounting events.

These are necessary logging/budget primitives, **not the complete
scientific execution harness**. The module does not call the model,
does not dispatch MCP tools, and cannot substantiate scientific
superiority. Its budget gate can stop a *subsequent* call, but alone
cannot cap a single in-flight call; an upstream key hard cap and
per-call worst-case controls remain necessary.

Plato next no-charge validation:

```bash
cd ~/PhenoAssistant
git pull --ff-only origin experiments/ijcai2027
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_attempt_ledger.py \
  tests/research/test_phase8_qualification_matrix_verify.py \
  tests/research/test_phase8_preflight.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/phase8_attempt_ledger.py --budget-usd 8
```

Required: tests pass; 108 registered trials; $8 planning
software ceiling; `PHASE8_LEDGER_APPROVED_TO_RUN=false`;
`PHASE8_LEDGER_NO_PROVIDER_CALLS=true`;
`PHASE8_LEDGER_GOLD_LABELS_READ=false`;
`PHASE8_LEDGER_PREFLIGHT_PASS=true`.

**Before outcome-bearing trials:** obtain genuine supervisor
provider/billing/model approval; preserve a newly approved final
runtime that includes the ledger/actual runner source hashes; implement
the distinct C3, C4, C8 conditions and actual scientific-model MCP
tool boundary; test and record measured-provider-cost accounting.
Do not claim the completed planning matrix or ledger tests as
scientific effectiveness results.


## Plato ledger gate passed; isolated condition rehearsal staged — 2026-11-19

The researcher pulled branch `d6d0c82`, ran the targeted
ledger / matrix / MAF preflight test suites, and observed **33/33 passed**.
The offline CLI reported:

```text
PHASE8_LEDGER_REGISTERED_TRIALS=108
PHASE8_LEDGER_BUDGET_CEILING_USD=8
PHASE8_LEDGER_APPROVED_TO_RUN=false
PHASE8_LEDGER_RUN_GATE_REASON=scientific execution prohibited by preserved runtime candidate
PHASE8_LEDGER_NO_PROVIDER_CALLS=true
PHASE8_LEDGER_GOLD_LABELS_READ=false
PHASE8_LEDGER_OUTCOME_BEARING=false
PHASE8_LEDGER_PREFLIGHT_PASS=true
```

These are correct successful *accounting and authorization* results.
The false execution approval is required until actual supervisor approval,
final runtime seal, verified MCP scientific dispatch and real C4 Critic
and C8 pre/post validation are in place. No paid scientific result exists.

A new executable **offline-only, injected-mock** condition isolation
rehearsal has been committed in
`scripts/research/phase8_condition_rehearsal.py` with negative-path
tests in `tests/research/test_phase8_condition_rehearsal.py`.

It explicitly exercises:
- C3: Manager proposal goes to a simulated executor with no SOE
  verifier or post-validation;
- C4: the same base request goes through an independent generic-Critic
  callback, with no SOE exposure;
- C8: the real frozen catalogue applicability resolver governs
  pre-execution selection, and a post-validator gates mock output
  reporting;
- identical allowlisted scenario-derived request facts in each condition;
- rejection of category, shift, gold, split and scenario-ID fields at
  the model-visible boundary.

**Scientific boundary:** these are *scripted unit fixtures*. The Critic
callback is a fake, not an LLM. The executor is a fake, not an MCP
scientific vision-model invocation. They do not estimate unsafe
execution rates, model accuracy or PhenoGuard efficacy and must never
be pooled with paid scientific traces.

Next Plato no-charge gate:

```bash
cd ~/PhenoAssistant
git pull --ff-only origin experiments/ijcai2027
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_condition_rehearsal.py \
  tests/research/test_phase8_attempt_ledger.py \
  tests/research/test_phase8_qualification_matrix_verify.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/phase8_condition_rehearsal.py
```

Expected: all tests pass,
`PHASE8_CONDITION_REHEARSAL_PASS=true`,
`PHASE8_CONDITION_REHEARSAL_PROVIDER_CALLS=0`,
`PHASE8_CONDITION_REHEARSAL_REAL_GENERIC_LLM_CRITIC=false`,
`PHASE8_CONDITION_REHEARSAL_REAL_SCIENTIFIC_DISPATCH=false`,
`PHASE8_CONDITION_REHEARSAL_EXECUTION_APPROVED=false`.

Next real engineering objective: integrate the real MAF/OpenRouter
Manager and second LLM Critic with the same proven compatibility
adapter, and an MCP-backed scientific capability/vision model
dispatcher which distinguishes proposal from safe execution.
The current Phase 6 MCP v2 calculator/ANOVA/Tukey bridge cannot
substitute for that scientific-model capability. A final approved
runtime hash and upstream spend cap are needed before outcome-bearing
trials.


### Condition-exposure refinement

The isolated C8 rehearsal now passes the real provenance-backed
Scientific Operating Envelopes to its mocked Manager, while C3 and
C4 receive the identical base scenario facts **without** SOEs. C4's
separate mocked Critic also sees no SOE. This matches the frozen
condition-information ordering, but does **not** establish that
the actual live C3/C4 MCP schema advertisement is wired, nor that
the C4 Critic is a real LLM. Those remain implementation gates.
Only the prescribed base request is hashed for paired equality;
condition-specific SOE exposure is expected and must be logged.

Additional offline tests reject gold/shift/category/ID exposure,
confirm that the user-visible base input cannot be mutated by
mock components, and exercise the pre/post verification boundaries.
No measured safety/accuracy results can be derived from these tests.
