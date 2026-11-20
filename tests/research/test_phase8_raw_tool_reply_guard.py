"""Raw provider tool-call budget gate tests, no network, gold or GPU."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from scripts.research.phase8_raw_tool_reply_guard import (
    Phase8RawToolReplyError,
    RawNativeToolReplyGuardTransport,
    inspect_native_reply,
)

MODEL = "openai/gpt-5.6-luna"
TOOL = "run_scientific_model"


def request(*, with_tool=True):
    payload = {"model": MODEL, "stream": False, "messages": [
        {"role": "user", "content": "synthetic offline test"},
    ]}
    if with_tool:
        payload["tools"] = [{
            "type": "function",
            "function": {"name": TOOL, "description": "test", "parameters": {
                "type": "object",
                "properties": {
                    "capability_id": {"type": "string"},
                    "image_asset_id": {"type": "string"},
                },
                "required": ["capability_id", "image_asset_id"],
            }},
        }]
        payload["tool_choice"] = "auto"
    return httpx.Request(
        "POST", "https://openrouter.ai/api/v1/chat/completions", json=payload
    )


def completion(*, tool_calls=None, model=MODEL, legacy=None):
    msg = {"role": "assistant", "content": None}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    if legacy is not None:
        msg["function_call"] = legacy
    reply = {
        "id": "chatcmpl-offline-tool-budget",
        "object": "chat.completion",
        "created": 1795095000,
        "model": model,
        "choices": [{
            "index": 0, "message": msg,
            "finish_reason": "tool_calls" if tool_calls else "stop",
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }
    return json.dumps(reply).encode("utf-8")


def native_call(index=0, *, name=TOOL, args=None):
    if args is None:
        args = {
            "capability_id": "model/approved_fake",
            "image_asset_id": "application_bound_image",
        }
    return {
        "id": f"call_{index}",
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args)},
    }


def inspect(body, *, req=None, already=0):
    return inspect_native_reply(
        request=req or request(),
        response_body=body,
        model_id=MODEL,
        already_accepted_native_calls=already,
    )


def test_single_actual_function_call_is_accepted_and_counted():
    assert inspect(completion(tool_calls=[native_call()])) == 1


def test_tool_free_completion_is_accepted_without_a_call():
    assert inspect(completion(), req=request(with_tool=False)) == 0


@pytest.mark.parametrize("raw", [
    [native_call(1), native_call(2)],
    [native_call(1), native_call(2), native_call(3)],
])
def test_parallel_raw_calls_are_rejected_before_maf(raw):
    with pytest.raises(Phase8RawToolReplyError, match="maximum of one"):
        inspect(completion(tool_calls=raw))


def test_second_raw_native_call_across_two_provider_roundtrips_fails():
    with pytest.raises(Phase8RawToolReplyError, match="maximum of one"):
        inspect(completion(tool_calls=[native_call(1)]), already=1)


def test_tool_free_critic_cannot_return_raw_tool_call():
    with pytest.raises(Phase8RawToolReplyError, match="not advertised"):
        inspect(completion(tool_calls=[native_call()]), req=request(with_tool=False))


@pytest.mark.parametrize("body", [
    completion(tool_calls=[native_call(name="unreviewed_tool")]),
    completion(tool_calls=[native_call(args={"arbitrary_path": "/tmp/private"})]),
    completion(tool_calls=[native_call(args={"capability_id": 12, "image_asset_id": "x"})]),
    completion(tool_calls=[native_call(args={"capability_id": "valid"})]),
])
def test_unexpected_raw_tool_name_or_arguments_fail_closed(body):
    with pytest.raises(Phase8RawToolReplyError):
        inspect(body)


def test_legacy_function_call_is_rejected():
    with pytest.raises(Phase8RawToolReplyError, match="legacy"):
        inspect(completion(legacy={"name": TOOL, "arguments": "{}"}))


def test_model_drift_in_raw_response_rejected():
    with pytest.raises(Phase8RawToolReplyError, match="model differs"):
        inspect(completion(model="other/unknown-model"))


def test_oversized_raw_completion_rejected():
    with pytest.raises(Phase8RawToolReplyError, match="response limit"):
        inspect(b" " * (2 * 1024 * 1024 + 1))


def test_raw_guard_transport_retains_one_call_count_across_responses():
    sent = 0

    async def fake_upstream(_request):
        nonlocal sent
        sent += 1
        if sent == 1:
            return httpx.Response(200, content=completion(tool_calls=[native_call()]))
        return httpx.Response(200, content=completion(tool_calls=[native_call(2)]))

    guard = RawNativeToolReplyGuardTransport(
        upstream=httpx.MockTransport(fake_upstream),
        expected_model=MODEL,
    )

    async def run():
        async with httpx.AsyncClient(transport=guard) as client:
            r1 = await client.send(request())
            assert r1.status_code == 200
            assert guard.native_tool_calls == 1
            with pytest.raises(Phase8RawToolReplyError, match="maximum of one"):
                await client.send(request())
    asyncio.run(run())
    assert sent == 2
    assert guard.native_tool_calls == 1
    assert guard.provider_replies_checked == 1


def test_raw_guard_refuses_multicall_before_downstream_maf_receives_reply():
    async def fake_upstream(_request):
        return httpx.Response(200, content=completion(
            tool_calls=[native_call(0), native_call(1)]
        ))
    guard = RawNativeToolReplyGuardTransport(
        upstream=httpx.MockTransport(fake_upstream), expected_model=MODEL,
    )
    async def run():
        async with httpx.AsyncClient(transport=guard) as client:
            with pytest.raises(Phase8RawToolReplyError, match="maximum of one"):
                await client.send(request())
    asyncio.run(run())
    assert guard.native_tool_calls == 0
    assert guard.provider_replies_checked == 0
