import os, sys, json
from typing import Annotated, Optional, Dict, Any, List
import autogen
import autogen
from typing import Annotated, List, Optional, Union
from functions.generic_tools import (
    set_env_vars, 
    set_random_seed, 
    print_trainable_parameters, 
    handle_grayscale_image, 
    download_hffile, 
    load_images,  
    get_model_zoo,
    calculator,
    make_dir,
    extract_column_name_from_csv,
)
from functions.generic_tools import set_env_vars
set_env_vars("./.env.yaml")

API_SUPPLIER = os.environ.get('API_SUPPLIER', 'azure')

if API_SUPPLIER == 'openrouter':
    config_list = [
        {
            "model": os.environ['MODEL_NAME'],
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.environ['OPENAI_API_KEY'],
            "api_type": "openai",
            "temperature": 0.1,
            "cache_seed": 42,
            "timeout": 540000,
        }
    ]
else:
    config_list = [
        {
            "model": os.environ['MODEL_NAME'],
            "base_url": os.environ['AZURE_API_URL'],
            "api_version": os.environ['AZURE_API_VERSION'],
            "temperature": 0.1,
            "cache_seed": 42,
            "timeout": 540000,
            "api_type": "azure",
            "api_key": os.environ['OPENAI_API_KEY'],
        }
    ]
gpt_config = {
    "config_list": config_list,
}

WORK_DIR = "./"
CODE_WRITER_SYSTEM_PROMPT = '''code_writer. Write python codes to accomplish a given task.

General instructions:
    1. Write the full Python code solution in a single code block. Do not return incomplete codes or multiple code blocks.
    2. 'code_executor' will execute the code. If the output shows errors, correct them and present the complete, updated code.
    3. Wait until the 'code_executor' completes the execution and returns the output. If the output shows task completion, return a single 'TERMINATE'. Do not write or print it within the code block.
'''
code_executor = autogen.UserProxyAgent(
    name="code_executor",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    system_message='''code_executor. Execute python code.''',
    # llm_config=gpt_config,
    code_execution_config= {
        "last_n_messages": "auto",
        "work_dir": WORK_DIR,
        "use_docker": False},
)
code_writer = autogen.AssistantAgent(
    name="code_writer",
    system_message=CODE_WRITER_SYSTEM_PROMPT,
    llm_config=gpt_config,
)
def coding(message: Annotated[str, "Describe the task to be solved."],
           file_path: Annotated[Optional[str], "(Optional) The path to an input csv file."]=None,
           ) -> str:   
    if file_path:
        message = f"{message}. The file to be analysed: {file_path}; it contains columns: {extract_column_name_from_csv(file_path)}."
    res = code_executor.initiate_chat(
        code_writer,
        clear_history=True,
        silent=False,
        message=message,
        summary_method="reflection_with_llm",
        summary_args={"summary_prompt":"Summarise all the necessary outputs needed to address the task. If the task involves saving files, make sure to return the saved file path."},
        max_turns=6,
    )
    return res.summary

