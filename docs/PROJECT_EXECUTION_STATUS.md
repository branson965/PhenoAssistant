# PhenoAssistant MAF + MCP + Research Execution Status

**Updated:** 2026-11-18  
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
| 5 | Execute and validate GPU scientific workflows | qualified (85%): Case 1 closed, full-FT Case 3 checkpoint/runtime validated; exact historical Case 3 training reproduction remains open |
| 6 | Migrate MCP to v2, integrate with MAF, prove parity | complete |
| 7 | Implement/freeze scientific-applicability research method | complete |
| 8 | Full experiments, ablations, hidden evaluation, failure analysis | active (20%): offline preparation closed; scientific outcomes pending |
| 9 | Manuscript, artifact, hostile review, submission | pending (15%): paper story/plan exists; outcome-grounded manuscript pending |

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

## Current progress — evidence-weighted recalibration (2026-11-18)

The older engineering-weighted progress figures are superseded by the authoritative,
reproducible managerial scorecard:
`docs/research/IJCAI_2027_COMPLETION_SCORECARD.md`.

**Overall completion: 51%** (unrounded weighted sum 51.25/100).

**Current phase, Phase 8: 20%**.

**Phases fully completed: 6/9** (Phases 1–4, 6 and 7).
Phase 5 is *qualified at 85%*, not counted fully closed because exact historical
Case 3 training reproduction or a formal scope disposition remains outstanding.
Phase 9 is 15%: the scientific story exists but no outcomes-backed complete
submission manuscript has been demonstrated.

Weights: Phases 1–4 each 3%, Phase 5 8%, Phase 6 8%, Phase 7 14%,
Phase 8 35%, and Phase 9 23%. This intentionally places 58% of the total
score on the outcome-bearing experiments and manuscript/submission work,
rather than treating migration infrastructure as equivalent to paper evidence.

Phase 8 is pre-outcome: the Phase 7 v0.2 method remains frozen, the
offline runtime candidate is preserved, and the live provider gate is still
documented as awaiting supervisor-approved access. The qualification-fixture
result and method unit tests are **not** scientific effectiveness results.
No live pilot, main/hidden evaluation, or outcome-bearing claims are yet
recorded. The 2026-11-30 internal IJCAI go/no-go is evidence-based.

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


## Phase 8A supervisor credential gate

The user does not yet have an OpenRouter account or API key and will ask Valerio on
Monday for the approved credential/provider route and next steps.

Because no Phase 8 scientific outcome has been observed, the provisional Luna/Sol
model plan and runtime plan remain safely changeable before the first live scientific
run. They are now explicitly marked
`PROVISIONAL_PRE_OUTCOME_PENDING_SUPERVISOR_CONFIRMATION`.

The offline runtime-capture script previously failed when executed directly because
Python placed `scripts/research` rather than the repository root on `sys.path`.
That defect is fixed on the experiment branch by bootstrapping the repository root
before importing `research.phenoguard`, with a regression guard added.

No OpenRouter account should be created and no personal credential should be purchased
or committed solely to unblock this gate before supervisor confirmation.


## Case 3 collaborator update — 2026-10-14

Feng confirmed that the previously discussed Case 3 models have been made public.
He clarified that the historical LoRA checkpoint is demonstration-only and was not
trained to convergence, while the non-LoRA fully fine-tuned model is the functioning
scientific checkpoint. He supplied the fallback/public identifier:

`fengchen025/dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020`

The experiment branch now:

- metadata-probes both the historical LoRA demonstration checkpoint and the
  collaborator-provided fully fine-tuned checkpoint;
- includes an inference-only Case 3 wrapper that runs the existing bounded GPU smoke
  against the fully fine-tuned checkpoint without changing the frozen model catalogue;
- adds a static regression test for that collaborator-approved checkpoint path.

The frozen `model_zoo.json` has intentionally not been modified yet. First verify the
public model metadata and one bounded GPU inference. If that passes, reopen Phase 7
explicitly, replace the demonstration checkpoint with the verified full-FT checkpoint,
recompute the content-addressed freeze, and rerun the affected suite before any
outcome-bearing IJCAI experiment.

Feng also authorised using a newly created model when the objective is to validate
PhenoAssistant's training ability rather than reproduce the historical Case 3 model.


## Case 3 public-model metadata gate — 2026-10-14

Runtime verification on Plato passed for Feng's collaborator-provided public full-FT
checkpoint.

Observed:

- full-FT checkpoint reachable: true;
- full-FT checkpoint private: false;
- full-FT immutable Hugging Face revision:
  `89d6b3ca17dba118d7d25c7b8a87ff205dc6235e`;
- pipeline tag: `image-classification`;
- architecture: `Dinov2ForImageClassification`;
- label mapping contains seven fertilizer-treatment classes;
- historical LoRA demonstration checkpoint is now also public at revision
  `1b2f6bfd4ccb0f28bfe8757f8468161cfa7104be`;
- historical prepared dataset remains unreachable.

The raw config does not serialize an explicit `num_labels` field, but it exposes
the complete seven-class `id2label` mapping; this is not treated as a metadata
failure.

