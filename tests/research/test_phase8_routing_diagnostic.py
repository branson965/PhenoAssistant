"""Free, offline checks for read-only Phase 8 routing diagnosis."""

from __future__ import annotations

from scripts.research import diagnose_phase8_openrouter_routing as diag


def test_model_summary_exposes_exact_parameter_support():
    assert diag.model_summary({
        "data": [{
            "id": diag.MODEL,
            "supported_parameters": ["tools", "tool_choice", "reasoning", "max_tokens"],
            "reasoning": {"supported_efforts": ["low", "medium"]},
        }]
    }) == {
        "model": diag.MODEL,
        "supported_parameters": ["max_tokens", "reasoning", "tool_choice", "tools"],
        "parameter_candidate_membership": {
            "tools": True,
            "tool_choice": True,
            "seed": False,
            "reasoning": True,
            "max_tokens": True,
            "max_completion_tokens": False,
            "parallel_tool_calls": False,
        },
        "top_level_reasoning": {"supported_efforts": ["low", "medium"]},
    }


def test_missing_model_is_not_fabricated():
    assert diag.model_summary({"data": [{"id": "unrelated"}]}) is None
    assert diag.model_summary({"data": {}}) is None


def test_endpoints_are_reported_individually_not_union_only():
    summary = diag.endpoint_summary({
        "data": {
            "endpoints": [
                {
                    "tag": "openai",
                    "name": "OpenAI A",
                    "provider_name": "OpenAI",
                    "supported_parameters": ["tools", "tool_choice"],
                    "supports_tool_choice": ["auto", "none"],
                },
                {
                    "tag": "other",
                    "name": "Other B",
                    "supported_parameters": ["seed"],
                    "supports_tool_choice": ["required"],
                },
            ]
        }
    })
    assert summary is not None
    assert len(summary) == 2
    assert summary[0]["parameter_candidate_membership"]["seed"] is False
    assert summary[1]["parameter_candidate_membership"]["seed"] is True
    assert summary[0]["parameter_candidate_membership"]["tools"] is True
    assert summary[1]["parameter_candidate_membership"]["tools"] is False


def test_source_has_only_read_only_api_paths_and_no_secret_print():
    with open(diag.__file__, encoding="utf-8") as source:
        text = source.read()
    assert '"/models"' in text
    assert '"/models/openai/gpt-5.6-luna/endpoints"' in text
    assert "chat/completions" not in text
    assert "responses/create" not in text
    assert "print(key)" not in text
    assert "PHASE8_ROUTING_PAID_INFERENCE=false" in text
    assert "PHASE8_ROUTING_OUTCOME_BEARING=false" in text
