"""Typed MAF boundary for the existing mixed-ANOVA implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, Protocol, cast

from agent_framework import FunctionTool
from pydantic import BaseModel, ConfigDict, field_validator


class MixedAnovaInput(BaseModel):
    """Model-controlled mixed-ANOVA column selections."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    descriptor: str
    within_subject_factor: str
    between_subject_factor: str
    subject_id: str

    @field_validator("*")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        """Strip column names and reject empty or whitespace-only values."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("mixed-ANOVA arguments must not be blank")
        return stripped


class MixedAnovaResult(BaseModel):
    """Stable result envelope for the mixed-ANOVA tool."""

    schema_version: Literal["1"] = "1"
    tool_name: Literal["perform_mixed_anova"] = "perform_mixed_anova"
    arguments: MixedAnovaInput
    records: list[dict[str, Any]]


class AnovaCallable(Protocol):
    """Callable boundary matching the existing ``perform_anova`` invocation."""

    def __call__(
        self,
        data_path: str,
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]: ...


def resolve_real_anova_callable() -> AnovaCallable:
    """Import the scientific implementation only when explicitly requested."""
    from functions.stat_test import perform_anova

    return cast(AnovaCallable, perform_anova)


def create_mixed_anova_tool(
    data_path: str,
    anova_callable: AnovaCallable | None = None,
) -> FunctionTool:
    """Bind a trusted data path and callable behind a four-field MAF tool."""
    implementation = (
        resolve_real_anova_callable() if anova_callable is None else anova_callable
    )

    def perform_mixed_anova(
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
    ) -> MixedAnovaResult:
        arguments = MixedAnovaInput(
            descriptor=descriptor,
            within_subject_factor=within_subject_factor,
            between_subject_factor=between_subject_factor,
            subject_id=subject_id,
        )
        records = implementation(
            data_path,
            arguments.descriptor,
            arguments.within_subject_factor,
            arguments.between_subject_factor,
            arguments.subject_id,
            save_path=None,
        )
        return MixedAnovaResult(arguments=arguments, records=records)

    return FunctionTool(
        name="perform_mixed_anova",
        description=(
            "Perform a mixed-design repeated-measures ANOVA using the trusted "
            "application dataset and the supplied column names."
        ),
        func=perform_mixed_anova,
        input_model=MixedAnovaInput,
    )
