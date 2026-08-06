"""Opt-in live OpenRouter proof of natural-language Tukey tool selection."""

from __future__ import annotations

import inspect
import math
import os
import re
from pathlib import Path
from typing import Any

import pytest

from functions.stat_test import perform_tukey_test
from phenoassistant_maf import (
    OpenRouterSettings,
    build_application,
    create_chat_client,
    run_application,
)

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE_OPENROUTER") != "1",
        reason="Set RUN_LIVE_OPENROUTER=1 to run the live provider test.",
    ),
]

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/maf/mixed_anova_plants.csv"


class RecordingTukey:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str, str | None]] = []
        self.results: list[list[dict[str, Any]]] = []

    def __call__(
        self,
        data_path: str,
        descriptor: str,
        between_subject_factor: str,
        subject_id: str,
        save_path: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            (
                data_path,
                descriptor,
                between_subject_factor,
                subject_id,
                save_path,
            )
        )
        result = perform_tukey_test(
            data_path=data_path,
            descriptor=descriptor,
            between_subject_factor=between_subject_factor,
            subject_id=subject_id,
            save_path=save_path,
        )
        self.results.append(result)
        return result


def forbidden_calculator(a: int, b: int, operator: str) -> int | float:
    raise AssertionError("The Manager selected calculator instead of Tukey.")


def forbidden_anova(
    data_path: str,
    descriptor: str,
    within_subject_factor: str,
    between_subject_factor: str,
    subject_id: str,
    save_path: str | None = None,
) -> list[dict[str, Any]]:
    raise AssertionError("The Manager selected ANOVA instead of Tukey.")


def normalise(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalise(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalise(item) for item in value]
    if hasattr(value, "item"):
        try:
            return normalise(value.item())
        except Exception:
            pass
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def canonical_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        normalise(records),
        key=lambda record: (
            str(record.get("A", "")),
            str(record.get("B", "")),
        ),
    )


def response_text(response: Any) -> str:
    for attribute in ("text", "content", "message"):
        value = getattr(response, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(response).strip()


def sanitise(value: object) -> str:
    text = str(value)
    text = re.sub(r"sk-or-v1-[A-Za-z0-9_-]+", "[REDACTED]", text)
    text = re.sub(
        r"Bearer[ \t]+[A-Za-z0-9._-]+",
        "Bearer [REDACTED]",
        text,
    )
    return text[:1200]


async def close_client(client: Any) -> None:
    seen: set[int] = set()
    candidates = [
        client,
        getattr(client, "client", None),
        getattr(client, "_client", None),
        getattr(client, "_openai_client", None),
    ]
    for candidate in candidates:
        if candidate is None or id(candidate) in seen:
            continue
        seen.add(id(candidate))
        for method_name in ("aclose", "close"):
            method = getattr(candidate, method_name, None)
            if not callable(method):
                continue
            try:
                result = method()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                pass
            break


@pytest.mark.parametrize("attempt_limit", [5])
async def test_live_openrouter_selects_real_tukey_from_natural_language(
    attempt_limit: int,
) -> None:
    assert FIXTURE.is_file()

    os.environ.setdefault("OPENROUTER_MODEL", "openrouter/free")
    settings = OpenRouterSettings.from_env()

    expected = canonical_records(
        perform_tukey_test(
            data_path=str(FIXTURE),
            descriptor="height",
            between_subject_factor="treatment",
            subject_id="plant_id",
            save_path=None,
        )
    )

    failures: list[str] = []

    prompt = (
        "Using the trusted plant dataset, run only the Tukey-Kramer post-hoc "
        "test on the height column. Use treatment as the between-subject "
        "factor and plant_id as the subject identifier. Do not run ANOVA and "
        "do not use the calculator. Call the Tukey tool exactly once, then "
        "summarise which treatment pairs are significant at alpha 0.05 using "
        "only the returned tool evidence."
    )

    for attempt in range(1, attempt_limit + 1):
        print(f"LIVE_TUKEY_ATTEMPT={attempt}/{attempt_limit}")
        recorder = RecordingTukey()
        client = create_chat_client(settings)

        try:
            application = build_application(
                client=client,
                data_path=str(FIXTURE),
                calculator_callable=forbidden_calculator,
                anova_callable=forbidden_anova,
                tukey_callable=recorder,
            )
            response = await run_application(application, prompt)
            text = response_text(response)

            assert len(recorder.calls) == 1, recorder.calls
            call = recorder.calls[0]
            assert Path(call[0]).resolve() == FIXTURE.resolve()
            assert call[1:] == ("height", "treatment", "plant_id", None)
            assert len(recorder.results) == 1
            assert canonical_records(recorder.results[0]) == expected
            assert text

            lowered = text.lower()
            assert all(group in lowered for group in ("control", "low", "high")), text
            assert any(
                phrase in lowered
                for phrase in ("significant", "tukey", "post-hoc", "post hoc")
            ), text

            print(f"LIVE_TUKEY_SELECTED_MODEL={settings.model}")
            print("LIVE_TUKEY_RECORDED_CALLS=1")
            print("LIVE_TUKEY_ARGUMENTS_PASS")
            print("LIVE_TUKEY_DIRECT_RESULT_PARITY_PASS")
            print("LIVE_TUKEY_SUMMARY_GROUNDING_PASS")
            print("LIVE_NATURAL_LANGUAGE_TUKEY_SELECTION_PASS")
            return
        except Exception as exc:
            failures.append(f"attempt {attempt}: {sanitise(exc)}")
            print(f"LIVE_TUKEY_ATTEMPT_FAILURE={sanitise(exc)}")
        finally:
            await close_client(client)

    pytest.fail("All live attempts failed:\n" + "\n".join(failures))
