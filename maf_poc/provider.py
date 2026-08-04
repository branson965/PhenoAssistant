"""Agent Framework client construction for OpenRouter."""

from agent_framework.openai import OpenAIChatCompletionClient

from maf_poc.config import OpenRouterSettings


def create_chat_client(
    settings: OpenRouterSettings,
) -> OpenAIChatCompletionClient:
    """Construct an OpenRouter-backed Agent Framework chat client."""
    return OpenAIChatCompletionClient(
        model=settings.model,
        api_key=settings.api_key.get_secret_value(),
        base_url=settings.base_url,
    )
