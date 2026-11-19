"""Fail-closed compatibility shim for frozen Phase 8 MAF/OpenRouter calls.

MAF 1.11.0 sends max_completion_tokens, and emits parallel_tool_calls=false
when application-side concurrency is disabled. The pinned OpenAI-routed
Luna endpoints advertise max_tokens but neither of these API controls.
This adapter changes only those two wire fields. It never changes a prompt,
model, scientific tool, seed, provider pin, reasoning effort or temperature.

This is an HTTP interface compatibility adapter, not an SOE method change.
"""

from __future__ import annotations

import json
from typing import Any

import httpx


class OpenRouterCompatibilityError(ValueError):
    """Local fail-closed error before a request can reach OpenRouter."""


def rewrite_request(
    request: httpx.Request,
    *,
    expected_model: str,
    token_ceiling: int = 2048,
    allowed_seeds: tuple[int, ...] = (2026, 2027, 2028),
) -> httpx.Request:
    """Return exact-compatible request without altering task or tool content.

    OpenRouter routing must remain pinned to OpenAI, without fallbacks, and
    require_parameters must remain true. Only a disabled parallel-tools field
    may be omitted; if it is true the call fails closed. Other than this and
    the token field name, all parsed JSON values remain identical.
    """
    if (
        request.method != "POST"
        or request.url.scheme != "https"
        or request.url.host != "openrouter.ai"
        or request.url.path != "/api/v1/chat/completions"
    ):
        raise OpenRouterCompatibilityError("unexpected request destination or method")

    try:
        body: Any = json.loads(request.content)
    except (ValueError, TypeError) as exc:
        raise OpenRouterCompatibilityError("invalid JSON request payload") from exc
    if not isinstance(body, dict):
        raise OpenRouterCompatibilityError("request payload must be a JSON object")
    if body.get("model") != expected_model:
        raise OpenRouterCompatibilityError("model identity changed")
    if body.get("provider") != {
        "order": ["openai"],
        "allow_fallbacks": False,
        "require_parameters": True,
    }:
        raise OpenRouterCompatibilityError("provider pin or parameter enforcement changed")
    if body.get("reasoning") != {"effort": "medium"}:
        raise OpenRouterCompatibilityError("reasoning effort changed")
    if "temperature" in body:
        raise OpenRouterCompatibilityError("unexpected temperature parameter")
    if body.get("seed") not in allowed_seeds or isinstance(body.get("seed"), bool):
        raise OpenRouterCompatibilityError("seed is not in frozen schedule")
    if body.get("stream") is not False:
        raise OpenRouterCompatibilityError("unexpected streaming request")
    if body.get("tool_choice") not in ("required", "auto", "none"):
        raise OpenRouterCompatibilityError("unexpected tool-choice policy")
    if not isinstance(body.get("messages"), list):
        raise OpenRouterCompatibilityError("messages are missing")

    original = body.get("max_completion_tokens")
    if "max_tokens" in body:
        raise OpenRouterCompatibilityError("unexpected or conflicting max_tokens field")
    if isinstance(original, bool) or not isinstance(original, int):
        raise OpenRouterCompatibilityError("missing or non-integer max_completion_tokens")
    if not (1 <= original <= token_ceiling):
        raise OpenRouterCompatibilityError("token ceiling outside frozen envelope")
    body.pop("max_completion_tokens")
    body["max_tokens"] = original

    if "parallel_tool_calls" in body:
        if body["parallel_tool_calls"] is not False:
            raise OpenRouterCompatibilityError("cannot omit enabled parallel tool calls")
        body.pop("parallel_tool_calls")

    # Reconstruct rather than mutate private httpx fields. httpx recalculates
    # Content-Length; authentication headers remain intact and unlogged.
    headers = [
        (name, value)
        for name, value in request.headers.multi_items()
        if name.lower() not in ("content-length", "transfer-encoding")
    ]
    return httpx.Request(
        method=request.method,
        url=request.url,
        headers=headers,
        content=json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
        extensions=request.extensions.copy(),
    )


class OpenRouterCompatTransport(httpx.AsyncBaseTransport):
    """Apply the audited parameter rewrite immediately before HTTPS send."""

    def __init__(
        self,
        *,
        expected_model: str,
        token_ceiling: int = 2048,
        upstream: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.expected_model = expected_model
        self.token_ceiling = token_ceiling
        self.upstream = upstream if upstream is not None else httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        rewritten = rewrite_request(
            request,
            expected_model=self.expected_model,
            token_ceiling=self.token_ceiling,
        )
        return await self.upstream.handle_async_request(rewritten)

    async def aclose(self) -> None:
        await self.upstream.aclose()
