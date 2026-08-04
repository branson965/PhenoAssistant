# AutoGen-to-Microsoft Agent Framework Component Map

## Status

- Branch: `feature/maf-linux-migration`
- Source commit: `27ac1f74484ecba37e253778f4e3fe95c0c83c58`
- Generated: `2026-08-04T22:22:02.726926+00:00`
- Original `agents.py` remains unchanged.
- Existing scientific function implementations remain unchanged.

## Migration objective

Replace AutoGen orchestration with Microsoft Agent Framework while preserving the scientific toolkit and retaining the original AutoGen implementation as a comparison baseline.

## Primary component mapping

| Current AutoGen responsibility | Production MAF responsibility | Migration rule |
|---|---|---|
| Azure-oriented LLM configuration | Typed OpenRouter settings | No provider activity during import |
| Global Manager `AssistantAgent` | Explicit MAF Manager factory | Preserve the Manager prompt initially |
| User Proxy function map | Typed `FunctionTool` registry | No implicit global registration |
| `register_function` calls | Explicit adapters and registry construction | Preserve published names and schemas |
| Global agent construction | Application factory | Construct only at runtime |
| Module-level Hugging Face login | Lazy optional authentication | Invoke only for workflows that need it |
| Import-time Chroma setup | Explicit retrieval-store factory | Configure storage and lifecycle |
| Nested AutoGen conversations | MAF specialist agents or ordinary tools | Decide component by component |
| `initiate_chat` entry points | Explicit runtime/session service | Test reset and ownership |
| String-serialized results | Typed tool outputs | No silent semantic coercion |

## Proposed production package

```text
phenoassistant_maf/
├── __init__.py
├── config.py
├── provider.py
├── manager.py
├── application.py
├── runtime.py
├── registry.py
└── tools/
    ├── __init__.py
    ├── calculator.py
    ├── statistics.py
    └── catalogue.py
```

`maf_poc` remains preserved as validated evidence until the production package reaches equivalent or stronger test coverage.

## Migration order

1. Create an import-safe production package.
2. Migrate calculator as the deterministic smoke test.
3. Adapt the existing ANOVA implementation without altering scientific logic.
4. Add an opt-in live OpenRouter tool-selection test.
5. Add Tukey and a reusable statistical registry.
6. Migrate a CPU-safe multi-tool demo.
7. Expand only after the vertical slice passes.

## Extracted imports from `agents.py`

- `autogen`
- `from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent`
- `from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent`
- `from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent`
- `from autogen import register_function`
- `from pandasai import Agent, SmartDataframe`
- `from pandasai.skills import skill`
- `from pandasai.llm import AzureOpenAI`
- `from huggingface_hub import login`
- `os`
- `glob`
- `json`
- `csv`
- `numpy`
- `pandas`
- `cv2`
- `from typing import Annotated, List, Optional, Union`
- `from functions.create_hf_dataset import prepare_dataset, get_dataset_format`
- `from functions.instance_segmentation import finetune_instance_segmentation, infer_instance_segmentation`
- `from functions.image_classification import finetune_image_classification, infer_image_classification`
- `from functions.image_regression import finetune_image_regression, infer_image_regression`
- `from functions.search import search_and_scrape`
- `from functions.compute_phenotypes import compute_phenotypes_from_ins_seg`
- `from functions.reproducible_pipeline import save_pipeline, load_chat_log, get_pipeline_zoo, get_pipeline_info, execute_pipeline`
- `from functions.stat_test import perform_anova, perform_tukey_test`
- `from functions.generic_tools import set_env_vars, set_random_seed, print_trainable_parameters, handle_grayscale_image, download_hffile, load_images, get_model_zoo, calculator, make_dir, extract_column_name_from_csv`

## Import-time top-level calls

