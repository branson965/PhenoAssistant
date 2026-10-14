"""Provenance-backed operating envelopes for real PhenoAssistant capabilities."""

from __future__ import annotations

from research.phenoguard.contracts import (
    ApplicabilityConstraint,
    ConstraintSeverity,
    ScientificOperatingEnvelope,
)

CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID = (
    "fengchen025/"
    "arabidopsis_leaf-instance-segmentation_cvppp2017-a1a4_m2fb_fullft"
)

CASE1_ARABIDOPSIS_SEGMENTATION_REVISION = (
    "a75bc3d595148ebc62afad7c9800908279e7aea8"
)


def build_case1_arabidopsis_segmentation_envelope(
) -> ScientificOperatingEnvelope:
    """Return the narrow evidence-backed envelope for the Case 1 model."""
    return ScientificOperatingEnvelope(
        capability_id=CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
        scientific_task="instance segmentation",
        constraints=(
            ApplicabilityConstraint(
                field="species",
                allowed_values=("Arabidopsis thaliana",),
                severity=ConstraintSeverity.HARD,
                rationale=(
                    "The PhenoAssistant paper describes this integrated "
                    "Mask2Former model as the Arabidopsis leaf instance "
                    "segmentation model used in Case Study 1."
                ),
            ),
        ),
        required_context_fields=("species",),
        output_semantics=(
            "leaf instance-segmentation masks used by PhenoAssistant "
            "phenotype extraction"
        ),
        assumptions=(
            "the input is suitable for the repository's preserved "
            "instance-segmentation preprocessing path",
        ),
        limitations=(
            "fine-tuning provenance is CVPPP LSC subsets A1 and A4",
            "applicability outside the explicitly evidenced Arabidopsis "
            "scope is not asserted",
            "modality, view, illumination, and environment constraints "
            "remain intentionally unfrozen pending provenance audit",
        ),
        known_failure_conditions=(
            "a non-Arabidopsis species is outside the explicitly evidenced "
            "model-selection scope",
        ),
        provenance=(
            "PhenoAssistant Nature Communications Case Study 1; "
            "Mask2Former fine-tuned on CVPPP LSC subsets A1/A4; "
            "Phase 5 Plato reproduction evidence"
        ),
        version_or_checkpoint=(
            f"{CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID}"
            f"@{CASE1_ARABIDOPSIS_SEGMENTATION_REVISION}"
        ),
    )


CASE2_POTATO_SEGMENTATION_MODEL_ID = (
    "potato_leaf-instance-segmentation_leaf-only-sam"
)


def build_case2_potato_segmentation_envelope(
) -> ScientificOperatingEnvelope:
    """Return the narrow evidence-backed envelope for the Case 2 model."""
    return ScientificOperatingEnvelope(
        capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
        scientific_task="instance segmentation",
        constraints=(
            ApplicabilityConstraint(
                field="species",
                allowed_values=("potato",),
                severity=ConstraintSeverity.HARD,
                rationale=(
                    "The PhenoAssistant paper describes Leaf-only SAM as "
                    "the potato leaf segmentation model integrated for "
                    "Case Study 2."
                ),
            ),
        ),
        required_context_fields=("species",),
        output_semantics=(
            "potato leaf instance-segmentation masks used to derive "
            "projected leaf area"
        ),
        assumptions=(
            "the input is suitable for the preserved Leaf-only SAM path",
        ),
        limitations=(
            "the paper states that the model and Case 2 dataset originate "
            "from Williams et al.",
            "the repository evidence does not currently freeze a model "
            "checkpoint hash for Leaf-only SAM",
            "view, modality, illumination, and environment constraints "
            "remain intentionally unfrozen pending provenance audit",
        ),
        known_failure_conditions=(
            "a non-potato species is outside the explicitly evidenced "
            "Case 2 model-selection scope",
        ),
        provenance=(
            "PhenoAssistant Nature Communications Case Study 2; "
            "Leaf-only SAM for potato leaf segmentation; "
            "model and 32-image dataset attributed to Williams et al."
        ),
        version_or_checkpoint=(
            "model-zoo:"
            + CASE2_POTATO_SEGMENTATION_MODEL_ID
        ),
    )


CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID = (
    "fengchen025/"
    "dinov2-base_winter-wheat_fertiliser-identification_dnd-ww2020"
)

CASE3_WINTER_WHEAT_CLASSIFICATION_REVISION = (
    "89d6b3ca17dba118d7d25c7b8a87ff205dc6235e"
)

CASE3_WINTER_WHEAT_CLASSIFICATION_WEIGHT_SHA256 = (
    "4a29f8b73438a6d16cbc80287c40002af40029fd529146f0be73d7825befbbf5"
)


def build_case3_winter_wheat_classification_envelope(
) -> ScientificOperatingEnvelope:
    """Return the evidence-backed envelope for the Case 3 full-FT classifier."""
    return ScientificOperatingEnvelope(
        capability_id=CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID,
        scientific_task="image classification",
        constraints=(
            ApplicabilityConstraint(
                field="species",
                allowed_values=("winter wheat",),
                severity=ConstraintSeverity.HARD,
                rationale=(
                    "The collaborator-provided functioning Case Study 3 "
                    "checkpoint is the fully fine-tuned DND-WW2020 winter-wheat "
                    "fertiliser-treatment classifier."
                ),
            ),
            ApplicabilityConstraint(
                field="modality",
                allowed_values=("RGB",),
                severity=ConstraintSeverity.HARD,
                rationale=(
                    "DND-WW2020 consists of UAV-based RGB images, so non-RGB "
                    "inputs are outside the directly evidenced operating scope."
                ),
            ),
        ),
        required_context_fields=(
            "species",
            "modality",
        ),
        output_semantics=(
            "seven-class fertiliser-treatment image classification with labels "
            "unfertilized, _PKCa, N_KCa, NP_Ca, NPK_, NPKCa, and NPKCa+m+s"
        ),
        assumptions=(
            "the input follows the preserved PhenoAssistant image-classification "
            "preprocessing path",
        ),
        limitations=(
            "training provenance is DND-WW2020 winter-wheat UAV RGB imagery",
            "the current request schema does not encode UAV acquisition platform "
            "as a dedicated operating-envelope field",
            "the official README montage GPU smoke establishes compatibility only "
            "and is not an accuracy estimate",
            "applicability to winter rye, other species, non-RGB modalities, or "
            "other acquisition regimes is not asserted",
        ),
        known_failure_conditions=(
            "a non-winter-wheat species is outside the directly evidenced scope",
            "a non-RGB modality is outside the directly evidenced scope",
        ),
        provenance=(
            "PhenoAssistant Nature Communications Case Study 3; Feng Chen "
            "collaborator clarification dated 2026-10-14; public full-FT "
            "DND-WW2020 checkpoint; Plato checkpoint-integrity audit and "
            "PEFT-isolated RTX A4000 compatibility execution"
        ),
        version_or_checkpoint=(
            f"{CASE3_WINTER_WHEAT_CLASSIFICATION_MODEL_ID}"
            f"@{CASE3_WINTER_WHEAT_CLASSIFICATION_REVISION}"
            f"#sha256={CASE3_WINTER_WHEAT_CLASSIFICATION_WEIGHT_SHA256}"
        ),
    )


def build_default_provenance_catalogue(
) -> tuple[ScientificOperatingEnvelope, ...]:
    """Return the currently evidence-backed instance-segmentation catalogue."""
    return (
        build_case1_arabidopsis_segmentation_envelope(),
        build_case2_potato_segmentation_envelope(),
        build_case3_winter_wheat_classification_envelope(),
    )
