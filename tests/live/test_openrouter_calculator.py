"""Opt-in live OpenRouter test for the production MAF Manager."""

from __future__ import annotations

import inspect
import os
import re
from typing import Any

import pytest

from phenoassistant_maf import (
    OpenRouterSettings,
    build_application,
    create_chat_client,
    run_application,
)


RUN_LIVE_OPENROUTER = (
    os.environ.get("RUN_LIVE_OPENROUTER") == "1"
)

pytestmark = pytest.mark.skipif(
    not RUN_LIVE_OPENROUTER,
    reason=(
        "Set RUN_LIVE_OPENROUTER=1 and provide "
        "OPENROUTER_API_KEY to run this live test."
    ),
)


class RecordingCalculator:
    """Record calculator calls selected by the live Manager."""

    def __init__(self) -> None:
        self.calls: list[tuple[int, int, str]] = []

    def __call__(
        self,
        a: int,
        b: int,
        operator: str,
    ) -> int:
        self.calls.append((a, b, operator))

        if operator == "+":
            return a + b
        if operator == "-":
            return a - b
        if operator == "*":
            return a * b
        if operator == "/":
            return int(a / b)

        raise ValueError("Invalid operator")


def forbidden_anova(
    data_path: str,
    descriptor: str,
    within_subject_factor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, Any]]:
    """Fail if the Manager selects ANOVA for arithmetic."""
    del (
        data_path,
        descriptor,
        within_subject_factor,
        between_subject_factor,
        subject_id,
        save_path,
    )

    raise AssertionError(
        "ANOVA must not be selected for the calculator test"
    )


def forbidden_tukey(
    data_path: str,
    descriptor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, Any]]:
    """Fail if the Manager selects Tukey for arithmetic."""
    del (
        data_path,
        descriptor,
        between_subject_factor,
        subject_id,
        save_path,
    )

    raise AssertionError(
        "Tukey must not be selected for the calculator test"
    )


def sanitise(value: object) -> str:
    """Remove credentials from live-test diagnostics."""
    text = str(value)
    secret = os.environ.get("OPENROUTER_API_KEY", "")

    if secret:
        text = text.replace(secret, "[REDACTED]")

    text = re.sub(
        r"sk-[A-Za-z0-9_-]{20,}",
        "[REDACTED_TOKEN]",
        text,
    )

    return text[:3000]


async def close_client(client: object) -> None:
    """Close the provider client when supported."""
    close = getattr(client, "close", None)

    if close is None:
        return

    result = close()

    if inspect.isawaitable(result):
        await result


@pytest.mark.asyncio
async def test_live_openrouter_calculator_through_manager() -> None:
    settings = OpenRouterSettings.from_env()
    failures: list[str] = []

    for attempt in range(1, 4):
        print(f"REUSABLE_LIVE_ATTEMPT={attempt}/3")

        client = create_chat_client(settings)
        calculator = RecordingCalculator()

        application = build_application(
            client=client,
            data_path="/trusted/not-used-by-calculator.csv",
            calculator_callable=calculator,
            anova_callable=forbidden_anova,
            tukey_callable=forbidden_tukey,
        )

        try:
            response = await run_application(
                application,
                (
                    "Calculate 7 plus 5. "
                    "Use the calculator tool exactly once. "
                    "Base the final answer only on returned tool evidence."
                ),
            )
        except Exception as exc:
            failures.append(
                f"attempt {attempt}: {type(exc).__name__}: {sanitise(exc)}"
            )
            continue
        finally:
            await close_client(client)

        if calculator.calls != [(7, 5, "+")]:
            failures.append(
                f"attempt {attempt}: unexpected calls {calculator.calls!r}"
            )
            continue

        if not response.messages or not response.messages[-1].text.strip():
            failures.append(
                f"attempt {attempt}: missing final response"
            )
            continue

        print(f"LIVE_SUCCESSFUL_ATTEMPT={attempt}")
        print(f"LIVE_RECORDED_CALLS={calculator.calls!r}")
        print("LIVE_CALCULATOR_CALL_MATCH_PASS")
        print("LIVE_CALCULATOR_RESULT=12")
        print("REUSABLE_LIVE_CALCULATOR_PASS")
        return

    pytest.fail(
        "All live attempts failed: " + " | ".join(failures)
    )
