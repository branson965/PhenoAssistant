"""Deterministic pre-execution scientific-applicability checker."""

from __future__ import annotations

from research.phenoguard.contracts import (
    ApplicabilityDecision,
    ConstraintEvaluation,
    ConstraintSeverity,
    ScientificApplicabilityAssessment,
    ScientificOperatingEnvelope,
    ScientificRequestContext,
)


def _normalise(value: str) -> str:
    return value.strip().casefold()


def _missing_metadata_keys(
    envelope: ScientificOperatingEnvelope,
    request: ScientificRequestContext,
) -> tuple[str, ...]:
    available = {
        key.casefold()
        for key in request.metadata
    }

    return tuple(
        key
        for key in envelope.required_metadata_keys
        if key.casefold() not in available
    )


def assess_scientific_applicability(
    envelope: ScientificOperatingEnvelope,
    request: ScientificRequestContext,
) -> ScientificApplicabilityAssessment:
    """Evaluate one capability against one request without executing the tool.

    This v0.1 deterministic checker emits EXECUTE, CLARIFY, or ABSTAIN.

    RESELECT and RECOMMEND_TRAINING remain valid system-level decisions but require
    evidence from a capability catalogue or training-readiness policy that is outside
    this single-capability primitive. They must not be inferred here.
    """
    task_match = (
        _normalise(envelope.scientific_task)
        == _normalise(request.scientific_task)
    )

    missing_context_fields = tuple(
        field
        for field in envelope.required_context_fields
        if getattr(request, field) is None
    )

    missing_metadata_keys = _missing_metadata_keys(
        envelope,
        request,
    )

    evaluations: list[ConstraintEvaluation] = []
    hard_violations: list[ConstraintEvaluation] = []
    soft_warnings: list[ConstraintEvaluation] = []

    for constraint in envelope.constraints:
        observed = getattr(
            request,
            constraint.field,
        )

        if observed is None:
            evaluation = ConstraintEvaluation(
                field=constraint.field,
                severity=constraint.severity,
                observed_value=None,
                allowed_values=constraint.allowed_values,
                matched=None,
                rationale=constraint.rationale,
            )
            evaluations.append(evaluation)
            continue

        allowed = {
            _normalise(value)
            for value in constraint.allowed_values
        }
        matched = _normalise(observed) in allowed

        evaluation = ConstraintEvaluation(
            field=constraint.field,
            severity=constraint.severity,
            observed_value=observed,
            allowed_values=constraint.allowed_values,
            matched=matched,
            rationale=constraint.rationale,
        )
        evaluations.append(evaluation)

        if matched:
            continue

        if constraint.severity is ConstraintSeverity.HARD:
            hard_violations.append(evaluation)
        else:
            soft_warnings.append(evaluation)

    if not task_match or hard_violations:
        decision = ApplicabilityDecision.ABSTAIN
    elif missing_context_fields or missing_metadata_keys:
        decision = ApplicabilityDecision.CLARIFY
    else:
        decision = ApplicabilityDecision.EXECUTE

    return ScientificApplicabilityAssessment(
        capability_id=envelope.capability_id,
        decision=decision,
        safe_to_execute=(
            decision is ApplicabilityDecision.EXECUTE
        ),
        task_match=task_match,
        missing_context_fields=missing_context_fields,
        missing_metadata_keys=missing_metadata_keys,
        hard_violations=tuple(hard_violations),
        soft_warnings=tuple(soft_warnings),
        evaluations=tuple(evaluations),
    )
