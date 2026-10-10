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
    TrainingReadinessAssessment,
    TrainingReadinessContext,
)
from research.phenoguard.checker import assess_scientific_applicability
from research.phenoguard.catalogue import resolve_capability_catalogue
from research.phenoguard.training import assess_training_readiness
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
    "TrainingReadinessAssessment",
    "TrainingReadinessContext",
    "assess_scientific_applicability",
    "resolve_capability_catalogue",
    "assess_training_readiness",
    "CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID",
    "CASE1_ARABIDOPSIS_SEGMENTATION_REVISION",
    "CASE2_POTATO_SEGMENTATION_MODEL_ID",
    "build_case1_arabidopsis_segmentation_envelope",
    "build_case2_potato_segmentation_envelope",
    "build_default_provenance_catalogue",
    "ApplicabilityDecisionTrace",
    "DecisionReason",
    "canonical_trace_json",
    "resolve_with_trace",
    "trace_sha256",
    "BenchmarkDecisionScore",
    "BenchmarkGoldLabel",
    "BenchmarkScenario",
    "BenchmarkSplit",
    "EvidenceSource",
    "ScenarioCategory",
    "ShiftDimension",
    "score_decision_trace",
    "validate_matched_pair",
    "PostExecutionValidation",
    "PostValidationIssue",
    "ValidationIssueCode",
    "ValidationSeverity",
    "validate_identifier_preservation",
    "validate_phenotype_records",
    "validate_statistical_claim",
]

from research.phenoguard.trace import (
    ApplicabilityDecisionTrace,
    DecisionReason,
    canonical_trace_json,
    resolve_with_trace,
    trace_sha256,
)

from research.phenoguard.benchmark import (
    BenchmarkDecisionScore,
    BenchmarkGoldLabel,
    BenchmarkScenario,
    BenchmarkSplit,
    EvidenceSource,
    ScenarioCategory,
    ShiftDimension,
    score_decision_trace,
    validate_matched_pair,
)

from research.phenoguard.post_validation import (
    PostExecutionValidation,
    PostValidationIssue,
    ValidationIssueCode,
    ValidationSeverity,
    validate_identifier_preservation,
    validate_phenotype_records,
    validate_statistical_claim,
)
