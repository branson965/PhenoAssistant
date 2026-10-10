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
