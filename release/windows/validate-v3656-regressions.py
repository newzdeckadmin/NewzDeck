#!/usr/bin/env python3
"""NewzDeck v3.6.62 Smart Import duplicate protection and diagnostics refinement guards."""
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

sab=load('v3656_sab',SAB)
auto=load('v3656_auto',AUTO)
if sab.ADAPTER_VERSION!='3.6.62': raise SystemExit(f'Wrong SAB adapter version: {sab.ADAPTER_VERSION}')
if sab.TERMINAL_HISTORY_VERSION!=3 or sab.TERMINAL_HISTORY_MAX_ROWS!=5000: raise SystemExit('Durable terminal-history contract changed.')
if sab.STATISTICS_ACCOUNTED_MAX_ROWS!=20000: raise SystemExit('Statistics-accounting retention changed.')

class DummyDownloadManager:
    def snapshot(self,*args,**kwargs): return {'jobs':[],'collections':[],'counts':{},'telemetry':{}}

def make_auto(root:pathlib.Path):
    return auto.MediaAutomationEngine(root,lambda value:value,lambda value:value,DummyDownloadManager(),lambda:[],version='3.6.62')

# Existing cross-episode duplicate: source for S01E02 is byte-identical to the
# already-owned S01E01 physical file. This must be detected before commit.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3656-fingerprint-existing-') as td:
    root=pathlib.Path(td); data=root/'data'; data.mkdir()
    mgr=make_auto(data)
    existing=root/'Episode1.mkv'; incoming=root/'Episode2.mkv'
    payload=(b'NEWZDECK-GUARD-'*65536)[:700000]
    existing.write_bytes(payload); incoming.write_bytes(payload)
    fp=mgr._media_fingerprint(existing)
    item={'id':'show','kind':'tv','title':'Guard Show','seasons':[{'season_number':1,'episodes':[
        {'episode_number':1,'name':'One','has_file':True,'file_path':str(existing),'file_fingerprint':fp},
        {'episode_number':2,'name':'Two','has_file':False,'file_path':'','file_fingerprint':''},
    ]}]}
    entries=[{'source':incoming,'dest':root/'library'/'Episode2.mkv','quality':'1080p','action':'IMPORT','season':1,'episode':2}]
    conflicts=mgr._preimport_cross_episode_fingerprint_conflicts(item,entries)
    if len(conflicts)!=1 or int(conflicts[0].get('conflicts_with_episode') or 0)!=1:
        raise SystemExit(f'Existing cross-episode fingerprint conflict was not detected: {conflicts}')

    # Same target is not a cross-episode conflict.
    same=[{'source':incoming,'dest':root/'library'/'Episode1.mkv','quality':'1080p','action':'UPGRADE','season':1,'episode':1}]
    if mgr._preimport_cross_episode_fingerprint_conflicts(item,same):
        raise SystemExit('Same-target fingerprint was incorrectly treated as a cross-episode conflict.')

# Two incoming season-pack files with identical bytes but different targets must
# also fail pre-commit even when the library contains neither episode yet.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3656-fingerprint-pack-') as td:
    root=pathlib.Path(td); data=root/'data'; data.mkdir(); mgr=make_auto(data)
    one=root/'S01E03.mkv'; two=root/'S01E04.mkv'; payload=b'PACK-DUPLICATE'*50000
    one.write_bytes(payload); two.write_bytes(payload)
    item={'id':'show','kind':'tv','title':'Guard Show','seasons':[{'season_number':1,'episodes':[]}]}
    entries=[
        {'source':one,'dest':root/'library'/'E03.mkv','quality':'1080p','action':'IMPORT','season':1,'episode':3},
        {'source':two,'dest':root/'library'/'E04.mkv','quality':'1080p','action':'IMPORT','season':1,'episode':4},
    ]
    conflicts=mgr._preimport_cross_episode_fingerprint_conflicts(item,entries)
    targets={(int(x.get('season') or 0),int(x.get('episode') or 0)) for x in conflicts}
    if targets!={(1,3),(1,4)}:
        raise SystemExit(f'Incoming season-pack duplicate conflict was not detected for both targets: {conflicts}')

# Durable Completed history must demote an exact path warning to resolved evidence;
# a failed/nonmatching release must not be suppressed.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3656-warning-') as td:
    root=pathlib.Path(td)
    mgr=sab.SabDownloadManager(user_root=root/'user',app_dir=root/'app',download_dir_getter=lambda:root/'completed',settings_getter=lambda:{},providers_getter=lambda:[],secret_unprotect=lambda x:x,parse_nzb=lambda b,n:{'files':[]},diagnostics=None,start_threads=False)
    release='Guard.Show.S01E02.1080p.WEB-DL-GROUP'
    with mgr._terminal_history_lock:
        mgr._terminal_history={'version':3,'rows':{'done':{'id':'done','status':'completed','post_status':'completed','collection_name':release,'filename':release,'automation_release_title':release}}}
        mgr._rebuild_terminal_history_indexes_locked()
    warning=rf'Deleting \\?\C:\NewzDeck\incomplete\{release}\{release}.vol031+32.par2 failed!'
    if not mgr._engine_warning_resolved_by_terminal_history(warning):
        raise SystemExit('Durably Completed release did not resolve its stale SAB path warning.')
    if mgr._engine_warning_resolved_by_terminal_history('Deleting C:\\other\\Different.Release\\file.par2 failed!'):
        raise SystemExit('Unrelated SAB warning was incorrectly suppressed.')

