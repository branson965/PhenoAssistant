"""No-network contract tests for Phase 8 MAF/OpenRouter wire compatibility."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from scripts.research.openrouter_compat import (
    OpenRouterCompatibilityError,
    OpenRouterCompatTransport,
    rewrite_request,
)
from scripts.research.capture_phase8_maf_request_shape import run_probe


MODEL = "openai/gpt-5.6-luna"


def build_request(**overrides):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "private-scientific-prompt"}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "echo",
                "description": "private-tool-description",
            },
        }],
        "provider": {
            "order": ["openai"],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
        "reasoning": {"effort": "medium"},
        "seed": 2026,
        "stream": False,
        "tool_choice": "required",
        "max_completion_tokens": 512,
        "parallel_tool_calls": False,
    }
    body.update(overrides)
    return httpx.Request(
        "POST",
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": "Bearer never-print-this"},
        json=body,
    )


def test_exact_rewrite_preserves_every_other_field():
    original = build_request()
    before = json.loads(original.content)
    rewritten = rewrite_request(original, expected_model=MODEL)
    after = json.loads(rewritten.content)

    assert "max_completion_tokens" not in after
    assert "parallel_tool_calls" not in after
    assert after.pop("max_tokens") == 512
    before.pop("max_completion_tokens")
    before.pop("parallel_tool_calls")
    assert after == before
    assert rewritten.headers["Authorization"] == original.headers["Authorization"]
    assert int(rewritten.headers["content-length"]) == len(rewritten.content)


@pytest.mark.parametrize("changes", [
    {"parallel_tool_calls": True},
    {"max_completion_tokens": 4096},
    {"max_completion_tokens": 0},
    {"max_completion_tokens": None},
    {"max_tokens": 512},
    {"temperature": 0.0},
    {"model": "unapproved-model"},
    {"provider": {
        "order": ["openai"],
        "allow_fallbacks": True,
        "require_parameters": True,
    }},
    {"provider": {
        "order": ["openai"],
        "allow_fallbacks": False,
        "require_parameters": False,
    }},
    {"seed": 999},
    {"reasoning": {"effort": "low"}},
    {"stream": True},
])
def test_unsafe_parameter_changes_fail_closed(changes):
    with pytest.raises(OpenRouterCompatibilityError):
        rewrite_request(build_request(**changes), expected_model=MODEL)


def test_non_openrouter_host_fails_closed():
    request = httpx.Request(
        "POST",
        "https://example.com/api/v1/chat/completions",
        json={"model": MODEL},
    )
    with pytest.raises(OpenRouterCompatibilityError):
        rewrite_request(request, expected_model=MODEL)


def test_mock_transport_receives_only_compatible_request():
    received = []

    async def sink(request):
        received.append(json.loads(request.content))
        return httpx.Response(200, json={"ok": True})

    async def run():
        transport = OpenRouterCompatTransport(
            expected_model=MODEL,
            upstream=httpx.MockTransport(sink),
        )
        try:
            result = await transport.handle_async_request(build_request())
            assert result.status_code == 200
        finally:
            await transport.aclose()

    asyncio.run(run())
    assert len(received) == 1
    assert received[0]["max_tokens"] == 512
    assert "max_completion_tokens" not in received[0]
    assert "parallel_tool_calls" not in received[0]


def test_integrated_maf_capture_inspects_post_rewrite_request():
    # Executes the actual MAF preflight with a synthetic key; intercepts
    # at the underlying HTTP transport before any network transmission.
    shape = asyncio.run(run_probe())
    controls = shape["controls"]
    assert shape["model"] == MODEL
    assert shape["tool_count"] == 1
    assert shape["messages_present"] is True
    assert shape["parallel_tool_calls_present"] is False
    assert "max_completion_tokens" not in shape["request_body_keys"]
    assert controls["max_tokens"] == 512
    assert controls["seed"] == 2026
    assert controls["reasoning"]["effort"] == "medium"
    assert controls["provider"]["order"] == ["openai"]
    assert controls["provider"]["allow_fallbacks"] is False
    assert controls["provider"]["require_parameters"] is True
    assert "temperature" not in shape["request_body_keys"]


def test_tool_free_proposal_with_omitted_choice_is_valid_without_exposing_tools():
    # MAF 1.11.0 omits tool_choice for tool-free proposal-only requests.
    # This is permitted only when no executable tool has been supplied.
    payload = json.loads(build_request().content)
    payload.pop("tools")
    payload.pop("tool_choice")
    request = httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions", json=payload
    )
    result = json.loads(rewrite_request(request, expected_model=MODEL).content)
    assert "tools" not in result
    assert "tool_choice" not in result
    assert result["max_tokens"] == 512
    assert "parallel_tool_calls" not in result
    assert result["provider"] == {
        "order": ["openai"], "allow_fallbacks": False,
        "require_parameters": True,
    }


def test_empty_explicit_tool_list_and_none_choice_are_allowed():
    payload = json.loads(build_request().content)
    payload["tools"] = []
    payload["tool_choice"] = "none"
    request = httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions", json=payload
    )
    result = json.loads(rewrite_request(request, expected_model=MODEL).content)
    assert result["tools"] == []
    assert result["tool_choice"] == "none"


def test_explicit_null_choice_is_only_removed_for_tool_free_requests():
    payload = json.loads(build_request().content)
    payload["tools"] = []
    payload["tool_choice"] = None
    request = httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions", json=payload
    )
    result = json.loads(rewrite_request(request, expected_model=MODEL).content)
    assert "tool_choice" not in result
    assert result["tools"] == []


@pytest.mark.parametrize("alteration", [
    {"tool_choice": None},
    {"tool_choice": "invalid"},
    {"tool_choice": "required_if_possible"},
])
def test_tool_enabled_request_with_invalid_choice_stays_fail_closed(alteration):
    payload = json.loads(build_request().content)
    payload.update(alteration)
    request = httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions", json=payload
    )
    with pytest.raises(OpenRouterCompatibilityError):
        rewrite_request(request, expected_model=MODEL)


def test_tool_enabled_request_missing_choice_stays_fail_closed():
    payload = json.loads(build_request().content)
    payload.pop("tool_choice")
    request = httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions", json=payload
    )
    with pytest.raises(OpenRouterCompatibilityError):
        rewrite_request(request, expected_model=MODEL)


@pytest.mark.parametrize("choice", ["required", "auto", "invalid"])
def test_tool_free_request_must_not_enable_native_tool_calling(choice):
    payload = json.loads(build_request().content)
    payload["tools"] = []
    payload["tool_choice"] = choice
    request = httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions", json=payload
    )
    with pytest.raises(OpenRouterCompatibilityError):
        rewrite_request(request, expected_model=MODEL)


def test_invalid_tool_declaration_is_rejected():
    payload = json.loads(build_request().content)
    payload["tools"] = None
    request = httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions", json=payload
    )
    with pytest.raises(OpenRouterCompatibilityError):
        rewrite_request(request, expected_model=MODEL)
