"""Minimal scripted MAF chat client for deterministic offline tests."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from agent_framework import (
    BaseChatClient,
    ChatResponse,
    Content,
    FunctionInvocationLayer,
    Message,
)


class ScriptedMixedAnovaClient(FunctionInvocationLayer, BaseChatClient):
    """Return one scripted tool call, then summarise its returned evidence."""

    def __init__(self, arguments: Mapping[str, Any]) -> None:
        super().__init__()
        self.arguments = dict(arguments)
        self.received_messages: list[list[Message]] = []
        self.received_options: list[dict[str, Any]] = []
        self.stream_values: list[bool] = []
        self.function_result: Content | None = None

    async def _inner_get_response(
        self,
        *,
        messages: Sequence[Message],
        stream: bool,
        options: Mapping[str, Any],
        **kwargs: Any,
    ) -> ChatResponse:
        del kwargs
        self.stream_values.append(stream)
        if stream:
            raise AssertionError("the scripted client does not support streaming")

        self.received_messages.append(deepcopy(list(messages)))
        self.received_options.append(dict(options))
        result = self._latest_function_result(messages)
        if result is None:
            return ChatResponse(
                messages=[
                    Message(
                        "assistant",
                        [
                            "Plan: validate the four column names, run the single "
                            "mixed-ANOVA tool, then summarise its returned records.",
                            Content.from_function_call(
                                "mixed-anova-call-1",
                                "perform_mixed_anova",
                                arguments=self.arguments,
                            ),
                        ],
                    )
                ],
                finish_reason="tool_calls",
            )

        self.function_result = deepcopy(result)
        if result.exception:
            summary = f"Mixed ANOVA failed: {result.exception}"
        else:
            evidence = json.loads(result.result)
            summary = (
                "Mixed ANOVA completed from tool evidence: "
                f"{len(evidence['records'])} record(s); "
                f"descriptor={evidence['arguments']['descriptor']}."
            )
        return ChatResponse(
            messages=[Message("assistant", [summary])],
            finish_reason="stop",
        )

    @staticmethod
    def _latest_function_result(messages: Sequence[Message]) -> Content | None:
        for message in reversed(messages):
            for content in reversed(message.contents):
                if content.type == "function_result":
                    return content
        return None
