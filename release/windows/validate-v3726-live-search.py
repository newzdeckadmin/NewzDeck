#!/usr/bin/env python3
"""Isolated real GroupSearchManager worker tests without external NNTP or disk writes.

Runs the actual class AST extracted from production server.py against deterministic
fake NNTP sockets. In particular, exercises cancellation of a blocking OVER,
range completeness, bounded socket fan-out, retries and terminal failures.
"""
from __future__ import annotations
import ast
import email.utils
import math
import pathlib
import re
import secrets
import threading
import time
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
source = (ROOT/'src/app/server.py').read_text(encoding='utf-8')
tree = ast.parse(source)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'GroupSearchManager')
class NntpError(RuntimeError): pass
class Diagnostic:
    def provider_result(self, *a, **kw): pass
    def event(self, *a, **kw): pass
DIAGNOSTICS = Diagnostic()
state = {'active': 0, 'max_active': 0, 'ranges': [], 'mode': 'normal', 'errors': 0, 'lock': threading.Lock()}

def make_article(n):
    return {'article': n, 'subject': f'needle {n}' if n % 127 == 0 else f'other {n}',
            'from': 'Test Poster', 'date': '', 'message_id': f'<{n}@example>',
            'bytes': 750000, 'media': None, 'multipart': None}

class FakeClient:
    def __init__(self,*a,**kw):
        self.stop = threading.Event(); self.connected=False
    def connect(self):
        with state['lock']:
            state['active'] += 1
            state['max_active'] = max(state['active'], state['max_active'])
        self.connected=True
    def group(self,group):return {'low':1,'high':state.get('total',19227),'count':state.get('total',19227)}
    def overview(self, start, end, *, search_filter=None):
        mode=state['mode']
        if mode=='slow':
            if self.stop.wait(3): raise NntpError('stopped by cancellation')
        if mode=='always_fail': raise NntpError('provider refused this range')
        if mode=='retry_once':
            with state['lock']:
                if not state['errors']:
                    state['errors']=1
                    raise NntpError('transient socket fault')
        if self.stop.is_set():raise NntpError('socket closed')
        time.sleep(.003)
        with state['lock']: state['ranges'].append((start,end))
        return [make_article(n) for n in range(start,end+1)]
    def overview_chunked(self,start,end,*,chunk_size,search_filter=None):
        rows=[]
        for lo in range(start,end+1,chunk_size): rows.extend(self.overview(lo,min(end,lo+chunk_size-1),search_filter=search_filter))
        return rows
    def abort(self):self.stop.set()
    def close(self):
        if self.connected:
            with state['lock']:state['active']-=1
            self.connected=False

def provider_by_id(pid):
    return {'host':'invalid.example','port':563,'ssl':True,'username':'fake',
            'password_protected':'','connections':state.get('connections',52)}
def capacity(provider):
    configured=int(provider['connections']);reserve=min(4,max(1,math.ceil(configured*.04))) if configured>2 else 0
    return configured,reserve,configured-reserve

def normalize_search_filters(f):return f or {}
def group_articles(a):return sorted(a,key=lambda x:x['article'],reverse=True)
def normalize_subject(s):return s

scope=globals().copy()
scope.update({'NntpClient': FakeClient,'_provider_download_capacity':capacity,
              '_GROUP_SEARCH_LANES':threading.BoundedSemaphore(4),
              'unprotect_secret':lambda x:x})
exec(compile(ast.Module(body=[cls],type_ignores=[]),str(ROOT/'src/app/server.py'),'exec'),scope)
Manager=scope['GroupSearchManager']

def reset(mode='normal',total=19227,connections=52):
    assert state['active']==0,(state['active'],'connections left open')
    state.update({'mode':mode,'total':total,'connections':connections,'ranges':[],
                  'max_active':0,'errors':0})

def wait_done(manager,jid,timeout=10):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        status=manager.status(jid)
        if status['status'] in ('completed','cancelled','failed'):return status
        time.sleep(.025)
    raise AssertionError('search did not terminate promptly: '+str(manager.status(jid)))

reset()
m=Manager()
jid=m.start('test','alt.binaries.test','needle')['id']
result=wait_done(m,jid)
assert result['status']=='completed',result
assert result['scanned_headers']==19227,result
assert result['workers']==3,result
assert 1<state['max_active']<=3,state
numbers=[]
for a,b in state['ranges']:numbers.extend(range(a,b+1))
assert sorted(numbers)==list(range(1,19228)), 'overlap or missing header-number positions'
assert len(numbers)==len(set(numbers))
assert result['match_headers']==sum(n%127==0 for n in numbers),result
items=m.results(jid,1,25)
assert items['paging']['result_count']==result['match_headers']
assert items['articles'][0]['article']==19227-19227%127
print('PASS: three bounded lanes, adaptive non-overlapping ranges and exact matching')

reset('normal',12150,2)
m=Manager();jid=m.start('test','alt.binaries.test','needle')['id'];s=wait_done(m,jid)
assert s['workers']==1 and state['max_active']==1,(s,state)
assert s['scanned_headers']==12150
print('PASS: low connection allowance uses one scanner')

reset('retry_once',9000,52)
m=Manager();jid=m.start('test','alt.binaries.test','needle')['id'];s=wait_done(m,jid)
assert s['status']=='completed' and s['retry_count']>=1,s
numbers=[v for a,b in state['ranges'] for v in range(a,b+1)]
assert sorted(numbers)==list(range(1,9001))
print('PASS: transient NNTP failure retries without missing ranges')

reset('always_fail',20000,52)
m=Manager();jid=m.start('test','alt.binaries.test','needle')['id'];s=wait_done(m,jid)
assert s['status']=='failed' and 'Search failed while scanning headers' in s['error'],s
assert s['scanned_headers']<s['total_headers']
print('PASS: permanent overview failure reports failed rather than silently completing')

reset('slow',20000,52)
m=Manager();jid=m.start('test','alt.binaries.test','needle')['id']
deadline=time.monotonic()+3
while m.status(jid)['active_workers']==0 and time.monotonic()<deadline:time.sleep(.01)
started=time.monotonic();m.cancel(jid);s=wait_done(m,jid,2)
assert s['status']=='cancelled',s
assert time.monotonic()-started<2, 'cancel did not interrupt in-flight read'
assert state['active']==0
print('PASS: cancellation promptly aborts only search sockets')

class_body=ast.get_source_segment(source,cls)
assert 'sqlite' not in class_body and 'json_write' not in class_body and 'SAVED_SEARCHES_FILE' not in class_body
assert '_GROUP_SEARCH_LANES' in source
print('PASS: search manager is in-memory only; no header index or search-history writes')
