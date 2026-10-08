# Phase 5 — Nottingham GPU Validation Protocol

**Status:** ready to execute  
**Date:** 2026-10-08  
**Branch:** `feature/maf-mcp-v2-integration`

## Fast execution sequence

Run these from the repository root on the Nottingham GPU machine, stopping at the first failing gate:

```bash
python scripts/gpu/phase5_preflight.py
python scripts/gpu/phase5_environment_probe.py
python scripts/gpu/phase5_case1_gpu.py --mode smoke
python scripts/gpu/phase5_case1_gpu.py --mode full --batch-size 1
python scripts/gpu/compare_case1_gpu_to_tracked.py
python scripts/gpu/phase5_case3_smoke.py
```

Do not run the full Case 1 job until the preflight, environment probe, and one-image smoke have passed.

## Objective

Cross the GPU boundary that was intentionally deferred during the CPU MAF migration, while preserving scientific provenance and avoiding any claim that an inherited artefact was regenerated unless the GPU path actually produces it.

Phase 5 validates two representative workflows:

1. **Case 1** — Arabidopsis instance segmentation → phenotype extraction.
2. **Case 3** — winter-wheat image-classification inference, then training only if the local dataset and credentials are genuinely available.

The GPU phase is executed before MAF↔MCP production integration so that backend transport is not mixed with environment/model failures.

## Gate 5A — Environment capture

Run from the repository root:

```bash
python scripts/gpu/phase5_environment_probe.py
```

Acceptance criteria:

- CUDA available from the active Python environment;
- at least one CUDA device visible;
- GPU model / driver recorded by `nvidia-smi`;
- active git SHA and branch recorded;
- package versions recorded;
- no credential values written;
- Case 1 and Case 3 data availability recorded explicitly.

Do not proceed to scientific execution if the probe reports CUDA unavailable.

## Gate 5B — Dependency and import smoke

In the intended GPU environment, verify imports without initiating model training:

```bash
python - <<'PY'
import torch
from functions.instance_segmentation import infer_instance_segmentation
from functions.compute_phenotypes import compute_phenotypes_from_ins_seg
from functions.image_classification import infer_image_classification

print({
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "device_count": torch.cuda.device_count(),
    "instance_segmentation_import": True,
    "phenotype_import": True,
    "image_classification_import": True,
})
PY
```

This is an environment/import gate only.

## Gate 5C — Case 1 data integrity

The historical Case 1 notebook used:

- metadata: `./data/aracrop_metadata.json`;
- image root: `./data/AraCropData`;
- checkpoint:
  `fengchen025/arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft`;
- pixel-to-cm scale: `0.03`.

The repository tracks the metadata but does not track the `AraCropData` image directory. The cluster environment must therefore provide the actual images before Case 1 can be claimed as GPU reproduced.

Validate:

```bash
python - <<'PY'
import json
from pathlib import Path

metadata = Path("data/aracrop_metadata.json")
payload = json.loads(metadata.read_text())
images = [Path(p) for p in payload["file_name"]]
missing = [str(p) for p in images if not p.is_file()]

print({
    "metadata_images": len(images),
    "existing_images": len(images) - len(missing),
    "missing_images": len(missing),
    "first_missing": missing[:5],
})

if missing:
    raise RuntimeError(
        "Case 1 images are incomplete in this environment; "
        "do not claim GPU reproduction."
    )
PY
```

Expected complete image count from the published Case 1 metadata: **1,248**.

## Gate 5D — Case 1 one-image GPU smoke

Before processing all 1,248 images, run one image through the real historical segmentation implementation.

```bash
python - <<'PY'
import json
from pathlib import Path

from functions.instance_segmentation import infer_instance_segmentation

payload = json.loads(Path("data/aracrop_metadata.json").read_text())
image = payload["file_name"][0]

result = infer_instance_segmentation(
    image_urls=[image],
    checkpoint=(
        "fengchen025/"
        "arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft"
    ),
    batch_size=1,
    device="cuda",
    output_dir="./results/maf_gpu_case1_smoke",
)
print(result)

target = Path("results/maf_gpu_case1_smoke/ins_seg_results.json")
if not target.is_file():
    raise RuntimeError("Case 1 smoke output was not created")

evidence = json.loads(target.read_text())
print({
    "output": str(target),
    "images": len(evidence.get("images", [])),
    "annotations": len(evidence.get("annotations", [])),
})
PY
```

Acceptance criteria:

- checkpoint downloads/loads successfully;
- CUDA inference completes;
- output JSON exists;
- at least one image record exists;
- result is parseable COCO-style JSON.

A one-image smoke does not establish scientific parity with the historical full dataset.

## Gate 5E — Case 1 full GPU inference

Only after Gate 5D passes:

```bash
python - <<'PY'
from functions.instance_segmentation import infer_instance_segmentation

print(
    infer_instance_segmentation(
        file_path="./data/aracrop_metadata.json",
        checkpoint=(
            "fengchen025/"
            "arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft"
        ),
        batch_size=1,
        device="cuda",
        output_dir="./results/maf_gpu_case1",
    )
)
PY
```