| Line | Call |
|---:|---|
| 43 | `set_env_vars('./.env.yaml')` |
| 44 | `login(token=os.environ['HF_TOKEN'])` |
| 371 | `register_function(perform_anova, caller=manager, executor=user_proxy, name='perform_anova', description='Perform Mixed-design Repeated Measures ANOVA on given data (Greenhouse-Geisser correction will be automatically applied if needed)')` |
| 379 | `register_function(perform_tukey_test, caller=manager, executor=user_proxy, name='perform_tukey_test', description='Perform Post-hoc Tukey-Kramer test on given data')` |
| 387 | `register_function(extract_pipeline, caller=manager, executor=user_proxy, name='extract_pipeline', description='Extract and save a reproducible pipeline from chat history. Ask user to provide a name for the pipeline.')` |
| 395 | `register_function(get_pipeline_zoo, caller=manager, executor=user_proxy, name='get_pipeline_zoo', description='Get the information of all registered pipelines. It is useful when a user wants to know what pipelines are available before executing any.')` |
| 403 | `register_function(get_pipeline_info, caller=manager, executor=user_proxy, name='get_pipeline_info', description='Get the information of a specific pipeline. This is useful for you to know how to use a pipeline selected by the user, including the description, arguments, and output type.')` |
| 411 | `register_function(execute_pipeline, caller=manager, executor=user_proxy, name='execute_pipeline', description="Execute a saved pipeline from the pipeline zoo. Before executing a pipeline, you must call 'get_pipeline_zoo' to know what pipelines are available, and call 'get_pipeline_info' to understand how to use the selected pipeline.")` |
| 419 | `register_function(calculator, caller=manager, executor=user_proxy, name='calculator', description='Perform basic arithmetic operations between two integers.')` |
| 427 | `register_function(search_and_scrape, caller=manager, executor=user_proxy, name='google_search', description='Search and scrape content from the web. Results are returned in a dictionary. Useful when you need to find information on a specific topic.')` |
| 435 | `register_function(get_model_zoo, caller=manager, executor=user_proxy, name='get_model_zoo', description='Check available computer vision checkpoints. Must be called before using computer vision models.')` |
| 443 | `register_function(infer_instance_segmentation, caller=manager, executor=user_proxy, name='infer_instance_segmentation', description='Perform instance segmentation on plant images')` |
| 451 | `register_function(infer_image_classification, caller=manager, executor=user_proxy, name='infer_image_classification', description='Perform image classification on plant images')` |
| 459 | `register_function(infer_image_regression, caller=manager, executor=user_proxy, name='infer_image_regression', description='Perform image regression on plant images')` |
| 467 | `register_function(compute_phenotypes_from_ins_seg, caller=manager, executor=user_proxy, name='compute_phenotypes_from_ins_seg', description='Compute phenotypes from an instance segmentation result file')` |
| 475 | `register_function(coding, caller=manager, executor=user_proxy, name='coding', description='Write and execute code to solve tasks. Please provide a complete task description rather than concrete code as the input to this function.')` |
| 482 | `register_function(analyse_plot, caller=manager, executor=user_proxy, name='analyse_plot', description='Analyse a plot using GPT-4o.')` |
| 490 | `register_function(compute_csv, caller=manager, executor=user_proxy, name='compute_from_csv', description='Compute statistics or new values from a CSV file. Optionally, it saves the results to a new file.')` |
| 498 | `register_function(query_csv, caller=manager, executor=user_proxy, name='query_csv', description='Ask a question to a CSV file such as which image has the most leaf count. It does not generate a new file.')` |
| 506 | `register_function(plot_from_csv, caller=manager, executor=user_proxy, name='plot_from_csv', description='Plot data from a CSV file. Be sure to provide details of requirements and the path to save the plot.')` |
| 514 | `register_function(retrieval_augmented_generation, caller=manager, executor=user_proxy, name='RAG', description='Retrieve knowledge from the Phenotiki paper. Use this only to retrieve information (e.g. asking questions starting with what/how/...). You need to reason the retrieved information to solve the task.')` |
| 523 | `register_function(get_dataset_format, caller=manager, executor=user_proxy, name='get_dataset_format', description='Instruct the user to prepare a dataset in the required format to train a model.')` |
| 531 | `register_function(prepare_dataset, caller=manager, executor=user_proxy, name='prepare_dataset', description='When the user upload a dataset for model training, use this function to process the dataset into the required format.')` |
| 539 | `register_function(finetune_image_classification, caller=manager, executor=user_proxy, name='finetune_image_classification', description='Train an image classification model on a user uploaded dataset.')` |
| 547 | `register_function(finetune_image_regression, caller=manager, executor=user_proxy, name='finetune_image_regression', description='Train an image regression model on a user uploaded dataset.')` |
| 555 | `register_function(finetune_instance_segmentation, caller=manager, executor=user_proxy, name='finetune_instance_segmentation', description='Train an instance segmentation model on a user uploaded dataset.')` |
| 563 | `register_function(make_dir, caller=manager, executor=user_proxy, name='make_dir', description='Check if a directory exists, and create it if it does not. Call it whenever you need to save files to a directory.')` |
| 581 | `print("PhenoAssistant's available tools:")` |

## Global constructor assignments

| Line | Target | Constructor |
|---:|---|---|
| 150 | `user_proxy` | `autogen.ConversableAgent` |
| 160 | `manager` | `autogen.AssistantAgent` |
| 167 | `code_executor` | `autogen.UserProxyAgent` |
| 179 | `code_writer` | `autogen.AssistantAgent` |
| 202 | `data_visualiser` | `autogen.AssistantAgent` |
| 222 | `plot_analyser` | `MultimodalConversableAgent` |
| 237 | `pdsllm` | `AzureOpenAI` |
| 310 | `rag_proxy` | `RetrieveUserProxyAgent` |
| 321 | `rag_assistant` | `RetrieveAssistantAgent` |
| 340 | `pipeline_summariser` | `autogen.AssistantAgent` |

