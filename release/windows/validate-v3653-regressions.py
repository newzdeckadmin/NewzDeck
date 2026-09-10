#!/usr/bin/env python3
"""NewzDeck v3.6.68 NZB identity, durable history and presentation-index guards."""
from __future__ import annotations
import importlib.util, json, pathlib, tempfile, time, ast

ROOT=pathlib.Path(__file__).resolve().parents[2]
APP=ROOT/'src'/'app'
AUTO=APP/'automation_engine.py'; SAB=APP/'sab_engine.py'; SERVER=APP/'server.py'; JS=APP/'static'/'app.js'; WORKFLOW=ROOT/'.github'/'workflows'/'publish-release-trigger.yml'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
auto=load('v3653_auto',AUTO); sab=load('v3653_sab',SAB)

if sab.ADAPTER_VERSION!='3.6.68': raise SystemExit(f'Wrong adapter version: {sab.ADAPTER_VERSION}')

def nzb(subjects):
    body=['<?xml version="1.0" encoding="utf-8"?><nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">']
    for i,subject in enumerate(subjects):
        body.append(f'<file poster="x" date="1" subject="{subject}"><groups><group>alt.binaries.test</group></groups><segments><segment bytes="100" number="1">m{i}@x</segment></segments></file>')
    body.append('</nzb>'); return ''.join(body).encode()
ctx={'source':'automation_grab','kind':'tv','title':'Big Brother Canada','season':7,'episode':29,'season_pack':False,'automatic':True,'target_key':'tv:bbc:s07e029'}
engine=object.__new__(auto.MediaAutomationEngine)
# Production-shaped 998-file disguised pack: 988 episode-bearing files across E01-E29 + 10 explicit Complete PAR2 files.
subjects=[f'Big.Brother.Canada.S07E{(i%29)+1:02d}.1080p.WEB.h264-DiRT.part{i:04d}.rar' for i in range(988)]
subjects += [f'Big.Brother.Canada.S07.Complete.1080p.WEB.h264-DiRT.vol{i:02d}.par2' for i in range(10)]
try:
    engine._validate_release_nzb_content(nzb(subjects),dict(ctx))
    raise SystemExit('Disguised S07E29 season pack was accepted.')
except auto.ReleaseContentValidationError as exc:
    ev=exc.evidence
    if int(ev.get('subject_count') or 0)!=998 or len(ev.get('episode_identities') or [])!=29 or 7 not in (ev.get('pack_seasons') or []):
        raise SystemExit(f'Disguised-pack evidence was incomplete: {ev}')
# Valid multipart single episode must pass.
valid=[f'Big.Brother.Canada.S07E29.1080p.WEB.h264-DiRT.part{i:02d}.rar' for i in range(30)]+['Big.Brother.Canada.S07E29.1080p.WEB.h264-DiRT.par2']
if not engine._validate_release_nzb_content(nzb(valid),dict(ctx)).get('accepted'):
    raise SystemExit('Valid multipart S07E29 was rejected.')
# Obfuscated/no-evidence stays admissible.
obfuscated=[f'9f3a72c4-{i:04d}.rar' for i in range(30)]+['recovery.vol00+20.par2']
ob=engine._validate_release_nzb_content(nzb(obfuscated),dict(ctx))
if not ob.get('accepted') or ob.get('episode_identities'):
    raise SystemExit(f'Obfuscated no-evidence NZB was rejected: {ob}')
# A declared season pack may contain many episodes in its own season.
pack_ctx=dict(ctx,episode=None,season_pack=True)
if not engine._validate_release_nzb_content(nzb(subjects),pack_ctx).get('accepted'):
    raise SystemExit('Legitimate Season 7 pack was rejected for a Season 7 pack target.')

# Structural order: actual NZB validation must occur after fetch and before queue_nzb/add_nzb.
auto_source=AUTO.read_text(encoding='utf-8')
grab_start=auto_source.index('    def grab_release(self,data):')
grab=auto_source[grab_start:]
pos_fetch=grab.index('raw=self._fetch_release_nzb(data)'); pos_validate=grab.index('self._validate_release_nzb_content(raw,context)'); pos_queue=grab.index("queue_submit=getattr(self.download_manager,'queue_nzb',None)")
if not pos_fetch < pos_validate < pos_queue: raise SystemExit('NZB content gate is not before SAB queue submission.')
for marker in ('except ReleaseContentValidationError as exc:', 'for candidate_index,candidate in enumerate(candidates):', "'rejected':'nzb_content_identity'", "'release-content-rejected'"):
    if marker not in auto_source: raise SystemExit(f'Missing automatic next-candidate content-rejection marker: {marker}')

