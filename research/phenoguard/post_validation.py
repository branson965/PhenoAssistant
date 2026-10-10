"""Deterministic post-execution scientific validation for Phase 7G.

These validators check bounded scientific invariants after a tool has executed.
They are deliberately separate from the pre-execution applicability decision.
"""

from __future__ import annotations

import math
from enum import StrEnum
from numbers import Real
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator


class ValidationSeverity(StrEnum):
    HARD = "hard"
    WARNING = "warning"


class ValidationIssueCode(StrEnum):
    MISSING_FIELD = "missing_field"
    NON_NUMERIC_VALUE = "non_numeric_value"
    NON_INTEGER_LEAF_COUNT = "non_integer_leaf_count"
    NEGATIVE_LEAF_COUNT = "negative_leaf_count"
    NEGATIVE_PROJECTED_LEAF_AREA = "negative_projected_leaf_area"
    NON_FINITE_VALUE = "non_finite_value"
    INVALID_P_VALUE = "invalid_p_value"
    INVALID_ALPHA = "invalid_alpha"
    P_VALUE_MISMATCH = "p_value_mismatch"
    SIGNIFICANCE_MISMATCH = "significance_mismatch"
    IDENTIFIER_MISMATCH = "identifier_mismatch"
    DUPLICATE_IDENTIFIER = "duplicate_identifier"


class PostValidationIssue(BaseModel):
    """One deterministic scientific validation finding."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    code: ValidationIssueCode
    severity: ValidationSeverity
    field: str | None = None
    record_index: int | None = None
    observed: str | None = None
    expected: str | None = None
    message: str


class PostExecutionValidation(BaseModel):
    """Structured post-execution scientific validation result."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: Literal["0.1"] = "0.1"
    validator_id: str
    safe_to_report: bool
    issues: tuple[PostValidationIssue, ...]

    @model_validator(mode="after")
    def validate_safety_flag(
        self,
    ) -> "PostExecutionValidation":
        has_hard = any(
            issue.severity is ValidationSeverity.HARD
            for issue in self.issues
        )

        if self.safe_to_report == has_hard:
            raise ValueError(
                "safe_to_report must be false iff at least one hard issue exists"
            )

        return self


def _issue(
    code: ValidationIssueCode,
    message: str,
    *,
    field: str | None = None,
    record_index: int | None = None,
    observed: Any | None = None,
    expected: Any | None = None,
    severity: ValidationSeverity = ValidationSeverity.HARD,
) -> PostValidationIssue:
    return PostValidationIssue(
        code=code,
        severity=severity,
        field=field,
        record_index=record_index,
        observed=None if observed is None else str(observed),
        expected=None if expected is None else str(expected),
        message=message,
    )


def _finalise(
    validator_id: str,
    issues: list[PostValidationIssue],
) -> PostExecutionValidation:
    return PostExecutionValidation(
        validator_id=validator_id,
        safe_to_report=not any(
            issue.severity is ValidationSeverity.HARD
            for issue in issues
        ),
        issues=tuple(issues),
    )


def validate_phenotype_records(
    records: tuple[dict[str, Any], ...],
    *,
    leaf_count_field: str = "leaf_count",
    projected_leaf_area_field: str = "projected_leaf_area",
) -> PostExecutionValidation:
    """Validate bounded phenotype invariants used by PhenoAssistant Case 1/2."""
    issues: list[PostValidationIssue] = []

    for index, record in enumerate(records):
        for field in (
            leaf_count_field,
            projected_leaf_area_field,
        ):
            if field not in record:
                issues.append(
                    _issue(
                        ValidationIssueCode.MISSING_FIELD,
                        "required phenotype field is missing",
                        field=field,
                        record_index=index,
                    )
                )

        if leaf_count_field in record:
            value = record[leaf_count_field]

            if isinstance(value, bool) or not isinstance(value, Real):
                issues.append(
                    _issue(
                        ValidationIssueCode.NON_NUMERIC_VALUE,
                        "leaf count must be numeric",
                        field=leaf_count_field,
                        record_index=index,
                        observed=value,
                    )
                )
            elif not math.isfinite(float(value)):
                issues.append(
                    _issue(
                        ValidationIssueCode.NON_FINITE_VALUE,
                        "leaf count must be finite",
                        field=leaf_count_field,
                        record_index=index,
                        observed=value,
                    )
                )
            else:
                numeric = float(value)

                if not numeric.is_integer():
                    issues.append(
                        _issue(
                            ValidationIssueCode.NON_INTEGER_LEAF_COUNT,
                            "leaf count must be integer-valued",
                            field=leaf_count_field,
                            record_index=index,
                            observed=value,
                        )
                    )

                if numeric < 0:
                    issues.append(
                        _issue(
                            ValidationIssueCode.NEGATIVE_LEAF_COUNT,
                            "leaf count must be non-negative",
                            field=leaf_count_field,
                            record_index=index,
                            observed=value,
                        )
                    )

        if projected_leaf_area_field in record:
            value = record[projected_leaf_area_field]

            if isinstance(value, bool) or not isinstance(value, Real):
                issues.append(
                    _issue(
                        ValidationIssueCode.NON_NUMERIC_VALUE,
                        "projected leaf area must be numeric",
                        field=projected_leaf_area_field,
                        record_index=index,
                        observed=value,
                    )
                )
            elif not math.isfinite(float(value)):
                issues.append(
                    _issue(
                        ValidationIssueCode.NON_FINITE_VALUE,
                        "projected leaf area must be finite",
                        field=projected_leaf_area_field,
                        record_index=index,
                        observed=value,
                    )
                )
            elif float(value) < 0:
                issues.append(
                    _issue(
                        ValidationIssueCode.NEGATIVE_PROJECTED_LEAF_AREA,
                        "projected leaf area must be non-negative",
                        field=projected_leaf_area_field,
                        record_index=index,
                        observed=value,
                    )
                )

    return _finalise(
        "phenotype-invariants-v0.1",
        issues,
    )


