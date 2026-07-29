"""Tests for the mixed-ANOVA MAF tool boundary."""

from __future__ import annotations

import importlib
import sys
from typing import Any
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from maf_poc.tool_adapter import (
    MixedAnovaInput,
    MixedAnovaResult,
    create_mixed_anova_tool,
)

VALID_ARGUMENTS = {
    "descriptor": "height",
    "within_subject_factor": "time",
    "between_subject_factor": "treatment",
    "subject_id": "plant_id",
}


def test_input_requires_all_four_fields() -> None:
    for missing in VALID_ARGUMENTS:
        values = VALID_ARGUMENTS.copy()
        values.pop(missing)
        with pytest.raises(ValidationError):
            MixedAnovaInput(**values)


@pytest.mark.parametrize("field_name", VALID_ARGUMENTS)
@pytest.mark.parametrize("blank", ["", " ", "\t"])
def test_input_rejects_blank_values(field_name: str, blank: str) -> None:
    values = VALID_ARGUMENTS.copy()
    values[field_name] = blank
    with pytest.raises(ValidationError, match="must not be blank"):
        MixedAnovaInput(**values)


def test_input_trims_whitespace() -> None:
    model = MixedAnovaInput(
        **{name: f"  {value}\t" for name, value in VALID_ARGUMENTS.items()}
    )
    assert model.model_dump() == VALID_ARGUMENTS


def test_input_rejects_extra_arguments() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        MixedAnovaInput(**VALID_ARGUMENTS, data_path="/untrusted.csv")


def test_tool_schema_hides_bound_data_path_and_save_path() -> None:
    tool = create_mixed_anova_tool("/trusted/data.csv", Mock())
    schema = tool.parameters()

    assert tool.name == "perform_mixed_anova"
    assert set(schema["properties"]) == set(VALID_ARGUMENTS)
    assert set(schema["required"]) == set(VALID_ARGUMENTS)
    assert "data_path" not in str(schema)
    assert "save_path" not in str(schema)


@pytest.mark.asyncio
async def test_tool_delegates_once_and_preserves_records() -> None:
    records: list[dict[str, Any]] = [{"Source": "time", "F": 4.25, "p-unc": 0.03}]
    implementation = Mock(return_value=records)
    tool = create_mixed_anova_tool("/trusted/data.csv", implementation)

    result = await tool.invoke(arguments=VALID_ARGUMENTS, skip_parsing=True)

    implementation.assert_called_once_with(
        "/trusted/data.csv",
        "height",
        "time",
        "treatment",
        "plant_id",
        save_path=None,
    )
    assert result == MixedAnovaResult(
        arguments=MixedAnovaInput(**VALID_ARGUMENTS),
        records=records,
    )
    assert result.records == records


@pytest.mark.asyncio
async def test_underlying_exception_remains_observable() -> None:
    implementation = Mock(side_effect=RuntimeError("scientific failure"))
    tool = create_mixed_anova_tool("/trusted/data.csv", implementation)

    with pytest.raises(RuntimeError, match="scientific failure"):
        await tool.invoke(arguments=VALID_ARGUMENTS, skip_parsing=True)

    implementation.assert_called_once()


def test_import_does_not_import_real_statistical_module() -> None:
    sys.modules.pop("maf_poc.tool_adapter", None)
    sys.modules.pop("functions.stat_test", None)

    importlib.import_module("maf_poc.tool_adapter")

    assert "functions.stat_test" not in sys.modules
