"""Deterministic catalogue-level scientific applicability resolution."""

from __future__ import annotations

from research.phenoguard.checker import assess_scientific_applicability
from research.phenoguard.contracts import (
    ApplicabilityDecision,
    CatalogueApplicabilityResolution,
    ScientificOperatingEnvelope,
    ScientificRequestContext,
)


def resolve_capability_catalogue(
    envelopes: tuple[ScientificOperatingEnvelope, ...],
    request: ScientificRequestContext,
    *,
    requested_capability_id: str | None = None,
) -> CatalogueApplicabilityResolution:
    """Resolve one request across a bounded capability catalogue.

    RESELECT is emitted only when the requested capability is not executable
    and exactly one alternative capability is executable.

    RECOMMEND_TRAINING is intentionally not emitted here. That decision requires
    a separate, explicit training-readiness policy.
    """
    if not envelopes:
        raise ValueError("capability catalogue must not be empty")

    capability_ids = tuple(
        envelope.capability_id
        for envelope in envelopes
    )

    if len(capability_ids) != len(set(capability_ids)):
        raise ValueError(
            "capability catalogue must use unique capability IDs"
        )

    assessments = tuple(
        assess_scientific_applicability(
            envelope,
            request,
        )
        for envelope in envelopes
    )

    by_id = {
        assessment.capability_id: assessment
        for assessment in assessments
    }

    executable = tuple(
        assessment.capability_id
        for assessment in assessments
        if assessment.decision is ApplicabilityDecision.EXECUTE
    )

    if requested_capability_id in executable:
        decision = ApplicabilityDecision.EXECUTE
        selected = requested_capability_id
    elif len(executable) == 1:
        selected = executable[0]

        if requested_capability_id is None:
            decision = ApplicabilityDecision.EXECUTE
        else:
            decision = ApplicabilityDecision.RESELECT
    elif len(executable) > 1:
        decision = ApplicabilityDecision.CLARIFY
        selected = None
    else:
        selected = None

        requested_assessment = (
            by_id.get(requested_capability_id)
            if requested_capability_id is not None
            else None
        )

        if (
            requested_assessment is not None
            and requested_assessment.decision
            is ApplicabilityDecision.CLARIFY
        ):
            decision = ApplicabilityDecision.CLARIFY
        elif any(
            assessment.decision is ApplicabilityDecision.CLARIFY
            for assessment in assessments
        ):
            decision = ApplicabilityDecision.CLARIFY
        else:
            decision = ApplicabilityDecision.ABSTAIN

    return CatalogueApplicabilityResolution(
        decision=decision,
        requested_capability_id=requested_capability_id,
        selected_capability_id=selected,
        executable_capability_ids=executable,
        assessments=assessments,
    )
