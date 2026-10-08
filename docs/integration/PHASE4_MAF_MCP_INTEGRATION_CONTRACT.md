# Phase 4 — MAF ↔ MCP Integration Contract

**Status:** frozen integration design  
**Date:** 2026-10-08  
**Owner:** Branson Kouaya  
**Target branch:** `feature/maf-mcp-v2-integration`

## 1. Frozen baselines

Do not rewrite either historical baseline.

| Baseline | Repository / branch | Commit | Purpose |
|---|---|---|---|
| MAF direct | `branson965/PhenoAssistant:feature/maf-linux-migration` | `e0f1626545dc7de2a4d246506564863c00e4c4cd` | independently validated CPU-side MAF implementation |
| MCP v1 / Vincent | `vios-s/PhenoAssistant:mcp` | `44e456811b0d07547fdf8c8ddfb03d1187c1ae1e` | merged generic MCP implementation from PR #3 |
| Common ancestor | upstream MAF baseline | `aff85512073d9629dfcd501474641eb1919fbe87` | common comparison point |

Additional preservation refs in Branson's fork:

- `baseline/maf-pre-mcp-integration-20261008`
- `baseline/vincent-mcp-v1-20261008`

The integration branch starts from the frozen MAF baseline:

- `feature/maf-mcp-v2-integration`

## 2. Verified branch facts

### MAF baseline

- Manager instruction version: `phenoassistant-manager-v5`.
- Full CPU Manager profile: 11 bounded MAF tools.
- Trusted repository/data/model paths are application-bound.
- Manager policy allows one tool call per supported request.
- Scientific computation is deterministic where migrated; the LLM performs semantic routing and summarisation.
- Last verified CPU regression before integration: 168 passed, 2 intentionally skipped.

### Vincent MCP baseline

Upstream PR #3 was merged on 2026-10-06 with title:

> Migrate 25 tools to generic MCP server

Verified PR shape:

- 18 commits;
- 41 changed files;
- 1,491 additions;
- 306 deletions;
- 25 tools in a central `TOOL_REGISTRY`;
- generic `server.py`;
- generic `bridge_factory.py`;
- AutoGen registration through MCP bridges;
- `mcp==1.28.1`.

The implementation is explicitly MCP v1-era:

- `FastMCP`;
- `ClientSession`;
- `session.initialize()`;
- stdio transport.

## 3. Architecture decision

Do **not** merge the two branches mechanically.

The final architecture is:

```text
User
  ↓
MAF Manager
  ↓
typed MAF FunctionTool contract
  ↓
backend choice
  ├── direct Python backend
  └── MCP backend
         ↓
      MCP v2 Client
         ↓
      MCPServer
         ↓
canonical scientific implementation
  ↓
structured evidence
  ↓
MAF Manager grounded summary
```

MAF remains the orchestration layer. MCP is an interchangeable capability-transport layer beneath selected MAF tool contracts.

The Manager must not be given Vincent's 25 raw legacy MCP schemas directly. That would re-introduce model-controlled file paths, broad legacy tool surfaces, and uncontrolled execution semantics that the MAF migration intentionally removed.

## 4. MCP v2 migration rule

The production/research integration targets the stable MCP Python SDK v2 and MCP protocol revision 2026-07-28.

Vincent's `mcp==1.28.1` branch remains immutable as the historical evaluated baseline.

Porting order:

1. dependency migration from `mcp==1.28.1` to `mcp>=2,<3`;
2. `FastMCP` → `MCPServer`;
3. retain the generic `add_tool()` registry pattern;
4. replace hand-managed `ClientSession` + `initialize()` with the first-class v2 `Client`;
5. verify all advertised schemas and result types under v2's stricter protocol validation;
6. keep stdout protection until a regression test proves it is redundant;
7. preserve one compatibility test where a v2 client talks to the frozen v1 server;
8. only then connect the MCP backend beneath MAF.

Important v2 migration risks:

- protocol type attributes are snake_case in Python;
- dependency floors change, including Pydantic;
- client-side inbound validation is stricter;
- sync server functions execute on worker threads;
- exception/error visibility semantics differ;
- v2 removes the modern handshake/session model, although compatibility with older clients remains.