A GPU compatibility smoke is now prepared using the official DND-Diko-WWWR example
image linked by the dataset authors. That smoke is explicitly checkpoint-load /
inference compatibility evidence only and cannot be used as an accuracy estimate.


## Case 3 GPU compatibility result — 2026-10-14

The collaborator-provided full-FT checkpoint executed successfully on Nottingham
Plato using one NVIDIA RTX A4000. The exact pinned Hugging Face revision was
`89d6b3ca17dba118d7d25c7b8a87ff205dc6235e`. The official
DND-Diko-WWWR README montage was used only as a compatibility input, so no accuracy
claim is authorised from this run.

Observed runtime evidence:

- CUDA available with one visible NVIDIA RTX A4000;
- exact pinned snapshot resolved from the shared Hugging Face cache;
- PhenoAssistant image-classification inference completed;
- compatibility marker passed;
- evidence verification passed;
- Phase 7 freeze still matched the original 22-file aggregate;
- dependency health remained clean.

The run emitted a Transformers warning stating that classifier weights were newly
initialized from `facebook/dinov2-base`. Because the public repository also contains
PEFT adapter artefacts alongside `model.safetensors`, this warning must be resolved
before treating the checkpoint as scientifically validated. A non-loading checkpoint
integrity audit has therefore been added to verify whether the full weight file itself
contains a seven-class classifier head and to hash that exact weight file.

Do not reopen or modify the frozen Phase 7 catalogue until this integrity audit passes.


## Case 3 checkpoint-integrity audit — 2026-10-14

The pinned collaborator checkpoint at revision
`89d6b3ca17dba118d7d25c7b8a87ff205dc6235e` passed a direct safetensors
integrity audit.

Observed:

- `model.safetensors` SHA-256:
  `4a29f8b73438a6d16cbc80287c40002af40029fd529146f0be73d7825befbbf5`;
- 225 state-dict keys;
- seven labels in `id2label`;
- `classifier.weight` present with shape `[7, 1536]`;
- `classifier.bias` present with shape `[7]`;
- classifier output dimension matches the seven-label config;
- PEFT `adapter_config.json` and `adapter_model.safetensors` also coexist in the
  same public repository.

This resolves the concern that the full weight file lacked a trained classifier head.
However, the coexistence of PEFT artefacts explains why ordinary Transformers loading
may auto-detect the repository as an adapter package and first instantiate the
`facebook/dinov2-base` base model, producing the earlier newly-initialized classifier
warning.

The authoritative compatibility smoke has therefore been hardened to construct a
clean local runtime view containing only the audited `config.json`,
`preprocessor_config.json`, and exact `model.safetensors`. The PEFT files are
explicitly excluded from runtime loading. A second GPU smoke using this clean full-FT
view is required before reopening the frozen Phase 7 catalogue.


## Case 3 authoritative full-FT runtime pass and Phase 7 reopen — 2026-10-14

The PEFT-isolated authoritative GPU rerun passed on Nottingham Plato using an
NVIDIA RTX A4000.

Observed authoritative runtime evidence:

- exact full-FT revision:
  `89d6b3ca17dba118d7d25c7b8a87ff205dc6235e`;
- exact `model.safetensors` SHA-256:
  `4a29f8b73438a6d16cbc80287c40002af40029fd529146f0be73d7825befbbf5`;
- clean runtime contained `config.json`, `preprocessor_config.json`, and
  `model.safetensors` only;
- colocated PEFT adapter files were excluded from runtime loading;
- the earlier newly-initialized classifier warning did not recur;
- PhenoAssistant image-classification inference completed successfully;
- the compatibility input was the official DND-Diko-WWWR README montage and remains
  explicitly non-accuracy evidence;
- Phase 7 v0.1 remained intact through the runtime gate.

Case 3 checkpoint access/callability is therefore closed for the functioning full-FT
model. The remaining unavailable historical prepared dataset is a separate
training-reproduction issue, not a checkpoint-access blocker.

Phase 7 is now explicitly reopened before any outcome-bearing IJCAI scientific run
to replace the demonstration-only LoRA catalogue entry with the verified full-FT
checkpoint and add its evidence-backed operating envelope. The v0.1 manifest has been
archived, and a controlled v0.2 manifest generator is committed. No benchmark,
scoring, C0-C9 condition, hidden-label, or claim-boundary rule is authorised to change
during this reopen.


## Phase 7 v0.2 re-freeze candidate — 2026-10-14

The controlled Case 3 provenance reopen has now produced an active v0.2 freeze
manifest. The frozen scope remains exactly 22 paths. Only four frozen files differ
from v0.1: the catalogue-resolution document, model catalogue, provenance exports,
and provenance envelope implementation.

v0.2 source commit:
`ed725f6c578717b61e855d694a0c450b431f183f`

v0.2 aggregate SHA-256:
`25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294`

The v0.1 manifest is preserved separately. Runtime verification on Plato, including
the complete research suite and Case 3 readiness tests, is still required before
Phase 7 is re-closed and a new preservation ref is created.


