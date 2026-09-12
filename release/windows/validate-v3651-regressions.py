#!/usr/bin/env python3
"""NewzDeck v3.6.51 heavy-load snapshot/handoff regression guards."""
from __future__ import annotations
import ast, importlib.util, json, pathlib, tempfile, threading, time

ROOT=pathlib.Path(__file__).resolve().parents[2]
APP=ROOT/'src'/'app'
SAB=APP/'sab_engine.py'
WORKFLOW=ROOT/'.github'/'workflows'/'publish-release-trigger.yml'

sab_source=SAB.read_text(encoding='utf-8')
for marker in (
    'ADAPTER_VERSION = "3.6.79"',
    'def engine_status_cached(self) -> dict[str, Any]:',
    'engine = self.engine_status_cached()',
    'self._engine_status_background_refreshes += 1',
    'def _untracked_queue_handoff_state(',
    'self._untracked_queue_grace_seconds = 4.0',
    'Finalizing NewzDeck ownership after SAB accepted the download',
    'multiple_active_slot_samples',
    'def _observe_multiple_active_condition(',
    'snapshot_projection_last_ms',
    '"projection": float(self._snapshot_projection_last_ms or 0.0)',
    'self._legacy_compaction_bytes_after = self._legacy_compaction_bytes_before',
):
    if marker not in sab_source:
        raise SystemExit(f'Missing v3.6.51 runtime marker: {marker}')

# Structural guarantee: presentation refresh may not read/parse/merge the shared
# jobs ledger at all. Cross-process reconciliation belongs to strict background paths.
tree=ast.parse(sab_source)
cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='SabDownloadManager')
def fn(name):
    return next(node for node in cls.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name)
