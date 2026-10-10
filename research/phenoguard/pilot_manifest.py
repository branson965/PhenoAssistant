"""Development/validation qualification manifest for the IJCAI harness.

These cases are intentionally small, mechanically adjudicable contract cases. They
qualify the experiment harness and scoring pipeline; they are not the final benchmark
and are not evidence of real-world distribution-shift performance.
"""

from __future__ import annotations

from research.phenoguard.benchmark import (
    BenchmarkGoldLabel,
    BenchmarkScenario,
    BenchmarkSplit,
    EvidenceSource,
    ScenarioCategory,
    ShiftDimension,
)
from research.phenoguard.contracts import (
    ApplicabilityDecision,
    ScientificRequestContext,
    TrainingReadinessContext,
)
from research.phenoguard.provenance import (
    CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
    CASE2_POTATO_SEGMENTATION_MODEL_ID,
)


def _scenario(
    *,
    scenario_id: str,
    split: BenchmarkSplit,
    category: ScenarioCategory,
    shift_dimension: ShiftDimension,
    scientific_task: str,
    species: str | None,
    requested_capability_id: str | None = None,
    pair_id: str | None = None,
    evidence_source: EvidenceSource = EvidenceSource.PROVENANCE_BACKED_METADATA,
    training_readiness: TrainingReadinessContext | None = None,
) -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id=scenario_id,
        pair_id=pair_id,
        split=split,
        category=category,
        evidence_source=evidence_source,
        shift_dimension=shift_dimension,
        request=ScientificRequestContext(
            scientific_task=scientific_task,
            species=species,
        ),
        requested_capability_id=requested_capability_id,
        training_readiness=training_readiness,
    )


def build_development_validation_manifest(
) -> tuple[BenchmarkScenario, ...]:
    """Return the frozen Phase 7H harness-qualification scenarios."""
    return (
        _scenario(
            scenario_id="dev-p001-valid-arabidopsis",
            pair_id="dev-p001",
            split=BenchmarkSplit.DEVELOPMENT,
            category=ScenarioCategory.VALID_EXECUTION,
            shift_dimension=ShiftDimension.NONE,
            scientific_task="instance segmentation",
            species="Arabidopsis thaliana",
            requested_capability_id=CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
        ),
        _scenario(
            scenario_id="dev-p001-species-potato",
            pair_id="dev-p001",
            split=BenchmarkSplit.DEVELOPMENT,
            category=ScenarioCategory.RESELECTION,
            shift_dimension=ShiftDimension.SPECIES,
            scientific_task="instance segmentation",
            species="potato",
            requested_capability_id=CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
        ),
        _scenario(
            scenario_id="dev-p002-valid-arabidopsis",
            pair_id="dev-p002",
            split=BenchmarkSplit.DEVELOPMENT,
            category=ScenarioCategory.VALID_EXECUTION,
            shift_dimension=ShiftDimension.NONE,
            scientific_task="instance segmentation",
            species="Arabidopsis thaliana",
            requested_capability_id=CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
        ),
        _scenario(
            scenario_id="dev-p002-missing-species",
            pair_id="dev-p002",
            split=BenchmarkSplit.DEVELOPMENT,
            category=ScenarioCategory.CLARIFICATION,
            shift_dimension=ShiftDimension.MISSING_METADATA,
            scientific_task="instance segmentation",
            species=None,
            requested_capability_id=CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
            evidence_source=EvidenceSource.SYNTHETIC_METADATA_STRESS,
        ),
        _scenario(
            scenario_id="dev-p003-valid-potato",
            pair_id="dev-p003",
            split=BenchmarkSplit.DEVELOPMENT,
            category=ScenarioCategory.VALID_EXECUTION,
            shift_dimension=ShiftDimension.NONE,
            scientific_task="instance segmentation",
            species="potato",
            requested_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
        ),
        _scenario(
            scenario_id="dev-p003-species-maize",
            pair_id="dev-p003",
            split=BenchmarkSplit.DEVELOPMENT,
            category=ScenarioCategory.ABSTENTION,
            shift_dimension=ShiftDimension.SPECIES,
            scientific_task="instance segmentation",
            species="maize",
            requested_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
        ),
        _scenario(
            scenario_id="dev-training-ready",
            split=BenchmarkSplit.DEVELOPMENT,
            category=ScenarioCategory.TRAINING_RECOMMENDATION,
            shift_dimension=ShiftDimension.CHECKPOINT_PROVENANCE,
            scientific_task="image classification",
            species="maize",
            training_readiness=TrainingReadinessContext(
                dataset_available=True,
                labels_available=True,
                dataset_format_valid=True,
            ),
        ),
        _scenario(
            scenario_id="dev-training-missing-data",
            split=BenchmarkSplit.DEVELOPMENT,
            category=ScenarioCategory.CLARIFICATION,
            shift_dimension=ShiftDimension.MISSING_METADATA,
            scientific_task="image classification",
            species="maize",
            training_readiness=TrainingReadinessContext(
                dataset_available=False,
                labels_available=False,
                dataset_format_valid=False,
            ),
            evidence_source=EvidenceSource.SYNTHETIC_METADATA_STRESS,
        ),
        _scenario(
            scenario_id="val-p001-valid-potato",
            pair_id="val-p001",
            split=BenchmarkSplit.VALIDATION,
            category=ScenarioCategory.VALID_EXECUTION,
            shift_dimension=ShiftDimension.NONE,
            scientific_task="instance segmentation",
            species="potato",
            requested_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
        ),
        _scenario(
            scenario_id="val-p001-species-arabidopsis",
            pair_id="val-p001",
            split=BenchmarkSplit.VALIDATION,
            category=ScenarioCategory.RESELECTION,
            shift_dimension=ShiftDimension.SPECIES,
            scientific_task="instance segmentation",
            species="Arabidopsis thaliana",
            requested_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
        ),
        _scenario(
            scenario_id="val-p002-valid-potato",
            pair_id="val-p002",
            split=BenchmarkSplit.VALIDATION,
            category=ScenarioCategory.VALID_EXECUTION,
            shift_dimension=ShiftDimension.NONE,
            scientific_task="instance segmentation",
            species="potato",
            requested_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
        ),
        _scenario(
            scenario_id="val-p002-missing-species",
            pair_id="val-p002",
            split=BenchmarkSplit.VALIDATION,
            category=ScenarioCategory.CLARIFICATION,
            shift_dimension=ShiftDimension.MISSING_METADATA,
            scientific_task="instance segmentation",
            species=None,
            requested_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
            evidence_source=EvidenceSource.SYNTHETIC_METADATA_STRESS,
        ),
    )


