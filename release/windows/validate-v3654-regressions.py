#!/usr/bin/env python3
"""NewzDeck v3.6.59 durable-history compaction and Automation startup guards."""
from __future__ import annotations
import copy
import importlib.util
import json
import pathlib
import tempfile
import time

ROOT=pathlib.Path(__file__).resolve().parents[2]
APP=ROOT/'src'/'app'
SAB=APP/'sab_engine.py'; AUTO=APP/'automation_engine.py'; SERVER=APP/'server.py'; JS=APP/'static'/'app.js'; MANIFEST=APP/'build-manifest.json'; WORKFLOW=ROOT/'.github'/'workflows'/'publish-release-trigger.yml'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

sab=load('v3654_sab',SAB)
auto=load('v3654_auto',AUTO)
if sab.ADAPTER_VERSION!='3.6.59': raise SystemExit(f'Wrong SAB adapter version: {sab.ADAPTER_VERSION}')
if sab.TERMINAL_HISTORY_VERSION!=3 or sab.TERMINAL_HISTORY_MAX_ROWS!=5000:
    raise SystemExit('Terminal-history v3/5,000-row contract is missing.')
if sab.STATISTICS_ACCOUNTED_MAX_ROWS!=20000:
    raise SystemExit('Statistics accounted-job ledger is not bounded to 20,000 rows.')

def make_mgr(root:pathlib.Path):
    return sab.SabDownloadManager(
        user_root=root/'user', app_dir=root/'app', download_dir_getter=lambda:root/'completed',
        settings_getter=lambda:{}, providers_getter=lambda:[], secret_unprotect=lambda x:x,
        parse_nzb=lambda b,n:{'files':[]}, diagnostics=None, start_threads=False,
    )

# Scale fixture: terminal history is the bounded presentation/audit store; jobs.json
# must retain only actionable/nonterminal state after safe terminal persistence.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3654-scale-') as td:
    root=pathlib.Path(td); engine_root=root/'user'/'sab-engine'; engine_root.mkdir(parents=True)
    now=time.time(); jobs={}
    for i in range(6000):
        n=f'done-{i:05d}'
        jobs[n]={
            'id':n,'name':f'Completed {i}','source_name':f'Completed {i}.nzb','expected_bytes':1000+i,
            'created_ts':1000+i,'completed_ts':2000+i,'terminal_status':'completed','imported':False,
            'import_status':'','_updated_ts':3000+i,
            'automation_context':{},
            'repair_telemetry':{'repair_outcome':'verified','repair_summary':'verified','verification_observed':True,'sab_stage_log':['Verifying: 01/01','Verification completed']},
        }
    for i in range(3):
        n=f'failed-{i}'
        jobs[n]={'id':n,'name':f'Failed {i}','expected_bytes':1000,'created_ts':9000+i,'completed_ts':9100+i,'terminal_status':'failed','failure_reason':'insufficient articles','_updated_ts':9200+i}
    jobs['importing']={'id':'importing','name':'Importing','expected_bytes':1000,'created_ts':9990,'completed_ts':9991,'terminal_status':'completed','import_status':'importing','imported':False,'automation_context':{'source':'automation_grab','kind':'tv','title':'Show','season':1,'episode':1},'_updated_ts':9992}
    jobs['live']={'id':'live','name':'Live','expected_bytes':1000,'created_ts':9999,'_updated_ts':9999}
    state={'version':2,'paused':False,'jobs':jobs,'statistics':{},'statistics_accounted_jobs':{f'a-{i:05d}':float(i) for i in range(21000)},'completed_imports':{},'removed_jobs':{},'removed_job_reasons':{},'_paused_updated_ts':0.0}
    (engine_root/'newzdeck-jobs.json').write_text(json.dumps(state),encoding='utf-8')
    mgr=make_mgr(root)
    disk=json.loads((engine_root/'newzdeck-jobs.json').read_text(encoding='utf-8'))
    history=json.loads((engine_root/'terminal-history.json').read_text(encoding='utf-8'))
    if len(history.get('rows') or {})!=5000:
        raise SystemExit('Terminal-history retention cap did not keep exactly 5,000 newest rows.')
    if set((disk.get('jobs') or {}).keys())!={'failed-0','failed-1','failed-2','importing','live'}:
        raise SystemExit(f'Operational ledger retained/removed the wrong jobs: {list((disk.get("jobs") or {}).keys())[:20]}')
    if len(disk.get('statistics_accounted_jobs') or {})!=20000:
        raise SystemExit('statistics_accounted_jobs did not compact to its bounded retention limit.')
    if any(isinstance(x,dict) and 'automation_context' in x for x in (history.get('rows') or {}).values()):
        raise SystemExit('Compact terminal-history v2 still persists full automation_context.')

    # Avoid live localhost calls while testing terminal page projection.
    base={'jobs':[{'id':'live','status':'queued','post_status':''}],'collections':[],'counts':{'queued':1,'downloading':0,'completed':4996,'failed':3},'telemetry':{},'statistics':{},'engine':{}}
    mgr.snapshot=lambda *args,**kwargs:copy.deepcopy(base)
    completed=mgr.snapshot_view('completed',limit=50,offset=0)
    failed=mgr.snapshot_view('failed',limit=50,offset=0)
    cview=completed.get('view') or {}; fview=failed.get('view') or {}
    if len(completed.get('jobs') or [])!=50 or cview.get('page_native') is not True or cview.get('total')!=4997:
        raise SystemExit(f'Completed page-native projection is wrong: {cview}')
    if 'matching_ids' in cview:
        raise SystemExit('Completed page still transports the all-history matching_ids list.')
    if len(fview.get('matching_ids') or [])!=3 or fview.get('total')!=3:
        raise SystemExit(f'Failed batch-ID coverage was lost: {fview}')
    for row in completed.get('jobs') or []:
        if 'automation_context' in row or 'sab_stage_log' in row or row.get('details_loaded') is not False:
            raise SystemExit('Compact Completed page leaked rich terminal detail/context.')
    detail=mgr.snapshot_view('detail',detail_id=completed['jobs'][0]['id'])
    drow=(detail.get('jobs') or [{}])[0]
    if drow.get('details_loaded') is not True or not drow.get('sab_stage_log'):
        raise SystemExit('Lazy terminal Details did not retain durable SAB repair-stage evidence after ledger compaction.')

    # A SAB History row already owned by durable history must not be re-adopted.
    victim=completed['jobs'][0]['id']
    before=set(mgr._tracked())
    adopted=mgr._adopt_untracked_slots([], [{'nzo_id':victim,'status':'Completed','filename':'old','completed':time.time(),'mb':1}])
    if adopted or set(mgr._tracked())!=before:
        raise SystemExit('Recent SAB History re-adopted a finalized row already owned by durable terminal history.')

