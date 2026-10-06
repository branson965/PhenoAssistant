import ast, sys
out_mod, tool_fn, *agents = sys.argv[1:]
src = open('agents.py').read(); L = src.splitlines(True); t = ast.parse(src)
s = lambda a,b: ''.join(L[a-1:b])
A=[n.lineno for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='API_SUPPLIER']
G=[n.end_lineno for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='gpt_config']
cfg_lines=set(range(A[0],G[0]+1))
assigns={}
for n in t.body:
    if isinstance(n,ast.Assign):
        for tg in n.targets:
            if isinstance(tg,ast.Name): assigns[tg.id]=(n.lineno,n.end_lineno)
imports=[]
for n in t.body:
    if isinstance(n,(ast.Import,ast.ImportFrom)):
        imports.append((n.lineno,n.end_lineno,[(a.asname or a.name).split('.')[0] for a in n.names]))
fn=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==tool_fn]
if not fn: sys.exit('tool fn not found: '+tool_fn)
spans=[assigns[a] for a in agents if a in assigns]+[(fn[0].lineno,fn[0].end_lineno)]
seen=set(agents)
for _ in range(6):
    newnames=set()
    for (a,b) in spans:
        try: newnames |= {x.id for x in ast.walk(ast.parse(''.join(L[a-1:b]))) if isinstance(x,ast.Name)}
        except SyntaxError: pass
    add=[nm for nm in newnames if nm in assigns and nm not in seen and assigns[nm][0] not in cfg_lines]
    if not add: break
    for nm in add:
        seen.add(nm); spans.append(assigns[nm])
allnames=set()
for (a,b) in spans:
    try: allnames |= {x.id for x in ast.walk(ast.parse(''.join(L[a-1:b]))) if isinstance(x,ast.Name)}
    except SyntaxError: pass
imp_src=[s(a,b) for (a,b,nms) in imports if set(nms)&allnames]
spans=sorted(set(spans))
nl=chr(10)
hdr=('import os, sys, json'+nl+'from typing import Annotated, Optional, Dict, Any, List'+nl+'import autogen'+nl
     +''.join(imp_src)+'from functions.generic_tools import set_env_vars'+nl+'set_env_vars("./.env.yaml")'+nl)
body=''.join(s(a,b).replace('"ALWAYS"','"NEVER"') for (a,b) in spans)
open('functions/%s.py'%out_mod,'w').write(hdr+nl+s(A[0],G[0])+nl+body+nl)
print('wrote functions/%s.py (resolved %d blocks)'%(out_mod,len(spans)))
