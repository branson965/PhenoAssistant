# Read-only architectural audit

> Status: Approved as the initial repository architecture baseline on
> 26 July 2026. MAF API choices and implementation decisions are recorded
> separately in DECISIONS.md so that this read-only audit remains an
> unmodified account of the repository findings.

## Scope, baseline, and method

Status: completed without edits, installs, Git mutations, imports of `agents.py`, or live network calls.

Verified baseline:

- `docs/maf/BASELINE_COMMIT` records `aff85512073d9629dfcd501474641eb1919fbe87`.
- `upstream/v2` currently resolves to that exact commit.
- The five focus files have no differences from that commit.
- The working tree remained clean.
- Current branch HEAD is `648c865f2900c340eca163afd752901862e9684b`; therefore this report treats the recorded commit—not current HEAD—as the comparison baseline.

Evidence: [BASELINE_COMMIT](/Users/brans965/Research/PhenoAssistant/docs/maf/BASELINE_COMMIT:1), repository checks described under “Commands run.”

Terminology used below:

- **Verified**: directly established from repository source or stored notebook output.
- **Inference**: conclusion from verified code, but not runtime-tested in this audit.
- **Recommendation**: proposed future design.
- **Unresolved**: cannot safely be determined from the repository alone.

Notebook caveat: `demo.ipynb` is JSON, so raw file lines do not correspond cleanly to notebook source/output presentation. I cite raw JSON ranges where useful and identify the relevant one-based cell number. Exact source-level line citations inside cells are not available without generating another representation, which was prohibited.

---

## 1. Current execution lifecycle

### 1.1 Import and initialization

**Verified**

1. The notebook imports the two preconstructed global agents:

   ```python
   from agents import user_proxy, manager
   ```

   Evidence: `demo.ipynb`, cell 1; raw JSON [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:31).

2. Importing `agents.py` first imports AutoGen classes, PandasAI, Hugging Face, scientific/vision modules, the statistics functions, and other tools.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:1), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:22).

3. It loads `.env.yaml` into `os.environ`, logs into Hugging Face, and constructs the Azure/OpenAI-style configuration.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:43), [generic_tools.py](/Users/brans965/Research/PhenoAssistant/functions/generic_tools.py:44), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:48).

4. It constructs the global `user_proxy`, Manager, nested coding agents, visualisation agent, multimodal plot agent, PandasAI Azure client, RAG agents, and pipeline summariser.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:149), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:159), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:166), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:179), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:201), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:221), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:236), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:296), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:339).

5. Static tools are registered with the Manager as caller and `user_proxy` as executor. Dynamic tool discovery then imports every module beneath `functions`, registers collected decorated functions, and prints the Manager’s tool list.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:371), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:571), [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:24), [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:33), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:581).

### 1.2 User input, planning, and selection

**Verified**

1. The notebook builds a natural-language `task` and starts:

   ```python
   user_proxy.initiate_chat(recipient=manager, message=task)
   ```

   Evidence: `demo.ipynb`, cells 2–5; cell 2 begins at raw JSON [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:39).

2. The Manager receives the task under a system prompt requiring it to:

   - begin with a step-by-step plan;
   - pass intermediate outputs between tools;
   - follow special computer-vision and pipeline-selection rules;
   - summarise at the end;
   - return `TERMINATE` when complete.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:67).

3. The Manager’s LLM receives registered tool schemas and selects tools through model-generated tool calls.

   Evidence: every registration uses `caller=manager` at [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:371); the saved demo shows Manager-generated `get_model_zoo`, `make_dir`, and inference calls in cell 2, raw JSON [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:66), [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:119), [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:152).

4. Planning is prompt-driven, not represented as a typed or independently validated plan object. In the demo, the first tool call occurred before the visible plan; the plan appeared only after a human interruption asking “what is your plan?”

   Evidence: `get_model_zoo` is proposed before the interruption at [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:66); the explicit plan begins at [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:83).

**Inference**

The lifecycle preserves “plan → select → execute → summarise” as an intended conversational policy, but does not technically enforce that ordering. The stored demo proves selection can precede an explicit plan.

### 1.3 Tool execution and result handling

**Verified**

1. AutoGen registers each callable with two roles:

   - Manager: tool caller/schema consumer.
   - `user_proxy`: Python executor.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:371).

2. The `user_proxy` is a `ConversableAgent` with `human_input_mode="ALWAYS"` and no LLM. It terminates when a message ends with `TERMINATE`.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:150).

3. Stored demo output shows the executor receiving the tool call, optionally waiting for human input, executing the Python callable, then returning its result to the Manager.

   Evidence: raw demo output for `get_model_zoo` at [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:113) and its returned JSON at [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:120).

4. A tool may itself start a nested AutoGen conversation:

   - `coding`: executor ↔ code writer, up to six turns, reflection summary.
   - `plot_from_csv`: executor ↔ visualiser, up to three turns.
   - `analyse_plot`: user proxy ↔ multimodal agent.
   - RAG: retrieval proxy ↔ retrieval assistant.
   - pipeline extraction: user proxy ↔ pipeline summariser.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:185), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:208), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:227), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:327), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:346).