## Phase 7 v0.2 runtime re-freeze closure — 2026-10-14

Plato verification completed successfully for the Case 3-controlled Phase 7 v0.2
re-freeze.

Verified runtime evidence:

- Phase 8 preflight regression: 11/11 passed;
- complete research suite: 103/103 passed;
- Case 3 MAF readiness suite: 9/9 passed;
- Case 3 provenance decisions: EXECUTE for valid winter-wheat RGB, CLARIFY for
  missing modality, ABSTAIN for wrong species, ABSTAIN for non-RGB modality;
- model catalogue contains only the verified full-FT Case 3 checkpoint for image
  classification;
- v0.1 archive aggregate preserved as
  `337764f319c33d3b3bb38dc2f4c64f214f0868398a139406f9d2cd0b92d42c9f`;
- v0.2 active aggregate verified as
  `25a6865458f29d5a91000de0cbca3dea8c1773cca8701af5f50f155205a6a294`;
- dependency health clean;
- bounded secret scan returned no matches;
- final repository state matched the experiment branch with no tracked changes.

Phase 7 v0.2 is therefore re-closed. Case 3 checkpoint access/callability and the
scientific-capability provenance correction are complete. The unavailable historical
prepared dataset remains a separate exact-training-reproduction limitation and does
not reopen the verified checkpoint/runtime gate.


## Phase 8A offline runtime-control capture — 2026-10-14

The post-Phase-7-v0.2 offline runtime-control capture completed successfully on Plato
without reading an API key and without executing any outcome-bearing scientific run.

Verified runtime evidence:

- Phase 7 v0.2 freeze verifier: pass, 22 frozen files;
- Phase 8 preflight regression: 12/12 passed;
- complete research suite: 104/104 passed;
- provider candidate: `OpenRouter->openai`;
- primary model candidate: `openai/gpt-5.6-luna`;
- provider-managed revision label:
  `openrouter-release-2026-07-09-provider-managed`;
- seed schedule: 2026, 2027, 2028;
- temperature parameter transmitted: false;
- prompt-bundle SHA-256:
  `386764c3a6c5afff140c404ee98eaa2626a04f20b784cae168c65bf7766eff0f`;
- tool-catalogue SHA-256:
  `72f217660486f54a2a53028c316287837f36dac057a1b844ac93d5b4c59484fe`;
- task-manifest SHA-256:
  `827c6ff2bb703f41c04174f8dbca755308cb1f22195242a22e414561e89d0bf0`;
- package-lock SHA-256:
  `2c67b0b895b81a482c148512ee5ab0de23e333bd21a4d44c31061e2fb19a6391`;
- runtime-controls candidate SHA-256:
  `85acd6efd5ae880051548977355f05d6bdd5e048c365a945a512378023355ce1`;
- API key read: false;
- outcome-bearing work performed: false.

The generated candidate remains explicitly
`CANDIDATE_PRE_OUTCOME_PENDING_SUPERVISOR_CONFIRMATION`. It is evidence of a
prospectively controlled pre-outcome state, not final approval of the provisional
provider/model plan. The generated runtime candidate and package lock should now be
committed as immutable evidence before any supervisor-driven provider/model change or
live preflight.


## Phase 8A offline evidence preserved — 2026-10-14

The exact offline runtime-control candidate and package lock were verified locally,
committed, and pushed at commit
`2c9717acf479191935fc0f19a980b66d813edfa5`.

Preservation ref:
`baseline/phase8a-runtime-candidate-20261014`

The preserved candidate remains pre-outcome and pending supervisor confirmation. It
records no API-key access and no outcome-bearing scientific work. The Phase 7 v0.2
freeze remains the governing scientific-method baseline.

At this point the offline Phase 8A preparation path is complete. The next live gate is
supervisor/provider confirmation followed by the already-committed non-scientific
OpenRouter/MAF echo-tool preflight. Scientific benchmark execution remains prohibited
until that live infrastructure preflight passes and the provider/model route is
confirmed.


## Phase 8B access and cost gate opened — 2026-11-19

The researcher reports receiving an OpenRouter API key with $9 credit.
The key has **not** been pasted into chat or repository. On 2026-11-19, Plato
verified authenticated key metadata, both exact study model IDs, current
catalogue pricing and a $6.2120448 estimated pre-outcome qualification pilot
against an $8 planning ceiling; targeted offline tests passed 17/17. No
paid MAF tool call or scientific outcome has occurred. The key's reported
$50 remaining spending cap is not the account balance, which remains the
researcher's unverified $9 estimate. Credential possession and successful
metadata authentication do not establish supervisor approval of the
provider/billing/model route.

Pre-outcome tooling committed without modifying the frozen Phase 7 method:

- `scripts/research/check_phase8_openrouter_budget.py` reads only the key
  metadata and model catalogue (GET requests, no completion/inference call);
- `tests/research/test_phase8_budget_preflight.py` covers catalogue ID/price
  validation, the $9 illustrative budget, overspend refusal, and secret-safe
  source constraints;
