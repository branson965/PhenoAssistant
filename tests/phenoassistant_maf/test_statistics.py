"""Tests for production ANOVA and Tukey adapters."""

from __future__ import annotations

import inspect

import pytest
from pydantic import ValidationError

from phenoassistant_maf.tools.statistics import (
    MixedAnovaInput,
    TukeyInput,
    build_anova_handler,
    build_tukey_handler,
    create_anova_tool,
    create_tukey_tool,
)


class RecordingAnova:
    def __init__(self, result: object | None = None) -> None:
        self.result = (
            [{"Source": "Interaction", "p-unc": 0.001}]
            if result is None
            else result
        )
        self.calls: list[tuple[object, ...]] = []

    def __call__(
        self,
        data_path: str,
        descriptor: str,
        within_subject_factor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> object:
        self.calls.append(
            (
                data_path,
                descriptor,
                within_subject_factor,
                between_subject_factor,
                subject_id,
                save_path,
            )
        )
        return self.result


class RecordingTukey:
    def __init__(self, result: object | None = None) -> None:
        self.result = (
            [{"A": "col0", "B": "ctr1", "p-tukey": 0.001}]
            if result is None
            else result
        )
        self.calls: list[tuple[object, ...]] = []

    def __call__(
        self,
        data_path: str,
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> object:
        self.calls.append(
            (
                data_path,
                descriptor,
                between_subject_factor,
                subject_id,
                save_path,
            )
        )
        return self.result


def test_anova_input_trims_column_names() -> None:
    arguments = MixedAnovaInput(
        descriptor=" PLA ",
        within_subject_factor=" Day ",
        between_subject_factor=" Ecotype ",
        subject_id=" Plant ",
    )

    assert arguments.descriptor == "PLA"
    assert arguments.within_subject_factor == "Day"
    assert arguments.between_subject_factor == "Ecotype"
    assert arguments.subject_id == "Plant"


def test_anova_input_rejects_blank_column_name() -> None:
    with pytest.raises(ValidationError):
        MixedAnovaInput(
            descriptor=" ",
            within_subject_factor="Day",
            between_subject_factor="Ecotype",
            subject_id="Plant",
        )


def test_tukey_input_trims_column_names() -> None:
    arguments = TukeyInput(
        descriptor=" PLA ",
        between_subject_factor=" Ecotype ",
        subject_id=" Plant ",
    )

    assert arguments.descriptor == "PLA"
    assert arguments.between_subject_factor == "Ecotype"
    assert arguments.subject_id == "Plant"


def test_anova_handler_binds_trusted_path_and_delegates_once() -> None:
    implementation = RecordingAnova()
    handler = build_anova_handler(
        "/trusted/data.csv",
        implementation,
    )

    result = handler(
        "PLA",
        "Day",
        "Ecotype",
        "Plant",
    )

    assert implementation.calls == [
        (
            "/trusted/data.csv",
            "PLA",
            "Day",
            "Ecotype",
            "Plant",
            None,
        )
    ]

    assert result.tool_name == "perform_anova"
    assert result.records == [
        {"Source": "Interaction", "p-unc": 0.001}
    ]


def test_tukey_handler_binds_trusted_path_and_delegates_once() -> None:
    implementation = RecordingTukey()
    handler = build_tukey_handler(
        "/trusted/data.csv",
        implementation,
    )

    result = handler(
        "PLA",
        "Ecotype",
        "Plant",
    )

    assert implementation.calls == [
        (
            "/trusted/data.csv",
            "PLA",
            "Ecotype",
            "Plant",
            None,
        )
    ]

    assert result.tool_name == "perform_tukey_test"
    assert result.records == [
        {"A": "col0", "B": "ctr1", "p-tukey": 0.001}
    ]


def test_anova_handler_rejects_non_record_result() -> None:
    handler = build_anova_handler(
        "/trusted/data.csv",
        RecordingAnova(result="saved"),
    )

    with pytest.raises(
        TypeError,
        match=r"must return list\[dict\]",
    ):
        handler("PLA", "Day", "Ecotype", "Plant")


def test_tukey_handler_rejects_non_record_result() -> None:
    handler = build_tukey_handler(
        "/trusted/data.csv",
        RecordingTukey(result="saved"),
    )

    with pytest.raises(
        TypeError,
        match=r"must return list\[dict\]",
    ):
        handler("PLA", "Ecotype", "Plant")


def test_statistical_handlers_hide_path_and_save_path() -> None:
    anova_handler = build_anova_handler(
        "/trusted/data.csv",
        RecordingAnova(),
    )

    tukey_handler = build_tukey_handler(
        "/trusted/data.csv",
        RecordingTukey(),
    )

    assert tuple(inspect.signature(anova_handler).parameters) == (
        "descriptor",
        "within_subject_factor",
        "between_subject_factor",
        "subject_id",
    )

    assert tuple(inspect.signature(tukey_handler).parameters) == (
        "descriptor",
        "between_subject_factor",
        "subject_id",
    )


def test_statistical_tool_names_match_original_registration() -> None:
    anova_tool = create_anova_tool(
        "/trusted/data.csv",
        RecordingAnova(),
    )

    tukey_tool = create_tukey_tool(
        "/trusted/data.csv",
        RecordingTukey(),
    )

    assert anova_tool.name == "perform_anova"
    assert tukey_tool.name == "perform_tukey_test"


def test_statistical_handlers_reject_blank_trusted_path() -> None:
    with pytest.raises(
        ValueError,
        match="trusted data_path must not be blank",
    ):
        build_anova_handler(" ", RecordingAnova())

    with pytest.raises(
        ValueError,
        match="trusted data_path must not be blank",
    ):
        build_tukey_handler("\t", RecordingTukey())
