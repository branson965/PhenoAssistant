# PhenoAssistant MAF + MCP + Research Execution Status

**Updated:** 2026-10-08  
**Active branch:** `feature/maf-mcp-v2-integration`  
**Current phase:** Phase 6 — MCP v2 + MAF integration (Phase 5 Case 3 external gate carried forward)

## Progress model

100% means a fully integrated, GPU-validated PhenoAssistant implementation using the agreed MAF/MCP architecture, accompanied by rigorous comparative evaluation, a defensible research contribution, reproducible experiments, and a submission-ready paper/artifact.

| Phase | Mission | State |
|---|---|---|
| 1 | Preserve and understand original AutoGen baseline | complete |
| 2 | Build bounded production-shaped MAF CPU architecture | complete |
| 3 | Migrate and validate CPU case-study behaviour | complete |
| 4 | Audit Vincent MCP branch and freeze integration contract | complete |
| 5 | Execute and validate GPU scientific workflows | blocked only on external Case 3 private-resource access; Case 1 closed |
| 6 | Migrate MCP to v2, integrate with MAF, prove parity | active |
| 7 | Implement/freeze scientific-applicability research method | pending |
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

## Current progress

**Overall completion: 55%**

**Current phase completion: 94%**

**Phases completed: 4/9**

The percentage is intentionally conservative. Case 1 GPU scientific reproduction is fully closed under the restored declared environment. The remaining Case 3 gate is externally blocked on the exact historical private artefacts, so it is carried forward without being counted as reproduced. Phase 6 can proceed independently.
