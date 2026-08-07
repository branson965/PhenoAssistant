import ast
src=open('agents.py').read(); L=src.splitlines(True); t=ast.parse(src)
s=lambda a,b: ''.join(L[a-1:b])
A=[n.lineno for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='API_SUPPLIER'][0]
G=[n.end_lineno for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='gpt_config'][0]
cfg=s(A,G)
pds=[n for n in t.body if isinstance(n,ast.Try) and 'pdsllm' in s(n.lineno,n.end_lineno)]
pds_src=s(pds[0].lineno,pds[0].end_lineno) if pds else ''
fns={n.name:(n.lineno,n.end_lineno) for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('save_csv','compute_csv','query_csv')}
order=['save_csv','compute_csv','query_csv']
body=''.join(s(*fns[n]) for n in order if n in fns)
nl=chr(10)
hdr=('"""Self-contained csv table-analyser tools for the MCP server."""'+nl
 +'import os, sys'+nl+'from typing import Annotated, Optional, Dict, Any, List'+nl
 +'import pandas as pd'+nl+'from pandasai import Agent, SmartDataframe'+nl
 +'from pandasai.skills import skill'+nl+'from pandasai.llm import AzureOpenAI'+nl
 +'from functions.generic_tools import set_env_vars'+nl+'set_env_vars("./.env.yaml")'+nl)
open('functions/csv_tools.py','w').write(hdr+nl+cfg+nl+pds_src+nl+body+nl)
print('wrote functions/csv_tools.py; included:',[n for n in order if n in fns])
