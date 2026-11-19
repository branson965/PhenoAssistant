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


## Plato condition-isolation rehearsal passed; real scientific MCP boundary staged (2026-11-19)

The researcher pulled `ad694f1` and passed **34/34** offline
regression tests in 0.31s. The isolated C3/C4/C8 mock exercise
reported the same scenario-derived request SHA-256
`da9f9cf2696e23f6249e417779792d5dfe9dbe75fe9ddf69cac735df311473c0`,
three *mock* executions, no actual scientific dispatch, no generic
LLM Critic, no provider calls, no gold reads, and
`PHASE8_CONDITION_REHEARSAL_PASS=true`.
This qualifies branch isolation, **not the paper's empirical claim**.

The next stage now implements the first bounded actual MCP
**scientific-vision-tool endpoint**, separate from Phase 6's
calculator/ANOVA/Tukey surface:

- `phenoassistant_mcp/scientific_inference_v1.py` exposes
  `run_scientific_model(capability_id,image_asset_id)` through
  `mcp.server.MCPServer`;
- a per-trial server instance requires a SHA-256-verified, **final**
  `PRE_OUTCOME_RUNTIME_APPROVED_FROZEN` record that explicitly
  permits scientific execution and attests supervisor-approved
  credential/billing/provider/model settings;
- only three provenance-backed Case 1/2/3 capability IDs are
  accepted; arbitrary model IDs are rejected;
- the model cannot supply a filesystem path, checkpoint URI,
  device, batch size or output directory. Opaque image IDs resolve
  to human-reviewed, hash-pinned image assets;
- the production delegate invokes the repository's existing
  `infer_instance_segmentation` or `infer_image_classification`
  with fixed batch_size=1, device=cuda, and an isolated
  never-overwrite per-trial output path;
- success requires a real COCO or classification-CSV artifact and
  returns its artifact SHA-256. No scientific fitness policy is
  enforced in this common MCP executor itself; baseline and
  PhenoGuard differences must occur in their explicit, audited
  per-condition orchestration stages;
- `tests/research/test_phase8_scientific_mcp.py` uses **actual
  MCP client/server protocol** with a synthetic local approval and
  a FAKE vision-inference delegate. It tests trusted image hashes,
  approval gating, duplicate rejection, model allowlist, structured
  outputs, and the exact two-argument MCP JSON schema.

**Strict interpretation:** the production canonical delegate is
implemented, but has not yet been run under real scientific GPU
conditions. The test's synthetic approval is not actual
supervisor approval and cannot authorise any production call.
The 12 pilot cases are presently metadata-oriented; they do not
yet contain a reviewed actual image-asset binding for all trials.
Those fixtures are a substantive outstanding requirement.

### Plato no-charge MCP integration verification

Pull the experiment branch and complete the SSH passphrase prompt
before the rest of the commands:

```bash
cd ~/PhenoAssistant
git pull --ff-only origin experiments/ijcai2027
```

Then:

```bash
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_scientific_mcp.py \
  tests/research/test_phase8_condition_rehearsal.py \
  tests/research/test_phase8_attempt_ledger.py

git status --short
```

All calls remain within pytest's temporary directories and injected
fake vision execution. This command does not require an OpenRouter
key, model invocation, GPU, or access to hidden gold labels.

No outcome-bearing scientific trial is authorized until a
complete real scientific runner connects:
- a live, compatible Luna MAF Manager;
- a genuinely independent Luna generic-Critic LLM for C4;
- the identical trusted real MCP scientific tool for all conditions;
- C8's pre/post verifier with real output-type-specific validators;
- sealed data/fixture binding and hidden-label separation;
- token usage and **provider-billed** cost accounting and a
  real upstream key spending limit;
- an approved hash-pinned final runtime with all source identities.

No progress percentage should increase merely from the staged
offline MCP adapter or its synthetic tests.


## Plato scientific MCP protocol passed; real MAF Manager/Critic transport staged (2026-11-19)

The researcher pulled branch `63360dc` and executed the exact
`tests/research/test_phase8_scientific_mcp.py`,
`tests/research/test_phase8_condition_rehearsal.py`, and
`tests/research/test_phase8_attempt_ledger.py` suites on Plato.
**36/36 passed** in 5.98 seconds; `git status --short` was empty.

This establishes that the real MCP protocol can advertise the
bounded scientific-model schema, validate approved image identifiers
and hashes, reject unapproved checkpoint/path/device inputs,
translate structured tool replies, block duplicate execution, and
retain C3/C4/C8 condition isolation **with fake vision inference**.
No real GPU inference, provider-paid calls or scientific outcomes
were produced.

The next component is now committed as
`scripts/research/phase8_maf_decision_v1.py`, with corresponding
`tests/research/test_phase8_maf_decision_v1.py`.