- `docs/research/PHASE8B_ACCESS_AND_BUDGET_RUNBOOK_20261119.md` contains
  exact, interactive-secret-safe Plato steps, ending at the single existing
  non-scientific MAF/OpenRouter echo-tool preflight.

Live authenticated catalogue prices on 2026-11-19: Luna $0.20/$1.20 and
Sol $4.00/$20.00 per million input/output tokens. Based on 4,000 input and
up to 2,048 output tokens for each of at most two model roundtrips, the
estimated 12-scenario Luna qualification and 4-scenario Sol subset is
$6.2120448, not measured cost or a guarantee. Reserve at least $1, and do not launch the full Sol
breadth programme on this balance without actual call-cost evidence.

**Evidence-weighted scores unchanged:** overall 51%; Phase 8 20%; 6/9 fully
closed. No scientific Phase 8 outcome yet exists.


## Phase 8 live echo first attempt — parameter routing failure (2026-11-19)

The first paid-capable but **non-scientific** MAF/OpenRouter echo
preflight was attempted on Plato using the existing strict provider
configuration and returned HTTP 404, `failed_routing_step=Filter by
Parameters`. OpenRouter reported 8 initial endpoints, reduced to 5
after region filtering and 3 after tier filtering, then no endpoint
supported the request's full parameter set. Exact offending
parameter is not yet known. No successful echo result or scientific
outcome exists; do not count this as a passed preflight.

To avoid guessing or weakening `require_parameters=true`, a
read-only capability diagnostic and its offline regression tests
were added:

- `scripts/research/diagnose_phase8_openrouter_routing.py`
- `tests/research/test_phase8_routing_diagnostic.py`

The diagnostic inspects authenticated model catalogue parameters
and per-provider endpoint capability metadata where the key has
permission. It performs no paid generation, changes no frozen
method file, and prints no credential. Preserve the failed attempt
and inspect the diagnostic results before any new paid call.
The existing provider/model/runtime study settings remain provisional
pre-outcome; any necessary modification must be versioned explicitly.

**Scores unchanged:** overall 51%; Phase 8 20%; 6/9 closed.


## Phase 8 live routing capability inspection — 2026-11-19

Plato fetched the read-only diagnostic and passed 16/16 targeted tests.
Authenticated endpoint metadata showed that the three OpenAI-tagged
Luna endpoints (`openai`, `openai/flex`, `openai/fast`) advertise
`tools`, `tool_choice`, `seed`, `reasoning`, and `max_tokens`,
but **not** `parallel_tool_calls`. The model-level supported-parameter
list also omits `parallel_tool_calls`.

Hypothesis, not yet verified: MAF may emit `parallel_tool_calls=false`
from `allow_multiple_tool_calls=False` and OpenRouter strict parameter
filtering rejects it. To establish the true request body without paying
for another inference or exposing credentials, a local
`httpx.AsyncClient.send` interception with a synthetic key and
blocked sockets was added:

- `scripts/research/capture_phase8_maf_request_shape.py`
- `tests/research/test_phase8_request_shape_capture.py`

The next Plato task is to pull the experiment branch, run the offline
capture regressions, and inspect the safe control-key report. No frozen
scientific-method file is modified, no further paid echo attempted, and
no scientific outcome is claimed.

**Scores unchanged:** overall 51%; Phase 8 20%; 6/9 fully closed.


## Phase 8 preflight 404 exact request diagnosis and compatibility remedy — 2026-11-19

Plato passed 16/16 offline wire-request capture tests. The captured
non-scientific MAF 1.11.0 request had both
`max_completion_tokens=512` and `parallel_tool_calls=false`.
OpenRouter's OpenAI-tagged Luna endpoints advertise neither field,
but do advertise `max_tokens` and the other transmitted controls.

An isolated fail-closed HTTP compatibility adapter was committed outside
the 22 frozen Phase 7 v0.2 scientific-method files. It translates
`max_completion_tokens` to `max_tokens` without altering the numerical
ceiling and omits `parallel_tool_calls` only when false, while keeping
the model, single-tool application limit, strict OpenAI provider pin,
retries, seed, reasoning and messages unchanged. The actual MAF
preflight now injects the adapter through an `AsyncOpenAI` client,
and the offline HTTP capture intercepts **after** the adapter.

New tests include a real MAF no-network post-rewrite capture and
negative-path rejection of changed model, provider, ceiling, seed,
reasoning, temperature, or enabled parallel tool calls. Isolated
adapter tests passed 14/14 in the authoring environment, but the
actual Plato integration suite and corrected live paid echo are
**not yet verified**.

Next: pull experiment branch; run targeted Plato tests and the
no-network post-adapter capture. Only if both pass, run a single
approved, non-scientific paid echo preflight. Then preserve the new
final pre-outcome runtime freeze before any scientific evaluation.

**Scores unchanged:** overall 51%, Phase 8 20%, 6/9 fully closed.


## Phase 8 corrected MAF preflight offline gate closed — 2026-11-19

On Plato the researcher fast-forwarded to `c52b2ab`,
ran the exact targeted compatibility/transport/preflight suite
(**32/32 passed**), and captured the real installed MAF
post-adapter request without paid inference.