5. For ordinary deterministic tools such as ANOVA and Tukey, the callable return value is sent back as tool output. The Manager then reasons over it and may issue another tool call or produce a user-facing response.

### 1.4 Final response and state

**Verified**

- The Manager prompt requires a result summary, an offer of further assistance, and `TERMINATE` on completion. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:78).
- `user_proxy` recognizes only content ending in `TERMINATE` as terminal. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:156).
- Notebook tasks reuse the same global agents without `clear_history=True`. Evidence: `demo.ipynb`, cells 2–5.

**Inference**

Conversation history may carry across successive notebook tasks. Exact retention behavior depends on AutoGen 0.2.39 internals, but the call sites do not explicitly clear it. This is a material reproducibility risk.

---

## 2. AutoGen dependency inventory

### Classes and modules

| AutoGen element | Use | Evidence |
|---|---|---|
| `autogen.ConversableAgent` | Human-facing Admin/executor | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:150) |
| `autogen.AssistantAgent` | Manager, code writer, visualiser, pipeline summariser | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:160), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:179), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:202), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:340) |
| `autogen.UserProxyAgent` | Code executor | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:167) |
| `MultimodalConversableAgent` | Plot/image analysis | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:2), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:222) |
| `RetrieveUserProxyAgent` | Retrieval, vector-store orchestration | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:3), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:310) |
| `RetrieveAssistantAgent` | Answers augmented prompts | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:4), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:321) |
| `register_function` | Generates/exposes schemas and binds caller/executor | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:5), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:371) |
| AutoGen image utilities | Used by generic multimodal helpers | [generic_tools.py](/Users/brans965/Research/PhenoAssistant/functions/generic_tools.py:14) |

### Configuration structures

**Verified**

- `config_list`: one Azure-style model dictionary containing model, base URL, API version, temperature, cache seed, timeout, API type, and API key. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:49).
- `gpt_config = {"config_list": config_list}` is shared by all LLM-backed AutoGen agents. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:63).
- `retrieve_config` supplies task, document path, chunk size, collection name, embedding model, and selected chat model. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:297).
- Code execution config uses the workspace root, host execution (`use_docker=False`), and automatic history selection. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:173).

### Registration mechanisms

**Verified**

1. Twenty-four explicit `register_function` calls expose the two statistics functions, pipeline operations, arithmetic/search, vision inference/training, phenotype computation, nested agents, RAG, and filesystem creation. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:371), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:569).

2. Extension registration uses:

   - `_PHENO_TOOLS`, a mutable module-global list;
   - `@pheno_tool` or `add_tool`;
   - import-all discovery under `functions`;
   - a second `register_function` loop.

   Evidence: [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:5), [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:8), [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:17), [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:24), [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:33).

3. Tool names and descriptions can override callable names/docstrings; parameter schemas are inferred from signatures and `Annotated` metadata.

### Runtime behaviors tied to AutoGen

- Tool-call generation by the Manager.
- Function dispatch through a separate executor agent.
- `initiate_chat` conversation loops.
- per-agent message histories.
- `clear_history`, `max_turns`, `silent`, and `human_input_mode`.
- `summary_method="reflection_with_llm"` or `"last_msg"`.
- suffix-based termination.
- local code execution without Docker.
- multimodal `<img path>` message convention.
- RAG proxy message generation.
- tool schema storage in `manager.llm_config["tools"]`.

Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:150), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:185), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:208), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:227), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:327), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:346), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:581).

Dependency pin: `autogen-agentchat==0.2.39`. Evidence: [environment.yml](/Users/brans965/Research/PhenoAssistant/environment.yml:143).

---

## 3. Provider dependency inventory

### 3.1 Configuration coupling

**Azure OpenAI**

- The Manager configuration hardcodes `"api_type": "azure"` and requires Azure endpoint and API version fields. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:49).
- PandasAI independently constructs its own Azure client from the same environment keys. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:237).
- Provider configuration and agent construction coexist in the same import-time module, rather than being separate concerns.

**OpenAI**

- `OPENAI_API_KEY` is the credential variable used even for Azure. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:59).
- `openai==1.62.0` is pinned. Evidence: [environment.yml](/Users/brans965/Research/PhenoAssistant/environment.yml:259).
- README says Azure OpenAI “or OpenAI,” but the active code is Azure-specific. Evidence: [README.md](/Users/brans965/Research/PhenoAssistant/README.md:49), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:53).

**Inference**

A standard OpenAI or OpenRouter endpoint cannot be selected solely through existing configuration because `api_type`, Azure API version, and PandasAI’s Azure-specific class are fixed in construction code.

### 3.2 API coupling

**Hugging Face**

- Unconditional import-time `huggingface_hub.login`. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:43).
- Dataset upload uses `DatasetDict.push_to_hub`. Evidence: [create_hf_dataset.py](/Users/brans965/Research/PhenoAssistant/functions/create_hf_dataset.py:111).
- Vision implementations use Hub download APIs and Transformers/PEFT `from_pretrained` calls during tool execution. Evidence: [instance_segmentation.py](/Users/brans965/Research/PhenoAssistant/functions/instance_segmentation.py:372), [image_classification.py](/Users/brans965/Research/PhenoAssistant/functions/image_classification.py:311), [image_regression.py](/Users/brans965/Research/PhenoAssistant/functions/image_regression.py:286).
- Training enables `push_to_hub=True`. Evidence: [instance_segmentation.py](/Users/brans965/Research/PhenoAssistant/functions/instance_segmentation.py:287), [image_classification.py](/Users/brans965/Research/PhenoAssistant/functions/image_classification.py:245), [image_regression.py](/Users/brans965/Research/PhenoAssistant/functions/image_regression.py:218).

