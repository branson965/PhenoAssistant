# PhenoAssistant MAF + MCP + Research Execution Status

**Updated:** 2026-10-10  
**Active branch:** `experiments/ijcai2027`  
**Current phase:** Phase 8 — full IJCAI experiments, ablations, hidden evaluation, and failure analysis (Phase 5 Case 3 external gate carried forward)

## Authoritative venue strategy

The current paper plan is **IJCAI 2027**.

- stretch target: IJCAI 2027;
- internal go/no-go: 2026-11-30;
- primary fallback: ECAI 2027;
- AAMAS 2028 is only a later option if the work needs a longer experimental programme;
- working title: *Beyond Callability: Scientific Applicability Verification for Tool-Using Agents Under Distribution Shift*;
- MAF/MCP work is infrastructure and a controlled portability/interface variable, not the primary novelty claim.

The authoritative research-plan source is
`docs/research/SCIENTIFIC_APPLICABILITY_PAPER_PLAN.md`.
Any older AAMAS-specific plan is historical context only and must not drive current execution.

## Progress model

100% means a fully integrated, GPU-validated PhenoAssistant implementation using the agreed MAF/MCP architecture, accompanied by rigorous comparative evaluation, a defensible research contribution, reproducible experiments, and a submission-ready paper/artifact.

| Phase | Mission | State |
|---|---|---|
| 1 | Preserve and understand original AutoGen baseline | complete |
| 2 | Build bounded production-shaped MAF CPU architecture | complete |
| 3 | Migrate and validate CPU case-study behaviour | complete |
| 4 | Audit Vincent MCP branch and freeze integration contract | complete |
| 5 | Execute and validate GPU scientific workflows | blocked only on external Case 3 private-resource access; Case 1 closed |
| 6 | Migrate MCP to v2, integrate with MAF, prove parity | complete |
| 7 | Implement/freeze scientific-applicability research method | complete |
| 8 | Full experiments, ablations, hidden evaluation, failure analysis | active |
| 9 | Manuscript, artifact, hostile review, submission | pending |

## Frozen baselines

- MAF direct baseline:
  `e0f1626545dc7de2a4d246506564863c00e4c4cd`
- Vincent MCP v1 baseline:
  `44e456811b0d07547fdf8c8ddfb03d1187c1ae1e`
- preservation refs:
  - `baseline/maf-pre-mcp-integration-20261008`
  - `baseline/vincent-mcp-v1-20261008`

## Phase 5 completed preparation and pre-GPU evidence

- secret-safe GPU environment probe;
- lightweight data/repository preflight;
- Case 1 one-image/full GPU runner;
- Case 1 deterministic regenerated-vs-tracked comparator;
- Case 3 bounded inference-only smoke runner;
- static tests locking the GPU-validation contracts;
- generated GPU output directories ignored from Git;
- full Phase 5 validation protocol documented;
- official Case 1 Zenodo archive downloaded and checksum-verified;
- all 1,248 Case 1 metadata-referenced images verified locally;
- isolated Plato Python 3.11.17 GPU environment bootstrapped;
- heavyweight PhenoAssistant imports passed with PyTorch 2.4.1+cu121;
- Case 1 model access verified without credentials at HF revision `a75bc3d595148ebc62afad7c9800908279e7aea8`;
- Case 3 dataset and registered checkpoint access boundary reproduced as HTTP 401 without credentials;
- `ada24/petra` inspected and found to have all eight GPUs allocated at the checkpoint time;
- real Nottingham GPU allocation established on `amp16/tamar` with one NVIDIA RTX A4000;
- CUDA probe passed (`cuda_available: true`, one visible device);
- one-image Case 1 GPU smoke completed successfully with 5 segmentation annotations;
- 16-image bounded Case 1 GPU sample completed successfully in 4.908 s with 106 segmentation annotations;
- full 1,248-image Case 1 GPU inference completed in 184.858 s with 11,848 segmentation annotations;
- phenotype regeneration completed from the newly generated segmentation output;
- regenerated-vs-tracked comparison aligned all 1,248 rows with 100% coverage, zero missing/extra rows, exact leaf-count and PLA ecotype rankings, and near-numerical identity across all seven phenotypes;
- Case 1 full reproduction evidence preserved in `docs/maf/evidence/PHASE5_CASE1_GPU_REPRODUCTION_20261008.md`;
- Case 1 scientific-conclusion parity passed: interaction decision, all ten Tukey pairwise significance decisions, and the three ordered phenotype groups matched exactly;
- Case 1 statistical environment restored to the declared pins, `pip check` clean, and the scientific-conclusion parity gate passed again under the frozen environment;
- Case 1 GPU scientific reproduction is closed;
- Case 3 public-source provenance mapped to DND-Diko-WWWR/WW2020;
- historical source code confirms the prepared Case 3 dataset and trained checkpoint were intentionally pushed as private Hugging Face resources;
- authenticated Case 3 probe still returns HTTP 404 for both exact historical resource identifiers, establishing that the current account lacks access or the resources no longer exist at those identifiers.

