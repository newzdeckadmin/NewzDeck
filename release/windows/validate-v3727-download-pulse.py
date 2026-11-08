#!/usr/bin/env python3
"""Exercise the production in-memory SAB queue pulse, including freshness and bounds.

Uses the real method AST against synthetic SAB samples. Never starts SABnzbd,
contacts NNTP, opens TCP ports, or writes user files.
"""
from __future__ import annotations
import ast, pathlib, threading, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
text=(ROOT/'src/app/sab_engine.py').read_text(encoding='utf-8')
tree=ast.parse(text)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SabEngine' ) if any(isinstance(n,ast.ClassDef) and n.name=='SabEngine' for n in tree.body) else None
if cls is None:
    choices=[n for n in tree.body if isinstance(n,ast.ClassDef) and any(isinstance(x,ast.FunctionDef) and x.name=='presentation_pulse' for x in n.body)]
    assert len(choices)==1,[x.name for x in choices]
    cls=choices[0]
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='presentation_pulse')
module=ast.Module(body=[ast.ClassDef(name='Probe',bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[])
# Real constants follow SAB units. Avoid float precision or format guessing.
def mb(s):
    try:return int(round(float(s or 0)*1024*1024))
    except (ValueError,TypeError):return 0
def kb(s):
    try:return int(round(float(s or 0)*1024))
    except (ValueError,TypeError):return 0
def num(s,default=0):
    try:return float(s)
    except (ValueError,TypeError):return default
scope={'time':time,'Any':object,'_mb_to_bytes':mb,'_kb_to_bps':kb,
       '_num':num,'_duration_seconds':lambda _:7}
exec(compile(ast.fix_missing_locations(module),'production_sab_pulse.py','exec'),scope)
Probe=scope['Probe']
p=Probe()
p._queue_sample_lock=threading.Lock()
p._queue_sample_pair=None
p._queue_sample_ts=0
p._queue_slots=lambda obj:(obj.get('queue',obj),obj.get('queue',obj).get('slots',[]))
def explode(*a,**k):raise AssertionError('pulse must not reach SAB, disk, or snapshot')
p.snapshot=explode;p._queue_and_history_fetch=explode;p._save_state=explode
v=p.presentation_pulse()
assert v['ready'] is False and v['fresh'] is False and v['jobs']==[]
now=time.time()
slots=[{'nzo_id':f'SAB-{n}','status':'Downloading','percentage':45.5,'mb':10,'mbleft':5.45,'kbpersec':100} for n in range(620)]
p._queue_sample_pair=({'queue':{'slots':slots}}, {'history':{'slots':[]}})
p._queue_sample_ts=now
v=p.presentation_pulse(limit=300)
assert v['ready'] and v['fresh'] and v['queue_total']==620 and v['truncated']
assert len(v['jobs'])==300 and v['jobs'][0]['id']=='SAB-0'
assert v['jobs'][0]['percent']==45.5 and v['jobs'][0]['speed_bps']==102400
assert v['jobs'][0]['remaining_bytes']==mb(5.45)
assert len(p.presentation_pulse(limit=99999)['jobs'])==500
assert len(p.presentation_pulse(limit=-1)['jobs'])==1
p._queue_sample_ts=time.time()-7
v=p.presentation_pulse()
assert not v['fresh'] and v['jobs']==[] and v['sample_age_seconds']>=6
p._queue_sample_ts=time.time()
p._queue_sample_pair=({'queue':{'slots':slots,'_newzdeck_fresh':False}}, {})
assert not p.presentation_pulse()['fresh']
source=(ROOT/'src/app/server.py').read_text(encoding='utf-8')
assert 'if parsed.path == "/api/downloads/pulse":' in source
assert 'if parsed.path == "/api/diagnostics/ping":' in source
assert 'DOWNLOAD_MANAGER.presentation_pulse()' in source
assert 'diagnostics_snapshot()' not in source.split('if parsed.path == "/api/diagnostics/ping":',1)[1].split('if parsed.path == "/api/downloads/pulse":',1)[0]
print('PASS: nonblocking SAB pulse, 500-row ceiling, stale protection, independent diagnostics heartbeat')