**Other network providers**

- Google search plus static and browser-driven scraping. Evidence: [search.py](/Users/brans965/Research/PhenoAssistant/functions/search.py:23), [search.py](/Users/brans965/Research/PhenoAssistant/functions/search.py:159), [search.py](/Users/brans965/Research/PhenoAssistant/functions/search.py:176).
- PandasAI may make Azure model calls when `compute_csv` or `query_csv` runs. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:256), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:278).

### 3.3 Model-specific behavior

- README says published results used GPT-4o version `2024-08-06` via Azure and warns provider/model changes may alter results. Evidence: [README.md](/Users/brans965/Research/PhenoAssistant/README.md:70).
- `analyse_plot` is described specifically as GPT-4o, though the actual agent uses whatever `MODEL_NAME` supplies. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:482).
- `all-mpnet-base-v2` is hardcoded for retrieval embeddings. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:297).
- Computer-vision implementations are coupled to Transformers, PEFT, task-specific model classes, CUDA-capable PyTorch, and Hugging Face checkpoint formats. Evidence: [environment.yml](/Users/brans965/Research/PhenoAssistant/environment.yml:102), [environment.yml](/Users/brans965/Research/PhenoAssistant/environment.yml:104), [environment.yml](/Users/brans965/Research/PhenoAssistant/environment.yml:317), [environment.yml](/Users/brans965/Research/PhenoAssistant/environment.yml:349).

### 3.4 Credentials and environment variables

**Verified without reading secret values**

`.env.yaml` is tracked by Git and contains keys for:

- `API_TYPE`
- `MODEL_NAME`
- `OPENAI_API_KEY`
- `AZURE_API_VERSION`
- `AZURE_API_URL`
- `HF_TOKEN`
- `HF_USER`
- Hugging Face/Transformers cache paths
- `PANDASAI_API_KEY`
- model/pipeline paths

`set_env_vars` copies every entry into the process environment. Evidence: [generic_tools.py](/Users/brans965/Research/PhenoAssistant/functions/generic_tools.py:44).

**Critical risk**

A credential-bearing `.env.yaml` is tracked. I did not inspect or reproduce any values. Whether its current values are real, placeholders, or already revoked is unresolved. It should be treated as a potential secret exposure and handled outside this read-only audit.

---

## 4. Import-time behavior

### Verified side effects

| Behavior | Evidence |
|---|---|
| Loads `.env.yaml` | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:43) |
| Mutates `os.environ` for every YAML key | [generic_tools.py](/Users/brans965/Research/PhenoAssistant/functions/generic_tools.py:44) |
| Calls Hugging Face `login` | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:44) |
| Constructs model/provider config globals | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:48) |
| Constructs all global agents | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:149) |
| Constructs PandasAI Azure client | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:237) |
| Constructs retrieval configuration and agents | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:296) |
| Mutates Manager tool schemas and executor function map through registrations | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:371) |
| Imports every module under `functions` dynamically | [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:24) |
| Mutates global `_PHENO_TOOLS` when decorated modules import | [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:5) |
| Emits warnings, including swallowed dynamic-registration failures | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:571) |
| Prints every available tool | [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:581) |

### Network behavior

**Verified**

`login(token=...)` is called unconditionally during import. This is the only explicit top-level network-capable call identified in `agents.py`.

**Inference**

Whether a particular `huggingface_hub.login` invocation performs a remote request can depend on library state/version, but import must be considered network-capable. Stored notebook output also shows Hugging Face login-related output and Albumentations update checking during import; see `demo.ipynb`, cell 1, raw output [demo.ipynb](/Users/brans965/Research/PhenoAssistant/demo.ipynb:7).

No chat completion is explicitly initiated at import. `from_pretrained`, dataset downloads, web search, and training uploads occur inside functions rather than directly at module top level.

### Failure behavior

- Missing `.env.yaml`, absent keys, malformed YAML, or import failures before the final registry block abort import.
- Dynamic tool discovery alone is wrapped in `except Exception`, converted to a warning, and allowed to continue. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:571).
- This broad handler can hide syntax, dependency, circular-import, or registration errors, contrary to the research instruction not to silently swallow exceptions.

### Mutable globals

- `config_list`, `gpt_config`, all agent objects, `pdsllm`, retrieval config, and Manager tool/function registrations.
- `_PHENO_TOOLS` can accumulate duplicate entries if modules are reloaded or `add_tool` is called repeatedly; no deduplication exists. Evidence: [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:5).

---

## 5. Tool architecture

### Definition and documentation

**Verified**

Tools are ordinary Python callables. Their contracts come from four partially independent sources:

1. Python signature and type annotation.
2. `Annotated` parameter descriptions.
3. Callable docstring.
4. Explicit `register_function(description=...)`.