## AutoGen tool registrations

| Line | Function | Published name | Caller | Executor |
|---:|---|---|---|---|
| 371 | `perform_anova` | `'perform_anova'` | `manager` | `user_proxy` |
| 379 | `perform_tukey_test` | `'perform_tukey_test'` | `manager` | `user_proxy` |
| 387 | `extract_pipeline` | `'extract_pipeline'` | `manager` | `user_proxy` |
| 395 | `get_pipeline_zoo` | `'get_pipeline_zoo'` | `manager` | `user_proxy` |
| 403 | `get_pipeline_info` | `'get_pipeline_info'` | `manager` | `user_proxy` |
| 411 | `execute_pipeline` | `'execute_pipeline'` | `manager` | `user_proxy` |
| 419 | `calculator` | `'calculator'` | `manager` | `user_proxy` |
| 427 | `search_and_scrape` | `'google_search'` | `manager` | `user_proxy` |
| 435 | `get_model_zoo` | `'get_model_zoo'` | `manager` | `user_proxy` |
| 443 | `infer_instance_segmentation` | `'infer_instance_segmentation'` | `manager` | `user_proxy` |
| 451 | `infer_image_classification` | `'infer_image_classification'` | `manager` | `user_proxy` |
| 459 | `infer_image_regression` | `'infer_image_regression'` | `manager` | `user_proxy` |
| 467 | `compute_phenotypes_from_ins_seg` | `'compute_phenotypes_from_ins_seg'` | `manager` | `user_proxy` |
| 475 | `coding` | `'coding'` | `manager` | `user_proxy` |
| 482 | `analyse_plot` | `'analyse_plot'` | `manager` | `user_proxy` |
| 490 | `compute_csv` | `'compute_from_csv'` | `manager` | `user_proxy` |
| 498 | `query_csv` | `'query_csv'` | `manager` | `user_proxy` |
| 506 | `plot_from_csv` | `'plot_from_csv'` | `manager` | `user_proxy` |
| 514 | `retrieval_augmented_generation` | `'RAG'` | `manager` | `user_proxy` |
| 523 | `get_dataset_format` | `'get_dataset_format'` | `manager` | `user_proxy` |
| 531 | `prepare_dataset` | `'prepare_dataset'` | `manager` | `user_proxy` |
| 539 | `finetune_image_classification` | `'finetune_image_classification'` | `manager` | `user_proxy` |
| 547 | `finetune_image_regression` | `'finetune_image_regression'` | `manager` | `user_proxy` |
| 555 | `finetune_instance_segmentation` | `'finetune_instance_segmentation'` | `manager` | `user_proxy` |
| 563 | `make_dir` | `'make_dir'` | `manager` | `user_proxy` |

Registration calls discovered: **25**.

## Recovered MAF POC inventory

### `maf_poc/__init__.py`

- No top-level classes or functions.

### `maf_poc/agent.py`

- `def build_mixed_anova_agent`
- `async def run_mixed_anova_agent`

### `maf_poc/config.py`

- `class OpenRouterSettings`

### `maf_poc/provider.py`

- `def create_chat_client`

### `maf_poc/tool_adapter.py`

- `class MixedAnovaInput`
- `class MixedAnovaResult`
- `class AnovaCallable`
- `def resolve_real_anova_callable`
- `def create_mixed_anova_tool`

## First production-slice acceptance gate

- Importing `phenoassistant_maf` performs no network, authentication, model, database, or filesystem initialization.
- An application factory creates a real MAF Manager explicitly.
- Calculator executes directly and through the registry with equivalent semantics.
- ANOVA delegates to the existing scientific implementation.
- Invalid ANOVA arguments and underlying exceptions remain observable.
- Offline tests require no OpenRouter credentials.
- Live OpenRouter execution is opt-in and secret-safe.
- Original AutoGen and scientific-function files remain unchanged.

## Deferred components

- GPU computer-vision inference and training;
- RAG and Chroma migration;
- code execution;
- PandasAI-backed agents;
- multimodal plot analysis;
- pipeline reproduction;
- MCP integration;
- complete 25-tool migration.

## Current evidence boundary

The recovered POC proves import-safe configuration, explicit provider construction, typed ANOVA adaptation, offline orchestration behaviour, session isolation, and visible failures through 42 tests.

It does not yet prove that the production PhenoAssistant Manager or a live scientific workflow executes through MAF.