# Sidebar cache: repeated startup reads reuse one result; any relevant file signature
# change invalidates without requiring a broad explicit invalidation call.
class DummyDM:
    pass
with tempfile.TemporaryDirectory(prefix='newzdeck-v3654-sidebar-') as td:
    data=pathlib.Path(td)
    for name,value in (
        ('media-library.json',[]),('quality-profiles.json',[]),('media-automation-config.json',{}),
        ('media-quality-cache.json',{}),('automation-activity.json',[]),('indexers.json',[]),
    ):
        (data/name).write_text(json.dumps(value),encoding='utf-8')
    engine=auto.MediaAutomationEngine(data,lambda x:x,lambda x:x,DummyDM(),lambda:[],version='3.6.59')
    # Isolate cache mechanics from unrelated Wanted fixture complexity.
    engine._library=lambda:[{'kind':'tv'},{'kind':'movie'}]
    engine.wanted=lambda:{'missing':[1,2],'upgrades':[1]}
    first=engine.sidebar_counts(); second=engine.sidebar_counts()
    if first.get('cache_hit') is not False or second.get('cache_hit') is not True:
        raise SystemExit(f'Automation sidebar counts did not cache unchanged inputs: {first} / {second}')
    p=data/'media-library.json'; p.write_text('[]\n',encoding='utf-8')
    third=engine.sidebar_counts()
    if third.get('cache_hit') is not False or int(third.get('cache_misses') or 0)<2:
        raise SystemExit('Automation sidebar-count cache did not invalidate on a library signature change.')

sab_source=SAB.read_text(encoding='utf-8'); auto_source=AUTO.read_text(encoding='utf-8'); server_source=SERVER.read_text(encoding='utf-8'); js=JS.read_text(encoding='utf-8')
for marker in (
    'ADAPTER_VERSION = "3.6.59"','TERMINAL_HISTORY_VERSION = 3','STATISTICS_ACCOUNTED_MAX_ROWS = 20000',
    '_terminal_history_index','_terminal_status_counts','_retire_finalized_terminal_jobs_locked',
    'Durable NewzDeck terminal history already owns this presentation','page_native',
    'if mode=="failed": view["matching_ids"]=matching_ids','matching_ids=list(ids) if mode=="failed" else []',
):
    if marker not in sab_source: raise SystemExit(f'Missing v3.6.59 SAB/history marker: {marker}')
for marker in ('sidebar_counts_cache_signature','sidebar_counts_cache_result','def _sidebar_counts_signature','cache_hit'):
    if marker not in auto_source: raise SystemExit(f'Missing v3.6.59 Automation cache marker: {marker}')
for marker in ("const UI_VERSION = '3.6.59';",'automationStartupPrimeGeneration++;','if(!state.automation)void loadAutomation'):
    if marker not in js: raise SystemExit(f'Missing v3.6.59 startup-probe guard: {marker}')
if 'APP_VERSION = "3.6.59"' not in server_source: raise SystemExit('Server version is not 3.6.59.')
manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
if manifest.get('version')!='3.6.59' or manifest.get('adapter_version')!='3.6.59' or manifest.get('base_version')!='3.6.58':
    raise SystemExit(f'Build manifest identity is wrong: {manifest.get("version")}/{manifest.get("adapter_version")}/{manifest.get("base_version")}')
if WORKFLOW.exists() and 'python release/windows/validate-v3654-regressions.py' not in WORKFLOW.read_text(encoding='utf-8'):
    raise SystemExit('Canonical release workflow does not run the v3.6.59 regression guard.')
print('v3.6.59 regression guard passed (bounded operational ledger + 5,000-row indexed terminal history + compact page transport + durable lazy detail + SAB re-adoption guard + sidebar cache/probe cancellation).')
