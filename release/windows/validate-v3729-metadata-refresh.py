#!/usr/bin/env python3
"""Behavioral v3.7.29 metadata refresh tests from the actual production AST.

No service, network access, or downloaded media is required. The tests execute
unmodified target methods extracted from src/app/automation_engine.py against an
in-memory 57-TV + 6-movie library, including provider failures and retry behavior.
"""
from __future__ import annotations
import ast, copy, threading, time, types, typing
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=(ROOT/'src/app/automation_engine.py').read_text('utf-8')
TREE=ast.parse(SOURCE)
CLAZ=next(x for x in TREE.body if isinstance(x,ast.ClassDef) and x.name=='MediaAutomationEngine')
METHODS={'refresh_monitored_metadata','_metadata_movie_detail','_metadata_tv_bundle','_metadata_refresh_worker','maybe_refresh_monitored_metadata','maybe_run_automatic'}
SELECTED=[copy.deepcopy(x) for x in CLAZ.body if isinstance(x,ast.FunctionDef) and x.name in METHODS]
assert {x.name for x in SELECTED}==METHODS, 'production functions unavailable for regression tests'
mod=ast.Module(body=[ast.ClassDef(name='Extracted',bases=[],keywords=[],body=SELECTED,decorator_list=[])],type_ignores=[])
ast.fix_missing_locations(mod)
def _date(x):
    s=str(x or '')
    return s[:10] if len(s)>=10 and s[4:5]=='-' else ''
def _now(): return datetime.now(timezone.utc).isoformat()
def _norm(x): return ''.join(c if c.isalnum() else ' ' for c in str(x).casefold()).strip()
namespace={'Any':typing.Any,'time':time,'copy':copy,'threading':threading,
           'datetime':datetime,'timezone':timezone,'_date':_date,'_now':_now,'_norm':_norm}
exec(compile(mod,'<v3729-production-ast>','exec'),namespace)
Extracted=namespace['Extracted']

class Harness(Extracted):
    def __init__(self,n=63):
        self.db=[];self.responses=[];self.errors_for=set();self.rt={};self.events=[];self.last_saved=0;self.calls=[]
        self.lock=threading.RLock();self.metadata_refresh_run_lock=threading.Lock();self.metadata_refresh_thread=None
        self.auto_thread=None
        for i in range(n):
            tv=i<57;id=f'id{i:02d}'
            self.db.append({'id':id,'kind':'tv' if tv else 'movie','title':f'Series {i:02d}' if tv else f'Film {i:02d}',
                            'tmdb_id':9000+i,'metadata_provider':'tmdb','monitored':True,
                            'year':2026,'release_date':'2026-07-01','monitor_mode':'all' if tv else 'movie',
                            'seasons':[],'movie_file':None,'metadata_refreshed_at':'2026-01-01T00:00:00+00:00'})
    def _library(self):return copy.deepcopy(self.db)
    def _save_library(self,rows):self.db=copy.deepcopy(rows);self.last_saved+=1
    def public_config(self):return {'automatic_metadata_refresh_hours':6,'automatic_movie_availability':'digital_physical','automatic_grab_enabled':True,'automatic_queue_depth':25}
    def _iso_epoch(self,value):return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp() if value else 0
    def _metadata_api(self,path,**kwargs):
        self.calls.append((path,kwargs))
        id=int(path.split('/')[3])
        if id in self.errors_for:
            # Cached old content may be presented by legacy callers; the live
            # metadata verifier explicitly rejects the stale fallback.
            if kwargs.get('allow_cached_fallback',True):
                return {'title':f'Old {id}','release_date':'2026-07-01'}
            raise TimeoutError('Metadata Service unavailable, cached response rejected')
        if path.startswith('/v1/movie/'):
            return {'title':f'Film {id-9000:02d}', 'release_date':'2026-07-01',
                    'digital_release_date':'2026-10-06','availability_date':'2026-10-06'}
        if path.endswith('/automation'):
            return {'series':{'title':f'Series {id-9000:02d}','seasons':[{'season_number':1}]},'seasons':[{'season_number':1,'episodes':[{'episode_number':1,'air_date':'2026-10-01'}]}]}
        raise AssertionError('Unexpected path '+path)
    def _metadata_service_search(self,*_a,**_kw):return []
    def _find_tmdb_match_for_legacy(self,_item):return None
    def _apply_tmdb_movie(self,item,detail,**_kw):
        item.update({k:v for k,v in detail.items() if k in {'digital_release_date','availability_date','title','release_date'}})
    def _apply_tmdb_tv(self,item,bundle,**_kw):
        item['seasons']=[{'season_number':1,'monitored':True,'episodes':[{'episode_number':1,'name':'Episode 1',
                            'air_date':'2026-10-01','monitored':True,'has_file':False}]}]
    def _refresh_tv_library_identity(self,*_args,**_kwargs):return ''
    def _movie_wanted_date(self,item,cfg):
        return (str(item.get('digital_release_date') or item.get('availability_date') or ''),'home')
    def _aired(self,value):return bool(value and value<='2026-11-08')
    def _event(self,*args,**kwargs):self.events.append((args,kwargs))
    def _patch_auto_runtime(self,**fields):self.rt.update(fields);return dict(self.rt)
    def _auto_runtime(self):return dict(self.rt)
    def _auto_active_targets(self):return []
    def _feed_cycle_interval(self,_cfg):return 300
    def _automatic_worker(self):pass

