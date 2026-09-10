#!/usr/bin/env python3
"""NewzDeck v3.6.66 import-hold semantics and Downloads-count integrity guards."""
from __future__ import annotations
import importlib.util
import json
import pathlib
import tempfile

ROOT=pathlib.Path(__file__).resolve().parents[2]
APP=ROOT/'src'/'app'
SAB=APP/'sab_engine.py'; AUTO=APP/'automation_engine.py'; SERVER=APP/'server.py'; JS=APP/'static'/'app.js'; INDEX=APP/'static'/'index.html'; MANIFEST=APP/'build-manifest.json'; WORKFLOW=ROOT/'.github'/'workflows'/'publish-release-trigger.yml'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

sab=load('v3657_sab',SAB)
auto=load('v3657_auto',AUTO)
if sab.ADAPTER_VERSION!='3.6.66': raise SystemExit(f'Wrong SAB adapter version: {sab.ADAPTER_VERSION}')
if sab.TERMINAL_HISTORY_VERSION!=3 or sab.TERMINAL_HISTORY_MAX_ROWS!=5000: raise SystemExit('Durable terminal-history contract changed.')
if sab.STATISTICS_ACCOUNTED_MAX_ROWS!=20000: raise SystemExit('Statistics-accounting retention changed.')

class DummyDownloadManager:
    def snapshot(self,*args,**kwargs): return {'jobs':[],'collections':[],'counts':{},'telemetry':{}}

def make_auto(root:pathlib.Path):
    return auto.MediaAutomationEngine(root,lambda value:value,lambda value:value,DummyDownloadManager(),lambda:[],version='3.6.66')

def make_sab(root:pathlib.Path):
    return sab.SabDownloadManager(user_root=root/'user',app_dir=root/'app',download_dir_getter=lambda:root/'completed',settings_getter=lambda:{},providers_getter=lambda:[],secret_unprotect=lambda x:x,parse_nzb=lambda b,n:{'files':[]},diagnostics=None,start_threads=False)

# User-facing terminal counts must classify by presentation outcome while preserving
# the raw SAB transfer outcome separately. Two SAB-completed/import-held jobs belong
# to Failed presentation, not Completed presentation.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3657-terminal-counts-') as td:
    mgr=make_sab(pathlib.Path(td))
    rows={}
    for i in range(3): rows[f'done-{i}']={'id':f'done-{i}','status':'completed','post_status':'completed','completed_ts':100+i}
    for i in range(2): rows[f'bad-{i}']={'id':f'bad-{i}','status':'failed','post_status':'failed','completed_ts':200+i}
    for i in range(2): rows[f'hold-{i}']={'id':f'hold-{i}','status':'completed','post_status':'failed','import_status':'failed','failure_class':'import_integrity_hold','completed_ts':300+i}
    rows['cancel']={'id':'cancel','status':'cancelled','post_status':'cancelled','completed_ts':400}
    with mgr._terminal_history_lock:
        mgr._terminal_history={'version':3,'rows':rows}
        mgr._rebuild_terminal_history_indexes_locked()
    presentation=mgr._terminal_counts(); transfer=mgr._terminal_transfer_counts()
    if presentation!={'completed':3,'failed':4,'cancelled':1}:
        raise SystemExit(f'Presentation terminal counts are wrong: {presentation}')
    if transfer!={'completed':5,'failed':2,'cancelled':1}:
        raise SystemExit(f'Raw transfer terminal counts are wrong: {transfer}')
    if len(mgr._terminal_history_index['completed'])!=3 or len(mgr._terminal_history_index['failed'])!=5:
        raise SystemExit(f'Terminal page indexes disagree with presentation counts: {mgr._terminal_history_index}')
    if presentation['failed']+presentation['cancelled']!=len(mgr._terminal_history_index['failed']):
        raise SystemExit('Failed/Cancelled presentation count does not equal Failed-page index size.')

    summary=mgr._terminal_summary_from_meta('hold-summary',{
        'id':'hold-summary','status':'completed','terminal_status':'completed','completed_ts':500,
        'post_status':'failed','import_status':'failed','import_failure_class':'import_integrity_hold',
        'failure_reason':'Incoming media is byte-identical to S01E01','integrity_hold_fingerprint':'123:abc',
        'target_integrity_hold':True,'integrity_hold_distinct_releases':2,
    })
    if not isinstance(summary,dict) or summary.get('status')!='completed' or summary.get('post_status')!='failed':
        raise SystemExit(f'Integrity-hold terminal summary lost transfer/presentation distinction: {summary}')
    if summary.get('failure_class')!='import_integrity_hold' or summary.get('integrity_hold_fingerprint')!='123:abc':
        raise SystemExit(f'Integrity-hold evidence was not preserved: {summary}')
    if mgr._terminal_history_scope_for_row(summary)!='failed':
        raise SystemExit('Integrity-hold terminal summary is not presented in Failed scope.')

