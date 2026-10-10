"""Scientific-applicability research primitives for PhenoGuard."""

from research.phenoguard.contracts import (
    ApplicabilityConstraint,
    ApplicabilityDecision,
    CatalogueApplicabilityResolution,
    ConstraintEvaluation,
    ConstraintSeverity,
    ScientificOperatingEnvelope,
    ScientificRequestContext,
    ScientificApplicabilityAssessment,
)
from research.phenoguard.checker import assess_scientific_applicability
from research.phenoguard.catalogue import resolve_capability_catalogue
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    CASE1_ARABIDOPSIS_SEGMENTATION_REVISION,
    CASE2_POTATO_SEGMENTATION_MODEL_ID,
    build_case1_arabidopsis_segmentation_envelope,
    build_case2_potato_segmentation_envelope,
    build_default_provenance_catalogue,
)

__all__ = [
    "ApplicabilityConstraint",
    "ApplicabilityDecision",
    "CatalogueApplicabilityResolution",
    "ConstraintEvaluation",
    "ConstraintSeverity",
    "ScientificOperatingEnvelope",
    "ScientificRequestContext",
    "ScientificApplicabilityAssessment",
    "assess_scientific_applicability",
    "resolve_capability_catalogue",
    "CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID",
    "CASE1_ARABIDOPSIS_SEGMENTATION_REVISION",
    "CASE2_POTATO_SEGMENTATION_MODEL_ID",
    "build_case1_arabidopsis_segmentation_envelope",
    "build_case2_potato_segmentation_envelope",
    "build_default_provenance_catalogue",
]
