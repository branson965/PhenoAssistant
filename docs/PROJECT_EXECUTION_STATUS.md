# PhenoAssistant MAF + MCP + Research Execution Status

**Updated:** 2026-10-08  
**Active branch:** `feature/maf-mcp-v2-integration`  
**Current phase:** Phase 5 — GPU scientific baseline

## Progress model

100% means a fully integrated, GPU-validated PhenoAssistant implementation using the agreed MAF/MCP architecture, accompanied by rigorous comparative evaluation, a defensible research contribution, reproducible experiments, and a submission-ready paper/artifact.

| Phase | Mission | State |
|---|---|---|
| 1 | Preserve and understand original AutoGen baseline | complete |
| 2 | Build bounded production-shaped MAF CPU architecture | complete |
| 3 | Migrate and validate CPU case-study behaviour | complete |
| 4 | Audit Vincent MCP branch and freeze integration contract | complete |
| 5 | Execute and validate GPU scientific workflows | active |
| 6 | Migrate MCP to v2, integrate with MAF, prove parity | pending |
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
- 16-image bounded Case 1 GPU sample completed successfully in 4.908 s with 106 segmentation annotations.

## Phase 5 evidence still required

- real Nottingham CUDA environment capture;
- allocate a free Nottingham GPU outside the saturated `ada24/petra` snapshot;
- real Nottingham CUDA environment capture inside the allocation;
- Case 1 full 1,248-image inference;
- Case 1 full 1,248-image inference;
- phenotype regeneration;
- regenerated-vs-historical comparison;
- Case 3 approved image discovery;
- Case 3 registered-checkpoint GPU inference;
- explicit evidence-backed decision on whether retraining is necessary.

## Current progress

**Overall completion: 44%**

**Current phase completion: 68%**

**Phases completed: 4/9**

The percentage is intentionally conservative. Data, environment, checkpoint access, CUDA execution, one-image smoke, and a 16-image Case 1 sample are now verified. The remaining Case 1 gate is the full 1,248-image run, phenotype regeneration, and scientific comparison; Case 3 remains an explicit access-controlled resource boundary.