## Phase 5 evidence still required

- Case 3 approved image discovery;
- Case 3 registered-checkpoint GPU inference;
- explicit evidence-backed decision on whether Case 3 retraining is necessary.

## Phase transition decision

Phase 6 may proceed without waiting for Case 3 private-resource access. The remaining
Case 3 gate is external to the local migration implementation: authenticated probing
has established that the exact historical private Hugging Face dataset/checkpoint are
not accessible to the current account. This blocker is preserved as an open Phase 5
evidence item and must not be silently counted as reproduced.

Moving into Phase 6 therefore does **not** mean Case 3 has passed. It means the
transport/orchestration integration work can proceed independently while the exact
historical Case 3 artefact remains pending collaborator access or an explicitly
approved alternative provenance route.

No retraining, substitution of a different checkpoint, or claim of Case 3
reproduction is authorised by this phase transition.

## Phase 6 work completed so far

- official MCP Python SDK v2 baseline fixed to stable `mcp==2.3.0`;
- modern protocol target remains `2026-07-28`;
- new `phenoassistant_mcp` package created without modifying the frozen Vincent v1 baseline;
- bounded MCP v2 server implemented for the three exact semantic parity tools only:
  `calculator`, `perform_anova`, and `perform_tukey_test`;
- server results use explicit structured envelopes rather than unvalidated free text;
- first-class MCP v2 `Client` boundary implemented with modern protocol pinning and
  fail-closed structured-result validation;
- isolated Plato Python 3.11.17 Phase 6 environment created;
- frozen MCP/MAF dependency set installed with `pip check` clean;
- first-class MCP v2 import contract verified on Plato;
- MCP protocol `2026-07-28` verified at runtime;
- bounded discovery/direct-vs-MCP transport suite passed 4/4 on Plato;
- real preserved ANOVA direct-versus-MCP parity passed with three identical records;
- real preserved Tukey direct-versus-MCP parity passed with three identical records;
- transport regression suite remained 4/4 after scientific dependencies were installed;
- MAF-facing MCP bridge implemented for the same three-tool parity slice;
- trusted dataset paths remain application-bound and are not exposed to the Manager;
- MCP-backed MAF tools preserve the direct MAF names, descriptions, input models,
  and typed result envelopes;
- deterministic MAF-to-MCP integration tests passed 7/7 on Plato;
- real MAF-to-MCP scientific validation passed for both ANOVA and Tukey typed
  result-envelope parity;
- the production-shaped Manager -> FunctionTool -> MCP v2 Client -> MCP Server ->
  preserved ANOVA implementation path passed on Plato;
- the Manager-facing MCP path kept the trusted dataset path hidden and returned the
  expected three ANOVA records;
- dependency health remained clean after the Phase 6C execution;
- Phase 6D fail-closed and lifecycle suite passed 14/14 together with all preceding
  MCP v2 transport and MAF-bridge tests on Plato;
