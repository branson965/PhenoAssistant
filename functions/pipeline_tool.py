import os, sys, json
from typing import Annotated, Optional, Dict, Any, List
import autogen
import autogen
from typing import Annotated, List, Optional, Union
from functions.reproducible_pipeline import save_pipeline, load_chat_log, get_pipeline_zoo, get_pipeline_info, execute_pipeline
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

PIPELINE_SUMMARISER_SYSTEM_PROMPT = """pipeline_summariser. Extract executed function calls and Python code snippets from a chat log, in order to form a pipeline that can be reused in the future. 
    Instructions:
      - Output the pipeline as a single Python function with key arguments.
      - Provide a clear description, annotate all key arguments with their data types and descriptions, and specify the output type.
      - Include only the executed function calls and Python code snippets. Do not include the unexcuted ones.
      - For code snippets, include them exactly as they were executed, including the library imports.
      - For function calls, you don't need to import them, just include the function execution with the same parameters that were used.
    
    Here is an example of the expected output:
      ```python
      def pipeline_name(param1: Annotated[str, 'description of param1'] = default_value_param1, param2: Annotated[int, 'description of param2'] = default_value_param2) -> Dict[str, Any]:
          \"\"\"
          Pipeline description.
          Returns:
              Dict[str, Any]: description of the output.
          \"\"\"

          import necessary_libraries  # Dynamically extract required imports

          try:
              logging.info("Starting pipeline execution.")

              # Step 1: Call function A
              logging.info("Executing function_call_1")
              result_1 = function_call_1(param1)

              # Step 2: Execute Python code snippet
              logging.info("Executing extracted Python logic for something.")
              def some_python_logic(input_data):
                  \"\"\" Extracted Python code block. \"\"\"
                  # { Insert copied code blocks here }
                  return output_data
              
              result_2 = some_python_logic(result_1)

              # Step 3: Call function B
              logging.info("Executing function_B")
              final_result = function_B(result_2, param2)

              logging.info("Pipeline executed successfully.")
              return {"status": "success", "result": final_result}

          except Exception as e:
              logging.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
              return {"status": "error", "message": str(e)}
        ```
      """
user_proxy = autogen.ConversableAgent(
    name="Admin",
    system_message="A human admin to pose the task", 
    # code_execution_config={"use_docker": False},
    llm_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
)
pipeline_summariser = autogen.AssistantAgent(
    name="pipeline_summariser",
    system_message=PIPELINE_SUMMARISER_SYSTEM_PROMPT,
    llm_config=gpt_config,
)
def extract_pipeline(
    pipeline_name: Annotated[str, "The name of the pipeline to be saved."],
    chat_log_path: Annotated[str, "The path to the chat log file."] = './autogen_logs/runtime.log',
) -> str:
    """
    Extract executed function calls and code to form a reproducible pipeline from a chat log.
    """
    # Load chat log
    log_data = load_chat_log(chat_log_path)
    summary_method = "last_msg" # or "reflection_with_llm"
    
    res = user_proxy.initiate_chat(
        pipeline_summariser,
        clear_history=True,
        silent=False,
        message=f'''Extract a pipeline from the chat log. Name the extracted pipeline as {pipeline_name}. Users should be able to use new data to run the pipeline.
        Here is the chat_log {log_data}.''',
        summary_method=summary_method,
        # summary_args={"summary_prompt": "Return only the extracted Python code block as it is. Ignore any irrelevant command like 'python' or execute command."},
        max_turns=1,
    )
    pipeline_code = res.summary
    save_pipeline(pipeline_name, pipeline_code)
    return f"Pipeline {pipeline_name} extracted successfully."

