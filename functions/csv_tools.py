"""Self-contained csv table-analyser tools for the MCP server."""
import os, sys
from typing import Annotated, Optional, Dict, Any, List
import pandas as pd
from pandasai import Agent, SmartDataframe
from pandasai.skills import skill
from pandasai.llm import AzureOpenAI
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

try:
    if API_SUPPLIER == 'openrouter':
        from pandasai.llm import OpenAI as _PdsOpenAI
        class _ORPdsLLM(_PdsOpenAI):
            _supported_chat_models = [os.environ['MODEL_NAME']]
        pdsllm = _ORPdsLLM(api_token=os.environ['OPENAI_API_KEY'], api_base='https://openrouter.ai/api/v1', model=os.environ['MODEL_NAME'])
    else:
        pdsllm = AzureOpenAI(
            api_token=os.environ['OPENAI_API_KEY'],
            azure_endpoint=os.environ['AZURE_API_URL'],
            api_version=os.environ['AZURE_API_VERSION'],
            deployment_name=os.environ['MODEL_NAME'],
        )
except Exception as e:
    print(f"Warning: table-analyser LLM (pdsllm) not configured: {e}")
    pdsllm = None

def save_csv(df: pd.DataFrame,
             save_path: str) -> str:
    """
    Save a dataframe to a CSV file.
    Args:
        df (pd.DataFrame): The dataframe to save.
        save_path (str): The path to save the CSV file.
    """
    df.to_csv(save_path, index=False)
    return f"CSV file saved to {save_path}"
def compute_csv(
        message: Annotated[str, "The request of computing from a CSV file. Example: 'Compute the average of A for B on C.'"],
        file_path: Annotated[str, "The path of the CSV file to be analysed."],
        save_path: Optional[Annotated[str, "Optional: The path to save the results. If not provided, the result is returned as plain text."]] = None,
        ) -> str:
    df = pd.read_csv(file_path)
    # GPT setting
    agent_config = {"llm": pdsllm,}
    agent = Agent(df, config=agent_config,)
    # # Bamboo seeting
    # agent = Agent(df)

    if save_path:
        agent.add_skills(save_csv)
        res = agent.chat(f'{message}. The path to save results is: {save_path}.')
        exp = agent.explain()
        return f'The new csv is saved at {save_path}. Here is an explanation of the operation process: {exp}.'
    else:
        res = agent.chat(message)
        exp = agent.explain()
        return f"Here is the result: {res}. Explanation: {exp}."
def query_csv(message: Annotated[str, "Asking questions to a CSV file. Example: 'What is the maximum number of column A?'"], 
              file_path: Annotated[str, "The path of the CSV file to be analysed."],) -> str:
    df = pd.read_csv(file_path)
    
    # GPT setting
    agent_config = {"llm": pdsllm,}
    agent = Agent(df, config=agent_config,)

    # # Bamboo setting
    # agent = Agent(df)
    
    res = agent.chat(message)
    # if isinstance(res, np.integer):
    #     res = int(res)
    # if isinstance(res, np.floating):
    #     res = float(res)
    return str(res)

