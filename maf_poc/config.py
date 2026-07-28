"""OpenRouter configuration for the MAF proof of concept."""

from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterSettings(BaseModel):
    """Immutable settings required to connect MAF to OpenRouter."""

    model_config = ConfigDict(frozen=True)

    api_key: SecretStr
    model: str
    base_url: str = DEFAULT_OPENROUTER_BASE_URL

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: SecretStr) -> SecretStr:
        """Reject empty API keys without exposing their contents."""
        if not value.get_secret_value().strip():
            raise ValueError("OPENROUTER_API_KEY must not be empty or whitespace")
        return value

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        """Reject empty OpenRouter model identifiers."""
        if not value.strip():
            raise ValueError("OPENROUTER_MODEL must not be empty or whitespace")
        return value

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        """Require an absolute HTTP(S) OpenRouter endpoint URL."""
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError(
                "OPENROUTER_BASE_URL must be a valid absolute HTTP(S) URL"
            )
        return value

    @classmethod
    def from_env(
        cls, environ: Mapping[str, str] | None = None
    ) -> OpenRouterSettings:
        """Build settings from an injected mapping or, explicitly, ``os.environ``."""
        source = os.environ if environ is None else environ
        values: dict[str, str] = {
            "api_key": source.get("OPENROUTER_API_KEY", ""),
            "model": source.get("OPENROUTER_MODEL", ""),
        }
        if "OPENROUTER_BASE_URL" in source:
            values["base_url"] = source["OPENROUTER_BASE_URL"]
        return cls(**values)
