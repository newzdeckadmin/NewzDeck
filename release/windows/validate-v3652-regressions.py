#!/usr/bin/env python3
"""NewzDeck v3.6.68 scope-native projection / probe-efficiency guards."""
from __future__ import annotations
import ast
import importlib.util
import pathlib
import tempfile
import threading
import time
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "app"
SAB = APP / "sab_engine.py"
WORKFLOW = ROOT / ".github" / "workflows" / "publish-release-trigger.yml"

sab_source = SAB.read_text(encoding="utf-8")
for marker in (
    'ADAPTER_VERSION = "3.6.68"',
    'def snapshot(self, scope: str = "all")',
    'snap=self.snapshot(scope="live" if mode=="live" else "all")',
    'def _snapshot_uncached(self, scope_mode: str = "all")',
    'scope-native Live projection',
    'snapshot_scope_native_live_builds',
    'snapshot_scope_native_terminal_skips',
    'snapshot_scope_native_last_projected_jobs',
    'scope_native_projection',
    'self._sab_version_current_recheck_seconds = 300.0',
    'sab_version_probe_cooldown_skips',
):
    if marker not in sab_source:
        raise SystemExit(f"Missing v3.6.68 runtime marker: {marker}")

# Structural guard: presentation state access is a single try-lock with no retry,
# sleep, disk read, JSON parse or cross-process file lock.
tree = ast.parse(sab_source)
cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SabDownloadManager")
def fn(name: str):
    return next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)
refresh = fn("_refresh_shared_state_for_snapshot")
refresh_text = ast.get_source_segment(sab_source, refresh) or ""
if refresh_text.count("acquire(blocking=False)") != 1:
    raise SystemExit("v3.6.68 state gate is not exactly one non-blocking lock attempt.")
for forbidden in ("time.sleep", "state_file", "state_lock_file", "_json_read", "_state_file_guard", "_try_state_file_guard"):
    if forbidden in refresh_text:
        raise SystemExit(f"v3.6.68 presentation state gate contains forbidden work: {forbidden}")

# Structural guard: recent authenticated API success may bypass the sparse
# version boundary only after this generation has already proven the pinned SAB
# version. An unknown/older generation must still reach the upgrade boundary.
ensure_text = ast.get_source_segment(sab_source, fn("ensure_running")) or ""
recent_pos = ensure_text.find("self._last_api_success_ts > 0")
known_version_pos = ensure_text.find("self._running_sab_version == SAB_VERSION")
upgrade_pos = ensure_text.find("self._upgrade_running_sab_if_needed()")
if recent_pos < 0 or known_version_pos < 0 or upgrade_pos < 0 or recent_pos > upgrade_pos or known_version_pos > upgrade_pos:
    raise SystemExit("ensure_running does not gate recent-API bypass on a previously proven pinned SAB version.")
upgrade_text = ast.get_source_segment(sab_source, fn("_upgrade_running_sab_if_needed")) or ""
for marker in ("self._sab_version_upgrade_next_ts = now + self._sab_version_current_recheck_seconds", "self._sab_version_probe_cooldown_skips += 1"):
    if marker not in upgrade_text:
        raise SystemExit(f"Sparse SAB version boundary missing: {marker}")

spec = importlib.util.spec_from_file_location("v3652_sab", SAB)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

# Zero-wait state gate under contention.
gate = object.__new__(mod.SabDownloadManager)
gate.lock = threading.RLock()
gate._snapshot_shared_state_last_ms = 0.0
gate._snapshot_shared_state_max_ms = 0.0
gate._snapshot_shared_state_lock_skips = 0
gate._snapshot_shared_state_lock_skip_last_ts = 0.0
held = threading.Event(); release = threading.Event()
def holder():
    with gate.lock:
        held.set(); release.wait(1.0)
th = threading.Thread(target=holder, daemon=True); th.start()
if not held.wait(1.0):
    raise SystemExit("Could not hold state lock for zero-wait regression test.")
