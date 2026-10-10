# Phase 7B — First Provenance-Backed Scientific Operating Envelope

**Date:** 2026-10-10  
**Branch:** research/phenoguard  
**Status:** implementation committed, runtime verification pending

## Capability

The first real envelope is tied to the registered Case Study 1 model:

`fengchen025/arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft`

Pinned reproduced revision:

`a75bc3d595148ebc62afad7c9800908279e7aea8`

## Evidence used

The current repository/paper evidence establishes that:

- the model is the Arabidopsis leaf instance-segmentation capability used in
  PhenoAssistant Case Study 1;
- the architecture is Mask2Former;
- the model was fine-tuned on CVPPP LSC subsets A1 and A4;
- the exact checkpoint revision above was successfully used in the Phase 5 full
  Plato reproduction;
- the model remains registered in `model_zoo.json` under
  `instance-segmentation`.

## Frozen v0.1 applicability rule

Only the following hard context rule is frozen at this stage:

```text
species == "Arabidopsis thaliana"
```

Species is therefore required before execution.

A matching request emits `EXECUTE`.  
A missing species emits `CLARIFY`.  
A different species emits `ABSTAIN`.

## Deliberately unfrozen dimensions

The envelope does **not** currently hard-code:

- acquisition view;
- modality;
- illumination;
- indoor/outdoor environment.

This omission is deliberate. The project must not convert plausible assumptions into
scientific applicability rules without sufficient provenance evidence.

## Claim boundary

Passing these tests proves that a real repository capability can be represented by the
Scientific Operating Envelope and checked deterministically against one
provenance-backed hard constraint.

It does not prove that species alone is sufficient for scientific applicability, that
the model generalises to every Arabidopsis acquisition condition, or that PhenoGuard
improves safety relative to baselines. Those remain empirical questions.
