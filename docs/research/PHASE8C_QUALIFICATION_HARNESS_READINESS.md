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


## Plato 87/87 end-to-end offline gate passed; canonical artifact audit (2026-11-19)

The researcher pulled `726cefe` and passed **87/87** targeted
mock-HTTP MAF-to-real-MCP protocol and regression tests in 4.97 seconds.
The standalone bridge reported 108 registered trials and
`PHASE8_BRIDGE_OFFLINE_PREFLIGHT_PASS=true` with
`PHASE8_BRIDGE_NATIVE_TOOL_CALLING=false`,
`PHASE8_BRIDGE_PROVIDER_CALLS=0`,
`PHASE8_BRIDGE_SCIENTIFIC_DISPATCH=0`,
`PHASE8_BRIDGE_OUTCOME_BEARING=false`, and
`PHASE8_BRIDGE_EXECUTION_APPROVED=false`.
The working tree remained clean. All synthetic executions were within
tests; no scientific inference or paid provider calls were performed.

### Audit of actual repository inference source revealed two corrections

The existing MCP scientific dispatcher assumed that all segmentation
models emit `ins_seg_results.json`. Inspection of the canonical
`functions/leaf_only_sam.py::infer_leaf_only_sam` established that
the *potato* Leaf-only SAM model instead writes
`leaf_only_sam_results.json`. In
`phenoassistant_mcp/scientific_inference_v1.py`, the artifact
filename is now selected by exact scientific capability, while Case 1
Arabidopsis Mask2Former still expects `ins_seg_results.json`.

The previous output directory was keyed by both trial ID and
capability/asset selection. That permitted two different model choices
to each receive a distinct output folder in the same trial. The MCP
server now atomically claims the **trial directory** on the first
invocation, forbidding a second tool call even if the model or image
ID changes. Separate tests exercise the duplicate-with-different-model
case and pin the actual potato naming convention from source.

### True output-format-specific C8 post-execution invariants

New `scripts/research/phase8_scientific_artifact_validator.py`
reads and checks the actual scientific artifacts that the
canonical functions produce:

- For C1/C2 segmentation COCO JSON: exact trusted input-image path,
  one image with positive pixel dimensions, valid category/annotation
  image references, unique annotation IDs, non-negative individual
  mask area within image bounds, finite confidence within [0,1],
  and COCO-RLE declared size consistent with image dimensions. A
  zero-prediction image is allowed. The predicted leaf count and
  summed mask area are derived from annotations and checked using
  frozen `research/phenoguard/post_validation.py` phenotype
  invariants, without changing Phase 7 source.
- For C3 winter-wheat classification CSV: one bound input image,
  required output columns, an integer class ID within the declared
  seven-class scope, a nonblank label, and finite confidence in
  [0,1]. The class label-to-ID mapping is not yet independently
  pinned and is **not fabricated** here.
- For both: matching MCP result identity and expected capability,
  SHA-256 equality between returned result and actual artifact,
  confined output-root layout, no symlinks, and a conservative
  file-size bound. A mismatch produces a typed hard validation result.

The actual output-bound callback is available through
`make_c8_artifact_validator` and the mediated bridge's
`bridge_one_with_real_artifact_check`, which deliberately
runs C8-only post-validation and leaves C3/C4 baseline outputs
`safe_to_report=null` (not assessed, rather than unsafe).

These tests use **synthetic artifact files** and actual MCP protocol
with fake vision inference. They do not establish model accuracy,
mask geometric correctness beyond declared invariants, confidence
calibration, a full scientific benchmark, or an approved runtime.

### Next Plato offline verification (not yet executed)

```bash
cd ~/PhenoAssistant
git pull --ff-only origin experiments/ijcai2027
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_scientific_artifact_validator.py \
  tests/research/test_phase8_proposal_mcp_bridge_v1.py \
  tests/research/test_phase8_scientific_mcp.py \
  tests/research/test_phase8_maf_decision_v1.py \
  tests/research/test_phase8_openrouter_compat.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/phase8_proposal_mcp_bridge_v1.py
git status --short
```

No API key is needed. The only intended outputs are passing offline
tests and the bridge's fail-closed `EXECUTION_APPROVED=false`
status. The new integration and validator code must be included in a
new approved final-runtime source hash **after** scientific harness,
credential/provider/model and cost controls are genuinely verified.

