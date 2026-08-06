# MAF Demo Notebook

## Purpose

`demo_maf.ipynb` migrates the CPU data-analysis portion of the original AutoGen `demo.ipynb` to the production Microsoft Agent Framework application.

The original notebook remains unchanged. The migrated workflow reuses the tracked dataset:

```text
results/demo/potato_phenotypes.csv
```

This avoids rerunning instance segmentation while the computer-vision tools remain a separate migration milestone.

## Demonstrated workflow

The notebook sends three stateless natural-language requests through the production MAF application:

1. Compare `manual_leaf_area` and `projected_leaf_area` as predictors of `manual_dried_weight`.
2. Find the maximum `manual_leaf_area` for the Desiree variety.
3. Find the mean `manual_leaf_area` for the Desiree variety.

The workflow exercises:

```text
compare_linear_relationships
query_csv_statistic
```

The trusted CSV and plot-output paths are bound by the application and are not controlled by the language model.

## Run from a clean session

Activate the validated environment:

```bash
conda activate /workspaces/.phenoassistant-runtime/conda-envs/phenoassistant-maf-poc
```

Set the OpenRouter configuration in the shell:

```bash
export OPENROUTER_API_KEY="your-key"
export OPENROUTER_MODEL="openrouter/free"
```

Launch the notebook:

```bash
jupyter lab demo_maf.ipynb
```

Restart the kernel and run every cell in order.

## Expected scientific values

For the tracked 32-row dataset:

```text
manual_leaf_area vs manual_dried_weight:
r = 0.8910860678113759

projected_leaf_area vs manual_dried_weight:
r = 0.7598824217936114

Desiree matching rows:
22

Desiree manual_leaf_area maximum:
649.69

Desiree manual_leaf_area mean:
225.65568181818182
```

Generated plots:

```text
results/maf_demo/potato_manual.png
results/maf_demo/potato_algorithm.png
```

## Current scope boundary

This notebook validates production MAF orchestration and deterministic CPU analysis. It does not yet migrate:

- instance-segmentation inference;
- model-zoo selection;
- phenotype extraction from COCO masks;
- GPU execution.
