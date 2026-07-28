"""Import-safe public interface for the MAF proof of concept."""

from maf_poc.config import OpenRouterSettings
from maf_poc.provider import create_chat_client

__all__ = ["OpenRouterSettings", "create_chat_client"]