**Current paper-validity gaps:** native tool-call proposal capture
(the bridge still uses text-JSON proposals), unalterable trusted
supervisor approval, approved real image fixtures for the 12
qualification scenarios, checkpoint/weight integrity for all three
models, GPU fidelity, measured provider charges and hard budget cap,
raw append-only scientific execution traces, independent scoring,
and real domain-shift benchmark. No result claim is permitted yet.


## 2026-11-19 Plato: 105/105 output-validation tests passed; independent approval gate corrected

The researcher pulled `e0319ff`, ran the scientific-artifact,
MAF-to-MCP bridge, scientific MCP, MAF decision and transport tests,
and obtained **105/105 passed in 5.22 seconds**. The direct bridge
reported `PHASE8_BRIDGE_OFFLINE_PREFLIGHT_PASS=true`,
`PHASE8_BRIDGE_REGISTERED_TRIALS=108`,
`PHASE8_BRIDGE_NATIVE_TOOL_CALLING=false`,
`PHASE8_BRIDGE_PROVIDER_CALLS=0`,
`PHASE8_BRIDGE_SCIENTIFIC_DISPATCH=0`,
`PHASE8_BRIDGE_OUTCOME_BEARING=false`, and
`PHASE8_BRIDGE_EXECUTION_APPROVED=false`. No working-tree changes
were reported. Real GPU outputs and real scientific outcomes remain
**unverified**; all output artifacts in these tests were synthetic.

A security and experimental-authorisation review found a **material
trust gap** in the staged pre-outcome integration: a caller could
produce a new JSON document containing
`scientific_execution_permitted=true` and
`researcher_attested_supervisor_provider_billing_and_models=true`,
then pass the SHA-256 of *that same self-created document* to
`verify_approved_runtime`. File integrity alone establishes that
the file matched the caller's digest; it does **not** establish that
the supervisor actually approved the file. The standalone source
code had not yet introduced an independently controlled final-runtime
hash pin.

The repository now includes an independent, default-deny
`TRUSTED_APPROVED_RUNTIME_SHA256 = None` trust anchor in
`phenoassistant_mcp/scientific_inference_v1.py`. The separate
`verify_trusted_runtime` checks it against a final runtime digest
before real canonical GPU inference. Similarly, real-network
`Phase8MafDecisionClient.create` requires the independent pin.
The **only** testing exception is a deliberately injected fake vision
delegate or an in-process `httpx.MockTransport`, which remains
subject to the structural runtime checks and the test-only fixture
contract. The unconfigured trust pin is deliberately NOT read
from CLI arguments, model outputs or environment variables.
No supervisor approval has been fabricated or asserted.

The default trust pin remains `None` and will remain so until
actual documented approval of the provider, credential, billing,
models and independently verified final source-hashed scientific
runtime. Synthetic test approvals must **never** be copied into
a production runtime. This is a prerequisite for native scientific
execution, *not* proof that the whole runner is approved. An operator
with ability to change or inject arbitrary Python remains outside
the threat model of a code-level gate; operational supervision and
the provider key hard spend cap are separately required.

Tests added in
`tests/research/test_phase8_scientific_mcp.py` and
`tests/research/test_phase8_maf_decision_v1.py` verify that a
self-declared 'approved' JSON and its correct hash cannot enable
the default real GPU delegate or an actual OpenRouter HTTP client.
Tests using intentionally mocked transport or fake scientific
inference can still verify the protocol with zero credits.

The standalone bridge status marker has been updated from
`implemented-pending-Plato-tests` to
`offline-tests-passed-real-GPU-unverified` to reflect the 105
observed Plato passes without overstating scientific readiness.

### Next Plato regression gate, no API key

After pulling the experiment branch:

```bash
cd ~/PhenoAssistant
unset OPENROUTER_API_KEY
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_scientific_mcp.py \
  tests/research/test_phase8_maf_decision_v1.py \
  tests/research/test_phase8_proposal_mcp_bridge_v1.py \
  tests/research/test_phase8_scientific_artifact_validator.py \
  tests/research/test_phase8_openrouter_compat.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/phase8_proposal_mcp_bridge_v1.py
git status --short
```