- injected tool exceptions, server return-contract violations, malformed structured
  payloads, trusted-path rejection, repeated one-shot client sessions, and
  Manager-level failure propagation all fail closed as intended;
- dependency health remained clean after Phase 6D;
- tracked Python bytecode was removed from the branch so future scientific imports
  no longer dirty Git status;
- explicit reusable MCP v2 client lifecycle and caller-controlled timeout semantics
  are committed for the next Plato gate;
- interface documentation now records the bounded tool surface, trust boundary,
  lifecycle, timeout, failure mapping, and current evidence;
- the final Phase 6E suite passed 19/19 on Plato;
- reusable persistent MCP sessions, lifecycle misuse rejection, and caller-controlled
  timeout semantics are runtime-verified;
- typed PhenoAssistant boundary exceptions remain visible across MCP SDK cleanup;
- the final 100-trial transport microbenchmark passed with exact result parity:
  direct median 0.0002445 ms, one-shot MCP median 1.5335825 ms, and persistent-session
  MCP median 0.3698135 ms;
- `pip check` remained clean;
- the bounded repository secret-pattern scan returned no matches;
- Phase 6 closure evidence is preserved in
  `docs/maf/evidence/PHASE6_MCP_V2_INTEGRATION_20261010.md`;
- machine-readable benchmark evidence is preserved in
  `docs/maf/evidence/PHASE6E_MCP_TRANSPORT_BENCHMARK_20261010.json`.

Phase 6 is closed. The verified MCP/MAF boundary is frozen as infrastructure for
Phase 7 scientific-applicability research work.

## Current progress

**Overall completion: 82%**

**Current phase completion: 12%**

**Phases completed: 6/9**

Case 1 GPU scientific reproduction remains fully closed and the remaining Case 3 gate
is externally blocked. Phase 6 is closed. Phase 7 is now also closed with a
content-addressed IJCAI scientific-applicability method freeze, prospectively frozen
condition protocol, label-free hidden-test contract, deterministic scoring, bounded
post-execution validation, and runtime-verified 82/82 research tests. Phase 8 begins
from the preserved Phase 7 closure without modifying the frozen scientific method.


## Phase 7 work committed so far

- dedicated research/phenoguard branch created from the closed Phase 6 interface;
- typed Scientific Operating Envelope v0.1 committed;
- typed request context, hard/soft constraints, five global decision actions, and
  structured applicability assessment committed;
- deterministic single-capability pre-execution checker committed;
- checker intentionally emits only EXECUTE, CLARIFY, or ABSTAIN until catalogue and
  training-readiness evidence exists for RESELECT and RECOMMEND_TRAINING;
- eight contract/mechanics tests committed;
- method contract documents the current claim boundary and explicitly states that
  synthetic unit fixtures do not establish scientific validity.

Phase 7A is runtime-verified on Plato: all eight contract tests passed, the valid
smoke request emitted EXECUTE, the hard-invalid smoke request emitted ABSTAIN, and
dependency health remained clean.

Phase 7B now adds the first provenance-backed real capability envelope for the
registered Case Study 1 Arabidopsis instance-segmentation model. Its scope is
intentionally narrow: species is the only currently frozen hard context rule.
Unverified view/modality/environment assumptions are not silently encoded as facts.
Phase 7B is runtime-verified on Plato. The combined Phase 7A+7B research suite passed
13/13, the real-envelope smoke test emitted EXECUTE for the evidenced Arabidopsis
request, CLARIFY for missing species, and ABSTAIN for a mismatched species, and
dependency health remained clean.

Phase 7C now adds a second provenance-backed real capability envelope for Case Study 2
potato Leaf-only SAM plus deterministic catalogue-level resolution. This is the first
method slice that can emit RESELECT: only when a requested capability is scientifically
inapplicable and exactly one alternative capability is currently executable. Ambiguous
multiple matches require CLARIFY, and no-match cases remain ABSTAIN. RECOMMEND_TRAINING
is still deliberately withheld until a separate training-readiness policy is defined.

