# MAF Proof-of-Concept Decision Log

## D001 — Preserve the original implementation

**Status:** Accepted  
**Date:** 2026-07-26

The initial proof of concept will not modify `agents.py`,
`functions/stat_test.py`, the original notebooks, or the existing
environment configuration.

**Reason:** The original implementation is the experimental baseline.
Changing it before comparison would remove evidence and introduce
confounding changes.

---

## D002 — Use a separate Python environment

**Status:** Accepted  
**Date:** 2026-07-26

MAF dependencies will be installed in `.venv-maf`, separate from the
published PhenoAssistant Conda environment.

**Reason:** This prevents dependency drift and preserves baseline
reproducibility.

---

## D003 — Use OpenAIChatCompletionClient for OpenRouter

**Status:** Accepted  
**Date:** 2026-07-26

The first provider implementation will use Microsoft Agent Framework's
`OpenAIChatCompletionClient` with an explicit OpenRouter base URL.

Initial execution will be:

- non-streaming;
- single-agent;
- no reasoning-specific provider options;
- one function tool;
- explicit model configuration.

**Reason:** Chat Completions provides the broadest compatibility with
OpenAI-compatible endpoints and minimises provider-specific variables.

---

## D004 — Preserve and adapt the statistical return contract

**Status:** Accepted  
**Date:** 2026-07-26

The original statistical functions will remain unchanged. A POC adapter
will retain the raw result and expose a stable typed envelope to MAF.

**Reason:** The mismatch between annotation, documentation and actual
return type is part of the baseline evidence.

---

## D005 — Planning is measured, not presumed

**Status:** Accepted  
**Date:** 2026-07-26

The initial comparison will record whether and when a plan is produced.
It will not assume that the original implementation enforces planning
before tool selection.

**Reason:** Stored baseline output shows that a tool can be proposed
before an explicit plan appears.

---

## D006 — MCP comes after direct-tool success

**Status:** Accepted  
**Date:** 2026-07-26

The existing statistical function must work through a direct MAF tool
before it is invoked through MCP.

**Reason:** This separates framework/provider failures from MCP
transport and schema failures.