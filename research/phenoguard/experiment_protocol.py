"""Prospectively frozen IJCAI 2027 experiment-protocol contracts.

This module freezes condition identities, controlled-variable requirements, metric
identifiers, and the pre-outcome claim boundary. It does not execute experiments.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class ConditionId(StrEnum):
    MODEL_ONLY = "C0_MODEL_ONLY"
    MANAGER_TOOL_NAMES = "C1_MANAGER_TOOL_NAMES"
    MANAGER_TOOL_DESCRIPTIONS = "C2_MANAGER_TOOL_DESCRIPTIONS"
    MANAGER_TOOL_SCHEMAS = "C3_MANAGER_TOOL_SCHEMAS"
    MANAGER_GENERIC_CRITIC = "C4_MANAGER_GENERIC_CRITIC"
    STRUCTURAL_VALIDATOR = "C5_STRUCTURAL_VALIDATOR"
    SOE_ONLY = "C6_SOE_ONLY"
    SOE_VERIFIER = "C7_SOE_VERIFIER"
    FULL_PHENOGUARD = "C8_FULL_PHENOGUARD"
    EXPERT_ORACLE = "C9_EXPERT_ORACLE"


class VerificationMode(StrEnum):
    NONE = "none"
    GENERIC_CRITIC = "generic_critic"
    STRUCTURAL_ONLY = "structural_only"
    SOE_ONLY = "scientific_operating_envelope_only"
    SOE_VERIFIER = "scientific_operating_envelope_plus_verifier"
    FULL_PHENOGUARD = "full_phenoguard"
    EXPERT_ORACLE = "expert_oracle"


class InterfaceMode(StrEnum):
    NONE = "none"
    DIRECT = "direct"
    MCP = "mcp"
    EXPERT = "expert"


class AgentArchitecture(StrEnum):
    MODEL_ONLY = "model_only"
    MANAGER = "manager"
    EXPERT = "expert"


class RequiredMetric(StrEnum):
    VALID_EXECUTION_ACCURACY = "valid_execution_accuracy"
    UNSAFE_EXECUTION_RATE = "unsafe_execution_rate"
    CORRECT_ABSTENTION_RATE = "correct_abstention_rate"
    UNNECESSARY_ABSTENTION_RATE = "unnecessary_abstention_rate"
    CLARIFICATION_ACCURACY = "clarification_accuracy"
    RESELECTION_ACCURACY = "reselection_accuracy"
    COVERAGE = "coverage"
    RISK_COVERAGE = "risk_coverage"
    REPEATED_RUN_RELIABILITY = "repeated_run_reliability"
    FINAL_ANSWER_GROUNDING = "final_answer_grounding"
    LATENCY = "latency"
    COST = "cost"
    FAILURE_CATEGORY_DISTRIBUTION = "failure_category_distribution"


class ExperimentCondition(BaseModel):
    """One frozen experimental condition identity."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    condition_id: ConditionId
    architecture: AgentArchitecture
    interface: InterfaceMode
    verification: VerificationMode
    tools_available: bool
    post_validation_enabled: bool
    description: str

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("description must not be blank")

        return cleaned

    @model_validator(mode="after")
    def validate_condition_semantics(
        self,
    ) -> "ExperimentCondition":
        if self.condition_id is ConditionId.MODEL_ONLY:
            if self.tools_available:
                raise ValueError("model-only baseline must not expose tools")
            if self.interface is not InterfaceMode.NONE:
                raise ValueError("model-only baseline must use interface=none")

        if self.condition_id is ConditionId.EXPERT_ORACLE:
            if self.architecture is not AgentArchitecture.EXPERT:
                raise ValueError("expert oracle must use expert architecture")
            if self.interface is not InterfaceMode.EXPERT:
                raise ValueError("expert oracle must use expert interface")

        if self.condition_id is ConditionId.FULL_PHENOGUARD:
            if not self.post_validation_enabled:
                raise ValueError(
                    "full PhenoGuard must include post-execution validation"
                )
            if self.verification is not VerificationMode.FULL_PHENOGUARD:
                raise ValueError(
                    "full PhenoGuard condition requires full verification mode"
                )

        if (
            self.verification is VerificationMode.FULL_PHENOGUARD
            and not self.post_validation_enabled
        ):
            raise ValueError(
                "full verification mode requires post-execution validation"
            )

        return self