It wires an actual `agent-framework-openai==1.11.0`
`OpenAIChatCompletionClient` to OpenRouter's exact Luna model via
the already qualified `OpenRouterCompatTransport`, for a separate
Manager proposal and genuine *independent* generic-Critic LLM
roundtrip. The tests use `httpx.MockTransport` with a synthetic API
key and isolated test-only approval record. No request leaves the
Plato process when these tests run.

### Information and control boundary

- C3 and C4 Managers receive the **identical** base scientific
  request, plus the **actual MCP-discovered** tool schema and
  description. C8 sees the same facts and provenance-backed SOEs.
- C4 Critic receives the proposal, same request and MCP schema,
  but never SOEs, case category/shift fields, labels or gold.
- All responses are parsed as narrow
  `{decision,capability_id}` JSON proposals, with registered
  capability checks and model-identity verification.
- Per model call: pinned Luna model, OpenAI-only provider route,
  no fallback, medium reasoning, scheduled seed, no temperature,
  SDK retries disabled, 2048 maximum output tokens, and only
  adapter-translated `max_tokens` on the final wire.
- **This is a proposal-only intermediate layer.** It does NOT
  claim to implement native model tool-call selection, actual
  scientific tool invocation, C8 post-validation, raw per-call
  provider-billed cost metering, or a complete experimental runner.
- The CLI checks the permanently unapproved historical v0.3
  candidate and makes **zero** model calls. Its offline checks
  do not set supervisor approval or unblock scientific execution.

### Plato tests for the staged MAF wiring

After a standalone `git pull --ff-only origin experiments/ijcai2027`
and completed Git SSH passphrase:

```bash
cd ~/PhenoAssistant
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_maf_decision_v1.py \
  tests/research/test_phase8_scientific_mcp.py \
  tests/research/test_phase8_condition_rehearsal.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/phase8_maf_decision_v1.py
git status --short
```

Expected: all tests pass; zero real outbound requests,
`PHASE8_MAF_DECISION_OFFLINE_PREFLIGHT_PASS=true`,
`PHASE8_MAF_DECISION_APPROVED_TO_RUN=false`,
`PHASE8_MAF_DECISION_REAL_CRITIC_CALLS=0`,
`PHASE8_MAF_DECISION_SCIENTIFIC_TOOL_CALLS=0`.
The real SDK calls in tests terminate at a fake HTTP transport.

After this, priority remains the full *scientific* bridge:
native model tool-call proposal with delayed execution,
per-condition C4/C8 mediation over the same MCP schema, vetted
real image-fixture bindings, actual C8 post-validation against
image-appropriate outputs, append-only measured usage/charge evidence,
approved provider/model route, upstream spend cap and new source-hashed
final runtime freeze. Do not claim results from simulated tests.


## 2026-11-19 Plato MAF SDK test failure and exact two-point repair

The researcher pulled `ed6ada2` and ran the targeted MAF/MCP/condition
offline suites. **48 tests passed, 1 failed**. The failing test was
`test_real_maf_manager_critic_wire_roundtrips_are_mock_only`.
The actual MAF SDK request reached the existing compatibility transport,
but that transport rejected `tool_choice` missing/None with
`OpenRouterCompatibilityError: unexpected tool-choice policy`.
This is a **tool-free proposal request**, whereas the original successful
live echo preflight had a real advertised tool and explicit
`tool_choice=required`. The exception occurred before the fake HTTP
provider and was wrapped as an SDK `APIConnectionError` and MAF
`ChatClientException`. There was **no paid request**.

A second, independent defect was exposed by running the file directly:
`ModuleNotFoundError: No module named 'phenoassistant_mcp'`.
The repository-local MCP import occurred before the script added the
project root to `sys.path`.

Both are corrected without changing the frozen Phase 7 method:
- `scripts/research/openrouter_compat.py` allows an omitted
  `tool_choice` only for a request with no advertised tools,
  and removes an explicit null choice only in that same case.
  A tool-enabled request **still requires** one of
  `required/auto/none`. A no-tool request must not request native
  tool calling. The earlier OpenAI provider, model, seed, reasoning,
  temperature and token checks remain unchanged.
- `scripts/research/phase8_maf_decision_v1.py` now inserts
  the repository root before importing `phenoassistant_mcp`.
- `tests/research/test_phase8_openrouter_compat.py` now covers
  no-tool omission, explicit empty tools, null normalization,
  tool-enabled invalid/missing tool_choice rejection and no-tool
  attempts to enable tool calling.
- `tests/research/test_phase8_maf_decision_v1.py` now invokes
  the real script in a subprocess without an API key to catch
  direct-path import regressions.

These corrections are **staged**, not yet verified on Plato. The
historic v0.3 runtime candidate remains unchanged and still prohibits
scientific calls. The final approved source-hashed runtime must
include the updated adapter once full harness qualification is done.

### Plato rerun (offline, no key)

