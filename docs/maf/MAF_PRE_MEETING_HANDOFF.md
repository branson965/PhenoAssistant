# PhenoAssistant MAF Pre-Meeting Handoff

## Status

This document records the independently validated Microsoft Agent Framework
migration state before discussion with Valerio and Vincent.

- Branch: `feature/maf-linux-migration`
- Parent checkpoint before this handoff: `0d84b0b4cf5beb2f58652a40644b8a3f51afcaf6`
- Manager instructions: `phenoassistant-manager-v5`
- Final CPU regression baseline: **168 passed, 2 skipped**
- Original AutoGen notebooks remain preserved.
- Migrated MAF notebooks now exist for demo and Cases 1–3.

This is a CPU-safe migration checkpoint. It does not claim completion of
GPU-dependent vision execution, MCP integration, or the proposed research
contribution.

## Migrated notebooks

| Original | MAF migration | Status |
|---|---|---|
| `demo.ipynb` | `demo_maf.ipynb` | CPU migration complete |
| `case1.ipynb` | `case1_maf.ipynb` | CPU analytical migration complete |
| `case2.ipynb` | `case2_maf.ipynb` | CPU analytical migration complete |
| `case3.ipynb` | `case3_maf.ipynb` | CPU discovery/readiness migration complete |

The original notebooks are retained as provenance and have not been replaced.

## Production MAF architecture

The production path is built around:

1. OpenRouter-backed MAF chat client.
2. MAF Manager with bounded tool profiles.
3. Typed production FunctionTools.
4. Application-side binding of trusted paths and resources.
5. Deterministic Python for scientific computation.
6. Model-driven semantic tool selection.
7. Explicit CPU/GPU and mutation boundaries.

The full CPU profile currently exposes 11 tools:

- `calculator`
- `perform_anova`
- `perform_tukey_test`
- `compare_linear_relationships`
- `query_csv_statistic`
- `plot_longitudinal_phenotypes`
- `rank_ecotypes_by_phenotype`
- `analyse_repeated_measures_with_posthoc`
- `get_pipeline_catalogue`
- `get_model_catalogue`
- `assess_case3_readiness`

The Manager is instructed to choose exactly one registered tool for the
bounded scientific requests validated in the current migration.

## Completed and validated

### Production foundation

- MAF/OpenRouter runtime established.
- Typed scientific adapters implemented.
- Production tool registry implemented.
- Production Manager and application graph implemented.
- Real-provider tool selection validated.
- Legacy AutoGen source remains available for provenance.

### Generic scientific analysis

Validated production capabilities include:

- calculator;
- ANOVA;
- Tukey post-hoc analysis;
- paired linear-regression comparison;
- bounded CSV aggregation/statistics.

Real OpenRouter selection has been demonstrated for multiple production
capabilities rather than only scripted test clients.

### Case 1 — Arabidopsis

CPU-side migration includes:

- longitudinal phenotype plots and statistics;
- ecotype ranking from trusted phenotype data;
- repeated-measures analysis;
- Tukey post-hoc evidence;
- safe read-only pipeline catalogue inspection.

Validated Case 1 evidence includes the significant time–ecotype interaction
and the preserved PLA grouping:

- large: `ein2`, `col0`;
- medium: `adh1`, `pgm`;
- small: `ctr`.

The pipeline catalogue represents the historical pipeline registry without
importing or executing arbitrary legacy generated pipeline code.

### Case 2 — potato phenotype analysis

The migration preserves the tracked 32-row phenotype table as a legacy
resumption artifact and does not claim that MAF regenerated it.

The migrated analytical workflow reproduces:

- manual leaf area versus dried weight:
  - Pearson `r = 0.8910860678113759`;
- projected leaf area versus dried weight:
  - Pearson `r = 0.7576836332304735`.

Manual leaf area therefore has the stronger relationship with dried weight
in the current tracked Case 2 dataset, while projected leaf area still has a
strong positive relationship.

The real OpenRouter Manager selected
`compare_linear_relationships` exactly once for the Case 2 analytical intent.

### Case 3 — winter-wheat image classification

The current repository is represented as a post-training state.

Registered checkpoint:

`fengchen025/winter-wheat_nutri-defi-identify_dndww20_dino2b_lora`

CPU-safe Case 3 migration includes:

- read-only image-classification model discovery;
- training-readiness assessment;
- inference-readiness assessment;
- preservation of the legacy fine-tuning contract;
- supported fine-tuning methods `lora` and `fullft`;
- explicit prevention of model loading, training, upload, or inference in the
  CPU validation phase.

Current repository evidence:

- expected checkpoint registered: true;
- local Case 3 dataset available: false;
- training preconditions satisfied: false;
- registered-model inference preconditions satisfied: true;
- execution status: `gpu_deferred`.