## 5. 25 MCP tools ↔ 11 MAF tools

### 5.1 Exact semantic matches

These are the first parity targets because both sides already point to the same underlying deterministic scientific implementation.

| MCP v1 tool | MAF tool | Mapping | Phase 6 action |
|---|---|---|---|
| `calculator` | `calculator` | exact | create MCP-backed `CalculatorCallable`; require identical result |
| `perform_anova` | `perform_anova` | exact | create MCP-backed `AnovaCallable`; compare complete records |
| `perform_tukey_test` | `perform_tukey_test` | exact | create MCP-backed `TukeyCallable`; compare complete records |

These three form the minimum vertical-slice gate.

### 5.2 Related but **not** valid direct-parity matches

These pairs share purpose but do not currently implement identical semantics. They must not be treated as transport-only comparisons.

| MCP v1 surface | MAF surface | Relationship |
|---|---|---|
| `get_pipeline_zoo`, `get_pipeline_info` | `get_pipeline_catalogue` | MAF is a read-only canonical family view and deliberately does not expose arbitrary execution |
| `get_model_zoo` | `get_model_catalogue` | MAF adds typed validation and task filtering |
| `plot_from_csv` | `plot_longitudinal_phenotypes` | MAF is a fixed scientific workflow, not a generic plotting agent |
| `compute_from_csv` | `compare_linear_relationships` | MAF is a deterministic regression-specific operation |
| `query_csv`, `compute_from_csv` | `query_csv_statistic` | MAF is a bounded deterministic aggregate, not free-form CSV QA |
| `query_csv` (conceptually) | `rank_ecotypes_by_phenotype` | MAF provides a dedicated deterministic ranking workflow |
| `perform_anova` + `perform_tukey_test` | `analyse_repeated_measures_with_posthoc` | MAF composes a fixed Case 1 analysis with explicit thresholds |

For research parity, expose the **same canonical deterministic implementation** through both direct and MCP backends rather than comparing a new deterministic MAF function against a different legacy generic MCP function.

### 5.3 MCP legacy capabilities not yet exposed in MAF

The following 16 MCP tools remain intentionally outside the current MAF Manager surface:

1. `make_dir`
2. `execute_pipeline`
3. `google_search`
4. `compute_phenotypes_from_ins_seg`
5. `get_dataset_format`
6. `prepare_dataset`
7. `infer_instance_segmentation`
8. `finetune_instance_segmentation`
9. `infer_image_classification`
10. `finetune_image_classification`
11. `infer_image_regression`
12. `finetune_image_regression`
13. `analyse_plot`
14. `RAG`
15. `coding`
16. `extract_pipeline`

Do not bulk-register these into MAF. Each capability must receive a bounded typed MAF contract, trusted-resource policy, deterministic/LLM classification, and explicit validation before Manager exposure.

### 5.4 MAF-only safety/reasoning capability

`assess_case3_readiness` has no direct MCP v1 equivalent. It is a migration-era safety boundary that reports training/inference preconditions without executing GPU work.

This capability should evolve rather than disappear: GPU execution should be a separate operation gated by readiness/applicability evidence.

## 6. MCP backend contract under MAF

### 6.1 Stable public interface

The MAF `FunctionTool` schema remains the model-facing contract.

The backend is invisible to the model:

```text
same prompt
same Manager
same MAF FunctionTool name
same Pydantic input model
same trusted application resources
same expected result model

variable:
  direct backend vs MCP backend
```

This is mandatory for valid direct-vs-MCP experiments.

### 6.2 Trusted-resource rule

Paths, checkpoint registries, output directories, credentials, server commands, and transport settings remain application-controlled.

A model may select scientific intent and bounded semantic arguments. It may not choose arbitrary local paths merely because the underlying MCP tool accepts a path.

For example:

```text
Manager-visible perform_anova:
    descriptor
    within_subject_factor
    between_subject_factor
    subject_id

application-bound:
    data_path
    save_path
    MCP server configuration
```

The MCP proxy reconstructs the complete server call from model arguments plus trusted application state.

### 6.3 Structured-result rule

