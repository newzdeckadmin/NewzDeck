#!/usr/bin/env python3
"""NewzDeck v3.6.50 snapshot-sampler/state-lock regression guards."""
from __future__ import annotations
import ast, importlib.util, json, pathlib, tempfile, threading, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
APP=ROOT/'src'/'app'
SAB=APP/'sab_engine.py'
AUTO=APP/'automation_engine.py'
INSTALLER=ROOT/'release'/'windows'/'NewzDeck.iss'
WORKFLOW=ROOT/'.github'/'workflows'/'publish-release-trigger.yml'

sab_source=SAB.read_text(encoding='utf-8')
for marker in (
    'ADAPTER_VERSION = "3.6.69"',
    'def _queue_sampler_loop(self) -> None:',
    'self._queue_sampler_thread',
    'return self._queue_and_history_fetch(live=False)',
    'def _queue_and_history_fetch(self, *, live: bool = False)',
    'def _refresh_shared_state_for_snapshot(self, max_wait_seconds: float = 0.0)',
    'msvcrt.LK_NBLCK',
    'self.lock.acquire(blocking=False)',
    'snapshot_shared_state_lock_skips',
    'snapshot_worst_phase',
    'phases["other"] = max(0.0, build_ms - sum(phases.values()))',
    'queue_sampler_successes',
    'def _publish_queue_sample(self, queue_data: dict[str, Any], history_data: dict[str, Any]) -> None:',
    'refresh_shared=False, defer_persist=True',
    'def _persist_terminal_history_evidence(self, history_slots: list[dict[str, Any]]) -> int:',
    'def _request_deferred_state_persist(self) -> None:',
    'def _flush_deferred_state_persist(self) -> bool:',
    'deferred_state_persist_requests',
    'self._flush_deferred_state_persist()',
):
    if marker not in sab_source: raise SystemExit(f'Missing v3.6.50 SAB marker: {marker}')


# Presentation generation must never call the strict blocking state save. Durable
# bookkeeping found while rendering is queued for the background engine worker.
sab_tree=ast.parse(sab_source)
snapshot_node=next((node for node in sab_tree.body if isinstance(node,ast.ClassDef) for child in node.body if isinstance(child,ast.FunctionDef) and child.name=='_snapshot_uncached' for node in [child]),None)
if snapshot_node is None:
    raise SystemExit('Could not locate _snapshot_uncached for blocking-save guard.')
