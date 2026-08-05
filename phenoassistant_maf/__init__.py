"""Import-safe production interface for PhenoAssistant on MAF."""

from phenoassistant_maf.application import (
    PhenoAssistantApplication,
    build_application,
)
from phenoassistant_maf.config import OpenRouterSettings
from phenoassistant_maf.manager import (
    INITIAL_MANAGER_TOOLS,
    MANAGER_INSTRUCTIONS_VERSION,
    build_manager_agent,
)
from phenoassistant_maf.provider import create_chat_client
from phenoassistant_maf.registry import (
    ProductionToolRegistry,
    build_production_tool_registry,
)
from phenoassistant_maf.runtime import run_application

__all__ = [
    "INITIAL_MANAGER_TOOLS",
    "MANAGER_INSTRUCTIONS_VERSION",
    "OpenRouterSettings",
    "PhenoAssistantApplication",
    "ProductionToolRegistry",
    "build_application",
    "build_manager_agent",
    "build_production_tool_registry",
    "create_chat_client",
    "run_application",
]