MCP-backed callables must return the same Python shape expected by the existing MAF handler.

Never pass arbitrary MCP text directly through to the scientific result model.

Preferred order:

1. consume `structured_content` when supplied;
2. validate it against the expected local schema;
3. otherwise decode an explicitly versioned JSON content block;
4. fail closed on unstructured or schema-incompatible results.

### 6.4 Error taxonomy

Every backend call must distinguish:

- `transport_error`: server unavailable, timeout, protocol failure;
- `schema_error`: request/result violates declared contract;
- `tool_error`: scientific implementation raised a declared execution failure;
- `scientific_validation_error`: execution completed but returned evidence fails local scientific/result validation.

No category may silently become a natural-language success response.

### 6.5 Trace record

Every direct and MCP execution used in evaluation records at minimum:

- run ID;
- timestamp;
- git commit;
- Manager instruction version;
- model/provider;
- tool name;
- backend = `direct` or `mcp`;
- MCP SDK/protocol/server version where relevant;
- public tool arguments;
- hashes/identifiers of trusted resources, not secrets;
- latency;
- success/failure category;
- structured result hash;
- final answer;
- token/cost data when available.

This trace becomes part of the paper's reproducibility artifact.

## 7. Direct ↔ MCP parity gates

### Gate A — discovery

Modern server advertises the expected canonical tools and schemas.

### Gate B — exact unit parity

For calculator, ANOVA, and Tukey:

```text
direct result == MCP result
```

using deterministic fixtures.

### Gate C — application parity

The same MAF Manager prompt is run with either backend injected. Tool selection and structured scientific evidence must remain equivalent.

### Gate D — case-study parity

Repeat representative Case 1 / Case 3 operations with the backend as the controlled variable.

### Gate E — failure parity

Inject:

- invalid columns;
- missing trusted file;
- MCP server unavailable;
- malformed response;
- timeout;
- scientific incompatibility.

The failure must be explicit, typed, traceable, and must not produce an unsupported final claim.

## 8. Merge-conflict audit

Both branches descend from `aff8551`.

From their recorded diffs, the only direct changed-file overlap is `.gitignore`.

This does **not** mean a raw merge is safe. The semantic conflict is much larger:

- Vincent modifies `agents.py` to route AutoGen registrations through MCP.
- MAF intentionally replaces AutoGen as the orchestration path.
- Vincent pins the full legacy `environment.yml` plus MCP v1.
- MAF uses separate lean requirements for CPU migration.
- Vincent's MCP registry exposes broad path-accepting legacy functions.
- MAF intentionally wraps a smaller bounded set and hides trusted resources.

Therefore integration uses selective porting/adapters, not a branch merge.

Files/concepts to port or recreate deliberately:

- `tool_registry.py` concept;
- `server.py` generic registration concept;
- client/bridge behaviour, rewritten for MCP v2;
- MCP-specific regression/evaluation knowledge.

Files **not** to copy wholesale into the MAF integration branch:

- MCP `agents.py`;
- MCP `environment.yml`;
- generated caches / `__pycache__`;
- logs and transient demo outputs;
- legacy AutoGen registration patching machinery.

## 9. Phase 4 exit criteria

Phase 4 is complete when all are true:

- [x] authoritative MAF SHA frozen;
- [x] authoritative MCP SHA frozen;
- [x] preservation branches created;
- [x] MCP protocol/SDK generation identified;
- [x] 25 ↔ 11 capability map written;
- [x] merge-conflict surface audited;
- [x] target MAF↔MCP architecture fixed;
- [x] backend adapter contract fixed;
- [x] direct/MCP parity gates fixed;
Phase 4 is complete at this checkpoint.

Phase 5 begins with GPU environment capture and a one-image scientific smoke test. No production MCP integration code should precede those environment/scientific baselines.

## 10. Research consequence

The integration itself is infrastructure, not the paper claim.

The experimental value is that direct and MCP execution can be made a controlled variable while the Manager, model, prompt, trusted resources, scientific implementation, and result contract stay fixed.

This enables a defensible research statement about whether transport/interoperability affects reliability while the main research contribution remains scientific applicability under distribution shift.