Do not assume the number of tests until Plato executes them. The
required real-work outcome is **denial**: unapproved canonical GPU
inference and real OpenRouter clients must fail before doing any
work. Test-only fake delegates and in-process fake HTTP may continue
to validate the integration. No outcome-bearing experimental calls
are permitted by this change.

**Still outstanding:** complete locked real-image fixture manifest,
native MAF function-call capture with a no-dispatch proposal boundary,
real scientific-model/checkpoint integrity and GPU fidelity,
C4 genuine Critic output measurements, append-only raw attempt
and per-call provider-billed cost capture, external approval evidence,
new final runtime lock, hidden-label protection and blinded scoring.
Progress percentages are unchanged.


## 2026-11-19: 109/109 Plato tests passed; private real-image binding gate staged

The researcher pulled `067e69f` on Plato and passed **109/109**
offline regression tests in 5.14 seconds. The direct bridge confirmed
108 registered qualification trials; the C3/C4/C8 mediated path,
output-aware C8 validation and independently pinned trust gate passed
their intended offline checks. Exact markers:
`PHASE8_BRIDGE_PROVIDER_CALLS=0`,
`PHASE8_BRIDGE_SCIENTIFIC_DISPATCH=0`,
`PHASE8_BRIDGE_NATIVE_TOOL_CALLING=false`,
`PHASE8_BRIDGE_C8_REAL_OUTPUT_VALIDATION=offline-tests-passed-real-GPU-unverified`,
`PHASE8_BRIDGE_OUTCOME_BEARING=false`, and
`PHASE8_BRIDGE_EXECUTION_APPROVED=false`.
The worktree was clean. **No scientific outcome or real GPU result** exists.

New pre-outcome source:
`scripts/research/phase8_image_fixture_registry.py`
and `tests/research/test_phase8_image_fixture_registry.py`.

The existing 12-case qualification manifest has **zero approved
physical image bindings**, even though the Manager and Critic can
propose models. Without those bindings, a real experimental executor
cannot legitimately attempt the intended scientific inference.
This module generates one private, unbound slot for each frozen
scenario, verified against the preserved 108-trial matrix and the
exact paired model-visible request hash. The slot is the same for
all three conditions and frozen seeds; it is *not* passed to the
Manager or Critic.

The eventual manually reviewed bindings must include:
- opaque image asset ID, absolute image path restricted to a trusted
  image root, source-image SHA-256, decodable image data;
- source dataset and source image ID, reviewed biological species,
  data-use/access evidence and separate reviewer evidence ID;
- exact 12-scenario coverage with no duplicates, conflicting asset
  identities, path escape or symlink traversal, and species/request
  contradictions rejected when scientific species is declared;
- **no case ID, dataset review, image path, reviewer data or fixture
  identifier in model-visible scientific requests.**

The incomplete template is written under `data/_staging/`, which
is already Git-ignored. Do not commit file paths or private image
review evidence into the repository. The existing
`TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256` is deliberately `None`.
Even a structurally valid self-attested registry is **not approved**
to execute real science until independent provenance review and a
subsequent source-hashed final runtime approval. The module never
opens gold labels, contacts OpenRouter or runs a GPU model.

### Plato offline verification

```bash
cd ~/PhenoAssistant
git pull --ff-only origin experiments/ijcai2027

unset OPENROUTER_API_KEY
~/.local/envs/phenoassistant-phase6-mcp/bin/python -m pytest -q \
  tests/research/test_phase8_image_fixture_registry.py \
  tests/research/test_phase8_scientific_mcp.py \
  tests/research/test_phase8_proposal_mcp_bridge_v1.py
~/.local/envs/phenoassistant-phase6-mcp/bin/python \
  scripts/research/phase8_image_fixture_registry.py --write-template
git status --short
```

Expected outputs: 12 frozen fixture slots; zero real images bound;
private source metadata model-visible=false; independent review
approved=false; zero provider calls, zero scientific execution;
`PHASE8_FIXTURE_PREFLIGHT_PASS=true`.
**The new tests have not yet been run on Plato**. The generated
template is unapproved and ignored by Git. The CLI refuses to
overwrite an existing template. No paid model calls are authorised.

Next major task remains to qualify *native* MAF function-call
capture, after which real image fixture evidence, checkpoint
integrity, provider-billed attempt logging and supervisor approval
must be reviewed before final trial-runtime freeze. The current
mediation via JSON proposal is explicitly not native tool calling.
