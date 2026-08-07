# MAF Case 1 Notebook

## Purpose

`case1_maf.ipynb` migrates the CPU analytical portion of the original AutoGen `case1.ipynb` to the production Microsoft Agent Framework application.

The original notebook remains unchanged. The migrated workflow reuses the tracked Arabidopsis phenotype table:

```text
results/Case1/aracrop_phenotypes.csv
```

This keeps the CPU migration scientifically reproducible while image segmentation and pipeline execution remain separate GPU/bounded-execution milestones.

## Original-task mapping

| Original Case 1 task | MAF status |
| --- | --- |
| Task 1: image segmentation and phenotype extraction | Deferred to GPU migration; notebook resumes from the tracked phenotype CSV |
| Task 1.1: save executed `ara_crop_pipeline` | Deferred until bounded pipeline persistence is migrated |
| Task 1.2: list reusable pipelines | Deferred until the read-only pipeline discovery tool is migrated |
| Task 1.3: execute saved pipeline | Deferred to allowlisted/bounded GPU pipeline execution |
| Task 2: longitudinal mean/STD plots | Migrated through `plot_longitudinal_phenotypes` |
| Task 3: rank ecotypes by PLA | Migrated through `rank_ecotypes_by_phenotype` |
| Task 4: ANOVA + Tukey-Kramer | Migrated through `analyse_repeated_measures_with_posthoc` |
| Task 5: Phenotiki/RAG comparison | Deferred until a production retrieval capability is registered |

The Task 3 migration ranks from the underlying trusted phenotype table instead of inferring numeric order from the rendered plot. This preserves the scientific question while removing an unnecessary multimodal interpretation step.

## Production MAF profile

The notebook opts into the Case 1 application profile by binding:

```text
case1_data_path=results/Case1/aracrop_phenotypes.csv
case1_output_dir=results/maf_case1
```

The trusted paths are supplied by application construction, not by the language model.

The Case 1 profile adds:

```text
plot_longitudinal_phenotypes
rank_ecotypes_by_phenotype
analyse_repeated_measures_with_posthoc
```

to the existing production tool set. The Manager retains its exactly-one-tool-call policy.

## Run from a clean session

Activate the validated environment:

```bash
conda activate /workspaces/.phenoassistant-runtime/conda-envs/phenoassistant-maf-poc
```

Set OpenRouter configuration:

```bash
export OPENROUTER_API_KEY="your-key"
export OPENROUTER_MODEL="openrouter/free"
```

Then launch:

```bash
jupyter lab case1_maf.ipynb
```

Restart the kernel and run every cell in order.

## Expected scientific evidence

For the tracked 1,248-row Case 1 dataset:

```text
ecotypes = 5
time points = 52
grouped longitudinal rows per phenotype = 260

PLA ranking:
ein2 > col0 > adh1 > pgm > ctr

time-ecotype interaction:
F = 22.6669360372141
P = 2.3834021910781097e-262
interaction threshold = 0.01

Tukey-Kramer comparisons = 10
post-hoc threshold = 0.05

evidence-supported PLA groups:
large  = col0, ein2
medium = adh1, pgm
small  = ctr
```

Expected generated files:

```text
results/maf_case1/leaf_count_plot.png
results/maf_case1/leaf_count_stats.csv
results/maf_case1/pla_plot.png
results/maf_case1/pla_stats.csv
results/maf_case1/plant_diameter_plot.png
results/maf_case1/plant_diameter_stats.csv
results/maf_case1/plant_perimeter_plot.png
results/maf_case1/plant_perimeter_stats.csv
```

## Current scope boundary

The notebook does not import `extracted_pipelines.py` or expose the legacy generic reproducible-pipeline executor. Those paths have heavy vision/legacy side effects and an arbitrary-code execution boundary.

The remaining full Case 1 migration work is intentionally separated into:

- GPU-backed image segmentation and phenotype extraction;
- read-only canonical pipeline discovery;
- allowlisted/bounded pipeline execution;
- production RAG/literature retrieval for the Phenotiki comparison.