def build_development_validation_gold(
) -> tuple[BenchmarkGoldLabel, ...]:
    """Return mechanical gold labels for the harness-qualification manifest."""
    return (
        BenchmarkGoldLabel(
            scenario_id="dev-p001-valid-arabidopsis",
            expected_decision=ApplicabilityDecision.EXECUTE,
            expected_selected_capability_id=CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
            rationale_code="provenance_backed_valid_case1",
        ),
        BenchmarkGoldLabel(
            scenario_id="dev-p001-species-potato",
            expected_decision=ApplicabilityDecision.RESELECT,
            expected_selected_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
            rationale_code="species_shift_unique_case2_alternative",
        ),
        BenchmarkGoldLabel(
            scenario_id="dev-p002-valid-arabidopsis",
            expected_decision=ApplicabilityDecision.EXECUTE,
            expected_selected_capability_id=CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
            rationale_code="provenance_backed_valid_case1",
        ),
        BenchmarkGoldLabel(
            scenario_id="dev-p002-missing-species",
            expected_decision=ApplicabilityDecision.CLARIFY,
            rationale_code="required_species_missing",
        ),
        BenchmarkGoldLabel(
            scenario_id="dev-p003-valid-potato",
            expected_decision=ApplicabilityDecision.EXECUTE,
            expected_selected_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
            rationale_code="provenance_backed_valid_case2",
        ),
        BenchmarkGoldLabel(
            scenario_id="dev-p003-species-maize",
            expected_decision=ApplicabilityDecision.ABSTAIN,
            rationale_code="no_species_compatible_segmenter",
        ),
        BenchmarkGoldLabel(
            scenario_id="dev-training-ready",
            expected_decision=ApplicabilityDecision.RECOMMEND_TRAINING,
            rationale_code="classification_gap_with_ready_training_data",
        ),
        BenchmarkGoldLabel(
            scenario_id="dev-training-missing-data",
            expected_decision=ApplicabilityDecision.CLARIFY,
            rationale_code="classification_training_data_missing",
        ),
        BenchmarkGoldLabel(
            scenario_id="val-p001-valid-potato",
            expected_decision=ApplicabilityDecision.EXECUTE,
            expected_selected_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
            rationale_code="provenance_backed_valid_case2",
        ),
        BenchmarkGoldLabel(
            scenario_id="val-p001-species-arabidopsis",
            expected_decision=ApplicabilityDecision.RESELECT,
            expected_selected_capability_id=CASE1_ARABIDOPSIS_SEGMENTATION_MODEL_ID,
            rationale_code="species_shift_unique_case1_alternative",
        ),
        BenchmarkGoldLabel(
            scenario_id="val-p002-valid-potato",
            expected_decision=ApplicabilityDecision.EXECUTE,
            expected_selected_capability_id=CASE2_POTATO_SEGMENTATION_MODEL_ID,
            rationale_code="provenance_backed_valid_case2",
        ),
        BenchmarkGoldLabel(
            scenario_id="val-p002-missing-species",
            expected_decision=ApplicabilityDecision.CLARIFY,
            rationale_code="required_species_missing",
        ),
    )