class ControlledVariables(BaseModel):
    """Values that must be frozen before a directly compared run set."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    provider: str
    model_id: str
    model_revision: str
    temperature: float
    max_output_tokens: int
    prompt_bundle_sha256: str
    tool_catalogue_sha256: str
    task_manifest_sha256: str
    retry_policy: str
    iteration_limit: int
    session_reset_policy: str
    package_lock_sha256: str
    hardware_class: str

    @field_validator(
        "provider",
        "model_id",
        "model_revision",
        "prompt_bundle_sha256",
        "tool_catalogue_sha256",
        "task_manifest_sha256",
        "retry_policy",
        "session_reset_policy",
        "package_lock_sha256",
        "hardware_class",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("controlled-variable fields must not be blank")

        return cleaned

    @field_validator("temperature")
    @classmethod
    def validate_temperature(
        cls,
        value: float,
    ) -> float:
        if value < 0:
            raise ValueError("temperature must be non-negative")
        return value

    @field_validator("max_output_tokens", "iteration_limit")
    @classmethod
    def validate_positive_integer(
        cls,
        value: int,
    ) -> int:
        if isinstance(value, bool) or value <= 0:
            raise ValueError("integer control values must be positive")
        return value


class IJCAIProtocolFreeze(BaseModel):
    """Machine-readable prospective protocol boundary."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["0.1"] = "0.1"
    venue: Literal["IJCAI 2027"] = "IJCAI 2027"
    internal_go_no_go: Literal["2026-11-30"] = "2026-11-30"
    conditions: tuple[ExperimentCondition, ...]
    required_metrics: tuple[RequiredMetric, ...]
    primary_interface: InterfaceMode
    portability_interfaces: tuple[InterfaceMode, ...]
    portability_condition_ids: tuple[ConditionId, ...]
    hidden_labels_available_to_method: Literal[False] = False
    negative_results_retained: Literal[True] = True
    post_unblinding_method_changes_authorized: Literal[False] = False

    @model_validator(mode="after")
    def validate_freeze(
        self,
    ) -> "IJCAIProtocolFreeze":
        condition_ids = tuple(
            condition.condition_id
            for condition in self.conditions
        )

        if len(condition_ids) != len(set(condition_ids)):
            raise ValueError("condition IDs must be unique")

        if set(condition_ids) != set(ConditionId):
            raise ValueError(
                "protocol must include every frozen condition exactly once"
            )

        if self.primary_interface is not InterfaceMode.MCP:
            raise ValueError(
                "primary tool-using comparison interface is frozen to MCP"
            )

        if set(self.portability_interfaces) != {
            InterfaceMode.DIRECT,
            InterfaceMode.MCP,
        }:
            raise ValueError(
                "portability subset must compare direct and MCP interfaces"
            )

        if ConditionId.FULL_PHENOGUARD not in self.portability_condition_ids:
            raise ValueError(
                "portability subset must include full PhenoGuard"
            )

        if len(self.required_metrics) != len(set(self.required_metrics)):
            raise ValueError("required metrics must be unique")

        if set(self.required_metrics) != set(RequiredMetric):
            raise ValueError("all authoritative IJCAI metrics must be retained")

        return self


