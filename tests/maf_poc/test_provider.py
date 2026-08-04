"""Tests for side-effect-free Agent Framework client construction."""

from __future__ import annotations

import importlib
import sys
from unittest.mock import Mock, patch

import pytest
from agent_framework.openai import OpenAIChatCompletionClient
from pydantic import ValidationError

from maf_poc.config import OpenRouterSettings


def test_importing_provider_does_not_construct_client() -> None:
    sys.modules.pop("maf_poc.provider", None)

    with patch(
        "agent_framework.openai.OpenAIChatCompletionClient"
    ) as constructor:
        importlib.import_module("maf_poc.provider")

    constructor.assert_not_called()
    sys.modules.pop("maf_poc.provider", None)
    importlib.import_module("maf_poc.provider")


def test_factory_passes_exact_constructor_arguments() -> None:
    provider = importlib.import_module("maf_poc.provider")
    settings = OpenRouterSettings(
        api_key="raw-secret",
        model="provider/model",
        base_url="https://example.test/v1",
    )
    expected_client = Mock()

    with patch.object(
        provider, "OpenAIChatCompletionClient", return_value=expected_client
    ) as constructor:
        result = provider.create_chat_client(settings)

    constructor.assert_called_once_with(
        model="provider/model",
        api_key="raw-secret",
        base_url="https://example.test/v1",
    )
    assert result is expected_client


def test_client_is_constructed_only_when_factory_is_called() -> None:
    provider = importlib.import_module("maf_poc.provider")
    settings = OpenRouterSettings(api_key="dummy-key", model="provider/model")

    with patch.object(provider, "OpenAIChatCompletionClient") as constructor:
        constructor.assert_not_called()
        provider.create_chat_client(settings)
        constructor.assert_called_once()


def test_invalid_configuration_prevents_provider_construction() -> None:
    provider = importlib.import_module("maf_poc.provider")

    with patch.object(provider, "OpenAIChatCompletionClient") as constructor:
        with pytest.raises(ValidationError):
            OpenRouterSettings(api_key=" ", model="provider/model")

    constructor.assert_not_called()


def test_real_client_can_be_constructed_without_completion() -> None:
    provider = importlib.import_module("maf_poc.provider")
    settings = OpenRouterSettings(
        api_key="dummy-key",
        model="provider/model",
    )

    client = provider.create_chat_client(settings)

    assert isinstance(client, OpenAIChatCompletionClient)
