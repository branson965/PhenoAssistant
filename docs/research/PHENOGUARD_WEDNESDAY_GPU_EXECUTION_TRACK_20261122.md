# PhenoGuard, 25 November 2026: GPU-first execution track

**Status:** one-image engineering validation only, not PhenoGuard experimental evidence.
**Replaces:** no frozen protocol, runtime JSON, source manifest, image registry or approval.
**Purpose:** check *now* whether the three actual scientific capability implementations
can run on Plato, before scheduling any large or outcome-bearing jobs.

## The central decision

The IJCAI hypothesis is the agent's scientifically appropriate **selection and
abstention**, measured by matched C3/C4/C8 comparisons. Large vision-training
jobs do not directly test this claim. Prioritise:

1. Dataset/checkpoint/environment readiness, with no GPU allocation.
2. One-image GPU engineering smoke for the relevant scientific tool, with
   explicit authorised image and existing institutional compute permission.
3. If necessary, short, bounded model-output compatibility checks.
4. Separately, obtain the required independent approvals for the frozen
   108-trial C3/C4/C8 qualification matrix. **Do not start paid/scientific
   trials through the unapproved Phase 8 runtime.**
5. Only after those gates, launch prospective comparisons and preserve
   every failed, negative and abstained result.

## First command, login node, zero GPU/provider cost

```bash
cd ~/PhenoAssistant
PY="$HOME/.local/envs/phenoassistant-phase6-mcp/bin/python"
{
    date -u
    git rev-parse --short HEAD
    git status --short
    echo "=== SLURM PARTITIONS ==="
    sinfo -o '%P %a %l %D %G' | head -30
    echo "=== MY JOBS ==="
    squeue -u "$USER" || true
    echo "=== DATA READINESS ==="
    "$PY" scripts/gpu/phase5_preflight.py
    echo "=== POTATO SAM CHECKPOINT ==="
    ls -lh models/sam_vit_h_4b8939.pth 2>&1 || true
    echo "=== DATASET ROOTS ==="
    du -sh data/AraCropData data/PotatoLeaf data/winter-wheat_nutri-defi-identify_dndww20 2>&1 || true
    echo "=== GPU PYTHON ENVIRONMENTS ==="
    find "$HOME/.local/envs" -maxdepth 3 -name python -type f 2>/dev/null | head -30
    echo "=== HISTORICAL GPU EVIDENCE ==="
    find results -maxdepth 4 -name gpu_execution_evidence.json -print 2>/dev/null | head -30
    echo "=== INDEPENDENT PHASE 8 SCIENCE APPROVAL ==="
    env -u OPENROUTER_API_KEY "$PY" scripts/research/phase8_attempt_ledger.py
    env -u OPENROUTER_API_KEY "$PY" scripts/research/phase8_image_fixture_registry.py
} 2>&1 | tee "$HOME/phase8_wednesday_preflight_$(date -u +%Y%m%dT%H%M%SZ).log"
```

**Interpretation:** Phase 8 approval markers remain false. The existing GPU
script below is an *engineering-only* check and cannot be counted among 108
qualification trials or any held-out benchmark results.

## Existing engineering smoke launcher

`scripts/gpu/phase8_gpu_engineering_smoke.py` takes exactly **one** explicitly
reviewed image (`--image`) and a fixed `--case`:

- `arabidopsis`: Mask2Former, COCO `ins_seg_results.json`
- `potato`: Leaf-only SAM, COCO `leaf_only_sam_results.json`
- `wheat`: DINOv2 classification, `img_classification_results.csv`

Case 2 requires `models/sam_vit_h_4b8939.pth`; the script fails before GPU
allocation if it is missing.

Dry-run on the login node, with **your authorised image path**:

```bash
python scripts/gpu/phase8_gpu_engineering_smoke.py \
  --case arabidopsis --image /absolute/path/to/approved-arabidopsis-image.png \
  --dry-run
```

Do not execute the actual inference directly on the login node.
Locate the previously verified Python environment containing CUDA/PyTorch
and PhenoAssistant's scientific inference dependencies. Confirm which
partition and GPU resources you are entitled to use.

## Slurm template, GPU engineering smoke only

The following job script deliberately **does not select a partition or
account**. Supply the correct values from Plato or your group allocation.
The requested resource values are starting points, not performance claims.

```bash
cat > "$HOME/pg_engineering_smoke.sbatch" <<'SLURM'
#!/bin/bash
#SBATCH --job-name=pg-one-image
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=pg-smoke-%j.out
#SBATCH --error=pg-smoke-%j.err
set -euo pipefail
cd "$HOME/PhenoAssistant"
: "${PHENO_GPU_PYTHON:?Provide absolute path to verified GPU Python}"
: "${PHENO_SMOKE_CASE:?Must be arabidopsis, potato, or wheat}"
: "${PHENO_SMOKE_IMAGE:?Provide one authorised absolute image path}"
"$PHENO_GPU_PYTHON" scripts/gpu/phase8_gpu_engineering_smoke.py \
  --case "$PHENO_SMOKE_CASE" --image "$PHENO_SMOKE_IMAGE"
SLURM

# Set these three values to verified values on Plato:
export PHENO_GPU_PYTHON=/absolute/path/to/verified/gpu/python
export PHENO_SMOKE_CASE=arabidopsis
export PHENO_SMOKE_IMAGE=/absolute/path/to/authorised/image.png

# Confirm your actual GPU partition and, if required, account.
# GPU_PARTITION=<from sinfo>; ACCOUNT=<assigned account>
sbatch --partition="$GPU_PARTITION" "$HOME/pg_engineering_smoke.sbatch"
```

No job should be submitted with placeholder paths, an unknown partition,
or an image lacking access permission. For a group requiring `--account`,
pass the account explicitly to `sbatch`.

Outputs are placed into **unique, immutable-in-practice** folders under
`results/phase8_gpu_engineering_smoke/<case>/<timestamp>_<pid>/`. The
per-run `engineering_evidence.json` records image hash, artifact hash,
checkpoint identifier, available local SAM checkpoint hash, Git commit,
CUDA/PyTorch and elapsed time. This is a technical provenance record only.

## Wednesday deliverables

- Real Case 1/Case 2/Case 3 inference status and recorded failure causes.
- Available/absent model checkpoint and image provenance evidence.
- A separate, independently approved plan to run 108 paired C3/C4/C8
  qualification trials, with actual measured external API cost.
- Expected first comparative figures: unsafe execution rate, correct and
  unnecessary abstention, decision accuracy, risk–coverage and cost.
- Unresolved final-run approvals and an explicit owner/date for each.

**Never** use a synthetic test-only approved runtime, or fill in a trusted
SHA pin just to make the Phase 8 execution gate return true.
