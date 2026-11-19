"""Capture MAF's outgoing OpenRouter request shape WITHOUT sending it.

Runs the non-scientific Phase 8A preflight with a synthetic API key, then
intercepts the rewritten request at httpx.AsyncHTTPTransport, immediately
before it could be sent over HTTPS.
Prints only an allowlisted set of request-control fields and top-level JSON
keys; it NEVER prints prompts, tool schemas, message contents or headers.

Do not use this capture as scientific or live-provider compatibility evidence.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import socket
import sys
from unittest.mock import patch

import httpx


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.validate_ijcai_openrouter_preflight import main as preflight_main  # noqa: E402


class _RequestIntercepted(BaseException):
    """Hard stop before the HTTP client can send the intercepted request."""


class _NetworkForbidden(BaseException):
    """Unexpected network attempt; not a retriable transport error."""


def safe_request_shape(request: httpx.Request) -> dict:
    """Never expose request payload content, headers or raw model prompts."""
    if request.method != "POST" or request.url.host != "openrouter.ai":
        raise _NetworkForbidden()
    if request.url.path != "/api/v1/chat/completions":
        raise _NetworkForbidden()
    try:
        body = json.loads(request.content)
    except (ValueError, TypeError) as exc:
        raise ValueError("MAF body is not a JSON object") from exc
    if not isinstance(body, dict):
        raise ValueError("MAF body is not a JSON object")

    # The presence/absence of controls is diagnostic; do not guess their
    # presence from ChatOptions or framework configuration alone.
    approved = (
        "model",
        "seed",
        "tool_choice",
        "parallel_tool_calls",
        "max_tokens",
        "max_completion_tokens",
        "reasoning",
        "provider",
        "temperature",
        "stream",
        "stream_options",
        "response_format",
        "n",
        "top_p",
        "verbosity",
    )
    allowed: dict = {}
    for name in approved:
        if name not in body:
            continue
        value = body[name]
        if name == "model":
            allowed[name] = (
                value if value == "openai/gpt-5.6-luna" else "<unexpected-model>"
            )
        elif name in ("reasoning", "provider"):
            # Emit keys and selected safe, bounded routing values only.
            if not isinstance(value, dict):
                allowed[name] = "<non-dict>"
            elif name == "provider":
                allowed[name] = {
                    "order": value.get("order") if value.get("order") in (["openai"], None) else "<other>",
                    "allow_fallbacks": value.get("allow_fallbacks"),
                    "require_parameters": value.get("require_parameters"),
                    "keys": sorted(value),
                }
            else:
                allowed[name] = {
                    "effort": value.get("effort") if value.get("effort") in (
                        "none", "low", "medium", "high", "xhigh", "max"
                    ) else "<other>",
                    "keys": sorted(value),
                }
        elif name in ("stream_options", "response_format"):
            allowed[name] = {"type": type(value).__name__}
        elif value is None or isinstance(value, (bool, int, float)):
            allowed[name] = value
        elif name == "tool_choice" and isinstance(value, str):
            allowed[name] = (
                value if value in ("required", "auto", "none") else "<other>"
            )
        else:
            allowed[name] = {"type": type(value).__name__}

    return {
        "method": "POST",
        "route": "/api/v1/chat/completions",
        "request_body_keys": sorted(str(key) for key in body),
        "tool_count": len(body["tools"]) if isinstance(body.get("tools"), list) else 0,
        "controls": allowed,
        "parallel_tool_calls_present": "parallel_tool_calls" in body,
        "parallel_tool_calls_value": body.get("parallel_tool_calls", "<absent>"),
        "model": "openai/gpt-5.6-luna" if body.get("model") == "openai/gpt-5.6-luna" else "<unexpected>",
        "messages_present": isinstance(body.get("messages"), list),
        "note": "post-adapter request intercepted before transmission; no real API key used",
    }


async def run_probe() -> dict:
    captured: list[dict] = []

    async def intercept_transport(self, request):
        captured.append(safe_request_shape(request))
        raise _RequestIntercepted()

    def refuse_socket_connect(*args, **kwargs):
        raise _NetworkForbidden()

    old_key = os.environ.get("OPENROUTER_API_KEY")
    # Force a non-functional credential even when the user's live key
    # remains in the Plato shell from the previous diagnostic.
    os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-OFFLINE-CAPTURE-NOT-A-REAL-KEY"
    try:
        with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", intercept_transport):
            with patch.object(socket.socket, "connect", refuse_socket_connect):
                try:
                    await preflight_main()
                except _RequestIntercepted:
                    pass
    finally:
        if old_key is None:
            os.environ.pop("OPENROUTER_API_KEY", None)
        else:
            os.environ["OPENROUTER_API_KEY"] = old_key
    if len(captured) != 1:
        raise RuntimeError(
            "Request capture did not intercept exactly one outbound request"
        )
    return captured[0]


def main() -> int:
    try:
        shape = asyncio.run(run_probe())
    except (_NetworkForbidden, RuntimeError, ValueError):
        print("PHASE8_WIRE_SHAPE_CAPTURE_PASS=false")
        print("PHASE8_WIRE_SHAPE_REASON=unexpected-transport-or-payload")
        return 3
    print("PHASE8_WIRE_SHAPE=" + json.dumps(shape, sort_keys=True))
    print("PHASE8_WIRE_SHAPE_PAID_INFERENCE=false")
    print("PHASE8_WIRE_SHAPE_OUTCOME_BEARING=false")
    print("PHASE8_WIRE_SHAPE_CAPTURE_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