For example, ANOVA has annotated parameters and a docstring in [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:5), while the Manager sees the separate registration description in [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:371).

### Registration and visibility

- Explicit tools are registered individually.
- Extension tools are collected by decorators into `_PHENO_TOOLS`, discovered by importing every `functions.*` module, and registered afterward.
- AutoGen stores the resulting schemas in `manager.llm_config["tools"]`, which `agents.py` enumerates.

Evidence: [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:8), [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:24), [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:33), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:581).

### Selection

The Manager’s LLM selects tools from names, descriptions, schemas, system prompt, conversation history, and prior tool results. There is no deterministic router, allow-list per task, or schema-level semantic validation.

### Execution

AutoGen binds registered callables to `user_proxy`. Tool calls generated by the Manager are executed directly in the same Python process.

This means statistical tool execution is not isolated from:

- process environment;
- filesystem;
- global module state;
- other registered tools;
- human-intervention settings.

### Extension issues

- Discovery imports all modules, despite the comment saying it should register only decorated tools. Evidence: [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:23).
- `functions/new_agents.py` imports `agents` during discovery, creating circular-import/reentrancy risk. Evidence: [new_agents.py](/Users/brans965/Research/PhenoAssistant/functions/new_agents.py:4).
- The broad catch around discovery masks failures. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:571).
- `utils/run.py` calls a nonexistent `agents.get_manager_and_proxy`, so the CLI path is inconsistent with the present global-construction design. Evidence: [run.py](/Users/brans965/Research/PhenoAssistant/utils/run.py:3), while no such definition exists in the 583-line `agents.py`.

---

## 6. Exact ANOVA call path

1. `perform_anova` is imported by reference from `functions.stat_test`.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:29).

2. `register_function` registers that callable under `"perform_anova"`:

   - caller: `manager`;
   - executor: `user_proxy`;
   - description: mixed-design repeated-measures ANOVA with automatic Greenhouse–Geisser correction.

   Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:371).

3. AutoGen derives its argument schema from:

   - `data_path`
   - `descriptor`
   - `within_subject_factor`
   - `between_subject_factor`
   - `subject_id`
   - optional `save_path`

   Evidence: [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:5).

4. The Manager produces a tool call; `user_proxy` dispatches the bound Python function.

5. `perform_anova`:

   - calls `pd.read_csv(data_path)`;
   - coerces within, between, and subject columns to categorical;
   - calls:

     ```python
     pg.mixed_anova(
         dv=descriptor,
         within=within_subject_factor,
         between=between_subject_factor,
         subject=subject_id,
         data=data,
         correction="auto",
     )
     ```

   - prints the DataFrame.

   Evidence: [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:19).

6. Return branches:

   - with `save_path`: writes CSV and returns a status string;
   - without `save_path`: returns `anova_results.to_dict(orient="records")`, a list of dictionaries.

   Evidence: [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:36).

7. AutoGen serializes/transports the returned value as the tool response to the Manager; the Manager then summarises it or continues selecting tools.

**No wrapper or duplicate scientific implementation exists in this path.**

---

## 7. Exact Tukey call path

1. `perform_tukey_test` is imported from the same module. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:29).

2. It is registered under `"perform_tukey_test"` with Manager as caller and `user_proxy` as executor. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:379).

3. Its schema contains:

   - `data_path`
   - `descriptor`
   - `between_subject_factor`
   - `subject_id`
   - optional `save_path`

   Evidence: [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:44).

4. The callable:

   - loads CSV;
   - groups by subject ID and between-subject factor;
   - averages the descriptor within those groups;
   - calls `pg.pairwise_tukey` using the aggregated descriptor and between factor;
   - prints the result.

   Evidence: [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:57).

5. Return branches:

   - with `save_path`: writes CSV and returns a status string;
   - without `save_path`: returns a list of record dictionaries.

   Evidence: [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:69).

6. The executor returns that value to the Manager for subsequent reasoning or final summarisation.

**Scientific observation:** time/repeated observations are collapsed by mean per subject and between-group before Tukey. There is no within-factor parameter, time-column validation, missing-data policy, or check that aggregation matches the preceding ANOVA design.

---

## 8. Contract audit

### Statistical functions

| Contract surface | Declared/documented | Actual | Finding |
|---|---|---|---|
| ANOVA return annotation | `str` | `str` when saved; `list[dict]` otherwise | Mismatch |
| ANOVA docstring | `pd.DataFrame` | Never returns a DataFrame | Mismatch |
| Tukey return annotation | `str` | `str` when saved; `list[dict]` otherwise | Mismatch |
| Tukey docstring | `pd.DataFrame` | Never returns a DataFrame | Mismatch |
| `save_path` | `Annotated[Optional[str]]` | String path or `None` | Broadly consistent |
| ANOVA correction | Description promises automatic GG “if needed” | Passes `correction="auto"` to Pingouin | Implementation aligned, dependent on Pingouin semantics |
| Printed output | Undocumented | Both print full result DataFrames | Side-effect not in contract |

Evidence: [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:5), [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:34), [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:44), [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:67).

### Schema and semantic gaps

**Verified**

