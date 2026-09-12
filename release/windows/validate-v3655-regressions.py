#!/usr/bin/env python3
"""NewzDeck v3.6.80 terminal-history index and diagnostics efficiency guards."""
from __future__ import annotations
import importlib.util
import json
import pathlib
import tempfile
import time

ROOT=pathlib.Path(__file__).resolve().parents[2]
APP=ROOT/'src'/'app'
SAB=APP/'sab_engine.py'; SERVER=APP/'server.py'; JS=APP/'static'/'app.js'; INDEX=APP/'static'/'index.html'; MANIFEST=APP/'build-manifest.json'; WORKFLOW=ROOT/'.github'/'workflows'/'publish-release-trigger.yml'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

sab=load('v3655_sab',SAB)
if sab.ADAPTER_VERSION!='3.6.80':
    raise SystemExit(f'Wrong SAB adapter version: {sab.ADAPTER_VERSION}')
if sab.TERMINAL_HISTORY_VERSION!=3 or sab.TERMINAL_HISTORY_MAX_ROWS!=5000:
    raise SystemExit('v3.6.80 changed the durable terminal-history v3/5,000-row contract.')
if sab.STATISTICS_ACCOUNTED_MAX_ROWS!=20000:
    raise SystemExit('v3.6.80 changed the 20,000-ID statistics accounting boundary.')

def make_mgr(root:pathlib.Path):
    return sab.SabDownloadManager(
        user_root=root/'user', app_dir=root/'app', download_dir_getter=lambda:root/'completed',
        settings_getter=lambda:{}, providers_getter=lambda:[], secret_unprotect=lambda x:x,
        parse_nzb=lambda b,n:{'files':[]}, diagnostics=None, start_threads=False,
    )

