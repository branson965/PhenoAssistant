# PhenoAssistant MAF + MCP + Research Execution Status

**Updated:** 2026-10-10  
**Active branch:** `research/phenoguard`  
**Current phase:** Phase 7 — scientific-applicability research method (Phase 5 Case 3 external gate carried forward)

## Authoritative venue strategy

The current paper plan is **IJCAI 2027**, not AAMAS 2027.

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
| 7 | Implement/freeze scientific-applicability research method | active |
| 8 | Full experiments, ablations, hidden evaluation, failure analysis | pending |
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

**Overall completion: 74%**

**Current phase completion: 64%**

**Phases completed: 5/9**

Case 1 GPU scientific reproduction remains fully closed and the remaining Case 3 gate
is externally blocked. Phase 6 is now closed with direct/MCP scientific parity,
production-shaped MAF -> MCP execution, fail-closed errors, explicit timeout/lifecycle
semantics, and cold/warm interface-overhead evidence. Phase 7 must now implement and
freeze the scientific-applicability method on a separate research branch without
polluting the frozen migration interface.


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

- corrected the only active research-document reference that still named the obsolete
  AAMAS benchmark; the authoritative target is IJCAI 2027;
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
- ten Phase 7F benchmark-contract tests are committed but not runtime-verified until
  they execute on Plato.