- Parameter annotations specify only `str`, not path existence, column membership, categorical cardinality, allowed nulls, or output union.
- AutoGen receives a schema generated from annotations, but the `-> str` annotation does not represent the unsaved result.
- Registration descriptions omit output shape, error behavior, and the distinction between a saved status message and inline records.
- No explicit structured error type is returned.

**Error behavior**

Exceptions propagate naturally from:

- missing/unreadable files;
- malformed CSV;
- absent columns;
- invalid data types;
- insufficient levels or subjects;
- Pingouin/statistical precondition violations;
- unwritable save paths.

No exception is caught in `stat_test.py`. Evidence: [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:19), [stat_test.py](/Users/brans965/Research/PhenoAssistant/functions/stat_test.py:57).

This is preferable to silent failure, but the tool contract does not document it and the Manager receives framework-shaped errors rather than a stable application error model.

### Scientific contract risks

- The name “ANOVA” can encourage use for ordinary one-way ANOVA, but the function strictly requires a mixed repeated-measures design.
- `perform_tukey_test` claims Tukey-Kramer but provides no explicit unequal-sample-size handling contract beyond delegating to Pingouin.
- Tukey aggregation assumes averaging observations for a subject is scientifically appropriate.
- No pairing between ANOVA output and post-hoc procedure is enforced.
- No multiple-testing policy beyond the delegated Tukey method is documented.
- Neither function returns metadata describing input rows, removed observations, package version, or statistical assumptions.

### Wider contract problems affecting migration

- `compute_csv` declares `str`, but discards `res` in the save branch and trusts the model/skill to write the requested file. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:256).
- `extract_pipeline` executes LLM-produced pipeline text through a saving path without a typed intermediate representation. Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:346).
- Dynamic registration can duplicate tool names and has no collision check. Evidence: [registry.py](/Users/brans965/Research/PhenoAssistant/utils/registry.py:33).

---

## 9. AutoGen-to-MAF mapping

Because network access was explicitly prohibited, these are architectural mappings based on repository behavior and general MAF concepts, not a claim about a particular current package/API signature.

| Current component | Plausible MAF equivalent | Classification | Notes |
|---|---|---|---|
| `AssistantAgent` Manager | MAF agent configured with chat client, instructions, and tools | **Direct migration** | Core single-agent/tool loop |
| `config_list` | OpenAI-compatible chat-client/provider options | **Adaptation required** | OpenRouter base URL, headers, model, timeout, temperature must be isolated |
| `register_function` | MAF function/tool wrapper generated from Python callable | **Adaptation required** | Preserve exact schema and normalize return contract |
| `user_proxy` as tool executor | Framework tool dispatcher or local function invocation | **Redesign required** | A separate conversational executor is unnecessary for the vertical slice |
| `human_input_mode="ALWAYS"` | Explicit approval/intervention callback | **Adaptation required** | Must define when approval is needed |
| termination suffix | Run completion/final response policy | **Adaptation required** | Avoid relying solely on literal `TERMINATE` |
| Manager message history | MAF session/thread/context state | **Adaptation required** | Explicit state lifecycle needed |
| `summary_method="reflection_with_llm"` | Follow-up summarisation invocation | **Adaptation required** | Adds calls, latency, tokens, and comparison confounds |
| `UserProxyAgent` code executor | MAF code-interpreter/sandbox integration | **Redesign required** | Explicitly out of initial scope |
| nested code writer/visualiser | Agent-as-tool or workflow sub-agent | **Redesign required** | Defer |
| `MultimodalConversableAgent` | Multimodal MAF messages/model client | **Unresolved** | Provider/model payload compatibility must be verified |
| retrieval agents/config | MAF retrieval/knowledge integration | **Redesign required** | Vector-store and embedding lifecycle differ |
| PandasAI agent | External tool/service wrapper | **Redesign required** | Separate agent ecosystem and Azure client |
| pipeline summariser | MAF workflow/trace-to-artifact component | **Redesign required** | Current pipeline extraction is code-generative |
| dynamic `_PHENO_TOOLS` registry | Explicit application tool registry | **Adaptation required** | Avoid import-all discovery |
| runtime logging/chat logs | MAF observability plus experiment recorder | **Adaptation required** | Research fields require a framework-neutral schema |
| direct `perform_anova` call | Local MAF function tool | **Direct migration** | Best candidate if mixed-design fixture is available |
| same function through MCP | MAF MCP tool/client integration | **Adaptation required** | Must invoke the identical underlying implementation |
| OpenRouter | OpenAI-compatible MAF client with custom endpoint | **Adaptation required** | Exact SDK support/version remains unresolved |

---

## 10. Smallest viable vertical slice

### Recommendation

Build an isolated, non-streaming, single-Manager path around one existing deterministic statistical function.

The minimum slice should contain:

1. A provider configuration object that reads OpenRouter settings at runtime and does not construct a client on import.
2. One MAF Manager with a short, versioned prompt that requires:

   - explicit plan;
   - tool selection;
   - tool execution;
   - evidence-based summary.