Phase 7C is runtime-verified on Plato. The combined Phase 7A+7B+7C suite passed
23/23. The real catalogue smoke emitted RESELECT from the invalid Arabidopsis model
to the potato Leaf-only SAM model, CLARIFY for missing context, and ABSTAIN when no
catalogue capability matched. The model-zoo provenance cross-check passed and
dependency health remained clean.

Phase 7D now adds the final global action, RECOMMEND_TRAINING, behind an explicit
training-readiness policy. The frozen v0.1 policy is deliberately limited to the
paper-documented image-classification training path. A catalogue miss alone cannot
trigger training: labelled data and supported-format evidence are required, missing
readiness yields CLARIFY, unsupported training tasks remain ABSTAIN, and an existing
applicable capability always takes precedence.

Phase 7D is runtime-verified on Plato. The complete Phase 7A-D suite passed 31/31.
The training-policy smoke emitted RECOMMEND_TRAINING for a supported classification
gap with ready labelled data, CLARIFY when required data evidence was missing,
ABSTAIN for an unsupported training task, and EXECUTE when an applicable existing
capability was already available. Dependency health remained clean.

Phase 7E now adds a deterministic, machine-readable pre-execution trace contract.
Each trace preserves the request, catalogue identifiers, complete structured
resolution, optional training-readiness evidence, final decision, selected capability,
and a stable reason code. Canonical JSON and SHA-256 helpers support reproducible
manifests. Runtime timestamps/cost/latency are intentionally excluded from the
semantic trace and belong to later experiment-run metadata.

Phase 7E is runtime-verified on Plato. The full Phase 7A-E suite passed 40/40.
All five decisions produced deterministic traces with stable reason codes and
SHA-256 digests, dependency health remained clean, the bounded secret scan returned
no matches, and the research branch remained clean.

Phase 7F will freeze the IJCAI benchmark contract before benchmark construction:
scenario schema, paired valid/invalid design, hard-negative taxonomy, gold-label
fields, split policy, deterministic scoring, and baseline/condition identifiers.
The hidden expert test must remain unavailable to method tuning.


## Phase 7F work committed

- corrected the remaining active research-document reference that still named the obsolete
  venue-specific benchmark; the authoritative target is IJCAI 2027;
- project status now explicitly records IJCAI 2027 as the stretch target, the
  2026-11-30 internal go/no-go, ECAI 2027 as primary fallback, and AAMAS 2028 only
  as a later option;
- benchmark scenario and hidden-gold schemas committed;
- matched valid/invalid pair contract committed;
- evidence-source hierarchy distinguishes real domain shifts from provenance-backed
  metadata cases and synthetic metadata stress tests;
- deterministic decision scoring committed for exact correctness, unsafe execution,
  and unnecessary abstention;
- hidden scenarios are structurally label-free;
- the current IJCAI baseline family is documented from the authoritative
  scientific-applicability paper plan;
- Phase 7F is runtime-verified on Plato: the complete Phase 7A-F suite passed 50/50,
  the matched species-shift pair scored exactly correct, hidden scenario payloads
  remained gold-label-free, dependency health was clean, the bounded secret scan
  returned no matches, and the branch remained clean;
- the active research documentation now contains no stale 2027 benchmark target.

Phase 7G is runtime-verified on Plato. The complete Phase 7A-G suite passed 62/62.
The post-validation smoke accepted valid phenotype/statistical/identifier evidence and
failed closed on negative phenotype values, inconsistent statistical claims, and
identifier mismatch. Dependency health was clean, the bounded secret scan returned no
matches, the active research documentation contained no stale 2027 target, and the
branch remained clean.

Phase 7H now prospectively freezes the IJCAI experiment structure before outcome-
bearing Phase 8 runs. It commits the ten authoritative baseline/method condition IDs,
the complete required metric set, an MCP-primary/direct-vs-MCP portability design,
a typed controlled-variable schema, a 12-case development/validation harness-
qualification manifest with five matched valid/shifted pairs, mechanical gold labels,
and an explicit pre-outcome claim boundary. The qualification manifest is not the
final benchmark and contains no hidden cases.

