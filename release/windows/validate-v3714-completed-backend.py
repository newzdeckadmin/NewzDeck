#!/usr/bin/env python3
"""NewzDeck 3.7.14 history-only clearing behavioral guard; no network needed."""
from __future__ import annotations
import sys,threading,copy,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2] / 'src' / 'app'))
from sab_engine import SabDownloadManager

def fake_manager(n=121,*,fail_api=False):
 m=object.__new__(SabDownloadManager)
 completed={f'done-{i:03}':{'id':f'done-{i:03}','status':'completed','post_status':'completed'} for i in range(n)}
 completed['pending-post']={'id':'pending-post','status':'completed','post_status':'importing'}
 completed['failed']={'id':'failed','status':'failed','post_status':'failed'}
 m._terminal_history={'version':3,'rows':copy.deepcopy(completed)}
 m._terminal_history_index={'completed':[f'done-{i:03}' for i in range(n)]+['pending-post'],'failed':['failed']}
 m._terminal_history_lock=threading.RLock();m.lock=threading.RLock()
 m.state={'jobs':{'done-002':{'terminal_status':'completed','post_status':'completed','created_ts':1},
                  'pending-post':{'terminal_status':'completed','post_status':'importing'},
                  'active-job':{'terminal_status':'','post_status':'queued'},
                  'failed':{'terminal_status':'failed','post_status':'failed'}},
          'removed_jobs':{},'removed_job_reasons':{},'statistics':{'total_downloaded_bytes':123456}}
 m._job_last_view={};m._job_last_seen_ts={}
 m._last_snapshot_ts=9;m._last_snapshot='old';m.calls=[]
 m._refresh_shared_state=lambda:None
 m._tracked=lambda:m.state['jobs']
 m._save_state=lambda:None
 def remove(ids):
  for j in ids:m._terminal_history['rows'].pop(j,None)
  m._terminal_history_index['completed']=[i for i in m._terminal_history_index['completed'] if i not in ids]
  return len(ids)
 m._remove_terminal_history_ids=remove
 m._event=lambda *args,**kw:None
 def sab_api(mode,**kwargs):
  m.calls.append((mode,kwargs));
  if fail_api:raise ConnectionError('SAB is offline')
  return {'status':True}
 m._api=sab_api
 m.snapshot=lambda:{'jobs':[], 'counts':{'completed':len(m._terminal_history_index['completed'])}}
 return m

def run():
 m=fake_manager();r=m.control('clear_completed'); assert r['counts']['completed']==1,r
 assert len(m.state['removed_jobs'])==121
 assert set(m.state['jobs'])=={'pending-post','active-job','failed'},m.state['jobs'].keys()
 assert m._terminal_history_index['completed']==['pending-post']
 assert len(m.calls)==2,m.calls
 assert all(mode=='history' and args['name']=='delete' and args['del_files']==0 and args['archive']==0 for mode,args in m.calls)
 assert m.state['statistics']['total_downloaded_bytes']==123456
 assert m._last_snapshot is None and m._last_snapshot_ts==0
 assert all(reason=='completed_history_clear' for reason in m.state['removed_job_reasons'].values())
 # Failure to contact SAB must NOT delete files, discard active work or resurrect a card.
 m=fake_manager(3,fail_api=True);m.control('clear_completed')
 assert set(m.state['jobs'])=={'pending-post','active-job','failed'}
 assert len(m._terminal_history_index['completed'])==1
 assert m.state['statistics']['total_downloaded_bytes']==123456
 # Idempotent, zero-data history clear does not mutate SAB.
 m=fake_manager(0);m._terminal_history['rows'].pop('pending-post');m._terminal_history_index['completed']=[]
 m.control('clear_completed');assert not m.calls
 # Reasonless legacy tombstones and history-only tombstones must NEVER trigger
 # the old safety reaper's queue deletion (which uses del_files=1).
 m=fake_manager(0);m._removed_cleanup_attempt_ts={}
 now=time.time()
 m.state['removed_jobs']={'legacy':now,'history':now,'removed':now}
 m.state['removed_job_reasons']={'history':'completed_history_clear','removed':'remove'}
 m._enforce_removed_tombstones([{'nzo_id':'legacy'},{'nzo_id':'history'},{'nzo_id':'removed'}])
 deletes=[(mode,args) for mode,args in m.calls if mode=='queue']
 assert len(deletes)==1 and deletes[0][1]['value']=='removed',deletes
 print('validate-v3714-completed-backend.py: PASS (121 history entries, all pages, protected imports/failed/queued, SAB offline, history-only tombstones, idempotence)')
if __name__=='__main__':run()