Verified controls:
`max_tokens=512`, `max_completion_tokens` absent,
`parallel_tool_calls` absent, `seed=2026`,
`reasoning.effort=medium`, `tool_choice=required`,
`provider.order=[openai]`, `allow_fallbacks=false`,
`require_parameters=true`, one tool advertised.
Markers:
`PHASE8_WIRE_SHAPE_PAID_INFERENCE=false`,
`PHASE8_WIRE_SHAPE_OUTCOME_BEARING=false`,
`PHASE8_WIRE_SHAPE_CAPTURE_PASS=true`.

The offline parameter-compatibility failure is now resolved
under Plato's installed SDK. **A paid live echo has not yet
succeeded and no scientific Phase 8 result exists.**
Next action: approved single non-scientific live echo, then
final runtime freeze before outcome-bearing experimental runs.
The frozen Phase 7 v0.2 method is unchanged.

**Scores remain:** overall 51%, Phase 8 20%, 6/9 fully closed.


## Phase 8 live MAF/OpenRouter preflight PASS — 2026-11-19

The researcher re-entered the API key securely in the Plato shell and
executed the bounded, non-scientific MAF echo-tool preflight.
Its output confirmed all required markers:
`PHASE8A_LIVE_PREFLIGHT_MODEL=openai/gpt-5.6-luna`,
`PHASE8A_LIVE_PREFLIGHT_TOOL_CALLS=1`,
`PHASE8A_LIVE_PREFLIGHT_PROVIDER_PIN=openai`,
`PHASE8A_LIVE_PREFLIGHT_PROVIDER_FALLBACKS=false`,
`PHASE8A_LIVE_PREFLIGHT_SEED=2026`,
`PHASE8A_LIVE_PREFLIGHT_TEMPERATURE_SENT=false`,
`PHASE8A_LIVE_PREFLIGHT_COMPAT_ADAPTER=enabled`,
`PHASE8A_LIVE_PREFLIGHT_OUTCOME_BEARING=false`, and
`PHASE8A_LIVE_OPENROUTER_MAF_PREFLIGHT_PASS=true`.
`PHASE8A_LIVE_PREFLIGHT_SYSTEM_FINGERPRINT=<none>`.

The live infrastructure gate **passed**, but this is not outcome-bearing
scientific evidence; no measured API usage was returned. A machine-readable
record captures the researcher-reported terminal evidence without
credentials at
`experiments/ijcai2027/runtime/live_preflight_evidence_20261119.json`.

The October offline runtime candidate and Phase 7 v0.2 scientific method
remain unchanged. A new pre-outcome runtime-v0.3 candidate preparation
script and tests were committed with strict evidence, package-lock,
source-hash and method-hash checks. It cannot silently overwrite
the October candidate. An attested supervisor-approved provider and
model route plus preserved verified v0.3 runtime controls and adoption
of the same compatibility adapter in the *scientific* harness remain
required before the first outcome-bearing trial.

**Completion scoring still 51% overall, Phase 8 20%, 6/9 fully closed.**
A live infrastructure success does not by itself justify credit for
unfinished experimental evaluation.


## Phase 8 v0.3 candidate pushed; C3/C4/C8 qualification matrix prepared (2026-11-19)

On Plato the researcher verified the generated v0.3 candidate SHA-256
`e3a8826b8942f2b0951775b557ce3530b2a54ed7666e827e3687443974718c12`,
committed **only** that generated candidate as commit `09ebaec`,
and pushed `experiments/ijcai2027`. GitHub independently confirmed
`09ebaec` as the branch head at the time and verified the file exists.
The candidate remains **pending supervisor provider/billing/model approval**,
with `scientific_execution_permitted=false`.

The next offline preparation is now committed as
`scripts/research/prepare_phase8_qualification_matrix.py` plus
`tests/research/test_phase8_qualification_matrix.py`. This plans an
exact **12-case × 3-condition × 3-seed = 108-trial** qualification
matrix for C3, C4 and C8, using the predeclared Luna model and
seed schedule. It does not read credentials, open gold labels,
send inference calls or change the frozen method.

**Leakage safeguard:** `BenchmarkScenario` contains category, shift
and scenario identifiers that could betray the expected decision.
The planner computes a separate allowlisted model-visible context
and permits only scientific request, requested capability ID and
training readiness. Scenario IDs and split labels are internal-only
trial metadata; no gold labels are loaded.

This matrix is **harness qualification only**, not a real-shift
benchmark or a successful scientific pilot. The actual C3/C4/C8
scientific model/tool runner, condition isolation, measured cost,
raw results and hidden evaluation remain to be built and validated.
See `docs/research/PHASE8C_QUALIFICATION_HARNESS_READINESS.md`.

**Scores unchanged:** 51% overall, Phase 8 20%, 6/9 phases fully closed.


## Phase 8 qualification matrix generation verified on Plato — 2026-11-19

Plato pulled the `b511bea` planning code, passed **27/27** offline
tests, and generated the 12-case / 108-trial C3/C4/C8 × 3-seed
qualification matrix. Exact output SHA-256:
`8a9688aa464564bf99121656430ea09fc93bbf2b1d262a73a9b2276944876692`.

