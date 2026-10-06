import os, sys, json
from typing import Annotated, Optional, Dict, Any, List
import autogen
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from typing import Annotated, List, Optional, Union
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

retrieve_config = {
    "task": "qa", # default (basically qa + code), qa, or code
    "docs_path": ['./papers/phenotiki.pdf'],
    # "vector_db": "qdrant", # defualt is chroma
    "chunk_token_size": 2000,
    "collection_name": "knowledge_base", # default name is autogen-docs
    "get_or_create": True,
    "embedding_model": "all-mpnet-base-v2",  # we can also use openai's models here by defining an `embedding_function`
    "must_break_at_empty_line": True,
    "model": gpt_config['config_list'][0]["model"],
}
rag_proxy = RetrieveUserProxyAgent(
    name="rag_proxy",
    # is_termination_msg=termination_msg,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    retrieve_config=retrieve_config,
    code_execution_config=False,  # we don't want to execute code in this case.
    # description="You are a proxy to retrieve knowledge from documents and augment your prompts.",
)
rag_assistant = RetrieveAssistantAgent(
    name="rag_assistant",
    system_message="You are a helpful assistant.",
    llm_config=gpt_config,
)
def retrieval_augmented_generation(problem: Annotated[str, "The question that can be answered based on knowledge retrieved from external source."]) -> str:
    '''
    Retrieve knowledge from the Phenotiki paper to answer a question. Provide the question as precise as possible.
    '''
    res = rag_proxy.initiate_chat(
        rag_assistant,
        message = rag_proxy.message_generator,
        problem = problem,
        silent=True,
    )
    return res.summary