3. A thin tool adapter that calls an existing function from `functions/stat_test.py` without changing it.
4. A framework-neutral result normalizer at the boundary, because the underlying function has a union return despite `-> str`.
5. A deterministic local CSV fixture satisfying the selected test’s scientific assumptions.
6. Unit tests using a fake/scripted model client and no live provider calls.
7. One opt-in integration test for OpenRouter.
8. A separate opt-in MCP integration path invoking the same underlying callable.
9. A structured experiment recorder containing every field required by `AGENTS.md`.

### Choice of initial tool

**Recommendation:** use `perform_anova` only if a scientifically valid mixed-design repeated-measures fixture can be agreed. Otherwise use `perform_tukey_test` with a carefully documented repeated-observation fixture.

ANOVA is preferable for traceability because:

- it is registered first and central to the stated statistical workflow;
- its schema is explicit;
- the existing implementation delegates deterministically to Pingouin;
- its “inline records” branch is straightforward to assert.

However, its five scientific input dimensions make it easier for an LLM to select semantically wrong arguments. This is both a useful evaluation target and a Stage 1 risk.

### Explicit exclusions

Do not include streaming, multiple agents, image inference, training, RAG, PandasAI, arbitrary code execution, plot analysis, pipeline reproduction, or human intervention in the first vertical slice. This follows [AGENTS.md](/Users/brans965/Research/PhenoAssistant/AGENTS.md:23).

---

## 11. Experimental validity risks

| Confound | Why comparison may be invalid | Required control |
|---|---|---|
| Model | README baseline used GPT-4o 2024-08-06; OpenRouter may expose another model/version | Use the same underlying model where possible; otherwise label comparison provider/model rather than framework-only |
| Provider | Azure and OpenRouter may transform schemas, prompts, sampling, usage, and errors differently | Record endpoint/provider and compare provider effects separately |
| Prompt | Rewriting the Manager prompt changes planning and tool selection | Freeze a prompt ID and exact text across both harnesses |
| Tool set | AutoGen Manager currently sees roughly two dozen tools; a MAF slice with one tool has an easier selection task | Compare both a controlled one-tool baseline and the full-baseline condition |
| Tool schema | Framework schema generators may encode `Annotated`, optional values, and return types differently | Save the exact emitted JSON schema for each run |
| Invalid return annotation | `-> str` conflicts with inline `list[dict]` | Normalize equally or preserve mismatch equally and document it |
| Conversation history | Demo reuses global agent history | Start every measured trial from a fresh, explicitly recorded state |
| Human input | AutoGen executor is `ALWAYS`; notebook output includes interruption/timeout behavior | Disable intervention for both or measure it as a separate condition |
| Retries | Provider and framework defaults may retry differently | Configure and record retry policy and actual retry count |
| Caching | AutoGen config has `cache_seed=42`; cache behavior could suppress calls or latency | Disable caching or reproduce equivalent cache conditions |
| Temperature | Current value is 0.1 | Fix temperature and all supported sampling parameters |
| Tool-call parallelism | Provider/framework defaults may allow parallel calls | Set explicitly or record behavior |
| Timeouts | AutoGen timeout is `540000` | Align timeout semantics |
| Summarisation | Some nested paths use an additional reflection LLM call | Count calls and separate execution from summarisation latency/cost |
| Dependency drift | Environment mixes exact pins, unpinned `metrics` and `xarray`, Conda/CUDA constraints | Capture lock/resolution and package versions per run |
| Hardware | Baseline environment is Linux/CUDA-specific, while statistical slice is CPU-capable | Run both frameworks in the same CPU environment |
| Dataset | Different CSV ordering, categories, null handling, or path text can alter output/prompt | Version fixture content and checksum it |
| Statistical package | Pingouin/pandas versions affect output columns and values | Pin and record exact versions |
| Error handling | Frameworks stringify exceptions differently | Define framework-neutral failure categories |
| Token accounting | Providers report usage/cost differently or incompletely | Save raw usage and mark unavailable fields explicitly |
| Warm-up | First import/client connection differs from subsequent trials | Define cold/warm run protocol |
| Baseline mismatch | Comparing current branch rather than recorded commit invalidates evidence | Run AutoGen comparison from an isolated worktree at the recorded commit |
| Survivorship | Reporting only successful runs hides selection/execution failures | Predeclare trial count and record every attempt |

---

## 12. Migration risks outside the initial slice

### Conversation state — adaptation required

Global agents are reused, while individual nested calls sometimes clear history and sometimes do not. MAF state must have explicit ownership, reset, and persistence semantics.

Evidence: notebook reuse plus [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:190), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:212), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:357).

### Nested agents — redesign required

Coding, visualisation, RAG, multimodal analysis, and pipeline extraction are exposed to the Manager as functions but internally run separate conversations. Their call counts, state, summarisation, and failure behavior do not map to a single local function tool.

### Multimodal messages — unresolved

The current plot analyzer passes `"<img {file_path}>"`, an AutoGen-specific convention. MAF/OpenRouter may require structured image parts, MIME types, or data URLs.

Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:227).

### Code execution — redesign required/high risk

The code executor runs generated Python on the host with `use_docker=False` and workspace root as working directory.

Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:167).

### PandasAI — redesign required

It uses a separate Azure-specific model client and performs agentic dataframe operations. Provider parity and execution safety cannot be inherited automatically from the MAF Manager.

Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:236), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:256).

