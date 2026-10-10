# Phase 7D — Evidence-Backed Training Recommendation Policy

**Date:** 2026-10-10  
**Branch:** research/phenoguard  
**Status:** implementation committed, runtime verification pending

## Purpose

Phase 7C made EXECUTE, RESELECT, CLARIFY, and ABSTAIN operational across a
provenance-backed capability catalogue. Phase 7D adds the final global action,
RECOMMEND_TRAINING, but only behind explicit evidence gates.

The goal is to avoid the unsafe shortcut:

```text
no applicable model -> automatically train something
```

A catalogue miss alone is not sufficient justification for training.

## Evidence boundary

The PhenoAssistant paper documents an automatic model-training pipeline for common
phenotyping tasks and explicitly demonstrates the image-classification path in Case
Study 3. When no capable model is available for winter-wheat nutrient-deficiency
classification, the system requests labelled data in the required format, prepares
the dataset, trains a DINOv2-based classifier using either LoRA or full fine-tuning,
evaluates it, and then adds the model to the model zoo.

The repository implementation additionally exposes the image-classification
fine-tuning function and the required classification dataset structure.

For Phase 7D v0.1, only the **image classification** training path is frozen into the
recommendation policy. Other trainable tasks may be added only after their evidence
and benchmark role are separately audited.

## Readiness inputs

Training readiness requires explicit evidence for:

- a dataset being available;
- labels being available;
- the dataset satisfying the supported PhenoAssistant classification format.

The recommendation policy does not itself launch training.

## Decision semantics

When no currently applicable capability exists:

- supported image-classification task + ready labelled/formatted dataset
  -> `RECOMMEND_TRAINING`;
- supported image-classification task + missing dataset/labels/format evidence
  -> `CLARIFY`;
- task outside the frozen v0.1 training-policy scope
  -> `ABSTAIN`;
- no training-readiness evidence
  -> `ABSTAIN`.

An already applicable capability always takes precedence over recommending new model
training.

## Safety and autonomy boundary

`RECOMMEND_TRAINING` is a recommendation, not authorisation to spend compute,
upload data, mutate a model zoo, or start a training job.

Actual training execution remains a separate action requiring the production tool
contract, resource checks, dataset validation, and user-controlled execution policy.

## Claim boundary

Passing Phase 7D proves only that all five PhenoGuard decision labels have explicit,
machine-readable preconditions.

It does not show that those decisions improve scientific outcomes. That requires the
paired benchmark, baseline comparisons, hidden evaluation, and failure analysis in
the subsequent research phases.