# Second line of defense: mixed explicit media output must not reach Smart Import.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3653-output-') as td:
    p=pathlib.Path(td)
    good=p/'Big Brother Canada - S07E29 - Finale.mkv'; wrong=p/'Big Brother Canada - S07E25 - Eviction.mkv'; good.write_bytes(b'x'); wrong.write_bytes(b'y')
    dm=object.__new__(sab.SabDownloadManager)
    ok,reason,evidence=dm._validate_automation_output_episode_identity(dict(ctx),[good,wrong])
    if ok or len(evidence.get('episode_identities') or [])!=2: raise SystemExit('Mixed-episode Smart Import output was not rejected.')
    ok,_,_=dm._validate_automation_output_episode_identity(dict(ctx),[good])
    if not ok: raise SystemExit('Exact S07E29 Smart Import output was rejected.')
    opaque=p/'9f3a72c4-final.mkv'; opaque.write_bytes(b'z')
    ok,_,_=dm._validate_automation_output_episode_identity(dict(ctx),[opaque])
    if not ok: raise SystemExit('Obfuscated single-output Smart Import was rejected without contradictory evidence.')

# Durable terminal-history bootstrap/paging independent of SAB's 200-row history.
def make_mgr(root):
    return sab.SabDownloadManager(user_root=root/'user',app_dir=root/'app',download_dir_getter=lambda:root/'completed',settings_getter=lambda:{},providers_getter=lambda:[],secret_unprotect=lambda x:x,parse_nzb=lambda b,n:{'files':[]},diagnostics=None,start_threads=False)
with tempfile.TemporaryDirectory(prefix='newzdeck-v3653-history-') as td:
    root=pathlib.Path(td); mgr=make_mgr(root)
    tracked={}
    for i in range(620):
        tracked[f'done-{i:04d}']={'id':f'done-{i:04d}','name':f'Completed {i}','expected_bytes':1000+i,'created_ts':1000+i,'completed_ts':2000+i,'terminal_status':'completed','imported':True,'import_status':'completed','_updated_ts':3000+i,'automation_context':{'source':'automation_grab','kind':'tv','season':1,'episode':i%20+1}}
    for i in range(10):
        tracked[f'live-{i}']={'id':f'live-{i}','name':f'Live {i}','expected_bytes':1000,'created_ts':5000+i,'_updated_ts':5000+i,'automation_context':{}}
    mgr.state['jobs']=tracked
    mgr._sync_terminal_history_from_state(persist=True); mgr._publish_presentation_index()
    pidx=mgr._presentation_index_snapshot()
    if len(pidx.get('active_jobs') or {})!=10 or int((pidx.get('terminal_counts') or {}).get('completed') or 0)!=620:
        raise SystemExit(f'Presentation index did not separate 10 Live from 620 terminal jobs: {pidx}')
    if not mgr.terminal_history_file.exists(): raise SystemExit('terminal-history.json was not persisted.')
    disk=json.loads(mgr.terminal_history_file.read_text(encoding='utf-8'))
    if len(disk.get('rows') or {})!=620: raise SystemExit('Terminal-history bootstrap lost durable rows.')
    base={'jobs':[{'id':f'live-{i}','status':'queued','post_status':''} for i in range(10)],'collections':[],'counts':{'queued':10,'downloading':0,'completed':620,'failed':0},'telemetry':{},'statistics':{},'engine':{}}
    mgr.snapshot=lambda *args,**kwargs:base
    first=mgr.snapshot_view('completed',limit=50,offset=0); second=mgr.snapshot_view('completed',limit=50,offset=50)
    if len(first.get('jobs') or [])!=50 or int((first.get('view') or {}).get('total') or 0)!=620 or not (first.get('view') or {}).get('has_more'):
        raise SystemExit(f'Durable Completed first page is wrong: {first.get("view")}')
    if set(x['id'] for x in first['jobs']) & set(x['id'] for x in second['jobs']): raise SystemExit('Terminal pages overlap.')
    if any(x.get('details_loaded') is not False for x in first['jobs']): raise SystemExit('Terminal summaries are not lazy.')
    detail=mgr._terminal_detail_job(first['jobs'][0]['id'])
    if not detail or detail.get('details_loaded') is not True: raise SystemExit('Lazy terminal detail lookup failed.')
    victim=first['jobs'][0]['id']; before=len(mgr._terminal_history_snapshot()); mgr._remove_terminal_history_ids([victim]); after=len(mgr._terminal_history_snapshot())
    if after!=before-1: raise SystemExit('Terminal remove did not remove the durable history row.')

