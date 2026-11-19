"""Offline request-capture tests. No real provider request or credentials."""

from __future__ import annotations

import json

import httpx

from scripts.research.capture_phase8_maf_request_shape import (
    safe_request_shape,
)


def make_request(body):
    return httpx.Request(
        "POST",
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer sk-or-v1-MUST-NOT-PRINT",
            "X-secret-payload": "never-appear-in-diagnostics",
        },
        json=body,
    )


def test_capture_shows_exact_parallel_control_without_leaking_text():
    request = make_request({
        "model": "openai/gpt-5.6-luna",
        "messages": [{"role": "user", "content": "TOP SECRET SCIENTIFIC PROMPT"}],
        "tools": [{"type": "function", "function": {"name": "echo", "description": "HIDDEN TOOL DESCRIPTION"}}],
        "parallel_tool_calls": False,
        "tool_choice": "required",
        "seed": 2026,
        "max_tokens": 512,
        "reasoning": {"effort": "medium"},
        "provider": {
            "order": ["openai"],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
    })
    result = safe_request_shape(request)
    assert result["parallel_tool_calls_present"] is True
    assert result["parallel_tool_calls_value"] is False
    assert result["controls"]["seed"] == 2026
    assert result["controls"]["provider"]["require_parameters"] is True
    assert result["tool_count"] == 1
    serialized = json.dumps(result)
    for secret in (
        "TOP SECRET",
        "HIDDEN TOOL",
        "sk-or-v1-MUST-NOT-PRINT",
        "never-appear-in-diagnostics",
    ):
        assert secret not in serialized


def test_capture_distinguishes_absent_parallel_control():
    result = safe_request_shape(make_request({
        "model": "openai/gpt-5.6-luna",
        "messages": [{"role": "user", "content": "hello"}],
        "tools": [],
        "tool_choice": "required",
    }))
    assert result["parallel_tool_calls_present"] is False
    assert result["parallel_tool_calls_value"] == "<absent>"


def test_capture_rejects_other_host_or_path_before_touching_body():
    bad = httpx.Request(
        "POST",
        "https://example.com/api/v1/chat/completions",
        json={"messages": []},
    )
    from scripts.research.capture_phase8_maf_request_shape import _NetworkForbidden
    import pytest
    with pytest.raises(_NetworkForbidden):
        safe_request_shape(bad)


def test_capture_script_never_calls_inference_endpoint_directly():
    from scripts.research import capture_phase8_maf_request_shape as module
    with open(module.__file__, encoding="utf-8") as file:
        source = file.read()
    assert "OFFLINE-CAPTURE-NOT-A-REAL-KEY" in source
    assert "patch.object(httpx.AsyncClient, \"send\"" in source
    assert "PHASE8_WIRE_SHAPE_PAID_INFERENCE=false" in source
    assert "print(old_key)" not in source
