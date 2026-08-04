"""Tests for explicit, secret-safe OpenRouter configuration."""

from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from maf_poc.config import DEFAULT_OPENROUTER_BASE_URL, OpenRouterSettings


def test_explicit_construction() -> None:
    settings = OpenRouterSettings(
        api_key="explicit-secret",
        model="provider/model",
        base_url="https://example.test/v1",
    )

    assert settings.api_key.get_secret_value() == "explicit-secret"
    assert settings.model == "provider/model"
    assert settings.base_url == "https://example.test/v1"


def test_from_env_loads_injected_mapping() -> None:
    settings = OpenRouterSettings.from_env(
        {
            "OPENROUTER_API_KEY": "mapping-secret",
            "OPENROUTER_MODEL": "provider/model",
        }
    )

    assert settings.api_key.get_secret_value() == "mapping-secret"
    assert settings.model == "provider/model"


def test_default_base_url() -> None:
    settings = OpenRouterSettings(api_key="secret", model="provider/model")

    assert settings.base_url == DEFAULT_OPENROUTER_BASE_URL


def test_explicit_base_url_override() -> None:
    settings = OpenRouterSettings.from_env(
        {
            "OPENROUTER_API_KEY": "secret",
            "OPENROUTER_MODEL": "provider/model",
            "OPENROUTER_BASE_URL": "https://example.test/openai/v1",
        }
    )

    assert settings.base_url == "https://example.test/openai/v1"


@pytest.mark.parametrize(
    ("environment", "variable_name"),
    [
        ({"OPENROUTER_MODEL": "provider/model"}, "OPENROUTER_API_KEY"),
        (
            {
                "OPENROUTER_API_KEY": " \t ",
                "OPENROUTER_MODEL": "provider/model",
            },
            "OPENROUTER_API_KEY",
        ),
        ({"OPENROUTER_API_KEY": "secret"}, "OPENROUTER_MODEL"),
        (
            {"OPENROUTER_API_KEY": "secret", "OPENROUTER_MODEL": " \t "},
            "OPENROUTER_MODEL",
        ),
    ],
)
def test_missing_or_whitespace_required_value(
    environment: dict[str, str], variable_name: str
) -> None:
    with pytest.raises(ValidationError, match=variable_name):
        OpenRouterSettings.from_env(environment)


def test_invalid_base_url() -> None:
    with pytest.raises(ValidationError, match="OPENROUTER_BASE_URL"):
        OpenRouterSettings(
            api_key="secret",
            model="provider/model",
            base_url="not-a-url",
        )


@pytest.mark.parametrize(
    "render",
    [
        repr,
        str,
        lambda settings: settings.model_dump_json(),
    ],
)
def test_api_key_is_redacted(
    render: object,
) -> None:
    secret = "complete-api-key-value"
    settings = OpenRouterSettings(api_key=secret, model="provider/model")

    assert secret not in render(settings)  # type: ignore[operator]


def test_validation_errors_do_not_expose_supplied_secrets() -> None:
    secret = "never-show-this-api-key"

    with pytest.raises(ValidationError) as exc_info:
        OpenRouterSettings(
            api_key=secret,
            model="provider/model",
            base_url="invalid",
        )

    assert secret not in str(exc_info.value)
    assert secret not in repr(exc_info.value)


def test_from_env_does_not_mutate_mapping_or_os_environ(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    injected = {
        "OPENROUTER_API_KEY": "mapping-secret",
        "OPENROUTER_MODEL": "provider/model",
    }
    injected_before = injected.copy()
    os_environ_before = dict(os.environ)

    OpenRouterSettings.from_env(injected)

    assert injected == injected_before
    assert dict(os.environ) == os_environ_before