def validate_statistical_claim(
    *,
    tool_p_value: float,
    reported_p_value: float,
    alpha: float,
    reported_significant: bool,
    absolute_tolerance: float = 1e-12,
) -> PostExecutionValidation:
    """Check that a reported significance claim is grounded in tool evidence."""
    issues: list[PostValidationIssue] = []

    for field, value in (
        ("tool_p_value", tool_p_value),
        ("reported_p_value", reported_p_value),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(float(value))
            or not 0.0 <= float(value) <= 1.0
        ):
            issues.append(
                _issue(
                    ValidationIssueCode.INVALID_P_VALUE,
                    "p-value must be finite and within [0, 1]",
                    field=field,
                    observed=value,
                )
            )

    if (
        isinstance(alpha, bool)
        or not isinstance(alpha, Real)
        or not math.isfinite(float(alpha))
        or not 0.0 < float(alpha) < 1.0
    ):
        issues.append(
            _issue(
                ValidationIssueCode.INVALID_ALPHA,
                "alpha must be finite and strictly within (0, 1)",
                field="alpha",
                observed=alpha,
            )
        )

    if issues:
        return _finalise(
            "statistical-claim-grounding-v0.1",
            issues,
        )

    if not math.isclose(
        float(tool_p_value),
        float(reported_p_value),
        rel_tol=0.0,
        abs_tol=absolute_tolerance,
    ):
        issues.append(
            _issue(
                ValidationIssueCode.P_VALUE_MISMATCH,
                "reported p-value does not match the tool result",
                field="reported_p_value",
                observed=reported_p_value,
                expected=tool_p_value,
            )
        )

    expected_significant = float(tool_p_value) < float(alpha)

    if reported_significant is not expected_significant:
        issues.append(
            _issue(
                ValidationIssueCode.SIGNIFICANCE_MISMATCH,
                "reported significance does not respect the declared alpha",
                field="reported_significant",
                observed=reported_significant,
                expected=expected_significant,
            )
        )

    return _finalise(
        "statistical-claim-grounding-v0.1",
        issues,
    )


def validate_identifier_preservation(
    *,
    expected_ids: tuple[str, ...],
    observed_ids: tuple[str, ...],
) -> PostExecutionValidation:
    """Check exact sample-identifier preservation across an output artifact."""
    issues: list[PostValidationIssue] = []

    if len(expected_ids) != len(set(expected_ids)):
        issues.append(
            _issue(
                ValidationIssueCode.DUPLICATE_IDENTIFIER,
                "expected identifiers contain duplicates",
                field="expected_ids",
            )
        )

    if len(observed_ids) != len(set(observed_ids)):
        issues.append(
            _issue(
                ValidationIssueCode.DUPLICATE_IDENTIFIER,
                "observed identifiers contain duplicates",
                field="observed_ids",
            )
        )

    if expected_ids != observed_ids:
        issues.append(
            _issue(
                ValidationIssueCode.IDENTIFIER_MISMATCH,
                "output identifiers must preserve the expected ordered identity set",
                field="observed_ids",
                observed=observed_ids,
                expected=expected_ids,
            )
        )

    return _finalise(
        "identifier-preservation-v0.1",
        issues,
    )