The file was **untracked locally at last observation**, not yet
committed/pushed. An independent verifier and its tests have since
been added to `experiments/ijcai2027` to pin the reported SHA
and rederive all entries while prohibiting gold-label leakage and
false scientific-execution claims.

No scientific trial was run. The $0.7036416 estimate covers only
assumed Luna manager roundtrips; genuine C4 generic-Critic calls and
other costs are additional. The existing MCP v2 adapter covers the
calculator/ANOVA/Tukey parity slice but does not yet constitute the
real scientific vision-model dispatcher for the full experiment.

The user must pull the verifier, run it on the unchanged generated
JSON, and commit/push only that file. Subsequent work is building
isolated C3/C4/C8 execution with matching MCP tool semantics and
verified scoring/usage capture. Supervisor approval remains
undocumented. **Scores unchanged: 51% overall; Phase 8 20%; 6/9 closed.**


## Phase 8C matrix preserved; append-only attempt accounting added (2026-11-19)

The qualification matrix was independently reverified on Plato:
**18/18 tests passed**; 108 trial identities, no gold read/no API
calls, exact SHA-256
`8a9688aa464564bf99121656430ea09fc93bbf2b1d262a73a9b2276944876692`.
The researcher committed and pushed the **single** matrix file as
commit `97c8db2`. The remote GitHub branch and file were checked
and found at that commit.

New `scripts/research/phase8_attempt_ledger.py` and corresponding
offline tests introduce an append-only, duplicate-rejecting,
single-trial-at-a-time attempt journal and fail-closed handling of
missing provider billing/usage data. The budget gate uses a $8
software ceiling plus prospective per-trial reserve; it is not a
substitute for a provider-side hard cap. The current candidate
explicitly blocks all scientific calls. The ledger does NOT execute
scientific tools or call an LLM. Plato must still run its new tests.

Separate unclosed issue: the current MCP v2 implementation proves
the calculator/ANOVA/Tukey parity slice, not a full scientific
vision-model invocation/authorization boundary. Implement and test
that boundary and genuinely distinct C3/C4/C8 execution before
any scientific results are claimed. Provider/model approval is
not attested.

**Scores unchanged:** 51% overall; Phase 8 20%; 6/9 fully closed.


## Phase 8 ledger gate PASS and offline C3/C4/C8 separation rehearsal — 2026-11-19

The user pulled `d6d0c82` on Plato and passed **33/33** targeted
offline tests in 0.27 seconds. Ledger output confirmed 108 registered
trials, an $8 software cost ceiling, no gold-label reads, no
provider calls, and `PHASE8_LEDGER_PREFLIGHT_PASS=true`.
`PHASE8_LEDGER_APPROVED_TO_RUN=false` is intentionally correct because
the pre-outcome runtime candidate still prohibits scientific execution.

The experiment branch now includes
`scripts/research/phase8_condition_rehearsal.py` and
`tests/research/test_phase8_condition_rehearsal.py`, a separate
OFFLINE simulated condition-isolation rehearsal. It instantiates
C3 with no SOE verifier, C4 with an explicit separate generic-Critic
callback (mocked in tests), and C8 with the real deterministic SOE
resolver and injected post-execution validator. All three use the
same narrowly allowlisted case facts. It rejects leaked gold,
scenario category, internal ID, split and shift information.

The staged rehearsal has **not yet been tested on Plato**.
Any scripted unsafe attempt, correction or rejected mock output
from its unit tests is *not a real LLM outcome*. The actual real
C4 LLM critic, provider-backed MAF manager, verified full scientific
MCP model dispatcher and measured billing integration are still
required. The earlier three-tool parity MCP v2 bridge cannot be
substituted for scientific model execution.

**Scores unchanged:** overall 51%, Phase 8 20%, 6/9 phases closed.


## Phase 8 condition rehearsal verified; scientific MCP adapter prepared (2026-11-19)

Plato successfully ran the C3/C4/C8 condition-isolation
rehearsal after pulling `ad694f1`: **34/34 tests passed**,
three simulated executions, identical base-request hash
`da9f9cf2696e23f6249e417779792d5dfe9dbe75fe9ddf69cac735df311473c0`.
Its explicit markers correctly confirm no real generic-Critic
LLM, no scientific model execution, no provider calls or outcome-bearing
scientific evaluation.

New pre-outcome scientific MCP integration code exists at
`phenoassistant_mcp/scientific_inference_v1.py`, with
`tests/research/test_phase8_scientific_mcp.py`.
It exposes a bounded real MCP scientific tool whose production delegate
calls canonical PhenoAssistant instance-segmentation or classification
functions only after verifying a SHA-256-pinned final approved runtime;
images must be explicitly authorized by opaque ID, source-file SHA and
existence. Model-provided paths/checkpoints/GPU configuration are forbidden,
and output artifacts are hashed. The real MCP-protocol tests use
synthetic local approval and injected FAKE inference only; no genuine
scientific inference has been performed through this new adapter.
The module has **not yet been tested on Plato**.

