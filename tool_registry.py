"""tool_registry.py — single source of truth for which functions become MCP tools.
Each entry: (function_object, name, description), copied verbatim from agents.py."""

from functions.stat_test import perform_anova, perform_tukey_test
from functions.generic_tools import calculator, make_dir, get_model_zoo
from functions.reproducible_pipeline import get_pipeline_zoo, get_pipeline_info, execute_pipeline
from functions.search import search_and_scrape
from functions.compute_phenotypes import compute_phenotypes_from_ins_seg
from functions.create_hf_dataset import get_dataset_format, prepare_dataset

TOOL_REGISTRY = [
    (perform_anova, "perform_anova",
     "Perform Mixed-design Repeated Measures ANOVA on given data "
     "(Greenhouse-Geisser correction will be automatically applied if needed)"),
    (perform_tukey_test, "perform_tukey_test",
     "Perform Post-hoc Tukey-Kramer test on given data"),
    (calculator, "calculator",
     "Perform basic arithmetic operations between two integers."),
    (make_dir, "make_dir",
     "Check if a directory exists, and create it if it does not. Call it whenever you need to save files to a directory."),
    (get_pipeline_zoo, "get_pipeline_zoo",
     "Get the information of all registered pipelines. It is useful when a user wants to know what pipelines are available before executing any."),
    (get_pipeline_info, "get_pipeline_info",
     "Get the information of a specific pipeline. This is useful for you to know how to use a pipeline selected by the user, including the description, arguments, and output type."),
    (execute_pipeline, "execute_pipeline",
     "Execute a saved pipeline from the pipeline zoo. Before executing a pipeline, you must call 'get_pipeline_zoo' to know what pipelines are available, and call 'get_pipeline_info' to understand how to use the selected pipeline."),
    (search_and_scrape, "google_search",
     "Search and scrape content from the web. Results are returned in a dictionary. Useful when you need to find information on a specific topic."),
    (get_model_zoo, "get_model_zoo",
     "Check available computer vision checkpoints. Must be called before using computer vision models."),
    (compute_phenotypes_from_ins_seg, "compute_phenotypes_from_ins_seg",
     "Compute phenotypes from an instance segmentation result file"),
    (get_dataset_format, "get_dataset_format",
     "Instruct the user to prepare a dataset in the required format to train a model."),
    (prepare_dataset, "prepare_dataset",
     "When the user upload a dataset for model training, use this function to process the dataset into the required format."),
]
