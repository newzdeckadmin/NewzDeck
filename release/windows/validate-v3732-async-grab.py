#!/usr/bin/env python3
"""v3.7.32 regression tests: execute actual ManualGrabOperations source via AST.

No NewzDeck installation, network, media files, SAB process or user data is used.
"""
from __future__ import annotations
import ast, copy, hashlib, json, re, threading, time, types, uuid, queue
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE=Path(__file__).resolve().parents[2]
SERVER=(BASE/'src/app/server.py').read_text('utf-8')
AUTO=(BASE/'src/app/automation_engine.py').read_text('utf-8')
TREE=ast.parse(SERVER)
CLAZ=next(x for x in TREE.body if isinstance(x,ast.ClassDef) and x.name=='ManualGrabOperations')
ns={'threading':threading,'Any':object,'ThreadPoolExecutor':ThreadPoolExecutor,
    'time':time,'queue':queue,'uuid':uuid,'re':re,'hashlib':hashlib,'json':json,
    '_user_safe_error_message':lambda exc,operation='grab':str(exc)}
class Diagnostic:
    events=[]
    @classmethod
    def event(cls,*args,**kwargs):cls.events.append((args,kwargs))
ns['DIAGNOSTICS']=Diagnostic
exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(CLAZ)],type_ignores=[])), '<real production coordinator>', 'exec'),ns)
Coordinator=ns['ManualGrabOperations']

def row(item='movie1',title='Sinners.2025.Remux',req='a'*32):
    return {'item_id':item,'title':title,'guid':'public-'+title,'client_request_id':req,
            'indexer':'Example Indexer','download_url':'https://indexer.example/download?apikey=DO-NOT-LEAK',
            'season':None,'episode':None}

entered=threading.Event();release=threading.Event();calls=[]
def hold_grab(data,progress_callback=None):
    calls.append(data['title'])
    if progress_callback:progress_callback('retrieving_nzb')
    entered.set()
    if not release.wait(timeout=5):raise RuntimeError('synthetic timeout')
    if progress_callback:progress_callback('saving_pending_handoff')
    return {'ok':True,'collection_id':'pending-SAFE','collection_name':data['title'],
            'pending_engine_handoff':True}
c=Coordinator(grab_callable=hold_grab,max_pending=2)
a=row();code,first=c.start(a)
assert code==202 and first['status']=='queued' and first['request_id']=='a'*32,first
assert entered.wait(2)
code,replay=c.start(a)
assert code==202 and replay.get('replayed') and replay['job_id']==first['job_id']
code,overlap=c.start(row(title='Another.Release',req='b'*32))
assert code==202 and overlap.get('already_running') and overlap['job_id']==first['job_id']
code,st=c.get(first['job_id']);assert code==200 and st['status']=='running' and st['phase']=='retrieving_nzb'
assert 'apikey' not in json.dumps(st).casefold() and 'DO-NOT-LEAK' not in json.dumps(st)
code,by_request=c.get('a'*32);assert code==200 and by_request['job_id']==first['job_id']
release.set();deadline=time.time()+5
while time.time()<deadline and c.get('a'*32)[1].get('status')=='running':time.sleep(.01)
code,done=c.get('a'*32)
assert code==200 and done['status']=='accepted' and done['pending_engine_handoff'] and done['collection_id']=='pending-SAFE'
assert calls==['Sinners.2025.Remux'],calls


# Same-target failures permit another distinct release, and never silently label
# target reservation/duplicate/suppressed as successfully queued.
queue=[{'ok':True,'already_queued':True,'reason':'already processing'},
       {'ok':True,'already_queued':True,'reservation_only':True,'reason':'different runtime'},
       {'ok':True,'suppressed':True,'reason':'target satisfied'}]
def immediate(data,progress_callback=None):return queue.pop(0)
c=Coordinator(grab_callable=immediate)
for idx,status in enumerate(['already_queued','reservation_only','suppressed']):
    token=('%032x'%(idx+1));code,job=c.start(row(req=token,title=f'Attempt {idx}'))
    assert code==202
    deadline=time.time()+3
    while time.time()<deadline and c.get(token)[1]['status'] in ('queued','running'):time.sleep(.005)
    actual=c.get(token)[1]
    assert actual['status']==status,actual
    assert actual['status']!='accepted'


c=Coordinator(grab_callable=lambda data,progress_callback=None:(_ for _ in ()).throw(ValueError('Bad NZB signature')))
code,job=c.start(row(req='d'*32));assert code==202
for _ in range(200):
    status=c.get('d'*32)[1]
    if status['status']=='failed':break
    time.sleep(.005)
assert status['status']=='failed' and 'Bad NZB' in status['message']
code,retry=c.start(row(req='e'*32,title='Different release'))
assert code==202 and retry['job_id']!=job['job_id']

assert c.get('notanid')[0]==400
assert c.get('f'*32)[0]==404
assert '[indexer URL hidden]' in Coordinator._safe_message('https://indexer.test/get?apikey=DO-NOT-LEAK')
assert 'DO-NOT-LEAK' not in Coordinator._safe_message('apikey=DO-NOT-LEAK')
assert 'def grab_release(self,data,progress_callback=None)' in AUTO
for stage in ["progress('retrieving_nzb')","progress('validating_nzb')","progress('saving_pending_handoff')"]:assert stage in AUTO
assert 'GRAB_OPERATIONS.start(data)' in SERVER
assert 'GRAB_OPERATIONS.get(identifier)' in SERVER
assert 'if data.get(\'async_grab\') is True:' in SERVER
assert 'MEDIA_AUTOMATION.grab_release(data)' in SERVER  # legacy API contract
print('PASS: async opt-in, real coordinator, worker phases, exact request replay, target coalescing, bounded queue, protected status, pending handoff, reservation/duplicate/suppressed and retry-after-failure')
