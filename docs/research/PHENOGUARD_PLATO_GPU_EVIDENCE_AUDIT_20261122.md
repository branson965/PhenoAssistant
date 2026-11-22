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

## Case 2, potato Leaf-only SAM (22 November Plato smoke)

- The source image `data/PotatoLeaf/IMG_8064.JPG` passed an explicit
  dry-run preflight with image SHA-256
  `9ceeae5973237712727240469a3bbb98d66a87265cbafcc2bc2b90449a4dca8e`.
- The local Meta SAM ViT-H checkpoint was present and verified with
  SHA-256 `a7bf3b02f3ebf1267aba913ff637d9a2d5c33d3173bb679e46d9f338c26f262e`.
  A subsequent `--download` did not download again because the existing
  file matched its pinned hash.
- Slurm job `63134`, `standard/core`, `amp16`, `dart`,
  GPU **NVIDIA RTX A4000**, started **2026-11-22 11:43:01 UTC** and
  completed **11:56:19 UTC** (`COMPLETED`, exit `0:0`, 13m19s).
- Runner printed `ENGINEERING_SMOKE_OK` and `record_count: 13`
  for one potato image. **13 are predicted instance masks, not
  expert-labelled leaves or accuracy measurements.**
- Researcher-reported output path:
  `results/phase8_gpu_engineering_smoke/potato/20261122T114432Z_447299/engineering_evidence.json`.
- Warning-only library messages included Albumentations version check,
  FLAML optional features and `torch.load(weights_only=False)`
  unpickling semantics for the Meta SAM checkpoint.
- The completion statement confirms model execution and initial artifact
  shape checks by the engineering runner.
- **Follow-up validation (researcher-reported Plato output):**
  `ARTIFACT_HASH_MATCH=true`;
  `PREDICTED_INSTANCES=13`;
  artifact SHA-256
  `5f4aaa3c68e0c0f1035e15bbd79c70a80b84cd998339e6ae448609f62f846180`.
- Real `validate_coco` returned
  `validator_id=phase8-actual-scientific-artifact-invariants-v0.1`,
  `safe_to_report=true`, `issues=[]`, with
  `C8_STRUCTURAL_VALIDATION_PASS=true`.
  This means **output structure and checked provenance/invariants passed**,
  not that 13 leaves are visually correct, scientifically calibrated,
  biologically accurate, or appropriate under domain shift.

**Action:** close the one-image GPU engineering compatibility workstream.
Retain the unmodified local evidence and artifact in place. Do **not**
rerun Case 2 merely to improve the paper's claimed novelty or count this
as a registered scientific C8 trial.

## Resource situation

Observed on Plato: partitions `amp16`, `amp20`, `amp48`,
`ada24`, `cs`, `general` and `cpu`, but **partition visibility is
not authorisation**. Earlier user queue showed `QOSMaxMemoryPerUser` delays. An
`amp48` submission was rejected for account/partition mismatch. Using
`--partition=amp16 --account=standard` worked immediately, and the
resulting Case 2 smoke job completed successfully.

## Frozen science boundary

- `TRUSTED_APPROVED_RUNTIME_SHA256` is unset.
- `TRUSTED_REVIEWED_FIXTURE_REGISTRY_SHA256` is unset.
- Scientific Phase 8 execution is explicitly prohibited by the historical
  runtime candidate until independent review, model/provider/billing approval,
  complete asset registration, and controlled harness sign-off.
- None of the existing Case 1/2/3 GPU files measure the novelty of
  PhenoGuard versus C3/C4. The 108-trial C3/C4/C8 comparison remains
  outstanding, as do final held-out generalisation and expert review.

This document is an inventory of **researcher-provided evidence and
prospective actions**, not a retrospective authority to modify the Phase 7
frozen method, claim manuscript results or launch paid calls.
