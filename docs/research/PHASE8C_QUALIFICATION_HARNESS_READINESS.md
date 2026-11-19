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
