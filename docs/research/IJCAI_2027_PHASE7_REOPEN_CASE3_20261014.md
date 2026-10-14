# Phase 7 Controlled Reopen — Case 3 Provenance Correction

**Date:** 2026-10-14  
**Venue:** IJCAI 2027 stretch target  
**Status:** reopened before any outcome-bearing IJCAI scientific run

## Trigger

Feng Chen confirmed that the historical Case 3 LoRA checkpoint is demonstration-only
and was not trained to convergence. He identified the non-LoRA fully fine-tuned model
as the functioning scientific checkpoint and made it public.

The functioning checkpoint is:

`fengchen025/dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020`

## Why a reopen is required

The Phase 7 v0.1 freeze included `model_zoo.json`, whose image-classification entry
still referenced the demonstration-only LoRA checkpoint. That catalogue state was
therefore no longer the strongest collaborator-backed provenance available.

Changing a frozen scientific capability identity is a scientific-method change under
the v0.1 freeze policy. It must not be patched silently.

## Timing and blinding status

This reopen occurred before:

- any outcome-bearing IJCAI scientific benchmark run;
- any hidden benchmark construction or unblinding;
- any empirical comparison of C0-C9 conditions;
- any model-selection decision based on favourable scientific outcomes.

The only new evidence inspected before reopening was resource/runtime provenance:

- public model metadata;
- immutable Hugging Face revision;
- direct safetensors integrity;
- one compatibility-only GPU execution on the official DND-Diko-WWWR README montage.

The montage run is explicitly not an accuracy result.

## Verified Case 3 identity

- model:
  `fengchen025/dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020`;
- Hugging Face revision:
  `89d6b3ca17dba118d7d25c7b8a87ff205dc6235e`;
- full `model.safetensors` SHA-256:
  `4a29f8b73438a6d16cbc80287c40002af40029fd529146f0be73d7825befbbf5`;
- architecture: `Dinov2ForImageClassification`;
- classifier head: weight shape `[7, 1536]`, bias shape `[7]`;
- labels: seven DND-WW2020 fertiliser-treatment classes;
- authoritative runtime path excludes colocated PEFT adapter artefacts.

## Controlled changes authorised

The reopen authorises only the following provenance correction:

1. replace the demonstration LoRA entry in `model_zoo.json` with the verified
   full-FT checkpoint;
2. add a provenance-backed Scientific Operating Envelope for that capability;
3. pin the immutable Hub revision and full-weight SHA;
4. align the bounded Case 3 readiness contract with the verified checkpoint;
5. add regression tests and update catalogue/freeze documentation;
6. generate a v0.2 freeze manifest and rerun the complete research suite.

No baseline, benchmark, scoring, hidden-label, C0-C9 condition, or claim-boundary rule
is changed by this reopen.

## Re-freeze rule

Phase 8 outcome-bearing scientific work remains prohibited until:

- the complete research test suite passes;
- Case 3 readiness tests pass;
- the active freeze manifest is regenerated as v0.2;
- all 22 frozen paths verify against the new manifest;
- the aggregate v0.2 SHA-256 is recorded;
- the working tree is clean after the re-freeze commit.
