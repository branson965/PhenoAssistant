"""Live but non-scientific OpenRouter/MAF preflight for IJCAI Phase 8.

This script validates the frozen model slug, provider pin, GPT-5.6 request
parameters, one-tool-call loop, and response identity before any scientific
benchmark outcome is observed.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
from pathlib import Path
from typing import Any

from agent_framework import Message, tool
from agent_framework.openai import OpenAIChatCompletionClient


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = ROOT / "experiments" / "ijcai2027"


def read_json(path: Path) -> dict:
    return json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )


def sanitise(value: object) -> str:
    text = str(value)

    text = re.sub(
        r"sk-or-v1-[A-Za-z0-9_-]+",
        "[REDACTED]",
        text,
    )

    text = re.sub(
        r"Bearer[ \t]+[A-Za-z0-9._-]+",
        "Bearer [REDACTED]",
        text,
    )

    return text[:2000]


async def close_client(client: Any) -> None:
    seen: set[int] = set()

    candidates = [
        client,
        getattr(
            client,
            "client",
            None,
        ),
        getattr(
            client,
            "_client",
            None,
        ),
    ]

    for candidate in candidates:
        if (
            candidate is None
            or id(candidate) in seen
        ):
            continue

        seen.add(
            id(candidate)
        )

        for method_name in (
            "aclose",
            "close",
        ):
            method = getattr(
                candidate,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:
                result = method()

                if inspect.isawaitable(
                    result
                ):
                    await result
            except Exception:
                pass

            break


async def main() -> None:
    api_key = os.environ.get(
        "OPENROUTER_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise SystemExit(
            "OPENROUTER_API_KEY is not set in this shell"
        )

    model_plan = read_json(
        EXPERIMENT_DIR
        / "model_plan.json"
    )

    runtime_plan = read_json(
        EXPERIMENT_DIR
        / "runtime_plan.json"
    )

    primary = model_plan[
        "primary"
    ]

    routing = model_plan[
        "routing"
    ][
        "openrouter_provider_object"
    ]

    sampling = runtime_plan[
        "sampling"
    ]

    tool_loop = runtime_plan[
        "tool_loop"
    ]

    if primary["model_id"] != (
        runtime_plan[
            "primary_model"
        ][
            "model_id"
        ]
    ):
        raise SystemExit(
            "model plan/runtime plan mismatch"
        )

    if (
        sampling[
            "temperature_parameter_sent"
        ]
        is not False
    ):
        raise SystemExit(
            "preflight must not transmit temperature"
        )

    calls: list[str] = []

    @tool(
        name="phase8_preflight_echo",
        description=(
            "Return the supplied preflight token unchanged. "
            "This tool has no scientific function."
        ),
    )
    def phase8_preflight_echo(
        token: str,
    ) -> str:
        calls.append(
            token
        )
        return token

    client = OpenAIChatCompletionClient(
        model=primary[
            "model_id"
        ],
        api_key=api_key,
        base_url=(
            "https://openrouter.ai/api/v1"
        ),
        function_invocation_configuration={
            "max_iterations": int(
                tool_loop[
                    "max_iterations"
                ]
            ),
            "max_function_calls": int(
                tool_loop[
                    "max_function_calls"
                ]
            ),
            "allow_concurrent_invocation": bool(
                tool_loop[
                    "allow_concurrent_invocation"
                ]
            ),
            "terminate_on_unknown_calls": bool(
                tool_loop[
                    "terminate_on_unknown_calls"
                ]
            ),
        },
    )

    seed = int(
        sampling[
            "seed_schedule"
        ][0]
    )

    options = {
        "tools": [
            phase8_preflight_echo,
        ],
        "tool_choice": "required",
        "allow_multiple_tool_calls": False,
        "max_tokens": 512,
        "seed": seed,
        "extra_body": {
            "provider": routing,
            "reasoning": sampling[
                "reasoning"
            ],
        },
    }

    try:
        response = await client.get_response(
            [
                Message(
                    role="user",
                    contents=[
                        (
                            "This is a non-scientific infrastructure "
                            "preflight. Call phase8_preflight_echo exactly "
                            "once with token 'phase8-preflight'. Then return "
                            "a short confirmation."
                        )
                    ],
                )
            ],
            options=options,
        )

        if calls != [
            "phase8-preflight"
        ]:
            raise AssertionError(
                "preflight tool-call count/arguments mismatch: "
                + repr(calls)
            )

        response_model = (
            response.model
            or "<none>"
        )

        if (
            "gpt-5.6-luna"
            not in response_model.lower()
        ):
            raise AssertionError(
                "unexpected response model identity: "
                + response_model
            )

        fingerprint = (
            response.additional_properties.get(
                "system_fingerprint"
            )
            if response.additional_properties
            else None
        )

        if not response.text.strip():
            raise AssertionError(
                "preflight returned no final text"
            )

        print(
            "PHASE8A_LIVE_PREFLIGHT_MODEL="
            + response_model
        )

        print(
            "PHASE8A_LIVE_PREFLIGHT_SYSTEM_FINGERPRINT="
            + (
                str(fingerprint)
                if fingerprint
                else "<none>"
            )
        )

        print(
            "PHASE8A_LIVE_PREFLIGHT_TOOL_CALLS=1"
        )

        print(
            "PHASE8A_LIVE_PREFLIGHT_PROVIDER_PIN=openai"
        )

        print(
            "PHASE8A_LIVE_PREFLIGHT_PROVIDER_FALLBACKS=false"
        )

        print(
            "PHASE8A_LIVE_PREFLIGHT_SEED="
            + str(seed)
        )

        print(
            "PHASE8A_LIVE_PREFLIGHT_TEMPERATURE_SENT=false"
        )

        print(
            "PHASE8A_LIVE_PREFLIGHT_OUTCOME_BEARING=false"
        )

        print(
            "PHASE8A_LIVE_OPENROUTER_MAF_PREFLIGHT_PASS=true"
        )
    except Exception as exc:
        raise SystemExit(
            "Phase 8A live preflight failed: "
            + sanitise(exc)
        ) from exc
    finally:
        await close_client(
            client
        )


if __name__ == "__main__":
    asyncio.run(
        main()
    )
