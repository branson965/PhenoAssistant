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

__all__ = [
    "ApplicabilityConstraint",
    "ApplicabilityDecision",
    "ConstraintEvaluation",
    "ConstraintSeverity",
    "ScientificOperatingEnvelope",
    "ScientificRequestContext",
    "ScientificApplicabilityAssessment",
    "assess_scientific_applicability",
]
