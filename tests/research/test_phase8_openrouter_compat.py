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
