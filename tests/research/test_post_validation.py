"""Phase 7G bounded post-execution scientific-validation tests."""

from __future__ import annotations

from research.phenoguard.post_validation import (
    ValidationIssueCode,
    validate_identifier_preservation,
    validate_phenotype_records,
    validate_statistical_claim,
)


def test_valid_phenotype_records_are_safe_to_report() -> None:
    result = validate_phenotype_records(
        (
            {
                "leaf_count": 5,
                "projected_leaf_area": 123.4,
            },
            {
                "leaf_count": 0.0,
                "projected_leaf_area": 0,
            },
        )
    )

    assert result.safe_to_report is True
    assert result.issues == ()


def test_negative_leaf_count_fails_closed() -> None:
    result = validate_phenotype_records(
        (
            {
                "leaf_count": -1,
                "projected_leaf_area": 10.0,
            },
        )
    )

    assert result.safe_to_report is False
    assert ValidationIssueCode.NEGATIVE_LEAF_COUNT in {
        issue.code
        for issue in result.issues
    }


def test_fractional_leaf_count_fails_closed() -> None:
    result = validate_phenotype_records(
        (
            {
                "leaf_count": 2.5,
                "projected_leaf_area": 10.0,
            },
        )
    )

    assert result.safe_to_report is False
    assert ValidationIssueCode.NON_INTEGER_LEAF_COUNT in {
        issue.code
        for issue in result.issues
    }


def test_negative_projected_leaf_area_fails_closed() -> None:
    result = validate_phenotype_records(
        (
            {
                "leaf_count": 2,
                "projected_leaf_area": -0.1,
            },
        )
    )

    assert result.safe_to_report is False
    assert ValidationIssueCode.NEGATIVE_PROJECTED_LEAF_AREA in {
        issue.code
        for issue in result.issues
    }


def test_missing_phenotype_field_fails_closed() -> None:
    result = validate_phenotype_records(
        (
            {
                "leaf_count": 2,
            },
        )
    )

    assert result.safe_to_report is False
    assert ValidationIssueCode.MISSING_FIELD in {
        issue.code
        for issue in result.issues
    }


def test_exact_statistical_claim_is_safe() -> None:
    result = validate_statistical_claim(
        tool_p_value=0.01,
        reported_p_value=0.01,
        alpha=0.05,
        reported_significant=True,
    )

    assert result.safe_to_report is True
    assert result.issues == ()


def test_p_value_mismatch_fails_closed() -> None:
    result = validate_statistical_claim(
        tool_p_value=0.01,
        reported_p_value=0.02,
        alpha=0.05,
        reported_significant=True,
    )

    assert result.safe_to_report is False
    assert ValidationIssueCode.P_VALUE_MISMATCH in {
        issue.code
        for issue in result.issues
    }


def test_significance_mismatch_fails_closed() -> None:
    result = validate_statistical_claim(
        tool_p_value=0.10,
        reported_p_value=0.10,
        alpha=0.05,
        reported_significant=True,
    )

    assert result.safe_to_report is False
    assert ValidationIssueCode.SIGNIFICANCE_MISMATCH in {
        issue.code
        for issue in result.issues
    }


def test_invalid_statistical_inputs_fail_closed() -> None:
    result = validate_statistical_claim(
        tool_p_value=1.2,
        reported_p_value=1.2,
        alpha=1.0,
        reported_significant=False,
    )

    assert result.safe_to_report is False
    assert ValidationIssueCode.INVALID_P_VALUE in {
        issue.code
        for issue in result.issues
    }
    assert ValidationIssueCode.INVALID_ALPHA in {
        issue.code
        for issue in result.issues
    }


def test_exact_identifier_preservation_is_safe() -> None:
    result = validate_identifier_preservation(
        expected_ids=("sample-a", "sample-b"),
        observed_ids=("sample-a", "sample-b"),
    )

    assert result.safe_to_report is True
    assert result.issues == ()


def test_identifier_order_or_identity_mismatch_fails_closed() -> None:
    result = validate_identifier_preservation(
        expected_ids=("sample-a", "sample-b"),
        observed_ids=("sample-b", "sample-a"),
    )

    assert result.safe_to_report is False
    assert ValidationIssueCode.IDENTIFIER_MISMATCH in {
        issue.code
        for issue in result.issues
    }


def test_duplicate_identifiers_fail_closed() -> None:
    result = validate_identifier_preservation(
        expected_ids=("sample-a", "sample-b"),
        observed_ids=("sample-a", "sample-a"),
    )

    assert result.safe_to_report is False
    assert ValidationIssueCode.DUPLICATE_IDENTIFIER in {
        issue.code
        for issue in result.issues
    }