```bash
cd ~/PhenoAssistant
git pull --ff-only origin experiments/ijcai2027
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_maf_decision_v1.py \
  tests/research/test_phase8_openrouter_compat.py \
  tests/research/test_phase8_scientific_mcp.py \
  tests/research/test_phase8_condition_rehearsal.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/phase8_maf_decision_v1.py
git status --short
```

Do not set `OPENROUTER_API_KEY`. The fixture uses a fake key,
`httpx.MockTransport`, and synthetic approval isolated to
`pytest` temporary storage. The standalone CLI invokes no
model or MCP scientific tool. The expected success marker is
`PHASE8_MAF_DECISION_OFFLINE_PREFLIGHT_PASS=true`; preserve
the exact test count as observed rather than predicting it.


## Plato MAF/compatibility repair passed: mediated MAF-to-MCP bridge staged (2026-11-19)

The researcher pulled `277c320` on Plato and ran the comprehensive
MAF SDK, compatibility, scientific MCP, and condition-isolation suites.
**77/77 passed in 3.72 seconds**, with
`PHASE8_MAF_DECISION_OFFLINE_PREFLIGHT_PASS=true`,
`PHASE8_MAF_DECISION_ACTUAL_REQUESTS=0`,
`PHASE8_MAF_DECISION_REAL_CRITIC_CALLS=0`,
`PHASE8_MAF_DECISION_SCIENTIFIC_TOOL_CALLS=0`,
`PHASE8_MAF_DECISION_APPROVED_TO_RUN=false`, and a clean worktree.

This closes the prior tool-free MAF routing and direct-script import
regressions. It is **not** a scientific run.

A new integrated, offline-testable bridge is staged:
- `scripts/research/phase8_proposal_mcp_bridge_v1.py`
- `tests/research/test_phase8_proposal_mcp_bridge_v1.py`

For a separately approved and hash-pinned final runtime, the bridge
discovers the actual MCP tool schema, requests a typed Manager
proposal from the MAF decision client, invokes an independent generic
Critic **only for C4**, applies the frozen SOE catalogue resolver
**only for C8**, and conditionally calls **the same** bounded MCP
`run_scientific_model` implementation with the application's
trusted image-asset binding. Only C8 may receive an output-specific
post-validator.

Tests exercise this path using actual MAF/OpenAI SDK request
translation to `httpx.MockTransport` plus a real MCP client/server
protocol connected to **fake** scientific-inference delegates.
Synthetic approvals are created inside test temporary directories,
not stored in the experiment branch. The CLI is explicitly offline
and refuses to treat the historic v0.3 candidate as approved.

This is **not** native model tool calling: it is an intermediary
JSON proposal followed by deterministic, mediated MCP dispatch.
It must not be presented as the final tool-calling protocol or
the basis for experimental effectiveness results without a
prospective protocol-equivalence review. The 108 scientific trials
remain unexecuted, and the real output-specific C8 validator is
still unimplemented.

### Baseline fairness fix

C3/C4 have **no C8-specific post-validator**, so their outputs
receive `safe_to_report=null` (not assessed) in the integration
record. A null value is not a failed scientific validity check.
For C8, `safe_to_report` is the actual typed post-validator result
where one is available. An independent scorer must evaluate
baseline safety from the same expert/gold reference, not from
whether PhenoGuard's privileged validator was present.
This prevents artificial C8 gains through a baseline
coverage/refusal scoring artefact.

### Next Plato gate: offline integration of actual SDK to MCP boundary

Run the commands separately to handle Git SSH authentication:

```bash
cd ~/PhenoAssistant
git pull --ff-only origin experiments/ijcai2027
```

```bash
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_proposal_mcp_bridge_v1.py \
  tests/research/test_phase8_maf_decision_v1.py \
  tests/research/test_phase8_scientific_mcp.py \
  tests/research/test_phase8_condition_rehearsal.py \
  tests/research/test_phase8_openrouter_compat.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/phase8_proposal_mcp_bridge_v1.py
git status --short
```

Do not supply `OPENROUTER_API_KEY`. Tests use only temporary synthetic
approvals and fake inference; the test harness must not send paid calls.
Required: all tests pass and
`PHASE8_BRIDGE_OFFLINE_PREFLIGHT_PASS=true`,
`PHASE8_BRIDGE_PROVIDER_CALLS=0`,
`PHASE8_BRIDGE_SCIENTIFIC_DISPATCH=0`,
`PHASE8_BRIDGE_NATIVE_TOOL_CALLING=false`,
`PHASE8_BRIDGE_EXECUTION_APPROVED=false`.

**Critical open work, not to be hidden behind integration test passes:**
(1) native tool-proposal capture versus text-JSON proposals,
(2) final independently trustworthy supervisor/credential/billing
attestation, not merely a caller-supplied JSON SHA,
(3) actual verified per-case image assets and GPU inference,
(4) independently audited scientific output-specific C8 validators,
(5) append-only raw attempts and exact per-call provider billing
metering plus upstream hard cap, and
(6) source-hashed final runtime approval before any outcome trial.