Phase 7H is runtime-verified on Plato. The complete Phase 7A-H suite passed 77/77.
All ten C0-C9 condition identities were present, all 13 required metrics were retained,
the 12-case qualification manifest scored 12/12 exactly with zero unsafe executions,
the machine-readable protocol freeze validated, dependency health was clean, the
bounded secret scan returned no matches, stale 2027-target checks returned no matches,
and the branch remained clean.

Phase 7I is runtime-verified on Plato. The complete Phase 7A-I targeted suite passed
82/82 and full `tests/research` discovery also passed 82/82. The standalone freeze
verifier confirmed all 22 frozen files and aggregate digest
`337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f`.
The venue/policy smoke passed, dependency health was clean, the bounded secret scan
returned no matches, the stale-target scan returned no matches, and the branch
remained clean.

Phase 7 is closed. Concrete provider/model/runtime values remain intentionally
unfilled and must be pinned and hashed before the first outcome-bearing Phase 8
pilot; they must not be selected after inspecting favourable outcomes.


## Phase 7H prospective IJCAI freeze

- condition catalogue frozen as C0-C9 from model-only through expert oracle;
- full PhenoGuard C8 structurally requires bounded post-execution validation;
- primary tool-using interface frozen to MCP;
- portability subset frozen to C3 and C8 under direct and MCP execution;
- all authoritative IJCAI metrics retained;
- typed controlled-variable contract requires provider/model revision, temperature,
  token limit, prompt/tool/task hashes, retry/iteration/session policy, package lock,
  and hardware class before compared runs;
- development/validation qualification manifest frozen at 12 mechanically
  adjudicable cases: 8 development, 4 validation, 5 matched pairs, 2 unpaired
  training-policy cases, 0 hidden;
- machine-readable protocol freeze committed at
  `docs/research/IJCAI_2027_PROTOCOL_FREEZE.json`;
- narrative protocol/claim boundary committed at
  `docs/research/IJCAI_2027_PROTOCOL_FREEZE.md`;
- strong Claim 2 is authorised only if unsafe execution falls versus both
  Manager+schemas and generic-Critic baselines without lower valid-execution accuracy
  than both; otherwise the claim is narrowed to the observed safety/coverage trade-off
  or a negative result;
- hidden labels remain inaccessible, negative results are retained, and post-unblinding
  method changes remain prohibited.


## Phase 7I final freeze package

- 22 scientific-method and protocol files content-addressed with SHA-256;
- frozen source snapshot: `c58741bb9b0bcc8ebef68755e3d8528de9533312`;
- aggregate digest:
  `337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f`;
- standalone verifier committed at
  `scripts/research/verify_phenoguard_method_freeze.py`;
- freeze manifest committed at
  `docs/research/IJCAI_2027_PHASE7_METHOD_FREEZE_MANIFEST.json`;
- freeze rationale and Phase 8 transition policy committed at
  `docs/research/IJCAI_2027_PHASE7_METHOD_FREEZE.md`;
- five freeze-integrity tests committed;
- scientific-method changes after Phase 8 outcomes require an explicit Phase 7 reopen,
  a new manifest version, re-verification, and retention of all pre-change results;
- preservation ref `baseline/phenoguard-method-freeze-20261010` is created at the verified Phase 7 closure commit.


## Phase 7 closure and Phase 8 transition

Phase 7 closure evidence on Plato:

- targeted Phase 7A-I suite: 82/82 passed;
- full `tests/research` discovery: 82/82 passed;
- frozen file count: 22;
- aggregate method digest:
  `337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f`;
- freeze policy: IJCAI 2027, hidden labels unavailable to method, negative results
  retained, post-unblinding method changes prohibited;
- dependency health: clean;
- bounded secret scan: no matches;
- stale 2027 target scan: no matches;
- worktree at runtime gate: clean.

Phase 8 rules:

