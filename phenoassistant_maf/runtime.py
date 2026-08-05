"""Stateless execution boundary for the production MAF application."""

from __future__ import annotations

from agent_framework import AgentResponse

from phenoassistant_maf.application import PhenoAssistantApplication


async def run_application(
    application: PhenoAssistantApplication,
    prompt: str,
) -> AgentResponse:
    """Execute one non-streaming request without retained session state."""
    normalised_prompt = prompt.strip()

    if not normalised_prompt:
        raise ValueError("prompt must not be blank")

    return await application.manager.run(
        normalised_prompt,
        stream=False,
        session=None,
    )