# First duplicate-content release: exact release is blacklisted and automatic
# searching is immediately eligible for the next candidate. Repeating the same
# collection is idempotent. A second distinct release with the same conflicting
# fingerprint pauses unattended search for that target.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3657-integrity-hold-') as td:
    mgr=make_auto(pathlib.Path(td))
    key='tv:show:1:25'
    base={'source':'automation_grab','automatic':True,'target_key':key,'item_id':'show','release_title':'Release One','release_guid':'guid-1','indexer':'Indexer A'}
    result={'integrity_hold':True,'reason':'Incoming media is byte-identical to S01E24','fingerprint_conflicts':[{'fingerprint':'3477:deadbeef','conflicts_with_episode':24}]}
    first=mgr.record_import_integrity_hold(dict(base),dict(result),collection_id='job-1')
    rt=mgr._auto_runtime(); rec=(rt.get('targets') or {}).get(key) or {}
    if not first.get('recorded') or not first.get('blacklist_added') or first.get('target_integrity_hold'):
        raise SystemExit(f'First integrity hold policy is wrong: {first}')
    if rec.get('status')!='retrying' or rec.get('next_search_ts')!=0 or bool(rec.get('integrity_hold')):
        raise SystemExit(f'First integrity hold did not immediately allow next automatic candidate: {rec}')
    blacklist=list(rec.get('blacklist') or [])
    if len(blacklist)!=1 or blacklist[0].get('error_code')!='import_integrity_hold' or blacklist[0].get('guid')!='guid-1':
        raise SystemExit(f'Exact duplicate-content release was not blacklisted: {blacklist}')

    again=mgr.record_import_integrity_hold(dict(base),dict(result),collection_id='job-1')
    rec=(mgr._auto_runtime().get('targets') or {}).get(key) or {}
    if len(rec.get('blacklist') or [])!=1 or len(rec.get('integrity_hold_history') or [])!=1:
        raise SystemExit(f'Repeated same collection was not idempotent: {again} / {rec}')

    second_ctx={**base,'release_title':'Release Two','release_guid':'guid-2','indexer':'Indexer B'}
    second=mgr.record_import_integrity_hold(second_ctx,dict(result),collection_id='job-2')
    rec=(mgr._auto_runtime().get('targets') or {}).get(key) or {}
    if not second.get('target_integrity_hold') or not bool(rec.get('integrity_hold')) or rec.get('status')!='integrity_hold':
        raise SystemExit(f'Second distinct duplicate payload did not pause target: {second} / {rec}')
    if int(rec.get('integrity_hold_distinct_releases') or 0)!=2 or len(rec.get('blacklist') or [])!=2:
        raise SystemExit(f'Repeated-conflict evidence is incomplete: {rec}')
    health=mgr.automation_health()
    if int(health.get('integrity_hold_count') or 0)!=1 or not health.get('integrity_holds'):
        raise SystemExit(f'Automation Health did not expose active Integrity Hold: {health}')
    telemetry=mgr.target_integrity_telemetry()
    if int(telemetry.get('integrity_hold_releases_blacklisted') or 0)!=2 or int(telemetry.get('integrity_hold_targets_paused') or 0)!=1:
        raise SystemExit(f'Integrity-hold telemetry counters are wrong: {telemetry}')

sab_source=SAB.read_text(encoding='utf-8'); auto_source=AUTO.read_text(encoding='utf-8'); server_source=SERVER.read_text(encoding='utf-8'); js=JS.read_text(encoding='utf-8'); index=INDEX.read_text(encoding='utf-8')
for marker in (
    'ADAPTER_VERSION = "3.6.66"','_terminal_transfer_status_counts','terminal_presentation_counts','terminal_transfer_counts',
    'import_failure_class','import_integrity_hold','Smart Import held for review','record_import_integrity_hold',
    '_engine_warning_resolved_by_terminal_history','resolved_engine_warnings','raw_sab_active_overlap_episodes',
    'terminal_history_index_rebuilds_avoided',
):
    if marker not in sab_source: raise SystemExit(f'Missing v3.6.66 SAB/count marker: {marker}')
for marker in (
    'def record_import_integrity_hold','integrity_hold_releases_blacklisted','integrity_hold_targets_paused',
    "if bool(rec.get('integrity_hold'))",'automatic search paused for manual review','integrity_hold_resolved_ts',
    '_preimport_cross_episode_fingerprint_conflicts','cross_episode_fingerprint_imports_blocked',
):
    if marker not in auto_source: raise SystemExit(f'Missing v3.6.66 Automation integrity-hold marker: {marker}')
for marker in (
    'APP_VERSION = "3.6.66"',"'presentation_terminal_counts':presentation_terminal_counts","'transfer_terminal_counts':transfer_terminal_counts",
    'integrity_hold_releases_blacklisted=','integrity_hold_targets_paused=',
    'DIAGNOSTICS_SNAPSHOT_CACHE_TTL_SECONDS = 1.5','resolved_historical=',
):
    if marker not in server_source: raise SystemExit(f'Missing v3.6.66 diagnostics/count marker: {marker}')
for marker in ("const UI_VERSION = '3.6.66';",'INTEGRITY HOLDS','automatic search paused'):
    if marker not in js: raise SystemExit(f'Missing v3.6.66 UI hold marker: {marker}')
if '3.6.66-preview-failure-classification-video-thumbnail-telemetry' not in index: raise SystemExit('Static cache identity is not v3.6.66.')
manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
if manifest.get('version')!='3.6.66' or manifest.get('adapter_version')!='3.6.66' or manifest.get('base_version')!='3.6.65':
    raise SystemExit(f'Build manifest identity is wrong: {manifest.get("version")}/{manifest.get("adapter_version")}/{manifest.get("base_version")}')
if WORKFLOW.exists() and 'python release/windows/validate-v3657-regressions.py' not in WORKFLOW.read_text(encoding='utf-8'):
    raise SystemExit('Canonical release workflow does not run the v3.6.66 regression guard.')
print('v3.6.66 regression guard passed (presentation-vs-transfer counts + explicit import_integrity_hold + exact release blacklist + repeated-conflict target pause + carried v3.6.56 protections).')