# Raw SAB overlap is independent from visible-card correction and examples are bounded.
probe=object.__new__(sab.SabDownloadManager)
probe._raw_sab_active_overlap_episodes=0; probe._raw_sab_active_overlap_samples=0; probe._raw_sab_active_overlap_active=False
probe._raw_sab_active_overlap_since=0.0; probe._raw_sab_active_overlap_last_ts=0.0; probe._raw_sab_active_slot_count=0
probe._raw_sab_active_slot_examples=[]; probe._raw_sab_foreground_id=''
ids=[f'id-{i}' for i in range(21)]
probe._observe_raw_sab_active_overlap(ids,ids[0],100.0)
if probe._raw_sab_active_overlap_episodes!=1 or probe._raw_sab_active_overlap_samples!=1 or probe._raw_sab_active_slot_count!=21:
    raise SystemExit('Raw SAB overlap telemetry did not count the overlap correctly.')
if probe._raw_sab_active_slot_examples!=ids[:3]: raise SystemExit('Raw SAB overlap examples are not bounded to three IDs.')
probe._observe_raw_sab_active_overlap(ids,ids[0],101.0)
if probe._raw_sab_active_overlap_episodes!=1 or probe._raw_sab_active_overlap_samples!=2:
    raise SystemExit('One sustained raw SAB overlap was incorrectly counted as multiple episodes.')
probe._observe_raw_sab_active_overlap([ids[0]],ids[0],102.0)
if probe._raw_sab_active_overlap_active: raise SystemExit('Raw SAB overlap did not clear when only one slot remained active.')

sab_source=SAB.read_text(encoding='utf-8'); auto_source=AUTO.read_text(encoding='utf-8'); server_source=SERVER.read_text(encoding='utf-8'); js=JS.read_text(encoding='utf-8'); index=INDEX.read_text(encoding='utf-8')
for marker in (
    'ADAPTER_VERSION = "3.6.62"','_terminal_resolved_warning_keys','_engine_warning_resolved_by_terminal_history',
    'resolved_engine_warnings','raw_sab_active_overlap_episodes','sab_active_slot_examples','visible_multi_active_corrections',
    '_observe_raw_sab_active_overlap','visible_multi_active_signature=f"visible:{len(visible_ids)}:{keep_id}:"',
):
    if marker not in sab_source: raise SystemExit(f'Missing v3.6.62 SAB marker: {marker}')
if 'multi_active_parts.append("sab:" + ",".join(explicit_active_ids))' in sab_source:
    raise SystemExit('Unbounded raw SAB UUID overlap signature remains.')
for marker in (
    '_preimport_cross_episode_fingerprint_conflicts','cross_episode_fingerprint_imports_blocked','import-integrity-hold',
    "'integrity_hold':True",'incoming media is byte-identical to a different episode',
):
    if marker not in auto_source: raise SystemExit(f'Missing v3.6.62 Smart Import marker: {marker}')
for marker in (
    'APP_VERSION = "3.6.62"','DIAGNOSTICS_SNAPSHOT_CACHE_TTL_SECONDS = 1.5','def _diagnostics_snapshot_uncached()',
    "result['diagnostics_cache']",'diagnostics_snapshot(force=True)','"Raw SAB slot overlap: "','resolved_historical=',
):
    if marker not in server_source: raise SystemExit(f'Missing v3.6.62 diagnostics marker: {marker}')
if "const UI_VERSION = '3.6.62';" not in js: raise SystemExit('UI version is not 3.6.62.')
if '3.6.62-progressive-header-reuse-thumbnail-phase-telemetry' not in index: raise SystemExit('Static cache identity is not v3.6.62.')
manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
if manifest.get('version')!='3.6.62' or manifest.get('adapter_version')!='3.6.62' or manifest.get('base_version')!='3.6.61':
    raise SystemExit(f'Build manifest identity is wrong: {manifest.get("version")}/{manifest.get("adapter_version")}/{manifest.get("base_version")}')
if WORKFLOW.exists() and 'python release/windows/validate-v3656-regressions.py' not in WORKFLOW.read_text(encoding='utf-8'):
    raise SystemExit('Canonical release workflow does not run the v3.6.62 regression guard.')
print('v3.6.62 regression guard passed (pre-import cross-episode duplicate hold + recovered SAB warnings + bounded raw-overlap telemetry + coherent diagnostics cache markers).')
