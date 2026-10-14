# Phase 7C — Catalogue-Level Applicability Resolution

**Date:** 2026-10-10  
**Branch:** research/phenoguard  
**Status:** implementation committed, runtime verification pending

## Purpose

Phase 7A established the single-capability applicability primitive. Phase 7B tied that
primitive to a real Case Study 1 capability. Phase 7C introduces the minimum
catalogue-level logic required to make `RESELECT` an evidence-backed decision.

## Real catalogue slice

The current provenance catalogue contains two real PhenoAssistant instance-segmentation
capabilities:

1. the Case Study 1 Arabidopsis Mask2Former capability;
2. the Case Study 2 potato Leaf-only SAM capability.

Both are registered in `model_zoo.json`.

The Case Study 2 paper evidence states that Leaf-only SAM is integrated for potato
leaf segmentation and that both the model and the 32-image Case Study 2 dataset
originate from Williams et al.

## Resolution policy v0.1

For a request and a bounded catalogue:

- if the explicitly requested capability is executable, emit `EXECUTE`;
- if the requested capability is not executable and exactly one alternative is
  executable, emit `RESELECT` and identify that alternative;
- if no capability was preselected and exactly one capability is executable, emit
  `EXECUTE` with that capability;
- if multiple capabilities are executable and no explicit executable choice exists,
  emit `CLARIFY`;
- if no capability is executable but at least one needs missing required context,
  emit `CLARIFY`;
- otherwise emit `ABSTAIN`.

## Training boundary

The catalogue resolver **does not emit `RECOMMEND_TRAINING`**.

A missing suitable capability is not by itself sufficient evidence that training is
the correct next action. Training recommendation requires a separate policy covering,
at minimum, task support, data availability/format, labels, resource requirements,
and the distinction between a genuinely unsupported operating envelope and merely
missing request metadata.

That policy is the next method gate.

## Claim boundary

The resolver is deterministic infrastructure for the research method. Its existence
does not demonstrate improved agent safety or scientific correctness. Those claims
require the frozen paired benchmark and controlled baseline comparison.


## Controlled Case 3 provenance extension — 2026-10-14

Phase 7 was explicitly reopened before any outcome-bearing IJCAI scientific run to
replace the historical demonstration-only LoRA classifier with Feng Chen's public,
functioning fully fine-tuned Case 3 checkpoint.

The default provenance catalogue now also contains the verified winter-wheat
image-classification capability:

`fengchen025/dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020`

Runtime provenance is pinned to:

- Hugging Face revision
  `89d6b3ca17dba118d7d25c7b8a87ff205dc6235e`;
- `model.safetensors` SHA-256
  `4a29f8b73438a6d16cbc80287c40002af40029fd529146f0be73d7825befbbf5`.

The envelope freezes only directly supported scientific applicability constraints:
winter wheat species and RGB modality are hard requirements. DND-WW2020's UAV
acquisition provenance is retained as a limitation rather than being overloaded into
the current `view` field. Missing modality therefore requires `CLARIFY`; a
non-winter-wheat species or non-RGB modality requires `ABSTAIN`.

The official DND-Diko-WWWR README montage GPU run is compatibility evidence only and
must not be interpreted as an accuracy result.