snapshot_text=ast.get_source_segment(sab_source,snapshot_node) or ''
called_attrs={node.func.attr for node in ast.walk(snapshot_node) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
for forbidden in {
    '_save_state','_refresh_shared_state','_reconcile_statistics','_adopt_untracked_slots',
    '_kick_completed_automation_imports','_remember_failed_automation_release',
    '_flatten_completed_browser_images','_enforce_removed_tombstones',
    '_cleanup_proven_stale_queue_duplicates','_api',
}:
    if forbidden in called_attrs:
        raise SystemExit(f'_snapshot_uncached still performs blocking/destructive background work: {forbidden}')
if sum(1 for node in ast.walk(snapshot_node) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='_request_deferred_state_persist') < 2:
    raise SystemExit('Snapshot durable bookkeeping is not routed through deferred persistence.')

# Exercise the bounded state-refresh helper without starting SAB. A held ledger
# lock on POSIX must not make a presentation refresh wait for the lock owner.
spec=importlib.util.spec_from_file_location('v3650_sab',SAB)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory(prefix='newzdeck-v3650-state-') as td:
    obj=object.__new__(mod.SabDownloadManager)
    obj.root=pathlib.Path(td)
    obj.state_file=obj.root/'newzdeck-jobs.json'
    obj.state_lock_file=obj.root/'.newzdeck-jobs.lock'
    obj.lock=threading.RLock(); obj.state={'version':2,'jobs':{}}
    obj._snapshot_shared_state_last_ms=0.0; obj._snapshot_shared_state_max_ms=0.0
    obj._snapshot_shared_state_lock_skips=0; obj._snapshot_shared_state_lock_skip_last_ts=0.0
    obj.state_file.write_text(json.dumps(obj.state),encoding='utf-8')
    if __import__('os').name!='nt':
        import fcntl
        blocker=obj.state_lock_file.open('a+b'); blocker.write(b'0'); blocker.flush(); blocker.seek(0)
        fcntl.flock(blocker.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        started=time.monotonic(); ok=obj._refresh_shared_state_for_snapshot(0.025); elapsed=time.monotonic()-started
        fcntl.flock(blocker.fileno(),fcntl.LOCK_UN); blocker.close()
        # v3.6.51 strengthens the v3.6.50 bound: presentation no longer touches
        # the cross-process ledger lock at all, so a held file lock must not block
        # or force a skip. The local in-process lock test below remains mandatory.
        if not ok or elapsed>0.20 or obj._snapshot_shared_state_lock_skips!=0:
            raise SystemExit(f'Presentation was affected by held cross-process ledger lock: ok={ok} elapsed={elapsed} skips={obj._snapshot_shared_state_lock_skips}')

    # The same budget must cover the in-process RLock. A strict background save
    # can hold it while waiting on a cross-process writer; presentation must not.
    held=threading.Event(); release=threading.Event()
    def hold_local_lock():
        with obj.lock:
            held.set(); release.wait(2.0)
    thread=threading.Thread(target=hold_local_lock,daemon=True); thread.start()
    if not held.wait(1.0): raise SystemExit('Could not establish held in-process state lock for regression test.')
    started=time.monotonic(); ok=obj._refresh_shared_state_for_snapshot(0.025); elapsed=time.monotonic()-started
    release.set(); thread.join(1.0)
    if ok or elapsed>0.20 or obj._snapshot_shared_state_lock_skips<1:
        raise SystemExit(f'Bounded shared-state local-lock refresh blocked or failed telemetry: ok={ok} elapsed={elapsed} skips={obj._snapshot_shared_state_lock_skips}')

# Runtime compaction: old successful evidence shrinks, but waiting/problem state
# and durable blacklists survive unchanged.
spec=importlib.util.spec_from_file_location('v3650_auto',AUTO)
auto=importlib.util.module_from_spec(spec); spec.loader.exec_module(auto)
class Dummy: pass
with tempfile.TemporaryDirectory(prefix='newzdeck-v3650-auto-') as td:
    eng=auto.MediaAutomationEngine(pathlib.Path(td),lambda x:x,lambda x:x,Dummy(),lambda:[],version='3.6.69')
    now=time.time(); old=now-8*86400
    rt={'targets':{
      'done':{'status':'imported','updated_ts':old,'last_candidates':[{'title':f'Candidate {i}'} for i in range(8)],'attempted_releases':[{'guid':'old','ts':old}],'blacklist':[{'guid':'bad','failed_ts':old}]},
      'wait':{'status':'waiting','updated_ts':old,'last_candidates':[{'title':f'Wait {i}'} for i in range(8)],'blacklist':[{'guid':'keep','failed_ts':old}]},
    }}
    eng._save_auto_runtime(rt); saved=json.loads(eng.automation_runtime_file.read_text(encoding='utf-8'))['targets']
    if len(saved['done'].get('last_candidates') or [])!=1 or 'attempted_releases' in saved['done'] or not saved['done'].get('candidate_history_compacted'):
        raise SystemExit(f'Old successful target was not compacted safely: {saved["done"]}')
    if len(saved['wait'].get('last_candidates') or [])!=8 or len(saved['wait'].get('blacklist') or [])!=1:
        raise SystemExit('Waiting/problem target evidence was compacted unexpectedly.')
    if len(saved['done'].get('blacklist') or [])!=1:
        raise SystemExit('Durable failed-release blacklist was lost during compaction.')
    compacted_ts=float(saved['done'].get('candidate_history_compacted_ts') or 0)
    eng._save_auto_runtime(saved and {'targets':saved})
    saved_again=json.loads(eng.automation_runtime_file.read_text(encoding='utf-8'))['targets']
    if float(saved_again['done'].get('candidate_history_compacted_ts') or 0)!=compacted_ts:
        raise SystemExit('Already-compacted Automation evidence churned its compaction timestamp on a later save.')

installer=INSTALLER.read_text(encoding='utf-8')
for marker in ('Type: files; Name: "{app}\\NewzDeckBootstrap.exe"','Type: files; Name: "{app}\\NewzDeckCore.exe"'):
    if marker not in installer: raise SystemExit(f'Missing retired-binary installer cleanup: {marker}')
workflow=WORKFLOW.read_text(encoding='utf-8')
if 'python release/windows/validate-v3650-regressions.py' not in workflow:
    raise SystemExit('Release workflow does not run v3.6.50 regression guard.')
print('v3.6.50 regression guard passed (bounded local/file ledger refresh + deferred state persistence + Queue/History sampler + stable runtime compaction + installer cleanup).')
