"""Explicit Microsoft Agent Framework client construction."""

from agent_framework.openai import OpenAIChatCompletionClient

from phenoassistant_maf.config import OpenRouterSettings


def create_chat_client(
    settings: OpenRouterSettings,
) -> OpenAIChatCompletionClient:
    """Construct an OpenRouter-backed MAF client only when called."""
    return OpenAIChatCompletionClient(
        model=settings.model,
        api_key=settings.api_key.get_secret_value(),
        base_url=settings.base_url,
    )