started = time.monotonic(); ok = gate._refresh_shared_state_for_snapshot(0.025); elapsed = time.monotonic() - started
release.set(); th.join(1.0)
if ok or elapsed > 0.05 or gate._snapshot_shared_state_lock_skips != 1:
    raise SystemExit(f"Zero-wait state gate failed: ok={ok} elapsed={elapsed:.4f}s skips={gate._snapshot_shared_state_lock_skips}")

# Recent successful authenticated SAB traffic may bypass full version probing only
# when this generation already proved that the running engine is the pinned version.
recent = object.__new__(mod.SabDownloadManager)
recent._last_api_success_ts = time.time()
recent._running_sab_version = mod.SAB_VERSION
recent._ensure_probe_miss_since = 99.0
recent._ensure_probe_miss_count = 4
recent._upgrade_running_sab_if_needed = lambda: (_ for _ in ()).throw(RuntimeError("version boundary must not run"))
if recent.ensure_running(blocking=True) is not True or recent._ensure_probe_miss_count != 0:
    raise SystemExit("Known-current SAB API success did not bypass version-boundary probing.")

# An unknown generation must not use recent traffic to suppress the identity/upgrade
# boundary, or a future NewzDeck release could keep an older SAB alive forever simply
# because the Queue sampler continues succeeding.
unknown = object.__new__(mod.SabDownloadManager)
unknown._last_api_success_ts = time.time()
unknown._running_sab_version = ""
unknown._ensure_probe_miss_since = 0.0
unknown._ensure_probe_miss_count = 0
unknown._last_api_success_ts = time.time()
unknown._upgrade_running_sab_if_needed = lambda: True
unknown._launch = lambda: None
if unknown.ensure_running(blocking=True) is not True:
    raise SystemExit("Unknown SAB generation did not reach the version/upgrade boundary.")

# Proving the current SAB version must establish a sparse recheck cooldown.
probe = object.__new__(mod.SabDownloadManager)
probe._sab_version_upgrade_next_ts = 0.0
probe._sab_version_current_recheck_seconds = 300.0
probe._sab_version_probe_cooldown_skips = 0
probe._running_sab_version = ""
probe._sab_version_upgrade_attempts = 0
probe._sab_version_upgrade_last_from = ""
probe._load_engine_identity = lambda: {"port": 65433, "api_key": "k"}
probe._port_available = lambda port: False
probe._probe_version = lambda port, timeout=0.8: mod.SAB_VERSION
probe._auth_kind = lambda port, key, timeout=0.8: "apikey"
now = time.time()
if probe._upgrade_running_sab_if_needed() is not False:
    raise SystemExit("Current SAB version unexpectedly requested an upgrade.")
if probe._sab_version_upgrade_next_ts < now + 250:
    raise SystemExit("Current SAB version did not establish the sparse recheck cooldown.")

