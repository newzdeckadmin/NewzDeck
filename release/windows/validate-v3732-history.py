#!/usr/bin/env python3
"""Exercise the production terminal-history classification with realistic post states."""
from pathlib import Path
import ast,copy
ROOT=Path(__file__).resolve().parents[2]
s=(ROOT/'src/app/sab_engine.py').read_text('utf8')
tree=ast.parse(s)
method=None
for cls in (x for x in tree.body if isinstance(x,ast.ClassDef)):
  for node in cls.body:
    if isinstance(node,ast.FunctionDef) and node.name=='_terminal_history_scope_for_row':method=copy.deepcopy(node);break
  if method:break
assert method is not None
method.decorator_list=[]
namespace={'Any':object};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'<production terminal scope>','exec'),namespace)
classify=namespace['_terminal_history_scope_for_row']
for p in ('','completed','not_needed','disabled'):
  assert classify({'status':'completed','post_status':p})=='completed',p
for p in ('queued','waiting','verifying','repairing','extracting','importing','needs_password'):
  assert classify({'status':'completed','post_status':p})=='',p
for p in ('failed','needs_attention','needs_tool','blocked','cancelled'):
  assert classify({'status':'completed','post_status':p})=='failed',p
for status in ('failed','cancelled'):
  assert classify({'status':status,'post_status':''})=='failed',status
assert classify({'status':'downloading','post_status':''})==''
assert "del_files=0" in s
assert "completed_history_clear" in s
print('PASS: completed counts include only finished transfers with finalized post-processing; unfinished remain live, failed remain failed, history-only clear retained')