# v3.6.54 full-load diagnostics showed 1,077 index rebuilds but only 22 durable
# writes. Seed an already-valid v3 history and prove frequent no-op completion
# monitor syncs neither copy into a write nor rebuild the cached page index.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3655-history-noop-') as td:
    root=pathlib.Path(td)
    engine_root=root/'user'/'sab-engine'
    engine_root.mkdir(parents=True)
    rows={}
    for i in range(100):
        n=f'done-{i:03d}'
        rows[n]={
            'id':n,'status':'completed','post_status':'completed',
            'collection_name':f'Completed {i}','filename':f'Completed {i}',
            'created_ts':1000+i,'completed_ts':2000+i,'details_loaded':False,
        }
    (engine_root/'terminal-history.json').write_text(
        json.dumps({'version':3,'updated_ts':1,'rows':rows}),encoding='utf-8'
    )
    (engine_root/'newzdeck-jobs.json').write_text(
        json.dumps({'version':2,'paused':False,'jobs':{
            'live':{'id':'live','name':'Live','created_ts':9999,'_updated_ts':9999}
        },'statistics':{},'statistics_accounted_jobs':{},'completed_imports':{},'removed_jobs':{},'removed_job_reasons':{},'_paused_updated_ts':0}),
        encoding='utf-8'
    )
    mgr=make_mgr(root)
    initial_rebuilds=mgr._terminal_history_index_rebuilds
    initial_writes=mgr._terminal_history_writes
    initial_noops=mgr._terminal_history_sync_noops
    if initial_rebuilds!=1:
        raise SystemExit(f'Loaded v3 history should build its cached index once, got {initial_rebuilds}.')
    if len(mgr._terminal_history_index.get('completed') or [])!=100:
        raise SystemExit('Loaded v2 Completed index did not contain all 100 rows.')

    for _ in range(25):
        if mgr._sync_terminal_history_from_state(persist=True)!=0:
            raise SystemExit('Unchanged terminal-history sync unexpectedly reported a mutation.')
    if mgr._terminal_history_index_rebuilds!=initial_rebuilds:
        raise SystemExit(
            f'No-op terminal sync rebuilt the index: {initial_rebuilds} -> {mgr._terminal_history_index_rebuilds}'
        )
    if mgr._terminal_history_writes!=initial_writes:
        raise SystemExit(
            f'No-op terminal sync rewrote durable history: {initial_writes} -> {mgr._terminal_history_writes}'
        )
    if mgr._terminal_history_sync_noops < initial_noops+25:
        raise SystemExit('No-op terminal sync telemetry did not count avoided maintenance passes.')

    # If a normalization write fails, the pending-maintenance flag must survive and
    # the next persistent sync must retry rather than silently treating RAM as disk.
    durable_row=mgr._terminal_history['rows']['done-000']
    durable_row['automation_context']={'source':'automation_grab','label':'Guard'}
    mgr._terminal_history_needs_normalization=True
    original_write=mgr._write_terminal_history
    def fail_write():
        raise RuntimeError('simulated durable write failure')
    mgr._write_terminal_history=fail_write
    try:
        mgr._sync_terminal_history_from_state(persist=True)
        raise SystemExit('Simulated terminal-history write failure did not propagate.')
    except RuntimeError as exc:
        if 'simulated durable write failure' not in str(exc):
            raise
    finally:
        mgr._write_terminal_history=original_write
    if not mgr._terminal_history_needs_normalization:
        raise SystemExit('Failed normalization write cleared the pending-maintenance flag.')
    before_writes=mgr._terminal_history_writes
    before_rebuilds=mgr._terminal_history_index_rebuilds
    if mgr._sync_terminal_history_from_state(persist=True)<1:
        raise SystemExit('Pending normalization was not retried after a failed durable write.')
    if mgr._terminal_history_needs_normalization:
        raise SystemExit('Successful normalization retry did not clear the maintenance flag.')
    if mgr._terminal_history_writes!=before_writes+1 or mgr._terminal_history_index_rebuilds!=before_rebuilds+1:
        raise SystemExit('Normalization retry did not produce exactly one write/rebuild.')

    # One actual finalized terminal mutation must produce one durable write and
    # exactly one index rebuild, not the v3.6.54 double-rebuild pattern.
    with mgr.lock:
        mgr.state['jobs']['new-done']={
            'id':'new-done','name':'New Completed','source_name':'New Completed.nzb',
            'expected_bytes':1234,'created_ts':12000,'completed_ts':12001,
            'terminal_status':'completed','post_status':'completed','_updated_ts':12002,
        }
    before_rebuilds=mgr._terminal_history_index_rebuilds
    before_writes=mgr._terminal_history_writes
    changed=mgr._sync_terminal_history_from_state(persist=True)
    if changed < 1:
        raise SystemExit('A new finalized terminal job did not update durable history.')
    if mgr._terminal_history_writes != before_writes+1:
        raise SystemExit('One terminal mutation did not produce exactly one durable history write.')
    if mgr._terminal_history_index_rebuilds != before_rebuilds+1:
        raise SystemExit('One terminal mutation did not produce exactly one cached-index rebuild.')
    if 'new-done' not in (mgr._terminal_history_index.get('completed') or []):
        raise SystemExit('New durable Completed row is missing from the cached index.')

    # Removal must also own a single write/rebuild.
    victim='done-050'
    before_rebuilds=mgr._terminal_history_index_rebuilds
    before_writes=mgr._terminal_history_writes
    if mgr._remove_terminal_history_ids([victim])!=1:
        raise SystemExit('Durable history removal did not remove the requested row.')
    if mgr._terminal_history_writes != before_writes+1:
        raise SystemExit('One durable history removal did not produce exactly one write.')
    if mgr._terminal_history_index_rebuilds != before_rebuilds+1:
        raise SystemExit('One durable history removal rebuilt the index more than once.')
    if victim in (mgr._terminal_history_index.get('completed') or []):
        raise SystemExit('Removed durable row remained in the Completed index.')

