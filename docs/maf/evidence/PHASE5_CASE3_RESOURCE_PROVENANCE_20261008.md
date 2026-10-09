# Phase 5 Case 3 Resource Provenance — 2026-10-08

## Historical PhenoAssistant state

The historical Case 3 notebook used a local prepared dataset at
`data/winter-wheat_nutri-defi-identify_dndww20` and the registered
image-classification checkpoint
`fengchen025/winter-wheat_nutri-defi-identify_dndww20_dino2b_lora`.

The historical prepared dataset contained 1,332 training images and 468 test
images, for 1,800 images total.

## Public source dataset

The upstream DND-Diko-WWWR project identifies the official source dataset as
Deep Nutrient Deficiency - Dikopshof - Winter Wheat and Winter Rye
(DND-Diko-WWWR), published through PhenoRoam.

Its public documentation reports:

- WW2020: 1,800 winter-wheat RGB images;
- WR2021: 1,800 winter-rye RGB images;
- seven fertilizer-treatment classes;
- train/test split per crop-year: 1,332 / 468;
- CC BY-NC-SA 4.0 license;
- PhenoRoam catalogue UUID:
  `1272b197-11ad-4138-a872-dc31d8051726`.

The exact 1,332 / 468 / 1,800 counts match the historical PhenoAssistant
prepared Case 3 dataset. This is strong provenance evidence that the historical
Case 3 data were derived from the WW2020 portion of DND-Diko-WWWR, but it is
not yet a byte-level identity proof.

## Current access boundary

The historical implementation makes the resource policy explicit:

- `prepare_dataset(...)` uploads datasets with `private=True`;
- image-classification training uses `hub_private_repo=True`;
- both resources are created under the namespace supplied by `HF_USER`.

This establishes that the historical Case 3 Hugging Face dataset and trained
checkpoint were intentionally private resources rather than public artefacts.

On Nottingham Plato, an unauthenticated probe returned HTTP 401 for both Case 3
resources. After successful Hugging Face authentication with the current user
account, both exact resource identifiers return HTTP 404 / RepositoryNotFound.
Because private Hub repositories are not visible to accounts without access,
this means the current authenticated account does not have access to the exact
historical resources, or the resources no longer exist at those identifiers.
It is not a local credential-cache failure.

The public PhenoRoam catalogue record remains discoverable, but the checked
record view does not currently expose a direct DATA download.

## Validation decision

Do not substitute a different model and do not retrain simply to remove the
blocker.

Preferred order:

1. ask the resource owner/collaborator to grant the current Hugging Face
   account access to the private registered checkpoint and prepared dataset,
   or provide an approved copy of those exact artefacts;
2. otherwise recover the exact historical prepared dataset artefact from the
   original collaborators, or reconstruct it from official WW2020 only after
   the preparation mapping is verified;
3. run the registered checkpoint on an approved image;
4. retrain only if required by a stated validation question under a frozen
   protocol.

Until then, Case 3 is an explicit access-controlled provenance boundary, not
a failed GPU implementation.