# Presentation path must not unconditionally lock the durable state for Live mode.
sab_source=SAB.read_text(encoding='utf-8')
if 'self._sync_terminal_history_from_state(persist=True)' not in sab_source:
    raise SystemExit('Startup does not persist any durable-ledger terminal-history reconciliation.')
for marker in ('terminal-history.json','TERMINAL_HISTORY_MAX_ROWS = 5000','_presentation_index_snapshot','_queue_snapshot_state_patch','_drain_snapshot_state_patches','history_source":"newzdeck-terminal-index','lazy_details','queue_sampler_last_failure_error','queue_sampler_failure_reasons','_validate_automation_output_episode_identity'):
    if marker not in sab_source: raise SystemExit(f'Missing v3.6.68 runtime marker: {marker}')
# Retained sampler failure survives a success publish.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3653-sampler-') as td:
    mgr=make_mgr(pathlib.Path(td)); mgr._queue_sampler_last_failure_error='transport busy'; mgr._queue_sampler_last_failure_ts=123.0; mgr._queue_sampler_failure_reasons={'RuntimeError: busy':3}
    mgr._publish_queue_sample({'queue':{'slots':[]}}, {'history':{'slots':[]}})
    if mgr._queue_sampler_last_error or mgr._queue_sampler_last_failure_error!='transport busy' or mgr._queue_sampler_last_failure_ts!=123.0 or mgr._queue_sampler_failure_reasons.get('RuntimeError: busy')!=3:
        raise SystemExit('Sampler recovery erased retained last-failure evidence.')


# Lifecycle guard: user Remove/Cancel and Retry must keep the NewzDeck-owned
# terminal index semantically aligned with the durable job ledger.
control_start=sab_source.index('    def control(self, action: str')
control_text=sab_source[control_start:sab_source.index('    def retry_automation_import', control_start)]
if control_text.count('self._remove_terminal_history_ids(') < 4:
    raise SystemExit('Remove/Cancel/Retry control paths do not consistently retire terminal-history rows.')
retry_pos=control_text.index('elif action == "retry":')
retry_block=control_text[retry_pos:control_text.index('elif action == "priority":', retry_pos)]
for marker in ('live.pop("terminal_status",None)', 'live.pop("completed_ts",None)', 'self._remove_terminal_history_ids(ids)'):
    if marker not in retry_block:
        raise SystemExit(f'Retry does not supersede the prior terminal-history state: {marker}')

# Live rendering may retain full-path locks for compatibility, but every direct
# state lock inside _snapshot_uncached must sit behind a non-Live branch. The
# v3.6.68 active presentation path itself is sourced from the copy-on-write index.
snapshot_start=sab_source.index('    def _snapshot_uncached(self, scope_mode: str = "all")')
snapshot_end=sab_source.index('    def _ids(self, job_id: str', snapshot_start)
snapshot_text=sab_source[snapshot_start:snapshot_end]
for required in ('if scope_mode == "live":\n                presentation_index=self._presentation_index_snapshot()',
                 'if scope_mode == "live":\n            presentation_index=self._presentation_index_snapshot()',
                 'if scope_mode == "live":\n            removed_reason_snapshot=dict(presentation_index.get("removed_job_reasons") or {})'):
    if required not in snapshot_text:
        raise SystemExit('Live snapshot no longer consumes the published presentation index at every ledger decision point.')

server_source=SERVER.read_text(encoding='utf-8'); js=JS.read_text(encoding='utf-8')
for marker in ('APP_VERSION = "3.6.68"','detail_id=str((query.get("id")','snapshot_view(scope,limit=limit,offset=offset,detail_id=detail_id)'):
    if marker not in server_source: raise SystemExit(f'Missing server detail/paging marker: {marker}')
for marker in ("const UI_VERSION = '3.6.68';",'downloadHistoryOffset:0','downloadHistoryLoaded:[]','scope=detail&id=','job.details_loaded===false',"state.downloadHistoryOffset=(state.downloadHistoryLoaded||[]).length"):
    if marker not in js: raise SystemExit(f'Missing durable-history UI marker: {marker}')
if WORKFLOW.exists() and 'python release/windows/validate-v3653-regressions.py' not in WORKFLOW.read_text(encoding='utf-8'):
    raise SystemExit('Release workflow does not run the v3.6.68 guard.')

print('v3.6.68 regression guard passed (998-file disguised pack rejection + output fail-closed + 620-row durable history + active presentation index + retained sampler failures).')
