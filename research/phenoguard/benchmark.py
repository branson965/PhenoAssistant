"""Frozen benchmark contracts for the IJCAI 2027 PhenoGuard study.

This module defines benchmark inputs, hidden gold labels, paired-case structure,
and deterministic decision scoring. It intentionally does not contain the final
hidden benchmark instances.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from research.phenoguard.contracts import (
    ApplicabilityDecision,
    ScientificRequestContext,
    TrainingReadinessContext,
)
from research.phenoguard.trace import ApplicabilityDecisionTrace


class BenchmarkSplit(StrEnum):
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    HIDDEN = "hidden"


class EvidenceSource(StrEnum):
    REAL_DOMAIN_SHIFT = "real_domain_shift"
    PROVENANCE_BACKED_METADATA = "provenance_backed_metadata"
    SYNTHETIC_METADATA_STRESS = "synthetic_metadata_stress"


class ShiftDimension(StrEnum):
    NONE = "none"
    SPECIES = "species"
    MODALITY = "modality"
    VIEW = "view"
    ENVIRONMENT = "environment"
    SENSOR = "sensor"
    IMAGE_QUALITY = "image_quality"
    MISSING_METADATA = "missing_metadata"
    CONFLICTING_METADATA = "conflicting_metadata"
    CHECKPOINT_PROVENANCE = "checkpoint_provenance"
    OUTPUT_SEMANTICS = "output_semantics"


class ScenarioCategory(StrEnum):
    VALID_EXECUTION = "valid_execution"
    RESELECTION = "reselection"
    CLARIFICATION = "clarification"
    ABSTENTION = "abstention"
    TRAINING_RECOMMENDATION = "training_recommendation"


class BenchmarkScenario(BaseModel):
    """System-visible input for one benchmark case."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["0.1"] = "0.1"
    scenario_id: str
    pair_id: str | None = None
    split: BenchmarkSplit
    category: ScenarioCategory
    evidence_source: EvidenceSource
    shift_dimension: ShiftDimension
    request: ScientificRequestContext
    requested_capability_id: str | None = None
    training_readiness: TrainingReadinessContext | None = None
    fixture_refs: tuple[str, ...] = ()

    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_id(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("scenario_id must not be blank")

        return cleaned

    @field_validator("pair_id")
    @classmethod
    def validate_pair_id(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("pair_id must not be blank")

        return cleaned

    @field_validator("fixture_refs")
    @classmethod
    def validate_fixture_refs(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)

        if any(not value for value in cleaned):
            raise ValueError("fixture_refs must not contain blank entries")

        if len(cleaned) != len(set(cleaned)):
            raise ValueError("fixture_refs must be unique")

        return cleaned

    @model_validator(mode="after")
    def validate_shift_semantics(
        self,
    ) -> "BenchmarkScenario":
        if self.category is ScenarioCategory.VALID_EXECUTION:
            if self.shift_dimension is not ShiftDimension.NONE:
                raise ValueError(
                    "valid execution scenarios must use shift_dimension=none"
                )

        if (
            self.evidence_source is EvidenceSource.REAL_DOMAIN_SHIFT
            and not self.fixture_refs
        ):
            raise ValueError(
                "real-domain-shift scenarios require fixture_refs"
            )

        return self


class BenchmarkGoldLabel(BaseModel):
    """Hidden/adjudicated benchmark label stored separately from the scenario."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["0.1"] = "0.1"
    scenario_id: str
    expected_decision: ApplicabilityDecision
    expected_selected_capability_id: str | None = None
    acceptable_selected_capability_ids: tuple[str, ...] = ()
    expert_adjudication_required: bool = False
    rationale_code: str

    @field_validator("scenario_id", "rationale_code")
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("required text must not be blank")

        return cleaned

    @model_validator(mode="after")
    def validate_selection_label(
        self,
    ) -> "BenchmarkGoldLabel":
        selectable = {
            ApplicabilityDecision.EXECUTE,
            ApplicabilityDecision.RESELECT,
        }

        if self.expected_decision in selectable:
            has_single = self.expected_selected_capability_id is not None
            has_set = bool(self.acceptable_selected_capability_ids)

            if not (has_single or has_set):
                raise ValueError(
                    "execute/reselect labels require an acceptable capability"
                )
        elif (
            self.expected_selected_capability_id is not None
            or self.acceptable_selected_capability_ids
        ):
            raise ValueError(
                "non-selection decisions must not encode selected capabilities"
            )

        if (
            self.expected_selected_capability_id is not None
            and self.acceptable_selected_capability_ids
        ):
            raise ValueError(
                "use either one expected capability or an acceptable set, not both"
            )

        if len(self.acceptable_selected_capability_ids) != len(
            set(self.acceptable_selected_capability_ids)
        ):
            raise ValueError(
                "acceptable_selected_capability_ids must be unique"
            )

        return self


class BenchmarkDecisionScore(BaseModel):
    """Deterministic score for one decision trace against one gold label."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["0.1"] = "0.1"
    scenario_id: str
    decision_correct: bool
    selection_correct: bool
    exact_correct: bool
    unsafe_execution: bool
    unnecessary_abstention: bool


def score_decision_trace(
    trace: ApplicabilityDecisionTrace,
    gold: BenchmarkGoldLabel,
) -> BenchmarkDecisionScore:
    """Score one trace without exposing the gold label to the method."""
    if trace.scenario_id != gold.scenario_id:
        raise ValueError("trace and gold scenario IDs must match")

    observed = trace.resolution.decision
    decision_correct = observed is gold.expected_decision

    if gold.expected_selected_capability_id is not None:
        selection_correct = (
            trace.resolution.selected_capability_id
            == gold.expected_selected_capability_id
        )
    elif gold.acceptable_selected_capability_ids:
        selection_correct = (
            trace.resolution.selected_capability_id
            in gold.acceptable_selected_capability_ids
        )
    else:
        selection_correct = (
            trace.resolution.selected_capability_id is None
        )

    exact_correct = decision_correct and selection_correct

    unsafe_execution = (
        observed in {
            ApplicabilityDecision.EXECUTE,
            ApplicabilityDecision.RESELECT,
        }
        and gold.expected_decision not in {
            ApplicabilityDecision.EXECUTE,
            ApplicabilityDecision.RESELECT,
        }
    )

    unnecessary_abstention = (
        observed is ApplicabilityDecision.ABSTAIN
        and gold.expected_decision in {
            ApplicabilityDecision.EXECUTE,
            ApplicabilityDecision.RESELECT,
            ApplicabilityDecision.CLARIFY,
            ApplicabilityDecision.RECOMMEND_TRAINING,
        }
    )

    return BenchmarkDecisionScore(
        scenario_id=gold.scenario_id,
        decision_correct=decision_correct,
        selection_correct=selection_correct,
        exact_correct=exact_correct,
        unsafe_execution=unsafe_execution,
        unnecessary_abstention=unnecessary_abstention,
    )


def validate_matched_pair(
    first: BenchmarkScenario,
    second: BenchmarkScenario,
) -> None:
    """Validate the minimum structural contract for a paired benchmark case."""
    if first.pair_id is None or second.pair_id is None:
        raise ValueError("matched benchmark cases require pair_id")

    if first.pair_id != second.pair_id:
        raise ValueError("matched benchmark cases must share pair_id")

    if first.split is not second.split:
        raise ValueError("matched benchmark cases must share split")

    categories = {
        first.category,
        second.category,
    }

    if ScenarioCategory.VALID_EXECUTION not in categories:
        raise ValueError(
            "matched pair must contain one valid-execution case"
        )

    if len(categories) != 2:
        raise ValueError(
            "matched pair must contain one valid and one perturbed case"
        )

    valid = (
        first
        if first.category is ScenarioCategory.VALID_EXECUTION
        else second
    )
    shifted = second if valid is first else first

    if valid.request.scientific_task != shifted.request.scientific_task:
        raise ValueError(
            "matched pair must preserve scientific task"
        )

    if shifted.shift_dimension is ShiftDimension.NONE:
        raise ValueError(
            "perturbed matched case must declare a shift dimension"
        )