Remaining critical work: test scientific MCP adapter on Plato, bind
reviewed real image fixtures, integrate genuine live Luna Manager and
generic LLM Critic, preserve identical MCP tool semantics for matched
conditions, apply C8 pre/post checking to actual tool outputs,
integrate provider-metered cost traces, obtain documented approvals,
freeze an approved runtime, and only then perform outcome-bearing
trials. The 12-case qualification matrix and 108 planned trials
remain unexecuted.

**Scores unchanged:** 51% overall, Phase 8 20%, 6/9 phases closed.


## Phase 8 scientific MCP passed; real MAF proposal and generic-Critic SDK wiring (2026-11-19)

Plato pulled `63360dc` and passed **36/36** offline scientific MCP,
condition and attempt-ledger tests in 5.98 seconds. The worktree was
clean. This validates actual MCP client/server protocol and the
provenance-bounded tool schema using **fake** vision inference, but
no GPU execution or scientific outcomes.

New `scripts/research/phase8_maf_decision_v1.py` and
`tests/research/test_phase8_maf_decision_v1.py` are now committed
to the experiment branch. They implement real MAF/OpenAI SDK proposal
client construction through the already verified OpenRouter
compatibility transport; C3/C4 exact same Manager prompts; C8-only
SOE exposure; and a distinct C4 generic Critic LLM request without
scientific-envelope/gold information. The client is impossible to
construct against the historic unapproved v0.3 candidate. Its tests
use a fake HTTP provider and a synthetic temporary approved record.
These new tests have **not yet been verified on Plato**.

The interface currently produces **typed proposals** and does not
invoke native LLM tool calls, GPU vision models or the scientific
MCP dispatcher. Real provider output, model/seed drift, per-call
usage and provider-billed charges remain to be checked. No
outcome-bearing experimental call is authorized, and supervisor
approval of the credential/provider/billing/model route remains
unconfirmed. Full scientific runner/harness and real protected
fixtures are still outstanding.

**Scores unchanged:** overall 51%, Phase 8 20%, 6/9 fully closed.


## Phase 8 MAF mocked-provider failure isolated and fixed in code (2026-11-19)

Plato pulled `ed6ada2` and ran the no-charge MAF/MCP/condition tests:
**48 passed, 1 failed**. The failed real MAF SDK mock-provider test
did not reach its fake OpenRouter transport because the compatibility
adapter required a tool_choice even for a tool-free Manager/Critic
proposal. The SDK wrapped the local validation exception into
`APIConnectionError` / `ChatClientException`. Separately, executing
the CLI directly exposed a repo import that preceded the project-root
`sys.path` insertion.

A narrow pre-outcome compatibility update now permits omitted/null
`tool_choice` only when **no tools are supplied**. Tool-enabled
requests still require an explicitly allowed choice, and no-tool
requests cannot enable native tool calls. The direct-script import
order is repaired. New regression tests cover this distinction and
run the CLI as an independent subprocess without an API key.

**The corrected tests remain unverified on Plato**. No paid inference
or scientific results were produced by the failing run; the
historical 22-file scientific method and v0.3 runtime candidate
remain unchanged. Next: pull branch, rerun offline MAF SDK, adapter,
scientific MCP and condition tests; verify direct CLI status. The
approved final runtime still requires separate source hashing and
supervisor/provider-route attestation before scientific execution.

**Scores unchanged: 51% overall, Phase 8 20%, 6/9 closed.**


## Phase 8 MAF request repair verified; mediated C3/C4/C8 MCP bridge staged — 2026-11-19

Plato successfully pulled `277c320` and passed **77/77** targeted
MAF/OpenRouter transport, scientific MCP and condition-isolation tests.
The direct MAF decision CLI confirmed no provider calls, no Critic
inference and no scientific execution, with
`PHASE8_MAF_DECISION_OFFLINE_PREFLIGHT_PASS=true`, and the worktree
was clean. The previous missing tool_choice and early import bugs
are corrected under the pinned environment.

New `scripts/research/phase8_proposal_mcp_bridge_v1.py`
and `tests/research/test_phase8_proposal_mcp_bridge_v1.py`
integrate approved-runtime-gated, model-proposed **typed JSON
decisions** with C4-only independent Critic, C8-only frozen SOE
resolver, and the identical MCP scientific tool protocol for
app-bound image IDs. New test coverage includes full MAF SDK
fake-HTTP → MCP real protocol → fake vision inference, no real
credits or outcomes.

The integration does **not** implement native model function
calling, image-appropriate real post-validation, provider-billed
metering, signed supervisor trust anchor, or the final approved
scientific runner. Test approvals are synthetic. The bridge's
C3/C4 post-validity is recorded as **unassessed/null**, never
automatically marked unsafe from absence of C8 validation.

These new bridge tests have **not yet run on Plato**; this commit
does not advance scientific effectiveness evidence or authorize
paid trials. Supervisor credential/billing/model approval remains
unverified; the 108 planned scientific trials remain unexecuted.

**Scores remain 51% overall, Phase 8 20%, six of nine phases closed.**


