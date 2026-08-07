"""Tests for safe read-only MAF pipeline catalogue discovery."""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from phenoassistant_maf.tools.pipeline_catalogue import (
    PipelineCatalogueInput,
    build_pipeline_catalogue_handler,
    create_pipeline_catalogue_tool,
    run_pipeline_catalogue,
)


ROOT = Path(__file__).resolve().parents[2]
PIPELINE_ZOO = ROOT / "pipeline_zoo.json"


def test_real_pipeline_zoo_is_canonicalised_without_execution() -> None:
    result = run_pipeline_catalogue(
        str(PIPELINE_ZOO),
    )

    assert result.schema_version == "1"
    assert result.tool_name == "get_pipeline_catalogue"
    assert result.arguments.family == "all"
    assert result.capability_count == 4

    by_family = {
        capability.family_id: capability
        for capability in result.capabilities
    }

    assert set(by_family) == {
        "arabidopsis_phenotype_extraction",
        "arabidopsis_longitudinal_plotting",
        "potato_phenotype_extraction",
        "arabidopsis_statistics",
    }

    assert sum(
        capability.variant_count
        for capability in result.capabilities
    ) == 20

    assert all(
        capability.variant_count == 5
        for capability in result.capabilities
    )

    arabidopsis = by_family[
        "arabidopsis_phenotype_extraction"
    ]
    assert arabidopsis.requires_gpu is True
    assert arabidopsis.execution_status == "gpu_deferred"
    assert arabidopsis.maf_replacement is None
    assert arabidopsis.legacy_dynamic_execution_allowed is False

    plotting = by_family[
        "arabidopsis_longitudinal_plotting"
    ]
    assert plotting.requires_gpu is False
    assert plotting.execution_status == "use_maf_replacement"
    assert plotting.maf_replacement == "plot_longitudinal_phenotypes"

    potato = by_family[
        "potato_phenotype_extraction"
    ]
    assert potato.requires_gpu is True
    assert potato.execution_status == "gpu_deferred"
    assert potato.maf_replacement is None

    statistics = by_family[
        "arabidopsis_statistics"
    ]
    assert statistics.requires_gpu is False
    assert statistics.execution_status == "use_maf_replacement"
    assert (
        statistics.maf_replacement
        == "analyse_repeated_measures_with_posthoc"
    )


def test_pipeline_family_filter_returns_only_requested_family() -> None:
    result = run_pipeline_catalogue(
        str(PIPELINE_ZOO),
        family="arabidopsis_phenotype_extraction",
    )

    assert result.capability_count == 1
    assert (
        result.capabilities[0].family_id
        == "arabidopsis_phenotype_extraction"
    )
    assert result.capabilities[0].variant_count == 5


def test_pipeline_catalogue_input_rejects_unknown_family() -> None:
    with pytest.raises(ValidationError):
        PipelineCatalogueInput(
            family="arbitrary_pipeline",
        )


def test_unknown_registry_entry_fails_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pipeline_zoo.json"

    path.write_text(
        json.dumps(
            {
                "unexpected_pipeline": {
                    "function_name": "unexpected_pipeline",
                    "description": "Unknown test pipeline",
                    "args": {},
                    "output": "Dict[str, Any]",
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="unrecognised pipeline registry entry",
    ):
        run_pipeline_catalogue(
            str(path),
        )


def test_handler_exposes_only_family_not_registry_path() -> None:
    handler = build_pipeline_catalogue_handler(
        str(PIPELINE_ZOO)
    )

    assert tuple(
        inspect.signature(handler).parameters
    ) == ("family",)

    result = handler(
        "arabidopsis_statistics"
    )

    assert result.capability_count == 1
    assert (
        result.capabilities[0].family_id
        == "arabidopsis_statistics"
    )


def test_function_tool_has_read_only_contract() -> None:
    tool = create_pipeline_catalogue_tool(
        str(PIPELINE_ZOO)
    )

    assert tool.name == "get_pipeline_catalogue"

    schema = PipelineCatalogueInput.model_json_schema()

    assert set(
        schema["properties"]
    ) == {"family"}

    serialised = json.dumps(
        schema
    )

    assert "pipeline_zoo_path" not in serialised
    assert "extracted_pipelines" not in serialised


def test_catalogue_import_does_not_import_legacy_execution_modules() -> None:
    assert "extracted_pipelines" not in sys.modules
    assert "agents" not in sys.modules
