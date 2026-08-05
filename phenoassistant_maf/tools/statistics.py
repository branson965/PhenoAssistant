"""Typed MAF adapters for PhenoAssistant statistical tests."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, Literal, Protocol, cast

from agent_framework import FunctionTool
from pydantic import BaseModel, ConfigDict, field_validator


def _normalise_trusted_data_path(data_path: str) -> str:
    """Reject a blank trusted application data path."""
    normalised = data_path.strip()

    if not normalised:
        raise ValueError("trusted data_path must not be blank")

    return normalised


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
        """Trim column names and reject blank values."""
        stripped = value.strip()

        if not stripped:
            raise ValueError(
                "mixed-ANOVA arguments must not be blank"
            )

        return stripped


class MixedAnovaResult(BaseModel):
    """Stable result envelope for mixed-ANOVA execution."""

    schema_version: Literal["1"] = "1"
    tool_name: Literal["perform_anova"] = "perform_anova"
    arguments: MixedAnovaInput
    records: list[dict[str, Any]]


class TukeyInput(BaseModel):
    """Model-controlled Tukey-Kramer column selections."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    descriptor: str
    between_subject_factor: str
    subject_id: str

    @field_validator("*")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        """Trim column names and reject blank values."""
        stripped = value.strip()

        if not stripped:
            raise ValueError(
                "Tukey-Kramer arguments must not be blank"
            )

        return stripped


class TukeyResult(BaseModel):
    """Stable result envelope for Tukey-Kramer execution."""

    schema_version: Literal["1"] = "1"
    tool_name: Literal["perform_tukey_test"] = "perform_tukey_test"
    arguments: TukeyInput
    records: list[dict[str, Any]]


class AnovaCallable(Protocol):
    """Boundary matching the original perform_anova invocation."""

    def __call__(
        self,
        data_path: str,
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]: ...


class TukeyCallable(Protocol):
    """Boundary matching the original perform_tukey_test invocation."""

    def __call__(
        self,
        data_path: str,
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]: ...


AnovaHandler = Callable[
    [str, str, str, str],
    MixedAnovaResult,
]

TukeyHandler = Callable[
    [str, str, str],
    TukeyResult,
]


def resolve_real_anova_callable() -> AnovaCallable:
    """Import the original ANOVA implementation only on explicit construction."""
    from functions.stat_test import perform_anova

    return cast(AnovaCallable, perform_anova)


def resolve_real_tukey_callable() -> TukeyCallable:
    """Import the original Tukey implementation only on explicit construction."""
    from functions.stat_test import perform_tukey_test

    return cast(TukeyCallable, perform_tukey_test)


def build_anova_handler(
    data_path: str,
    anova_callable: AnovaCallable | None = None,
) -> AnovaHandler:
    """Bind the trusted data path behind a four-field ANOVA interface."""
    trusted_data_path = _normalise_trusted_data_path(data_path)

    implementation = (
        resolve_real_anova_callable()
        if anova_callable is None
        else anova_callable
    )

    def perform_anova(
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
            trusted_data_path,
            arguments.descriptor,
            arguments.within_subject_factor,
            arguments.between_subject_factor,
            arguments.subject_id,
            save_path=None,
        )

        if not isinstance(records, list):
            raise TypeError(
                "perform_anova must return list[dict] when save_path is None"
            )

        return MixedAnovaResult(
            arguments=arguments,
            records=records,
        )

    expected_parameters = (
        "descriptor",
        "within_subject_factor",
        "between_subject_factor",
        "subject_id",
    )

    if tuple(inspect.signature(perform_anova).parameters) != expected_parameters:
        raise RuntimeError(
            "ANOVA handler exposes an unexpected signature"
        )

    return perform_anova


def build_tukey_handler(
    data_path: str,
    tukey_callable: TukeyCallable | None = None,
) -> TukeyHandler:
    """Bind the trusted data path behind a three-field Tukey interface."""
    trusted_data_path = _normalise_trusted_data_path(data_path)

    implementation = (
        resolve_real_tukey_callable()
        if tukey_callable is None
        else tukey_callable
    )

    def perform_tukey_test(
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
    ) -> TukeyResult:
        arguments = TukeyInput(
            descriptor=descriptor,
            between_subject_factor=between_subject_factor,
            subject_id=subject_id,
        )

        records = implementation(
            trusted_data_path,
            arguments.descriptor,
            arguments.between_subject_factor,
            arguments.subject_id,
            save_path=None,
        )

        if not isinstance(records, list):
            raise TypeError(
                "perform_tukey_test must return list[dict] "
                "when save_path is None"
            )

        return TukeyResult(
            arguments=arguments,
            records=records,
        )

    expected_parameters = (
        "descriptor",
        "between_subject_factor",
        "subject_id",
    )

    if tuple(
        inspect.signature(perform_tukey_test).parameters
    ) != expected_parameters:
        raise RuntimeError(
            "Tukey handler exposes an unexpected signature"
        )

    return perform_tukey_test


def create_anova_tool(
    data_path: str,
    anova_callable: AnovaCallable | None = None,
) -> FunctionTool:
    """Expose the original ANOVA implementation through MAF."""
    return FunctionTool(
        name="perform_anova",
        description=(
            "Perform a mixed-design repeated-measures ANOVA using the "
            "trusted application dataset and supplied column names."
        ),
        func=build_anova_handler(
            data_path=data_path,
            anova_callable=anova_callable,
        ),
        input_model=MixedAnovaInput,
    )


def create_tukey_tool(
    data_path: str,
    tukey_callable: TukeyCallable | None = None,
) -> FunctionTool:
    """Expose the original Tukey-Kramer implementation through MAF."""
    return FunctionTool(
        name="perform_tukey_test",
        description=(
            "Perform a Tukey-Kramer post-hoc test using the trusted "
            "application dataset and supplied column names."
        ),
        func=build_tukey_handler(
            data_path=data_path,
            tukey_callable=tukey_callable,
        ),
        input_model=TukeyInput,
    )
