"""Inspect native OpenRouter tool-call replies before MAF executes callbacks.

The request-side compatibility shim enforces provider/seed/temperature/limits,
but cannot by itself guarantee the provider returns at most ONE function call.
This guard inspects each raw, non-streaming chat-completion response while it
is still in the HTTP transport and blocks malformed, parallel, unexpected,
or repeated tool calls before the framework can dispatch any callback.

One guard instance is bound to ONE frozen trial/client session. It records
tool-call count only, not prompts, credentials or scientific outcomes.
It does not infer provider-billed cost from token counts and does not
constitute approval to use the real provider or invoke a scientific model.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

TOOL_NAME = "run_scientific_model"
TOOL_ARGUMENT_KEYS = frozenset(("capability_id", "image_asset_id"))
MAX_REPLY_BYTES = 2 * 1024 * 1024


class Phase8RawToolReplyError(ValueError):
    """Provider's raw function-call response violates frozen controls."""


def inspect_native_reply(
    *,
    request: httpx.Request,
    response_body: bytes,
    model_id: str,
    already_accepted_native_calls: int,
) -> int:
    """Return accepted calls in this reply; reject all protocol drift.

    All checks run before updating the shared count or returning a
    provider response to MAF. The callback therefore cannot execute
    a second raw tool call ignored by application-side policy.
    """
    if (
        type(already_accepted_native_calls) is not int
        or already_accepted_native_calls not in (0, 1)
    ):
        raise Phase8RawToolReplyError("invalid prior native call count")
    if len(response_body) > MAX_REPLY_BYTES:
        raise Phase8RawToolReplyError("provider completion exceeds response limit")
    try:
        outgoing = json.loads(request.content)
        reply: Any = json.loads(response_body)
    except (ValueError, UnicodeDecodeError, TypeError) as exc:
        raise Phase8RawToolReplyError("malformed provider JSON") from exc
    if not isinstance(outgoing, dict) or not isinstance(reply, dict):
        raise Phase8RawToolReplyError("provider chat completion is not an object")
    if reply.get("model") != model_id:
        raise Phase8RawToolReplyError("raw reply model differs from approved model")
    if reply.get("object") != "chat.completion":
        raise Phase8RawToolReplyError("unexpected provider response type")
    choices = reply.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise Phase8RawToolReplyError("one nonstreaming completion choice required")
    choice = choices[0]
    if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
        raise Phase8RawToolReplyError("completion has no typed assistant message")
    message = choice["message"]
    if message.get("role") != "assistant":
        raise Phase8RawToolReplyError("completion role is not assistant")
    if message.get("function_call") is not None:
        raise Phase8RawToolReplyError("unsupported legacy function-call format")
    raw_calls = message.get("tool_calls")
    if raw_calls is None:
        raw_calls = []
    if not isinstance(raw_calls, list):
        raise Phase8RawToolReplyError("raw tool_calls must be a list")
    finish = choice.get("finish_reason")
    if finish == "tool_calls" and not raw_calls:
        raise Phase8RawToolReplyError("tool-call finish without tool-call data")
    if raw_calls and finish != "tool_calls":
        raise Phase8RawToolReplyError("raw tool-call data lacks tool-call finish reason")
    if len(raw_calls) + already_accepted_native_calls > 1:
        raise Phase8RawToolReplyError("frozen maximum of one native function call exceeded")
    if raw_calls:
        tools = outgoing.get("tools")
        if (
            not isinstance(tools, list)
            or len(tools) != 1
            or tools[0].get("type") != "function"
            or tools[0].get("function", {}).get("name") != TOOL_NAME
            or outgoing.get("tool_choice") not in ("auto", "required")
        ):
            raise Phase8RawToolReplyError("provider used a tool not advertised for this turn")
        entry = raw_calls[0]
        if not isinstance(entry, dict) or entry.get("type") != "function":
            raise Phase8RawToolReplyError("unsupported raw tool-call type")
        func = entry.get("function")
        if not isinstance(func, dict) or func.get("name") != TOOL_NAME:
            raise Phase8RawToolReplyError("raw function name differs from frozen MCP name")
        if not isinstance(entry.get("id"), str) or not entry["id"].strip():
            raise Phase8RawToolReplyError("native function call missing provider call ID")
        if not isinstance(func.get("arguments"), str):
            raise Phase8RawToolReplyError("native function arguments are not encoded JSON")
        try:
            arguments = json.loads(func["arguments"])
        except (ValueError, TypeError) as exc:
            raise Phase8RawToolReplyError("invalid native function-call JSON") from exc
        if not isinstance(arguments, dict) or set(arguments) != TOOL_ARGUMENT_KEYS:
            raise Phase8RawToolReplyError("native function call has wrong argument keys")
        if any(not isinstance(v, str) or not v for v in arguments.values()):
            raise Phase8RawToolReplyError("native function arguments must be nonempty strings")
    return len(raw_calls)


class RawNativeToolReplyGuardTransport(httpx.AsyncBaseTransport):
    """Read-only response validator after existing compatibility rewrite."""

    def __init__(
        self,
        *,
        upstream: httpx.AsyncBaseTransport,
        expected_model: str,
    ) -> None:
        self.upstream = upstream
        self.expected_model = expected_model
        self.native_tool_calls = 0
        self.provider_replies_checked = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await self.upstream.handle_async_request(request)
        if response.status_code != 200:
            return response
        try:
            if response.headers.get("content-length"):
                length = int(response.headers["content-length"])
                if length > MAX_REPLY_BYTES:
                    raise Phase8RawToolReplyError("provider response declared oversized payload")
            payload = await response.aread()
            newly_seen = inspect_native_reply(
                request=request,
                response_body=payload,
                model_id=self.expected_model,
                already_accepted_native_calls=self.native_tool_calls,
            )
        except Exception:
            await response.aclose()
            raise
        self.native_tool_calls += newly_seen
        self.provider_replies_checked += 1
        return response

    async def aclose(self) -> None:
        await self.upstream.aclose()