h=Harness()
result=h.refresh_monitored_metadata(force=True)
assert result['attempted']==63 and result['updated']==63 and result['failed']==0,result
assert result['monitored_total']==63 and result['new_episodes']==57,result
assert result['became_wanted']==63 and result['availability_changed']==6,result
assert len({x['id'] for x in h.db})==63
assert all(x.get('metadata_refreshed_at','').startswith('2026-') for x in h.db)
assert len([x for x in h.db if x['kind']=='tv' and x.get('seasons')])==57
assert all(not kwargs.get('allow_cached_fallback',True) for path,kwargs in h.calls if path.startswith('/v1/movie/') or path.endswith('/automation'))
assert len(h.calls)>=63

# A manual refresh selects precisely its requested item, not the first or all.
h=Harness()
r=h.refresh_monitored_metadata(force=True,ident='id60')
assert r['attempted']==r['updated']==1 and r['attempted_ids']==['id60'],r
assert not h.db[59].get('digital_release_date') and h.db[60].get('digital_release_date')

# Unavailable metadata must never falsely stamp a valid refresh or clear old dates.
h=Harness();h.db[60]['digital_release_date']='2026-09-01';h.errors_for={9060,9000}
r=h.refresh_monitored_metadata(force=True)
assert r['attempted']==63 and r['updated']==61 and r['failed']==2,r
assert set(r['failed_ids'])=={'id00','id60'},r
assert h.db[60]['digital_release_date']=='2026-09-01'
assert h.db[60]['metadata_refreshed_at']=='2026-01-01T00:00:00+00:00'
assert 'unavailable' in h.db[60]['metadata_refresh_error'].lower()
assert h.db[0]['seasons']==[]
h._metadata_refresh_worker()
assert h.rt['metadata_refresh_schema']==2
assert set(h.rt['metadata_pending_retry_ids'])=={'id00','id60'}
assert h.rt['last_metadata_result']['failed']==2 and h.rt['last_metadata_error']
assert h.rt['last_metadata_refresh_ts']>0
h.errors_for=set()
h._metadata_refresh_worker(retry_ids=['id00','id60'])
assert h.rt['metadata_pending_retry_ids']==[] and not h.rt['last_metadata_error']
assert h.db[0]['seasons'] and h.db[60]['digital_release_date']=='2026-10-06'
assert h.rt['last_metadata_retry_ts']>0 and h.rt['last_metadata_refresh_ts']>0

# A fresh upgrade (schema 0) must force a *full* sweep even when the old version
# incorrectly recorded a recent 'successful' one-title refresh.
h=Harness()
h.rt={'last_metadata_refresh_ts':time.time()-10,'last_metadata_result':{'updated':1},'last_cycle_ts':time.time()-20}
class DeferredThread:
    def __init__(self,*,target,kwargs=None,name,daemon):
        self.kwargs=kwargs;self.target=target;self.name=name;self.started=False
    def start(self):self.started=True
    def is_alive(self):return self.started
old=namespace['threading'];namespace['threading']=types.SimpleNamespace(Thread=DeferredThread)
try:
    r=h.maybe_refresh_monitored_metadata()
    assert r['started'] and r['mode']=='full' and h.metadata_refresh_thread.kwargs['retry_ids'] is None,r
finally:namespace['threading']=old

# A new home date or episode makes Wanted eligible and wakes Auto Grab, even if
# the normal 5-minute release-feed interval has not expired.
h=Harness()
h._metadata_refresh_worker()
assert h.rt['last_metadata_wanted_transition_ts']>0
h.rt['last_cycle_ts']=h.rt['last_metadata_wanted_transition_ts']-10
namespace['threading']=types.SimpleNamespace(Thread=DeferredThread)
try:
    r=h.maybe_run_automatic()
    assert r['started'],r
finally:namespace['threading']=old

# A second full sweep with metadata already known does not duplicate Wanted.
h=Harness()
a=h.refresh_monitored_metadata(force=True)
b=h.refresh_monitored_metadata(force=True)
assert a['became_wanted']==63 and b['became_wanted']==0,(a,b)

print('PASS: v3.7.29 63 monitored titles, 57 TV + 6 movie fresh metadata, manual targeting, stale fallback rejection, per-title failure/retry, migration full sweep, Wanted wake and deduplication')