Real OpenRouter validation selected the correct Case 3 tools for model
discovery, training readiness, and inference readiness.

## Safety and provenance decisions

The migration deliberately avoids several unsafe shortcuts.

### Trusted paths are application-side

The model does not choose arbitrary repository data paths or output paths for
the bounded migrated workflows.

### Historical pipeline code is not dynamically executed

`pipeline_zoo.json` is treated as provenance/catalogue data.

The MAF pipeline catalogue does not import or execute
`extracted_pipelines.py`.

### Model discovery is read-only

`model_zoo.json` can be inspected without importing the heavyweight vision
stack or loading model checkpoints.

### Scientific computation remains deterministic

The LLM selects the requested bounded operation.

Python performs the statistical and scientific computation.

The model is required to summarise returned evidence rather than invent
scientific values.

## Explicitly deferred — environment dependent

The following work has not been claimed as complete because the canonical
Nottingham GPU environment is not yet available:

### Case 1

- raw Arabidopsis image segmentation;
- phenotype extraction from source images;
- GPU vision validation;
- vision execution parity.

### Case 2

- potato image segmentation;
- image-to-PLA phenotype extraction;
- regeneration of the phenotype table from raw images;
- GPU vision validation.

### Case 3

- actual model loading;
- winter-wheat training/fine-tuning;
- inference execution;
- CUDA/memory/runtime validation;
- GPU performance benchmarking.

These are deferred validation/execution boundaries, not simulated successes.

## Explicitly deferred — architecture/team decision

### MCP

Vincent's MCP work has intentionally not been ingested before discussion with
him.

Still outstanding:

- identify the authoritative MCP branch/interface;
- agree the integration boundary;
- decide which production tools should use MCP;
- invoke at least one agreed real capability through MCP;
- compare direct versus MCP outputs;
- perform MCP error and parity testing.

No current MAF evidence should be interpreted as MCP validation.

### Case 1 literature/RAG task

The original Case 1 Phenotiki comparison does not currently have a production
retrieval/RAG tool.

The MAF notebook therefore preserves the analytical result but does not
fabricate literature retrieval.

The retrieval source, architecture, and evaluation boundary should be agreed
before implementing it.

### Research contribution

PhenoGuard / the proposed AAMAS-oriented research contribution has not been
started in this migration checkpoint.

That work should begin only after the migration baseline and research
direction are discussed with Valerio.

## Evidence map

Key evidence files include:

- `phase10b-case1-cpu-20260807T003628Z.log`
- `phase10b-case1-live-20260807T010207Z.log`
- `phase10c-pipeline-catalogue-cpu-20260807T105846Z.log`
- `phase10c-pipeline-catalogue-live-20260807T105348Z.log`
- `phase10d-case3-cpu-20260807T152103Z.log`
- `phase10d-case3-live-20260807T150745Z.log`
- `phase10e-case2-cpu-20260807T160923Z.log`
- `phase10e-case2-live-20260807T161521Z.log`
- `phase10e-case2-regression-20260807T161808Z.log`
- `phase10f-case3-notebook-20260807T164500Z.log`
- `phase10f-premeeting-regression-20260807T171139Z.log`

Earlier production-foundation, ANOVA, Tukey, calculator, environment, and
migration evidence remains under `docs/maf/evidence/`.

## Questions for the Valerio / Vincent discussion

The next engineering work should be driven by decisions on:

1. Which Nottingham GPU environment should be treated as the canonical
   validation target?
2. When will GPU/cluster access be available?
3. Which MCP implementation/branch is authoritative?
4. Which MAF capabilities should execute through MCP rather than directly?
5. Is MCP parity required for every tool or only selected representative
   workflows?
6. Should the Case 1 Phenotiki/RAG comparison remain in migration scope, and
   what retrieval source should be authoritative?
7. Which GPU case should be validated first?
8. What research hypothesis and evaluation protocol should follow the
   engineering migration?
9. How should the migration baseline feed into the planned AAMAS work?

## Recommended post-meeting execution order

Subject to supervisor/team agreement:

1. confirm authoritative MCP interface;
2. obtain canonical Nottingham GPU access;
3. validate one bounded MCP path and direct/MCP parity;
4. validate Case 1 and Case 2 vision execution on GPU;
5. validate Case 3 model loading/inference and training contract on GPU;
6. close any agreed RAG/retrieval requirement;
7. run migration-wide parity/evaluation;
8. prepare upstream PR into the agreed `maf` branch;
9. begin the separately agreed research contribution.

## Current stopping point

The independent CPU-side MAF engineering baseline is now suitable for
supervisor/team review.

Further implementation before the meeting risks making assumptions about:

- Vincent's MCP interface;
- the canonical GPU runtime;
- literature retrieval architecture;
- the intended research contribution.

The appropriate next action is therefore review and alignment, not additional
feature implementation.