- branch: `experiments/ijcai2027`;
- do not modify the 22 frozen scientific-method/protocol files;
- pin concrete provider/model/runtime controls before the first outcome-bearing pilot;
- begin with development/validation pilot execution and harness qualification;
- retain every attempt, including negative or failed runs;
- do not create or inspect final hidden expert labels until the experiment harness,
  scoring analysis, and run controls are frozen;
- carry the externally blocked Case 3 historical-resource gate separately without
  substituting an unapproved dataset/checkpoint.


## Phase 8A pre-outcome runtime-control preparation

The experiment branch has been initialised from the verified Phase 7 closure commit.
No frozen scientific-method file has been modified.

Committed Phase 8A scaffolding:

- `experiments/ijcai2027/README.md` with experiment ordering and freeze rules;
- `experiments/ijcai2027/condition_prompt_contract.json` covering C0-C9 and
  prohibiting hidden-gold leakage;
- `scripts/research/prepare_ijcai_runtime_controls.py`, which performs no LLM call
  and no scientific benchmark, reads no API key, verifies the Phase 7 aggregate,
  captures provider/model/runtime identity, hashes prompt/tool/task inputs, captures a
  package lock and hardware snapshot, and writes a pre-outcome candidate;
- `tests/research/test_phase8_preflight.py` with four guardrail tests.

Phase 8A branch preflight is runtime-verified on Plato: the experiment branch matched
origin, the Phase 7 freeze verifier passed, the complete research/preflight suite
passed 86/86, and the non-secret runtime probe confirmed Python 3.11.17, MCP 2.3.0,
Pydantic 2.13.4, and a CPU-only Phase 8A shell. The earlier
`AGENT_FRAMEWORK_VERSION=<not-installed>` line was produced by probing the wrong
distribution name; the repository pins `agent-framework-core==1.11.0` and
`agent-framework-openai==1.11.0`, which are now checked explicitly by the runtime
capture.

No model/runtime variables were configured in the shell, so no outcome-bearing run
has occurred.

Before outcomes, the primary model is now prospectively frozen to
`openai/gpt-5.6-luna` and the stronger breadth model to
`openai/gpt-5.6-sol`. Both are routed through OpenRouter but pinned to the OpenAI
upstream provider with provider fallbacks disabled. The historical
`openrouter/free` router is excluded from the paper evaluation because its
underlying model identity is dynamic.

The Phase 8A runtime plan is also prospectively frozen: reasoning effort medium,
paired seed schedule 2026/2027/2028, 2 model roundtrips, 1 function execution,
no concurrent invocation, transport-only retries, and fresh client/agent/session
state per scenario replicate. GPT-5.6 Luna's selected OpenRouter parameter surface
does not expose temperature, so temperature is explicitly not sent; the frozen
Phase 7 numeric temperature field uses a documented 0.0 schema sentinel only.

A non-scientific live MAF/OpenRouter echo-tool preflight is committed. It must pass
before the runtime-control candidate is marked frozen and before any scientific
benchmark case is executed.


## Phase 8A model and runtime freeze work

- primary model predeclared: `openai/gpt-5.6-luna`;
- breadth model predeclared: `openai/gpt-5.6-sol`;
- breadth conditions predeclared: C3, C4, C8;
- OpenRouter upstream provider pinned to `openai`;
- provider fallbacks disabled and required-parameter routing enabled;
- dynamic `openrouter/free` explicitly prohibited for the main IJCAI evaluation;
- provider-managed revision limitation documented; response model identity and
  `system_fingerprint` will be recorded on every live run when available;
- sampling extension frozen to medium reasoning effort and paired seeds
  2026/2027/2028;
- temperature is not transmitted for the selected GPT-5.6 API surface;
- tool loop frozen to 2 model roundtrips and at most 1 function execution;
- transport retries frozen to at most 2; semantic/model retries frozen to 0;
- package expectations now explicitly validate
  `agent-framework-core==1.11.0`,
  `agent-framework-openai==1.11.0`, `mcp==2.3.0`, and
  `pydantic==2.13.4`;
- non-scientific live provider/tool-call preflight committed;
- no Phase 8 scientific outcome has been observed.