The historical notebook wrote `./results/Case1/ins_seg_results.json`. The migration intentionally writes to a new directory so that historical artefacts are never overwritten.

Record:

- wall-clock time;
- peak GPU memory if available;
- output file hash;
- number of images;
- number of annotations;
- checkpoint identifier.

## Gate 5F — Case 1 phenotype extraction

Use the newly generated segmentation file, not the historical result:

```bash
python - <<'PY'
from functions.compute_phenotypes import compute_phenotypes_from_ins_seg

print(
    compute_phenotypes_from_ins_seg(
        ins_seg_result_path="./results/maf_gpu_case1/ins_seg_results.json",
        save_path="./results/maf_gpu_case1/phenotypes.csv",
        pixel_to_cm=0.03,
    )
)
PY
```

Acceptance criteria:

- output CSV exists;
- 1,248 rows are expected if all images produced results;
- required phenotype columns exist:
  `file_name`, `leaf_count`, `average_leaf_area`,
  `projected_leaf_area`, `diameter`, `perimeter`,
  `compactness`, `stockiness`.

Do not use the historical notebook's free-form Code Writer merge step. Implement the metadata merge deterministically and test it. The historical notebook contains evidence of an attempted merge on a non-existent `id` key before repair; this is useful provenance and a reason to replace the merge with a deterministic function.

## Gate 5G — Case 1 scientific comparison

Compare the GPU-regenerated phenotype table with the trusted tracked Case 1 phenotype artefact.

Required analysis:

- row/key alignment by `file_name`;
- coverage percentage;
- per-phenotype absolute and relative differences;
- ecotype ranking consistency;
- repeated-measures interaction conclusion consistency;
- Tukey grouping consistency.

A numerical mismatch is not automatically a failure. First determine whether it comes from model/library/version drift, stochasticity, data mismatch, or an implementation error.

## Gate 5H — Case 3 local-data inspection

Current repository truth:

- checkpoint is registered:
  `fengchen025/winter-wheat_nutri-defi-identify_dndww20_dino2b_lora`;
- local winter-wheat dataset is not tracked in the GitHub repository.

Check the cluster:

```bash
python - <<'PY'
from pathlib import Path

root = Path("data/winter-wheat_nutri-defi-identify_dndww20")
required = [
    root,
    root / "train",
    root / "train" / "metadata.csv",
    root / "label2id.json",
]

print({str(p): p.exists() for p in required})
PY
```

Inference does not require the training dataset if suitable test images are available.

## Gate 5I — Case 3 inference smoke

Select a real winter-wheat image from the local dataset or another approved source and execute the registered checkpoint through the historical deterministic inference function:

```python
from functions.image_classification import infer_image_classification

result = infer_image_classification(
    image_urls=[APPROVED_IMAGE_PATH],
    checkpoint=(
        "fengchen025/"
        "winter-wheat_nutri-defi-identify_dndww20_dino2b_lora"
    ),
    batch_size=1,
    device="cuda",
    output_dir="./results/maf_gpu_case3_smoke",
)
```

Acceptance criteria:

- model and LoRA adapter load;
- CUDA inference completes;
- result CSV exists;
- class ID, class label, and confidence are present;
- input image provenance is recorded.

Until an approved image path is known, Case 3 inference remains unexecuted.

## Gate 5J — Case 3 training decision

Do **not** retrain simply because GPU access now exists.

Training is justified only when all are true:

- local dataset satisfies the audited layout;
- `HF_USER` and `HF_TOKEN` are present;
- intended Hugging Face side effects are approved;
- training is required for a stated validation question;
- output/model-zoo mutation is isolated from historical evidence.

The historical notebook used:

- dataset: `winter-wheat_nutri-defi-identify_dndww20`;
- pretrained model: `facebook/dinov2-base`;
- method: LoRA;
- train batch: 32;
- validation batch: 1;
- image size: 512×512;
- learning rate: 1e-4;
- one epoch in the demonstrated call.

Because the trained checkpoint already exists, inference validation has higher priority than retraining.

## Gate 5K — Evidence policy

Every GPU run must preserve:

- branch + commit;
- environment probe;
- command/script;
- input data identifiers;
- checkpoint;
- output hashes;
- timings;
- failures;
- warnings;
- CUDA device details;
- exact result files.

Do not commit credentials, Hugging Face tokens, OpenRouter keys, W&B keys, or environment files containing them.

## Phase 5 exit criteria

Phase 5 is complete only when:

- [ ] CUDA environment evidence captured;
- [ ] heavyweight imports pass;
- [ ] Case 1 images are available and verified;
- [ ] Case 1 one-image inference passes;
- [ ] Case 1 full inference completes;
- [ ] Case 1 phenotype extraction completes;
- [ ] regenerated-vs-tracked Case 1 comparison is documented;
- [ ] Case 3 approved inference image(s) are identified;
- [ ] Case 3 registered checkpoint inference passes;
- [ ] training is either executed under a frozen protocol or explicitly ruled unnecessary with evidence;
- [ ] all outputs are preserved outside historical result paths.

Once these gates pass, the project can move into MCP v2 + MAF integration without confusing transport failures with GPU/model/environment failures.
