"""Scientific-applicability research primitives for PhenoGuard."""

from research.phenoguard.contracts import (
    ApplicabilityConstraint,
    ApplicabilityDecision,
    ConstraintEvaluation,
    ConstraintSeverity,
    ScientificOperatingEnvelope,
    ScientificRequestContext,
    ScientificApplicabilityAssessment,
)
from research.phenoguard.checker import assess_scientific_applicability
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    CASE1_ARABIDOPSIS_SEGMENTATION_REVISION,
    build_case1_arabidopsis_segmentation_envelope,
)

__all__ = [
    "ApplicabilityConstraint",
    "ApplicabilityDecision",
    "ConstraintEvaluation",
    "ConstraintSeverity",
    "ScientificOperatingEnvelope",
    "ScientificRequestContext",
    "ScientificApplicabilityAssessment",
    "assess_scientific_applicability",
    "CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID",
    "CASE1_ARABIDOPSIS_SEGMENTATION_REVISION",
    "build_case1_arabidopsis_segmentation_envelope",
]