# Scope-native production-shaped fixture: 250 SAB-History terminal jobs, 100
# older ledger-only imported completions, and 10 live jobs. Live must build only
# the 10 live cards and preserve the *visible* 250 Completed count without counting
# retired ledger-only history. Full Completed paging must remain unchanged.
with tempfile.TemporaryDirectory(prefix="newzdeck-v3652-scope-") as td:
    base = pathlib.Path(td)
    mgr = mod.SabDownloadManager(
        user_root=base / "user", app_dir=base / "app",
        download_dir_getter=lambda: base / "downloads", settings_getter=lambda: {},
        providers_getter=lambda: [], secret_unprotect=lambda value: value,
        parse_nzb=lambda raw, name: {}, start_threads=False,
    )
    now = time.time(); tracked = {}; history = []
    for i in range(250):
        nzo = f"completed-{i}"
        tracked[nzo] = {
            "id": nzo, "name": f"Completed {i}", "expected_bytes": 1000,
            "file_count": 1, "created_ts": now - i - 100,
            "terminal_status": "completed", "imported": True, "post_status": "completed",
        }
        history.append({"nzo_id": nzo, "filename": f"Completed {i}", "status": "Completed", "bytes": 1000, "completed": now - i})
    # Durable NewzDeck state intentionally outlives SAB History. These older
    # imported records must be skipped from Live projection *and* from visible
    # Completed counts, exactly as the established full presentation does.
    for i in range(100):
        nzo = f"retired-{i}"
        tracked[nzo] = {
            "id": nzo, "name": f"Retired {i}", "expected_bytes": 1000,
            "file_count": 1, "created_ts": now - i - 10000,
            "terminal_status": "completed", "imported": True, "post_status": "completed",
        }

    queue = []
    for i in range(10):
        nzo = f"live-{i}"
        tracked[nzo] = {"id": nzo, "name": f"Live {i}", "expected_bytes": 1024 * 1024, "file_count": 1, "created_ts": now + i, "priority": "normal"}
        queue.append({"nzo_id": nzo, "filename": f"Live {i}", "status": "Queued", "mb": 1, "mbleft": 1, "index": i, "nrof": 1})
    mgr.state["jobs"] = tracked
    mgr._sync_terminal_history_from_state(persist=False)
    mgr._publish_presentation_index()
    mgr._engine_status_cache = {"name": "SABnzbd", "version": mod.SAB_VERSION, "ready": True, "probe_ready": True, "port": 65433}
    mgr._engine_status_ts = now
    mgr._queue_and_history = types.MethodType(lambda self, live=False: (
        {"queue": {"slots": queue, "status": "Idle", "paused": False, "mbleft": 10, "kbpersec": 0, "_newzdeck_fresh": True}},
        {"history": {"slots": history, "_newzdeck_fresh": True}},
    ), mgr)
    mgr._provider_health_cached_snapshot = types.MethodType(lambda self: {
        "capacity": 0, "active_connections": 0, "runtime_state_known": True,
        "servers": [], "errors": [], "warnings": [], "provider_warnings": [],
        "engine_warnings": [], "engine_notices": [], "cache_source": "test", "cache_age_seconds": 0,
    }, mgr)
    mgr._recover_zero_socket_transfer = types.MethodType(lambda self, **kwargs: kwargs["health"], mgr)

    live = mgr.snapshot_view("live", limit=100)
    if len(live.get("jobs") or []) != 10:
        raise SystemExit(f"Live-native projection built terminal cards: {len(live.get('jobs') or [])}")
    if int((live.get("counts") or {}).get("completed") or 0) != 350:
        raise SystemExit(f"Live-native projection lost durable global Completed count: {live.get('counts')}")
    if not bool((live.get("view") or {}).get("scope_native_projection")):
        raise SystemExit(f"Live response is not marked scope-native: {live.get('view')}")
    tel = live.get("telemetry") or {}
    if int(tel.get("snapshot_scope_native_last_projected_jobs") or -1) != 10 or int(tel.get("snapshot_scope_native_terminal_skips") or 0) < 350:
        raise SystemExit(f"Scope-native projection telemetry is wrong: {tel}")

    completed = mgr.snapshot_view("completed", limit=50, offset=0)
    if len(completed.get("jobs") or []) != 50 or int((completed.get("view") or {}).get("total") or 0) != 350:
        raise SystemExit(f"Durable Completed history was damaged by Live-native projection: {completed.get('view')}")

if WORKFLOW.exists():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for guard in ("validate-v3650-regressions.py", "validate-v3651-regressions.py", "validate-v3652-regressions.py"):
        if f"python release/windows/{guard}" not in workflow:
            raise SystemExit(f"Release workflow does not run {guard}.")

print("v3.6.68 regression guard passed (scope-native Live projection + zero-wait state gate + sparse SAB version boundary).")
