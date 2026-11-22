# PhenoGuard evidence triage, Plato, 22 November 2026

**Source:** researcher-provided direct Plato terminal audit, not a separate
third-party replication. **Scope:** existing Phase 5 scientific execution
compatibility and artifact integrity, **not** the frozen IJCAI C3/C4/C8
qualification or a generalisation benchmark.

## Case 1, Arabidopsis Mask2Former

- All 1,248 AraCrop input files available on Plato, none missing.
- Historical CUDA device: NVIDIA RTX A4000.
- Full-run evidence: `results/maf_gpu_case1/gpu_execution_evidence.json`.
- 1,248/1,248 image result records; segmentation and phenotype CSV hashes
  were recomputed and matched their recorded SHA-256 values.
- Full-run GPU inference: ~184.86 seconds, as recorded in the run evidence.
- Comparison to tracked reference: **1,248/1,248** aligned,
  no missing or extra regenerated images.
- Both projected-leaf-area and leaf-count ecotype rankings matched exactly:
  `ein2, col0, adh1, pgm, ctr`.
- `scientific_conclusion_comparison.json` reported
  `scientific_conclusion_match: true`; retain the complete stored report
  to substantiate its component ANOVA and Tukey comparison.
- Earlier one-image and 16-image smoke/sample segmentation artifact hashes
  also matched their evidence records.

**Action:** do not rerun the full 1,248 images for engineering readiness.
Do not count this as an IJCAI agent-selection result or independently claim
segmentation model accuracy.

## Case 3, winter-wheat DINOv2

- Official example image inference evidence exists and its reported
  classification CSV and input-image SHA-256 values matched the files.
- Full fine-tuned checkpoint revision:
  `89d6b3ca17dba118d7d25c7b8a87ff205dc6235e`.
- Checkpoint weight SHA-256:
  `4a29f8b73438a6d16cbc80287c40002af40029fd529146f0be73d7825befbbf5`.
- Audit reported classifier head present and matched label count.
- Inference compatibility measured at ~0.879 seconds, NVIDIA RTX A4000.
- The official-example image was a **montage, not an individual labelled
  WW2020 test image**, so no accuracy claim is warranted.
- The local winter-wheat evaluation dataset directory is absent.

**Action:** retain compatibility evidence. Resolve actual dataset/provenance
only if the final experiment needs wheat images; no immediate repeat needed.

## Case 2, potato Leaf-only SAM

- Source images found under `data/PotatoLeaf`.
- The canonical inference code expects
  `models/sam_vit_h_4b8939.pth` (SAM 1, ViT-H).
- Checkpoint search under user's home (7 levels deep) found no file.
- The official Meta project publishes the same checkpoint filename at:
  `https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth`.
- Two independent hosted copies list content SHA-256
  `a7bf3b02f3ebf1267aba913ff637d9a2d5c33d3173bb679e46d9f338c26f262e`.
- File size approximately 2.56 GB. Institutional download and storage
  permissions must be verified, and the file checked before loading it.

**Action:** verify user storage quota and network policy; then optionally
run the new explicit download helper. A short one-image CUDA engineering
smoke should follow only on an appropriately resourced, permitted Slurm GPU
allocation. Avoid submitting the task when user memory QOS is saturated.

## Resource situation

Observed on Plato: partitions `amp16`, `amp20`, `amp48`,
`ada24`, `cs`, `general` and `cpu`, but **partition visibility is
not authorisation**. User's queue showed other pending GPU jobs blocked
by `QOSMaxMemoryPerUser`, as well as a running job.

## Frozen science boundary

- `TRUSTED_APPROVED_RUNTIME_SHA256` is unset.
- `TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256` is unset.
- Scientific Phase 8 execution is explicitly prohibited by the historical
  runtime candidate until independent review, model/provider/billing approval,
  complete asset registration, and controlled harness sign-off.
- None of the existing Case 1/3 GPU files measure the novelty of
  PhenoGuard versus C3/C4. The 108-trial C3/C4/C8 comparison remains
  outstanding, as do final held-out generalisation and expert review.

This document is an inventory of **researcher-provided evidence and
prospective actions**, not a retrospective authority to modify the Phase 7
frozen method, claim manuscript results or launch paid calls.
