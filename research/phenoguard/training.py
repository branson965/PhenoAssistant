"""Evidence-backed training recommendation policy for Phase 7D."""

from __future__ import annotations

from research.phenoguard.contracts import (
    ScientificRequestContext,
    TrainingReadinessAssessment,
    TrainingReadinessContext,
)


def _normalise(value: str) -> str:
    return value.strip().casefold()


def assess_training_readiness(
    request: ScientificRequestContext,
    readiness: TrainingReadinessContext,
) -> TrainingReadinessAssessment:
    """Assess whether recommending new model training is justified.

    Phase 7D deliberately freezes only the image-classification training path
    because the PhenoAssistant paper and Case Study 3 explicitly document that
    workflow end to end.
    """
    task_supported = (
        _normalise(request.scientific_task)
        == "image classification"
    )

    missing: list[str] = []

    if task_supported:
        if not readiness.dataset_available:
            missing.append("labelled_dataset")
        else:
            if not readiness.labels_available:
                missing.append("labels")

            if not readiness.dataset_format_valid:
                missing.append("supported_dataset_format")

    recommend = (
        task_supported
        and not missing
    )

    return TrainingReadinessAssessment(
        task_supported=task_supported,
        recommend_training=recommend,
        missing_requirements=tuple(missing),
        policy_scope=(
            "Phase 7D v0.1: PhenoAssistant automatic image-classification "
            "training path documented in Case Study 3 and repository code"
        ),
    )