# Multi-active evidence must retain provenance after the transient condition clears.
probe=object.__new__(sab.SabDownloadManager)
probe._multiple_active_slot_corrections=0
probe._multiple_active_slot_samples=0
probe._multiple_active_slot_condition=''
probe._multiple_active_slot_condition_since=0.0
probe._multiple_active_slot_last_ts=0.0
probe._multiple_active_slot_last_signature=''
probe._observe_multiple_active_condition('sab:a,b|visible:a,b',100.0)
if probe._multiple_active_slot_condition!='sab:a,b|visible:a,b' or probe._multiple_active_slot_last_signature!='sab:a,b|visible:a,b':
    raise SystemExit('Multi-active overlap provenance was not retained.')
probe._observe_multiple_active_condition('',101.0)
if probe._multiple_active_slot_condition or probe._multiple_active_slot_last_signature!='sab:a,b|visible:a,b':
    raise SystemExit('Clearing current multi-active state erased the last overlap signature.')

sab_source=SAB.read_text(encoding='utf-8')
server_source=SERVER.read_text(encoding='utf-8')
js=JS.read_text(encoding='utf-8')
index=INDEX.read_text(encoding='utf-8')

for marker in (
    'ADAPTER_VERSION = "3.6.80"',
    '_terminal_history_sync_runs',
    '_terminal_history_sync_noops',
    '_terminal_history_sync_changed_rows',
    "'terminal_history_index_rebuilds_avoided': int(self._terminal_history_sync_noops)",
    'if not updates and not needs_maintenance:',
    'self._terminal_history_sync_noops+=1',
    '# _write_terminal_history owns the single rebuild for this mutation.',
    'Keep a pending normalization flag set until a persistent write actually',
    'This flag also means the normalized form is not yet proven durable.',
    'multiple_active_slot_current_signature',
    'multiple_active_slot_last_signature',
    'multiple_active_slot_current_has_sab_overlap',
    'multiple_active_slot_current_has_visible_correction',
):
    if marker not in sab_source:
        raise SystemExit(f'Missing v3.6.80 history/overlap marker: {marker}')

for marker in (
    'APP_VERSION = "3.6.80"',
    'snap = DOWNLOAD_MANAGER.snapshot(scope="live")',
    "'durable_terminal_counts':durable_terminal_counts",
    "'operational_tracked_jobs':int(telemetry.get('presentation_index_tracked_total'",
    "'operational_presentable_jobs':int(telemetry.get('presentation_index_active_jobs'",
    "'measurement_state': 'measured' if (latency_measured or total) else 'unmeasured'",
    'latency_text = f"{float(latency):.0f}ms" if latency is not None and bool(p.get(\'latency_measured\')) else "N/A"',
    'success_text = f"{float(success):.1f}%" if success is not None and bool(p.get(\'success_rate_measured\')) else "N/A"',
    '"Terminal history efficiency: "',
    '"Multi-active normalization: "',
):
    if marker not in server_source:
        raise SystemExit(f'Missing v3.6.80 diagnostics marker: {marker}')
for forbidden in (
    "snap = DOWNLOAD_MANAGER.snapshot()\n",
    "latency={p.get('last_latency_ms',0)}ms",
    "success={p.get('success_rate')}%",
):
    if forbidden in server_source:
        raise SystemExit(f'Stale v3.6.54 diagnostics behavior remains: {forbidden!r}')

if "const UI_VERSION = '3.6.80';" not in js:
    raise SystemExit('UI version is not 3.6.80.')
if '3.6.80-ux-final-consistency-accessibility' not in index:
    raise SystemExit('Static asset cache identity is not v3.6.80.')
manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
if manifest.get('version')!='3.6.80' or manifest.get('adapter_version')!='3.6.80' or manifest.get('base_version')!='3.6.79':
    raise SystemExit(f'Build manifest identity is wrong: {manifest.get("version")}/{manifest.get("adapter_version")}/{manifest.get("base_version")}')
if WORKFLOW.exists() and 'python release/windows/validate-v3655-regressions.py' not in WORKFLOW.read_text(encoding='utf-8'):
    raise SystemExit('Canonical release workflow does not run the v3.6.80 regression guard.')

print('v3.6.80 regression guard passed (no-op history fast path + one rebuild per mutation + durable diagnostic counts + N/A provider measurements + overlap provenance).')
