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

## Phase 5 completed preparation

- secret-safe GPU environment probe;
- lightweight data/repository preflight;
- Case 1 one-image/full GPU runner;
- Case 1 deterministic regenerated-vs-tracked comparator;
- Case 3 bounded inference-only smoke runner;
- static tests locking the GPU-validation contracts;
- generated GPU output directories ignored from Git;
- full Phase 5 validation protocol documented.

## Phase 5 evidence still required

- real Nottingham CUDA environment capture;
- heavyweight import smoke;
- verify all 1,248 Case 1 images are present;
- Case 1 one-image GPU inference;
- Case 1 full 1,248-image inference;
- phenotype regeneration;
- regenerated-vs-historical comparison;
- Case 3 approved image discovery;
- Case 3 registered-checkpoint GPU inference;
- explicit evidence-backed decision on whether retraining is necessary.

## Current progress

**Overall completion: 44%**

**Current phase completion: 20%**

**Phases completed: 4/9**

The percentage is intentionally conservative. Phase 5 preparation is complete enough to execute, but the scientific GPU evidence itself has not yet been produced.