### RAG — redesign required

The current path relies on AutoGen retrieval agents, a hardcoded local PDF, a named collection, a sentence-transformer embedding model, and implicit vector-database behavior.

Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:296).

### Human intervention — adaptation required

`human_input_mode="ALWAYS"` affects every tool execution and termination. A MAF proof must either reproduce that approval lifecycle or explicitly exclude it and ensure the AutoGen comparison does the same.

### Pipeline reproduction — redesign required

The current design extracts Python from chat logs through an LLM, saves it into a pipeline registry, dynamically imports saved code, and can execute it. This requires provenance, validation, sandboxing, and reproducibility controls beyond simple tool migration.

Evidence: [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:83), [agents.py](/Users/brans965/Research/PhenoAssistant/agents.py:346), [reproducible_pipeline.py](/Users/brans965/Research/PhenoAssistant/functions/reproducible_pipeline.py:12), [reproducible_pipeline.py](/Users/brans965/Research/PhenoAssistant/functions/reproducible_pipeline.py:93), [reproducible_pipeline.py](/Users/brans965/Research/PhenoAssistant/functions/reproducible_pipeline.py:149).

### Vision and training — redesign required

These rely on GPU/CUDA, Hugging Face repositories, checkpoint conventions, local model zoo state, file outputs, and tool-specific preprocessing. They should remain excluded until the statistical slice is stable.

---

# A. Files that must remain untouched initially

At minimum:

- `agents.py`
- `functions/stat_test.py`
- every existing file under `functions/` containing scientific implementations
- `environment.yml`
- `README.md`
- `demo.ipynb`
- `.env.yaml`
- `model_zoo.json`
- `pipeline_zoo.json`
- `extracted_pipelines.py`
- all baseline notebooks and stored results
- all files on `upstream/v2`
- all files on `upstream/mcp`

The proof should import existing statistical functions but not modify them.

Additionally, the tracked `.env.yaml` requires separate security handling; it must not be copied into experiments, tests, logs, commits, or prompts.

---

# B. Proposed new files

| Proposed file | Responsibility |
|---|---|
| `maf_poc/__init__.py` | Package boundary with no import-time client construction |
| `maf_poc/config.py` | Typed OpenRouter/provider settings loaded explicitly at runtime |
| `maf_poc/provider.py` | Construct the OpenAI-compatible MAF chat client |
| `maf_poc/prompts.py` | Versioned Manager prompt and prompt identifier |
| `maf_poc/tool_adapters.py` | Register the existing statistical callable and normalize its boundary contract |
| `maf_poc/manager.py` | Construct and run the single non-streaming Manager |
| `maf_poc/records.py` | Framework-neutral experimental-run record schema |
| `maf_poc/mcp_client.py` | Opt-in MCP invocation of the same tool contract |
| `tests/maf_poc/test_tool_adapter.py` | Direct deterministic tool/contract tests |
| `tests/maf_poc/test_manager_unit.py` | Fake-client plan/select/execute/summarise test |
| `tests/maf_poc/test_config.py` | Configuration validation and secret-safety tests |
| `tests/maf_poc/test_openrouter_integration.py` | Marked live provider integration test |
| `tests/maf_poc/test_mcp_integration.py` | Marked MCP integration test |
| `tests/maf_poc/fixtures/mixed_anova.csv` | Versioned scientifically valid deterministic input |
| `docs/maf/ARCHITECTURE.md` | POC design and AutoGen/MAF mapping |
| `docs/maf/EXPERIMENT_PROTOCOL.md` | Predeclared controlled comparison method |
| `experiments/prompts/manager_stage1.txt` | Immutable prompt artifact |
| `experiments/schemas/run_record.schema.json` | Machine-validatable experiment record |
| `experiments/runs/.gitkeep` | Location only; actual policy should prevent secrets/raw sensitive data |

Exact filenames may be consolidated, but provider configuration, agent construction, tool adaptation, and experimental recording should remain separate responsibilities.

---

# C. Unresolved questions for Feng, Valerio, or Vincent

1. Which person owns scientific approval of the Stage 1 CSV fixture and expected ANOVA result?
2. Is the intended first tool definitely mixed repeated-measures ANOVA, or is a simpler deterministic tool acceptable?
3. Should the unsaved statistical return contract be preserved as `list[dict]`, or normalized externally to a typed result envelope?
4. Was `.env.yaml` intentionally committed with placeholders, and have any historical real credentials been rotated?
5. Which exact AutoGen run constitutes the comparison baseline: a new controlled run at the recorded commit, or a published notebook run?
6. Must AutoGen and MAF use the identical underlying model, or is the research question explicitly framework-plus-provider migration?
7. Which OpenRouter model identifier and revision are approved?
8. Should the Manager see only the selected tool in controlled Stage 1, or the complete baseline tool catalogue?
9. Is human approval part of the behavior to preserve, or explicitly excluded from the initial comparison?
10. What MCP server is the authoritative existing implementation, given that `upstream/mcp` must not be merged or modified?
11. May the POC consume MCP from an isolated worktree/process pinned to `upstream/mcp`?
12. What tolerance and canonical column ordering define scientific equality for ANOVA results?
13. Should planning be an observable text phase, a structured object, or merely a prompt instruction?
14. Who owns the reproducibility record format and retention policy for raw prompts/responses?
15. Are token and cost values from OpenRouter considered authoritative when upstream-provider usage differs?