## Phase 8: 87/87 MAF/MCP bridge tests passed, output-specific C8 checks staged (2026-11-19)

Plato passed **87/87** offline MAF-to-MCP bridge tests after pulling
`726cefe`. The CLI confirmed 108 planned trial identities, zero
real provider calls, zero scientific dispatch from the CLI, no native
model tool calling, and `PHASE8_BRIDGE_OFFLINE_PREFLIGHT_PASS=true`.
The working tree was clean. These are infrastructure results only.

Canonical source review exposed an important potato-branch mismatch:
`functions/leaf_only_sam.py` emits
`leaf_only_sam_results.json` whereas the new common MCP dispatcher
had wrongly expected `ins_seg_results.json`. The dispatcher now
selects the correct canonical file per capability. Its first tool
invocation also atomically claims the trial directory, prohibiting
a second model/image invocation within the same trial even if the
capability differs.

New output-specific validation in
`scripts/research/phase8_scientific_artifact_validator.py`
and tests check real COCO/CSV artifact contracts, scientific file
binding and checksum, pixel-area/confidence ranges, class scope,
trusted source-image identity, and derivation of leaf count and
predicted area for the existing frozen Phase 7 phenotype invariants.
C8 can now receive this real file-based post-validator via
`bridge_one_with_real_artifact_check`. C3/C4 remain unassessed
by C8-specific validation. All source files and tests are committed
but the **new tests have not yet run on Plato**.

Remaining critical gate: this mediated JSON proposal path is not
native model tool calling; no actual reviewed image data, GPU
scientific inference, measured billing, independently trustworthy
supervisor approval, final runtime seal or outcome-bearing
comparisons exist yet. Do not infer biological correctness from
COCO/CSV structural validation.

**Scores unchanged: 51% overall; Phase 8 20%; 6/9 phases closed.**


## Phase 8 scientific output validation PASS; real execution approval hardening (2026-11-19)

Plato pulled `e0319ff` and ran the expanded scientific
COCO/CSV post-validation, MAF/OpenRouter adapter, real MCP
fake-inference, and condition-bridge integration tests: **105/105
passed in 5.22 seconds**. The direct bridge CLI confirmed the
108 planned trials, zero real provider calls, zero scientific
dispatch, no native tool calling and scientific execution denied.
The worktree was clean. No real GPU science or measured model
performance resulted.

Subsequent source review uncovered an approval trust-boundary gap.
Previously an arbitrary caller-produced self-attested JSON plus
its own matching SHA-256 could pass the runtime file verifier,
because checksum integrity was mistaken for supervisor approval.
This has been addressed by requiring a **separate pinned final
runtime digest** for default real OpenRouter and canonical GPU
entry points; the independent pin is deliberately `None`
(pending actual supervisor approval). Fake HTTP transport and
fake vision delegates preserve offline testing but are not
production authorisation. Negative-path tests were added for
untrusted synthetic approvals. The bridge CLI's C8 validator
marker was corrected to
`offline-tests-passed-real-GPU-unverified`.

The new trust-gate tests are **not yet tested on Plato**. The
current change does not sign a runtime, establish billing/model
approval, implement native model tool-call capture, bind real
per-case images, run GPUs or produce scientific benchmark results.
The previously committed 108-trial matrix and Phase 7 v0.2
method digest remain unchanged.

Next: run the updated offline suite and direct bridge CLI on
Plato, confirm denial of self-declared production approval,
then continue to native function-call capture, real fixture
binding, provider-metered append-only trial execution and
independent scoring. **Scores unchanged: overall 51%,
Phase 8 20%, 6/9 fully closed.**


## Phase 8: approval trust gate 109/109 PASS, image-fixture registry staged (2026-11-19)

Plato pulled `067e69f`, passed **109/109** offline tests in
5.14 seconds, and confirmed direct MAF-to-MCP bridge preflight.
No real OpenRouter calls, GPU dispatch or outcome-bearing trials
occurred; the historical method and 108-trial qualification matrix
remain preserved.

The next source and tests,
`scripts/research/phase8_image_fixture_registry.py` and
`tests/research/test_phase8_image_fixture_registry.py`, now bind the
frozen 12 scenario IDs to **unapproved private image slots** with the
exact model-visible request fingerprints from the preserved matrix.
They require real decodable images under an explicitly trusted root,
SHA-256 integrity, reviewed species, source dataset/image IDs,
license/access and reviewer evidence, and independent provenance
approval. Source paths and reviewer records are kept in Git-ignored
`data/_staging/`, not exposed to the Manager or Critic. A standalone
registry generated by a researcher plus its own hash is NOT sufficient
to enable real experiments. Its independent SHA pin is intentionally
unset. The tests are newly committed and not yet verified on Plato.

At this stage the **full experimental result is still absent**.
Native MAF tool-call capture (rather than mediated text-JSON
proposals), actual real-image review, physical GPU checkpoint
integrity, provider-billed attempt logs, independent supervisor
provider/billing/model approval and final source-hashed runtime
are still incomplete.

**Scores unchanged: overall 51%, Phase 8 20%, 6/9 phases closed.**
