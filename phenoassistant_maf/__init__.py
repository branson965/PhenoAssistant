"""Import-safe production interface for PhenoAssistant on MAF."""

from phenoassistant_maf.config import OpenRouterSettings
from phenoassistant_maf.provider import create_chat_client
from phenoassistant_maf.registry import (
    ProductionToolRegistry,
    build_production_tool_registry,
)

__all__ = [
    "OpenRouterSettings",
    "ProductionToolRegistry",
    "build_production_tool_registry",
    "create_chat_client",
]
