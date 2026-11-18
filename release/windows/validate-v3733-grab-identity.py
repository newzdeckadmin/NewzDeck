#!/usr/bin/env python3
"""Real v3.7.33 ManualGrabOperations target-identity regression."""
from __future__ import annotations
import ast, copy, hashlib, json, queue, re, threading, time, uuid
from pathlib import Path

server=(Path(__file__).resolve().parents[2]/'src/app/server.py').read_text('utf8')
node=next(x for x in ast.parse(server).body if isinstance(x,ast.ClassDef) and x.name=='ManualGrabOperations')
ns={'threading':threading,'Any':object,'time':time,'queue':queue,'uuid':uuid,'re':re,'hashlib':hashlib,'json':json,
    '_user_safe_error_message':lambda exc,operation='grab':str(exc)}
class Diagnostics:
    @staticmethod
    def event(*args,**kwargs):pass
ns['DIAGNOSTICS']=Diagnostics
exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)],type_ignores=[])),'source','exec'),ns)
C=ns['ManualGrabOperations']
release=threading.Event();entered=threading.Event()
def block_grab(data,progress_callback=None):
    entered.set();release.wait(3)
    return {'ok':True,'pending_engine_handoff':True}
c=C(grab_callable=block_grab,max_workers=2)
def req(token,season=1,episode=1,pack=False):
    return {'media_title':'EXAMPLE SHOW','media_kind':'tv','media_year':2026,'season':season,'episode':episode,
            'season_pack':pack,'title':'Distinct release','client_request_id':f'{token:032x}'}
_,first=c.start(req(1));assert entered.wait(1)
_,again=c.start(req(2));assert again.get('already_running') and again['job_id']==first['job_id']
_,second=c.start(req(3,episode=2));assert second['job_id']!=first['job_id'] and not second.get('already_running')
_,season=c.start(req(4,episode=None,pack=True));assert season['job_id'] not in {first['job_id'],second['job_id']}
_,diff_season=c.start(req(5,season=2,episode=1));assert diff_season['job_id'] not in {first['job_id'],second['job_id'],season['job_id']}
_,replay=c.start(req(1));assert replay.get('replayed') and replay['job_id']==first['job_id']
release.set()
print('PASS: real coordinator separates episodes, seasons and packs, preserves same-target coalescing and request replay')