def build_frozen_condition_catalogue(
) -> tuple[ExperimentCondition, ...]:
    """Return the frozen IJCAI baseline/method condition catalogue."""
    return (
        ExperimentCondition(
            condition_id=ConditionId.MODEL_ONLY,
            architecture=AgentArchitecture.MODEL_ONLY,
            interface=InterfaceMode.NONE,
            verification=VerificationMode.NONE,
            tools_available=False,
            post_validation_enabled=False,
            description="model without tools",
        ),
        ExperimentCondition(
            condition_id=ConditionId.MANAGER_TOOL_NAMES,
            architecture=AgentArchitecture.MANAGER,
            interface=InterfaceMode.MCP,
            verification=VerificationMode.NONE,
            tools_available=True,
            post_validation_enabled=False,
            description="Manager exposed only to tool names",
        ),
        ExperimentCondition(
            condition_id=ConditionId.MANAGER_TOOL_DESCRIPTIONS,
            architecture=AgentArchitecture.MANAGER,
            interface=InterfaceMode.MCP,
            verification=VerificationMode.NONE,
            tools_available=True,
            post_validation_enabled=False,
            description="Manager exposed to tool names and descriptions",
        ),
        ExperimentCondition(
            condition_id=ConditionId.MANAGER_TOOL_SCHEMAS,
            architecture=AgentArchitecture.MANAGER,
            interface=InterfaceMode.MCP,
            verification=VerificationMode.NONE,
            tools_available=True,
            post_validation_enabled=False,
            description="Manager exposed to tool schemas and MCP metadata",
        ),
        ExperimentCondition(
            condition_id=ConditionId.MANAGER_GENERIC_CRITIC,
            architecture=AgentArchitecture.MANAGER,
            interface=InterfaceMode.MCP,
            verification=VerificationMode.GENERIC_CRITIC,
            tools_available=True,
            post_validation_enabled=False,
            description="Manager plus generic LLM critic",
        ),
        ExperimentCondition(
            condition_id=ConditionId.STRUCTURAL_VALIDATOR,
            architecture=AgentArchitecture.MANAGER,
            interface=InterfaceMode.MCP,
            verification=VerificationMode.STRUCTURAL_ONLY,
            tools_available=True,
            post_validation_enabled=False,
            description="Manager plus deterministic structural/schema validator",
        ),
        ExperimentCondition(
            condition_id=ConditionId.SOE_ONLY,
            architecture=AgentArchitecture.MANAGER,
            interface=InterfaceMode.MCP,
            verification=VerificationMode.SOE_ONLY,
            tools_available=True,
            post_validation_enabled=False,
            description="Scientific Operating Envelope metadata only",
        ),
        ExperimentCondition(
            condition_id=ConditionId.SOE_VERIFIER,
            architecture=AgentArchitecture.MANAGER,
            interface=InterfaceMode.MCP,
            verification=VerificationMode.SOE_VERIFIER,
            tools_available=True,
            post_validation_enabled=False,
            description="Scientific Operating Envelope plus pre-execution verifier",
        ),
        ExperimentCondition(
            condition_id=ConditionId.FULL_PHENOGUARD,
            architecture=AgentArchitecture.MANAGER,
            interface=InterfaceMode.MCP,
            verification=VerificationMode.FULL_PHENOGUARD,
            tools_available=True,
            post_validation_enabled=True,
            description=(
                "full applicability verification, controlled decision policy, "
                "deterministic trace, and bounded post-execution validation"
            ),
        ),
        ExperimentCondition(
            condition_id=ConditionId.EXPERT_ORACLE,
            architecture=AgentArchitecture.EXPERT,
            interface=InterfaceMode.EXPERT,
            verification=VerificationMode.EXPERT_ORACLE,
            tools_available=True,
            post_validation_enabled=True,
            description="expert gold-label upper bound",
        ),
    )


def build_protocol_freeze() -> IJCAIProtocolFreeze:
    """Return the venue-aligned protocol structure frozen before Phase 8."""
    return IJCAIProtocolFreeze(
        conditions=build_frozen_condition_catalogue(),
        required_metrics=tuple(RequiredMetric),
        primary_interface=InterfaceMode.MCP,
        portability_interfaces=(
            InterfaceMode.DIRECT,
            InterfaceMode.MCP,
        ),
        portability_condition_ids=(
            ConditionId.MANAGER_TOOL_SCHEMAS,
            ConditionId.FULL_PHENOGUARD,
        ),
    )