---

# D. Maximum six-stage implementation sequence

1. **Freeze protocol and contracts**
   Approve baseline commit, model/provider conditions, prompt, fixture, expected tool/arguments/output, and result-record schema.

2. **Direct deterministic tool slice**
   Add isolated configuration, a single MAF Manager, direct statistical adapter, fake-client unit tests, and no live calls.

3. **OpenRouter integration**
   Add opt-in non-streaming integration test, explicit retries/timeouts, secret-safe configuration, and one recorded trial.

4. **Controlled AutoGen baseline**
   Run the same prompt, model, fixture, tool set, sampling settings, and fresh-state protocol from an isolated baseline worktree.

5. **MCP parity**
   Expose or consume the identical underlying function through the approved MCP path and verify direct-versus-MCP equality.

6. **Measured comparison and decision**
   Execute predeclared repetitions, classify failures, compare selection/argument/result/latency/cost metrics, and document limitations without claiming unsupported improvement.

---

# E. Explicit Stage 1 acceptance criteria

Stage 1 is complete only if all of the following hold:

1. No existing baseline or scientific implementation file is modified.
2. `agents.py` is neither imported nor modified by the Stage 1 implementation or unit tests.
3. The POC uses an actual Microsoft Agent Framework agent abstraction, not a local imitation.
4. Provider configuration is separate from Manager construction.
5. Importing `maf_poc` causes no network call, login, model-client construction, environment mutation, or filesystem write.
6. Exactly one existing callable from `functions/stat_test.py` is exposed.
7. The adapter calls that callable directly; it does not duplicate or reimplement scientific logic.
8. The Manager performs observable plan, selection, execution, and summarisation phases.
9. Execution is non-streaming and uses one Manager only.
10. Unit tests use a fake/scripted model client and make no provider calls.
11. Tests assert the selected tool name and exact arguments.
12. Tests assert the raw underlying return and final summary behavior.
13. The return-type mismatch is handled at the adapter boundary and documented.
14. A deterministic, scientifically approved fixture and expected result are versioned.
15. Failures propagate or are converted to an explicit typed failure; none are silently swallowed.
16. OpenRouter credentials are read only at explicit runtime and are never logged.
17. Each test/run can produce the complete research record required by `AGENTS.md`, with unavailable cost/token data represented explicitly rather than omitted.
18. Live OpenRouter and MCP tests are marked integration tests and excluded from ordinary unit runs.
19. Focused tests pass in a CPU-only environment.
20. A final `git diff` confirms no accidental baseline changes.

---

# F. Five highest-priority technical risks

1. **Potential secret exposure:** `.env.yaml` is Git-tracked and contains credential-shaped fields.
2. **Scientific/tool contract mismatch:** statistical annotations, docstrings, schemas, and actual returns disagree.
3. **Invalid comparison design:** changing provider/model/tool count/history/retry defaults could dominate any measured framework difference.
4. **Import-time coupling and side effects:** importing the current agent module loads configuration, logs into Hugging Face, constructs all systems, and registers every tool.
5. **State and executor mismatch:** AutoGen’s persistent conversations, `human_input_mode="ALWAYS"`, nested chats, and executor-agent model do not directly match a simple MAF function-tool loop.

---

# G. Readiness judgement

**Judgement: conditionally ready for an isolated MAF proof of concept, but not yet ready for a defensible AutoGen-versus-MAF performance claim.**

Reasons it is ready for the isolated engineering POC:

- The immutable baseline is precisely recorded and currently matches `upstream/v2`.
- The statistical implementations are small, deterministic, locally callable, and separable from `agents.py`.
- The direct ANOVA and Tukey call paths are clear.
- The repository already defines safe new-code locations.
- A one-Manager, one-tool slice can be built without touching the baseline.

Reasons the comparison is not yet experimentally ready:

- The first scientific fixture and expected result are not defined.
- The statistical return contracts are inconsistent.
- OpenRouter model/provider parity with the Azure GPT-4o baseline is unresolved.
- Existing AutoGen lifecycle state, human intervention, caching, retries, and tool-set size are not yet controlled.
- The experiment record schema and run protocol do not yet exist.
- MCP ownership and the exact approved cross-branch invocation mechanism are unresolved.
- The tracked `.env.yaml` creates an immediate security concern requiring owner review.

## Commands run

All commands were read-only:

- `pwd`
- `rg --files`
- `sed` and `nl` for source inspection
- `wc -l`
- `rg -n` for call-path/provider discovery
- `jq` for notebook cell inspection
- `find` for existing POC/documentation inventory
- `git status --short --branch`
- `git cat-file -t`
- `git branch -r --contains`
- `git diff --name-status` and `git diff --quiet`
- `git show`
- `git rev-parse`
- `git log`
- `git ls-files`

No tests were run because the request was an architectural audit and importing the target module would trigger prohibited network-capable and other side effects. No files or Git state were changed.