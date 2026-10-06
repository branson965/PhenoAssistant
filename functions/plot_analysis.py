import os, sys, contextlib
from typing import Annotated
import autogen
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from functions.generic_tools import set_env_vars
set_env_vars('./.env.yaml')

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

user_proxy = autogen.ConversableAgent(
    name="Admin",
    system_message="A human admin to pose the task", 
    # code_execution_config={"use_docker": False},
    llm_config=False,
    human_input_mode="NEVER",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
)

plot_analyser = MultimodalConversableAgent(name="plot_analyser",
                  system_message='''plot_analyser. You are a plant data scientist to analyse figures.
                  ''',
                  llm_config=gpt_config,)

def _quiet(fn):
    import functools
    @functools.wraps(fn)
    def w(*a, **k):
        with contextlib.redirect_stdout(sys.stderr):
            return fn(*a, **k)
    return w

@_quiet
def analyse_plot(message: Annotated[str, "The request of analysing a plot. e.g. 'what plant yields the most leaves at the end of the experiment?'"],
                 file_path: Annotated[str, "The path of the plot to be analysed, including the suffix."]) -> str:
    res = user_proxy.initiate_chat(
        recipient=plot_analyser,
        message=f'{message}. The plot to be analysed is <img {file_path}>.',
        max_turns=1,
    )
    return res.chat_history[-1]['content']

