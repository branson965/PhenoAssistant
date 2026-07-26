# PhenoAssistant MAF Research Instructions

## Research objective

Build and evaluate an isolated proof of concept that:

1. Implements a PhenoAssistant Manager using Microsoft Agent Framework.
2. Uses OpenRouter through an OpenAI-compatible interface.
3. Invokes an existing PhenoAssistant statistical tool directly.
4. Invokes the same underlying tool through MCP.
5. Preserves the plan → select → execute → summarise behaviour.
6. Produces reproducible evidence for an AutoGen/MAF comparison.

## Baseline protection

- Treat upstream/v2 as the immutable baseline.
- Do not edit agents.py during the initial proof of concept.
- Do not alter scientific implementations merely to simplify migration.
- Reuse functions from functions/ rather than duplicating them.
- Do not merge or modify upstream/mcp.
- Never commit API keys, access tokens, model weights or .env files.

## New code locations

- MAF implementation: maf_poc/
- Tests: tests/maf_poc/
- Research documentation: docs/maf/
- Prompts and run records: experiments/

## Initial scope

- Begin with one deterministic statistical tool.
- Start without streaming.
- Use one Manager before attempting multi-agent workflows.
- Do not initially migrate vision inference, model training, RAG,
  PandasAI, code execution, plot analysis or pipeline reproduction.
- Keep provider configuration separate from agent construction.

## Engineering requirements

- Inspect relevant code and provide a plan before editing.
- Make the smallest change that meets the acceptance criteria.
- Use type hints and focused docstrings.
- Avoid import-time network calls.
- Do not silently swallow exceptions.
- Unit tests must not make live provider calls.
- Mark live provider and MCP tests as integration tests.
- Run focused tests after every implementation.
- Report files changed, commands run, test results and remaining risks.

## Research requirements

For every experimental run, record:

- Timestamp
- Git commit
- Python and dependency versions
- Framework
- Provider and model
- Temperature and inference settings
- Prompt identifier
- Expected tool
- Actual tool
- Expected arguments
- Actual arguments
- Raw tool output
- Final response
- Success or failure
- Latency
- Retries
- Tokens and cost where available
- Failure category
- Research notes

Do not claim an improvement without a defined baseline and measurements.

## Review priorities

1. Scientific correctness
2. Tool schema correctness
3. Provider coupling
4. Async lifecycle and resource cleanup
5. Secret leakage
6. Dependency drift
7. Reproducibility
8. Accidental baseline modification