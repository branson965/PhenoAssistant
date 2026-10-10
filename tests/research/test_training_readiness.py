"""Phase 7D evidence-backed training recommendation tests."""

from __future__ import annotations

from research.phenoguard import (
    ApplicabilityDecision,
    ScientificRequestContext,
    TrainingReadinessContext,
    assess_training_readiness,
    build_default_provenance_catalogue,
    resolve_capability_catalogue,
)


def ready_training_data() -> TrainingReadinessContext:
    return TrainingReadinessContext(
        dataset_available=True,
        labels_available=True,
        dataset_format_valid=True,
    )


def classification_request() -> ScientificRequestContext:
    return ScientificRequestContext(
        scientific_task="image classification",
        species="maize",
    )


def test_ready_classification_training_is_recommendable() -> None:
    assessment = assess_training_readiness(
        classification_request(),
        ready_training_data(),
    )

    assert assessment.task_supported is True
    assert assessment.recommend_training is True
    assert assessment.missing_requirements == ()


def test_missing_dataset_requires_clarification_evidence() -> None:
    assessment = assess_training_readiness(
        classification_request(),
        TrainingReadinessContext(
            dataset_available=False,
            labels_available=False,
            dataset_format_valid=False,
        ),
    )

    assert assessment.task_supported is True
    assert assessment.recommend_training is False
    assert assessment.missing_requirements == (
        "labelled_dataset",
    )


def test_present_dataset_requires_labels_and_supported_format() -> None:
    assessment = assess_training_readiness(
        classification_request(),
        TrainingReadinessContext(
            dataset_available=True,
            labels_available=False,
            dataset_format_valid=False,
        ),
    )

    assert assessment.recommend_training is False
    assert assessment.missing_requirements == (
        "labels",
        "supported_dataset_format",
    )


def test_catalogue_gap_plus_ready_data_recommends_training() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        classification_request(),
        training_readiness=ready_training_data(),
    )

    assert result.decision is ApplicabilityDecision.RECOMMEND_TRAINING
    assert result.selected_capability_id is None
    assert result.executable_capability_ids == ()
    assert result.training_readiness is not None
    assert result.training_readiness.recommend_training is True


def test_catalogue_gap_plus_missing_dataset_clarifies() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        classification_request(),
        training_readiness=TrainingReadinessContext(
            dataset_available=False,
            labels_available=False,
            dataset_format_valid=False,
        ),
    )

    assert result.decision is ApplicabilityDecision.CLARIFY
    assert result.selected_capability_id is None
    assert result.training_readiness is not None
    assert result.training_readiness.missing_requirements == (
        "labelled_dataset",
    )


def test_no_training_evidence_preserves_abstention() -> None:
    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        classification_request(),
    )

    assert result.decision is ApplicabilityDecision.ABSTAIN
    assert result.training_readiness is None


def test_unfrozen_training_task_is_not_recommended() -> None:
    request = ScientificRequestContext(
        scientific_task="instance segmentation",
        species="maize",
    )

    assessment = assess_training_readiness(
        request,
        ready_training_data(),
    )

    assert assessment.task_supported is False
    assert assessment.recommend_training is False

    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        request,
        training_readiness=ready_training_data(),
    )

    assert result.decision is ApplicabilityDecision.ABSTAIN


def test_existing_applicable_capability_still_executes() -> None:
    request = ScientificRequestContext(
        scientific_task="instance segmentation",
        species="potato",
    )

    result = resolve_capability_catalogue(
        build_default_provenance_catalogue(),
        request,
        training_readiness=ready_training_data(),
    )

    assert result.decision is ApplicabilityDecision.EXECUTE
    assert result.selected_capability_id is not None
