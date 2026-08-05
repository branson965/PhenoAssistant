"""Scripted native MAF client for deterministic production tests."""

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


class ScriptedToolClient(
    FunctionInvocationLayer,
    BaseChatClient,
):
    """Call one selected tool and summarise its returned evidence."""

    def __init__(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
    ) -> None:
        super().__init__()

        self.tool_name = tool_name
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
            raise AssertionError(
                "the scripted client does not support streaming"
            )

        self.received_messages.append(
            deepcopy(list(messages))
        )

        self.received_options.append(
            dict(options)
        )

        function_result = self._latest_function_result(
            messages
        )

        if function_result is None:
            return ChatResponse(
                messages=[
                    Message(
                        "assistant",
                        [
                            (
                                "Plan: select the appropriate registered "
                                "tool, execute it once, and summarise only "
                                "its returned evidence."
                            ),
                            Content.from_function_call(
                                "production-tool-call-1",
                                self.tool_name,
                                arguments=self.arguments,
                            ),
                        ],
                    )
                ],
                finish_reason="tool_calls",
            )

        self.function_result = deepcopy(
            function_result
        )

        if function_result.exception:
            summary = (
                f"{self.tool_name} failed: "
                f"{function_result.exception}"
            )
        else:
            evidence = json.loads(
                function_result.result
            )

            summary = (
                f"{evidence['tool_name']} completed "
                "from tool evidence."
            )

        return ChatResponse(
            messages=[
                Message(
                    "assistant",
                    [summary],
                )
            ],
            finish_reason="stop",
        )

    @staticmethod
    def _latest_function_result(
        messages: Sequence[Message],
    ) -> Content | None:
        for message in reversed(messages):
            for content in reversed(
                message.contents
            ):
                if content.type == "function_result":
                    return content

        return None