refresh=fn('_refresh_shared_state_for_snapshot')
refresh_calls={n.func.attr for n in ast.walk(refresh) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
for forbidden in {'_json_read','_json_read_retry','_merge_shared_states','_try_state_file_guard','_state_file_guard'}:
    if forbidden in refresh_calls:
        raise SystemExit(f'Presentation state refresh still performs forbidden ledger work: {forbidden}')
refresh_text=ast.get_source_segment(sab_source,refresh) or ''
for forbidden_text in ('state_file','state_lock_file','read_text(','read_bytes('):
    if forbidden_text in refresh_text:
        raise SystemExit(f'Presentation state refresh still references disk state: {forbidden_text}')

snapshot=fn('_snapshot_uncached')
snapshot_calls=[n.func.attr for n in ast.walk(snapshot) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
if 'engine_status_cached' not in snapshot_calls or 'engine_status' in snapshot_calls:
    raise SystemExit('Snapshot does not exclusively consume cached engine status.')
engine_loop=fn('_engine_loop')
engine_loop_calls=[n.func.attr for n in ast.walk(engine_loop) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
if 'engine_status' not in engine_loop_calls:
    raise SystemExit('Background engine loop does not refresh live engine status.')

spec=importlib.util.spec_from_file_location('v3651_sab',SAB)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

# The 25 ms presentation budget now covers the whole operation because the only
# operation is bounded local-lock access; there is no post-acquisition file parse.
obj=object.__new__(mod.SabDownloadManager)
obj.lock=threading.RLock()
obj._snapshot_shared_state_last_ms=0.0; obj._snapshot_shared_state_max_ms=0.0
obj._snapshot_shared_state_lock_skips=0; obj._snapshot_shared_state_lock_skip_last_ts=0.0
if not obj._refresh_shared_state_for_snapshot(0.025):
    raise SystemExit('Uncontended in-memory snapshot state access failed.')
held=threading.Event(); release=threading.Event()
def holder():
    with obj.lock:
        held.set(); release.wait(2.0)
th=threading.Thread(target=holder,daemon=True); th.start()
if not held.wait(1.0): raise SystemExit('Could not hold local state lock for v3.6.51 test.')
started=time.monotonic(); ok=obj._refresh_shared_state_for_snapshot(0.025); elapsed=time.monotonic()-started
release.set(); th.join(1.0)
if ok or elapsed>0.20 or obj._snapshot_shared_state_lock_skips!=1:
    raise SystemExit(f'Bounded in-memory state gate failed: ok={ok} elapsed={elapsed} skips={obj._snapshot_shared_state_lock_skips}')

# Newly accepted SAB slot grace: visible immediately, warning-free for four
# seconds, then exactly one warning if ownership never arrives. Tombstones bypass grace.
h=object.__new__(mod.SabDownloadManager)
h._untracked_queue_first_seen_ts={}; h._untracked_queue_warned=set(); h._untracked_queue_grace_seconds=4.0
age,grace,emit=h._untracked_queue_handoff_state('job-a',tombstoned=False,now=100.0)
if not grace or emit or age!=0:
    raise SystemExit(f'Fresh SAB handoff did not enter grace: {(age,grace,emit)}')
age,grace,emit=h._untracked_queue_handoff_state('job-a',tombstoned=False,now=103.9)
if not grace or emit:
    raise SystemExit('SAB handoff warned before four-second grace expired.')
age,grace,emit=h._untracked_queue_handoff_state('job-a',tombstoned=False,now=104.1)
if grace or not emit:
    raise SystemExit('Persistent orphan did not emit one warning after grace.')
age,grace,emit=h._untracked_queue_handoff_state('job-a',tombstoned=False,now=110.0)
if grace or emit:
    raise SystemExit('Persistent orphan emitted duplicate warning after first report.')
age,grace,emit=h._untracked_queue_handoff_state('job-b',tombstoned=True,now=200.0)
if grace or not emit:
    raise SystemExit('Explicitly tombstoned live SAB job incorrectly received handoff grace.')

# Multiple-active correction count represents episodes, not every poll sample.
m=object.__new__(mod.SabDownloadManager)
m._multiple_active_slot_corrections=0; m._multiple_active_slot_samples=0
m._multiple_active_slot_condition=''; m._multiple_active_slot_condition_since=0.0; m._multiple_active_slot_last_ts=0.0
m._observe_multiple_active_condition('sab:a,b',100.0)
m._observe_multiple_active_condition('sab:a,b',100.4)
if m._multiple_active_slot_corrections!=1 or m._multiple_active_slot_samples!=2:
    raise SystemExit('Repeated overlap samples inflated correction episode count.')
m._observe_multiple_active_condition('',101.0)
m._observe_multiple_active_condition('sab:a,b',102.0)
if m._multiple_active_slot_corrections!=2 or m._multiple_active_slot_samples!=3:
    raise SystemExit('Cleared/new overlap episode was not counted correctly.')

# Cached engine status must not probe localhost or read engine identity.
e=object.__new__(mod.SabDownloadManager)
e._engine_status_cache={'name':'SABnzbd','ready':True,'port':65433}
e._engine_status_ts=time.time()-0.5
e._runtime_ping=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('runtime ping must not run'))
e._load_engine_identity=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('identity read must not run'))
status=e.engine_status_cached()
if not status.get('ready') or status.get('cache_source')!='background':
    raise SystemExit(f'Cached engine status projection failed: {status}')

# Legacy no-op compaction telemetry must report actual unchanged size, not zero.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3651-legacy-') as td:
    base=pathlib.Path(td); legacy=base/'downloads.json'
    legacy.write_text(json.dumps({'jobs':[{'id':'old','status':'completed','segments':[],'segment_errors':[],'recovery_sources':{}}]}),encoding='utf-8')
    before=legacy.stat().st_size
    mgr=mod.SabDownloadManager(
        user_root=base/'user', app_dir=base/'app', download_dir_getter=lambda:base/'downloads',
        settings_getter=lambda:{}, providers_getter=lambda:[], secret_unprotect=lambda x:x,
        parse_nzb=lambda raw,name:{}, diagnostics=None, legacy_statistics_file=legacy,
        start_threads=False,
    )
    if mgr._legacy_compaction_bytes_before!=before or mgr._legacy_compaction_bytes_after!=before:
        raise SystemExit(f'Legacy no-op compaction byte telemetry is wrong: before={mgr._legacy_compaction_bytes_before} after={mgr._legacy_compaction_bytes_after} actual={before}')

workflow=WORKFLOW.read_text(encoding='utf-8')
if 'python release/windows/validate-v3650-regressions.py' not in workflow:
    raise SystemExit('Release workflow no longer runs v3.6.50 carried-forward guard.')
if 'python release/windows/validate-v3651-regressions.py' not in workflow:
    raise SystemExit('Release workflow does not run v3.6.51 regression guard.')

print('v3.6.51 regression guard passed (memory-only snapshot state + cached engine status + handoff grace + episode-based active telemetry + compaction telemetry).')
