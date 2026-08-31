from __future__ import annotations

import configparser
import contextlib
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable

SAB_VERSION = "5.1.1"
SAB_WINDOWS_X64_URL = "https://github.com/sabnzbd/sabnzbd/releases/download/5.1.1/SABnzbd-5.1.1-win64-bin.zip"
SAB_WINDOWS_X64_SHA256 = "2991b7d7500fe85394417fc7e3c416ff72631528c10cabf8db00bd0e44ee42d6"
ENGINE_STATE_VERSION = 2
AUTOMATION_MEDIA_EXTS = {".mkv", ".mp4", ".m4v", ".avi", ".mov", ".wmv", ".ts", ".m2ts", ".webm", ".mpg", ".mpeg"}

SMART_IMPORT_SOURCES = {"automation_grab", "manual_media_grab"}

def _sab_text(value: Any) -> str:
    """Return the most useful human-readable string from a SAB API field."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        for item in reversed(value):
            text = _sab_text(item)
            if text:
                return text
        return ""
    if isinstance(value, dict):
        for key in ("text", "message", "detail", "status"):
            text = _sab_text(value.get(key))
            if text:
                return text
        return ""
    return str(value).strip() if value is not None else ""

def _sab_post_progress(slot: dict[str, Any], fallback_stage: str = "") -> tuple[str, int, bool, str]:
    """Translate SAB's live action_line into NewzDeck post-processing progress.

    SAB 5.x intentionally exposes current post-processing work through ``action_line``
    (for example ``Verifying: 03/12`` or ``Unpacking: 04/18 00:31``) rather
    than a dedicated percentage field.  Parse only explicit percentages/fractions;
    stages without measurable counters stay indeterminate rather than inventing progress.
    """
    raw = _sab_text(slot.get("action_line"))
    action = ""
    detail = ""
    if raw:
        if ":" in raw:
            action, detail = (part.strip() for part in raw.split(":", 1))
        else:
            detail = raw.strip()
    low_action = action.casefold()
    low_detail = detail.casefold()
    stage = str(fallback_stage or "").strip()
    if "direct unpack" in low_action or "unpack" in low_action or "extract" in low_action:
        stage = "extracting"
    elif "verifying repair" in low_action:
        stage = "repairing"
    elif "repair" in low_action:
        stage = "verifying" if "quick check" in low_detail else "repairing"
    elif "fetching" in low_action:
        stage = "repairing"
    elif "verify" in low_action or "checking" in low_action:
        stage = "verifying"
    elif "moving" in low_action or "running script" in low_action:
        stage = "importing"

    progress = 0
    known = False
    source = detail or raw
    if source:
        percent = re.search(r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*%", source)
        if percent:
            progress = max(0, min(100, int(round(float(percent.group(1))))))
            known = True
        else:
            fraction = re.search(r"(?<!\d)(\d+)\s*/\s*(\d+)", source)
            if fraction:
                current, total = int(fraction.group(1)), int(fraction.group(2))
                if total > 0:
                    progress = max(0, min(100, int(round(current * 100.0 / total))))
                    known = True
    if source.casefold() == "completed":
        progress, known = 100, True

    message = raw or _sab_text(slot.get("stage_log")) or _sab_text(slot.get("status"))
    return stage, progress, known, message

def _is_smart_import_context(context: dict[str, Any] | None) -> bool:
    return isinstance(context, dict) and str(context.get("source") or "") in SMART_IMPORT_SOURCES


def _atomic_json_write(path: Path, value: Any) -> None:
    """Atomically replace a local JSON state file, tolerating brief Windows sharing locks.

    Windows can reject ``os.replace`` with ERROR_ACCESS_DENIED/ERROR_SHARING_VIOLATION
    when another NewzDeck thread has the old JSON file open for a very short read.
    The state files are tiny, so retrying only those transient sharing errors avoids
    turning a harmless read/write overlap into a failed SAB completion/import cycle.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}-{threading.get_ident()}-{uuid.uuid4().hex[:8]}")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        for attempt in range(20):
            try:
                os.replace(temp, path)
                return
            except PermissionError as exc:
                winerror = getattr(exc, "winerror", None)
                if os.name != "nt" or winerror not in {5, 32} or attempt >= 19:
                    raise
                time.sleep(min(0.01 * (attempt + 1), 0.08))
    finally:
        try:
            if temp.exists():
                temp.unlink()
        except OSError:
            pass


def _json_read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _json_read_retry(path: Path, default: Any, *, attempts: int = 20, strict_existing: bool = False) -> Any:
    """Read JSON without treating a transient Windows sharing/partial-read failure as missing state."""
    path = Path(path)
    existed = path.exists()
    last: Exception | None = None
    for attempt in range(max(1, int(attempts))):
        try:
            if not path.exists():
                if existed and strict_existing:
                    raise FileNotFoundError(str(path))
                return default
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            last = exc
            if attempt + 1 >= max(1, int(attempts)):
                break
            time.sleep(min(0.01 * (attempt + 1), 0.08))
    if strict_existing and existed:
        raise RuntimeError(f"Could not read existing state file {path.name} after retries: {last}")
    return default


def _clamp_int(value: Any, low: int, high: int, default: int = 0) -> int:
    try:
        return max(low, min(high, int(float(value))))
    except (TypeError, ValueError):
        return default


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        return float(value)
    except (TypeError, ValueError):
        return default


def _mb_to_bytes(value: Any) -> int:
    return max(0, int(_num(value) * 1024 * 1024))


def _kb_to_bps(value: Any) -> int:
    return max(0, int(_num(value) * 1024))


def _duration_seconds(value: Any) -> int:
    """Parse SAB-style H:MM:SS / D:HH:MM:SS duration strings."""
    text = str(value or "").strip()
    if not text or text.casefold() in {"unknown", "none", "-", "—"}:
        return 0
    try:
        if ":" not in text:
            return max(0, int(float(text)))
        parts = [int(float(x or 0)) for x in text.split(":")]
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return max(0, hours * 3600 + minutes * 60 + seconds)
        if len(parts) == 4:
            days, hours, minutes, seconds = parts
            return max(0, days * 86400 + hours * 3600 + minutes * 60 + seconds)
    except (TypeError, ValueError):
        return 0
    return 0


def _safe_name(value: str, fallback: str = "NewzDeck Download") -> str:
    text = str(value or "").strip()
    for char in '<>:"/\\|?*':
        text = text.replace(char, "_")
    text = " ".join(text.split()).strip(" .")
    return (text[:180] or fallback)



def _automation_identity(context: dict[str, Any] | None) -> tuple[str, str, str]:
    """Return human-readable target, original release and planned library root.

    SAB payload filenames are often intentionally obfuscated. The Downloads UI must
    therefore describe Automation work from the preserved release/target context,
    never from the payload filename alone.
    """
    ctx = context if isinstance(context, dict) else {}
    if not _is_smart_import_context(ctx):
        return "", "", ""
    title = str(ctx.get("title") or "TV/Movies").strip() or "TV/Movies"
    kind = str(ctx.get("kind") or "")
    label = title
    if kind == "tv" and ctx.get("season") is not None:
        try:
            season = int(ctx.get("season") or 0)
        except (TypeError, ValueError):
            season = 0
        if bool(ctx.get("season_pack")) or ctx.get("episode") is None:
            label = f"{title} • Season {season}"
        else:
            try:
                episode = int(ctx.get("episode") or 0)
            except (TypeError, ValueError):
                episode = 0
            label = f"{title} • S{season:02d}E{episode:02d}"
            ep_title = str(ctx.get("episode_title") or "").strip()
            if ep_title:
                label += f" • {ep_title}"
    release = str(ctx.get("release_title") or "").strip()
    root = str(ctx.get("planned_root_folder") or "").strip()
    return label, release, root

def _xml_text(value: str) -> str:
    return str(value or "").strip().strip("<>")


def build_nzb_bytes(name: str, entries: list[dict[str, Any]], password: str = "") -> bytes:
    """Create a standard NZB from NewzDeck's normalized article entries."""
    ns = "http://www.newzbin.com/DTD/2003/nzb"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}nzb")
    head = ET.SubElement(root, f"{{{ns}}}head")
    meta = ET.SubElement(head, f"{{{ns}}}meta", {"type": "title"})
    meta.text = _safe_name(name)
    if password:
        pw = ET.SubElement(head, f"{{{ns}}}meta", {"type": "password"})
        pw.text = str(password)
    usable = 0
    for index, entry in enumerate(entries):
        media = entry.get("media") if isinstance(entry.get("media"), dict) else {}
        filename = str(media.get("filename") or entry.get("filename") or f"file-{index+1}.bin")
        segments = entry.get("segments") if isinstance(entry.get("segments"), list) else []
        good_segments = []
        for seg in segments:
            if not isinstance(seg, dict):
                continue
            msgid = _xml_text(seg.get("message_id") or "")
            if not msgid:
                continue
            good_segments.append((
                max(1, _clamp_int(seg.get("part"), 1, 10_000_000, len(good_segments) + 1)),
                max(0, _clamp_int(seg.get("bytes"), 0, 2_147_483_647, 0)),
                msgid,
            ))
        if not good_segments:
            continue
        good_segments.sort(key=lambda x: x[0])
        subject = str(entry.get("subject") or f'"{filename}" yEnc ({len(good_segments)}/{len(good_segments)})')
        attrs = {
            "poster": str(entry.get("from") or entry.get("poster") or "NewzDeck"),
            "date": str(max(0, _clamp_int(entry.get("posted_ts"), 0, 4_000_000_000, int(time.time())))),
            "subject": subject,
        }
        fnode = ET.SubElement(root, f"{{{ns}}}file", attrs)
        groups = ET.SubElement(fnode, f"{{{ns}}}groups")
        raw_groups = entry.get("groups") if isinstance(entry.get("groups"), list) else []
        if not raw_groups and entry.get("group"):
            raw_groups = [entry.get("group")]
        for group in raw_groups or ["alt.binaries.multimedia"]:
            g = ET.SubElement(groups, f"{{{ns}}}group")
            g.text = str(group)
        snode = ET.SubElement(fnode, f"{{{ns}}}segments")
        for number, byte_count, msgid in good_segments:
            segnode = ET.SubElement(snode, f"{{{ns}}}segment", {"bytes": str(byte_count), "number": str(number)})
            segnode.text = msgid
        usable += 1
    if usable <= 0:
        raise ValueError("The selected articles do not contain Message-ID values that can be submitted to the download engine")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)



class _ExternalWindowsProcess:
    """Minimal Popen-like reference for a process brokered into the user session."""
    STILL_ACTIVE = 259
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    PROCESS_TERMINATE = 0x0001

    def __init__(self, pid: int):
        self.pid = int(pid)
        self.returncode = None

    @staticmethod
    def _kernel32():
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k32.GetExitCodeProcess.restype = wintypes.BOOL
        k32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        k32.TerminateProcess.restype = wintypes.BOOL
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        k32.CloseHandle.restype = wintypes.BOOL
        return k32

    def poll(self):
        if os.name != "nt":
            return self.returncode
        import ctypes
        k32 = self._kernel32()
        handle = k32.OpenProcess(self.PROCESS_QUERY_LIMITED_INFORMATION, False, self.pid)
        if not handle:
            self.returncode = 0
            return self.returncode
        try:
            from ctypes import wintypes
            code = wintypes.DWORD()
            if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return None
            if int(code.value) == self.STILL_ACTIVE:
                return None
            self.returncode = int(code.value)
            return self.returncode
        finally:
            k32.CloseHandle(handle)

    def terminate(self):
        if os.name != "nt":
            return
        k32 = self._kernel32()
        handle = k32.OpenProcess(self.PROCESS_TERMINATE, False, self.pid)
        if handle:
            try:
                k32.TerminateProcess(handle, 1)
            finally:
                k32.CloseHandle(handle)

    kill = terminate

    def wait(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + float(timeout)
        while True:
            rc = self.poll()
            if rc is not None:
                return rc
            if deadline is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(str(self.pid), timeout)
            time.sleep(0.05)

class SabDownloadManager:
    """NewzDeck Download Engine v2 adapter around a private SABnzbd instance.

    NewzDeck owns the visible queue metadata and Automation context. SABnzbd owns
    NNTP transfer, article caching, yEnc, repair and unpack. The engine is bound
    to localhost and provisioned from the official Windows portable release.
    """

    def __init__(self, *, user_root: Path, app_dir: Path, download_dir_getter: Callable[[], Path],
                 settings_getter: Callable[[], dict[str, Any]], providers_getter: Callable[[], list[dict[str, Any]]],
                 secret_unprotect: Callable[[str], str], parse_nzb: Callable[[bytes, str], dict[str, Any]],
                 diagnostics: Any = None, legacy_statistics_file: Path | None = None, start_threads: bool = True,
                 keep_engine_running: Callable[[], bool] | None = None,
                 process_launcher: Callable[[Path, list[str], Path, Path], dict[str, Any]] | None = None):
        self.user_root = Path(user_root)
        self.app_dir = Path(app_dir)
        self.download_dir_getter = download_dir_getter
        self.settings_getter = settings_getter
        self.providers_getter = providers_getter
        self.secret_unprotect = secret_unprotect
        self.parse_nzb = parse_nzb
        self.diagnostics = diagnostics
        self.legacy_statistics_file = legacy_statistics_file
        legacy_raw = _json_read(legacy_statistics_file, {}) if legacy_statistics_file else {}
        self.legacy_statistics = dict(legacy_raw.get("statistics") or {}) if isinstance(legacy_raw, dict) and isinstance(legacy_raw.get("statistics"), dict) else {}
        self.keep_engine_running = keep_engine_running or (lambda: False)
        self.process_launcher = process_launcher

        self.root = self.user_root / "sab-engine"
        self.engine_dir = self.root / SAB_VERSION
        self.admin_dir = self.root / "admin"
        self.legacy_admin_dir = self.root / "admin"
        self.incoming_dir = self.root / "incoming"
        self.incomplete_dir = self.root / "incomplete"
        self.cache_dir = self.root / "cache"
        self.state_file = self.root / "newzdeck-jobs.json"
        self.state_lock_file = self.root / ".newzdeck-jobs.lock"
        self.engine_state_file = self.root / "engine.json"
        self.identity_history_file = self.root / "engine-identities.json"
        self.identity_lock_file = self.root / ".engine-identity.lock"
        self.bootstrap_lock_file = self.root / ".bootstrap.lock"
        self.launch_lock_file = self.root / ".engine-start.lock"
        self.config_file = self.admin_dir / "sabnzbd.ini"
        for d in (self.root, self.admin_dir, self.incoming_dir, self.incomplete_dir, self.cache_dir):
            d.mkdir(parents=True, exist_ok=True)
        self._cleanup_stale_identity_temps()

        raw = _json_read(self.state_file, {})
        self.state = raw if isinstance(raw, dict) else {}
        self.state.setdefault("version", ENGINE_STATE_VERSION)
        self.state.setdefault("paused", False)
        self.state.setdefault("jobs", {})
        self.state.setdefault("statistics", {})
        self.state.setdefault("completed_imports", {})
        self.state.setdefault("removed_jobs", {})
        self.state.setdefault("removed_job_reasons", {})
        self.state.setdefault("_paused_updated_ts", 0.0)
        self.lock = threading.RLock()
        # engine.json is shared by the UI polling, SAB coordination and completion
        # threads.  Serializing identity normalization prevents Windows read/replace
        # races from starving the Automation completion monitor.
        self._identity_lock = threading.RLock()
        self.shutdown_event = threading.Event()
        self.sync_event = threading.Event()
        self.media_automation = None
        self._process: subprocess.Popen | _ExternalWindowsProcess | None = None
        self._last_error = ""
        self._last_ready_ts = 0.0
        # v3.5.11: a single slow localhost heartbeat must never remap a finished
        # history item back into a synthetic Queued placeholder. Keep the download
        # engine logically ready through a short probe grace window; if the queue
        # API also times out, snapshot() simply returns the last coherent view.
        self._engine_unready_since = 0.0
        self._engine_probe_grace_seconds = 8.0
        # The Downloads live path already probes SAB Queue frequently. Cache the
        # heavier identity/auth heartbeat so 250 ms UI refreshes do not perform
        # redundant version/auth requests four times per second.
        self._engine_status_cache: dict[str, Any] = {}
        self._engine_status_ts = 0.0
        self._last_snapshot: dict[str, Any] | None = None
        self._last_snapshot_ts = 0.0
        # v3.5.37 Live Downloads: serialize snapshot generation so fast foreground
        # polling never launches overlapping Queue/History reads that can complete
        # out of order. The browser can poll at 250 ms while most requests are
        # served from this short-lived coherent snapshot.
        self._snapshot_lock = threading.Lock()
        self._snapshot_cache_seconds = 0.22
        self._snapshot_sequence = 0
        # v3.6.20: all NewzDeck -> SAB HTTP requests share one transport lock.
        # The anonymized SAB log proved SAB itself stayed alive and downloaded while
        # NewzDeck saw WinError 10054 from overlapping localhost control requests.
        # Serialize control-plane traffic and make Queue/History freshness explicit.
        self._sab_transport_lock = threading.RLock()
        self._queue_history_lock = threading.RLock()
        self._last_good_queue_payload: dict[str, Any] | None = None
        self._last_good_queue_ts = 0.0
        self._last_good_history_payload: dict[str, Any] | None = None
        self._last_good_history_ts = 0.0
        self._last_coherent_sab_snapshot_ts = 0.0
        self._sab_read_resets = 0
        self._sab_read_stale_uses = 0
        self._sab_control_degraded_snapshots = 0
        self._sab_stale_snapshot_suppressed = 0
        # Queue is the live data plane. History changes much less often, so cache it
        # briefly and refresh immediately when a queue id disappears (the normal
        # Queue -> History handoff). This keeps live progress responsive without
        # hammering SAB's History API four times per second.
        self._live_history_payload: dict[str, Any] | None = None
        self._live_history_fetch_ts = 0.0
        self._live_queue_ids: set[str] = set()
        # SAB queue snapshots can briefly report the foreground job as Queued, or
        # omit a slot for one poll while its internal queue is being reshaped. Keep
        # a short presentation latch so NewzDeck does not flicker Active/Queued
        # even though the underlying transfer never stopped.
        self._job_last_seen_ts: dict[str, float] = {}
        self._job_last_view: dict[str, dict[str, Any]] = {}
        self._active_latch_until: dict[str, float] = {}
        self._job_missing_since: dict[str, float] = {}
        # Consecutive queued observations are used only for presentation stability.
        # A previously-active package must be coherently observed as queued several
        # times before NewzDeck removes it from Active, unless another package has
        # clearly become SAB's foreground transfer.
        self._job_queued_observations: dict[str, int] = {}
        # v3.6.13: once SAB has positively proven that a package is the live
        # transfer owner, keep that ownership stable across longer all-zero / Queued
        # presentation gaps. SAB can spend more than the old 8-second latch reshaping
        # its queue at file boundaries while the transfer itself continues. A job is
        # demoted immediately when SAB explicitly pauses it, exposes a terminal history
        # record, or clearly moves a different package into the foreground. Otherwise
        # a bounded continuity lease prevents the Active card from disappearing.
        self._job_active_confirmed_ts: dict[str, float] = {}
        self._active_continuity_seconds = 35.0
        self._active_bridge_open: set[str] = set()
        self._active_continuity_bridges = 0
        self._active_continuity_last_ts = 0.0
        # v3.6.20: SAB can briefly report the *whole queue* as Paused during
        # internal queue/file transitions even though NewzDeck never requested a
        # pause and the underlying transfer resumes moments later. The older Active
        # continuity lease intentionally treats any pause as authoritative, so that
        # one transient aggregate sample could still empty the Active tab. Keep a
        # separate bounded presentation bridge keyed to NewzDeck's own pause intent.
        self._unexpected_sab_pause_since = 0.0
        self._unexpected_sab_pause_bridge_open = False
        self._unexpected_sab_pause_bridges = 0
        self._unexpected_sab_pause_last_ts = 0.0
        self._unexpected_sab_pause_grace_seconds = 12.0
        self._unexpected_sab_pause_last_resume_request_ts = 0.0
        self._resume_intent_event = threading.Event()
        # v3.6.20 canonical Downloads-state invariants.
        # SAB aggregate counters are retained for diagnostics, but user-facing
        # Remaining/counts are derived from the same visible job set as the cards.
        self._snapshot_consistency_mismatches = 0
        self._snapshot_consistency_last_ts = 0.0
        self._engine_pause_mismatch_since = 0.0
        self._engine_pause_reassert_count = 0
        self._engine_pause_reassert_last_ts = 0.0
        self._import_dead_owner_reclaims = 0
        self._import_dead_owner_last_ts = 0.0
        # v3.6.13: an explicit Remove/Cancel must not hide a card until SAB has
        # actually stopped owning that NZO id. Earlier code treated the localhost
        # delete call as best-effort, immediately tombstoned the NewzDeck record,
        # and could therefore leave a hidden SAB transfer consuming bandwidth.
        self._removed_cleanup_attempt_ts: dict[str, float] = {}
        self._orphan_removed_cleanup_count = 0
        self._orphan_removed_cleanup_last_ts = 0.0
        # Terminal SAB failures need to feed back into Interactive Search promptly.
        # Keep an in-process guard as well as a persisted per-job flag so the UI poll
        # and completion thread can both observe a fast failure without duplicate work.
        self._failed_release_feedback_seen: set[str] = set()
        self._last_sync_signature = ""
        # v3.6.20: do not let a transient localhost control-plane miss become a
        # disruptive private-engine/configuration recovery. SAB's data plane can be
        # perfectly healthy while one HTTP probe times out under load.
        self._last_api_success_ts = 0.0
        self._ensure_probe_miss_since = 0.0
        self._ensure_probe_miss_count = 0
        self._ensure_transient_probe_misses = 0
        self._ensure_recovery_deferred = 0
        self._ensure_launch_recoveries = 0
        self._config_sync_attempts = 0
        self._config_sync_failures = 0
        self._config_retry_storms_suppressed = 0
        self._config_sync_last_error_ts = 0.0
        self._multiple_active_slot_corrections = 0
        self._multiple_active_slot_last_ts = 0.0
        self._progress_regression_corrections = 0
        self._progress_regression_last_ts = 0.0
        # v3.6.20: one authoritative private SAB identity. Historical identities
        # are retirement credentials only and may never be adopted into engine.json.
        self._identity_cross_adoptions_blocked = 0
        self._identity_authoritative_key_repairs = 0
        self._stale_engine_quarantine_last_ts = 0.0
        self._stale_engine_ports_seen = 0
        self._stale_engine_live_slots_paused = 0
        self._stale_engines_shutdown = 0
        self._stale_engine_last_port = 0
        self._stale_engine_last_slots = 0
        self._stale_duplicate_queue_cleanups = 0
        self._stale_duplicate_queue_last_ts = 0.0
        self._completion_control_failures = 0
        self._completion_backoff_seconds = 2.0
        self._completion_last_warning_ts = 0.0
        self._engine_fault = ""
        self._engine_fault_last_ts = 0.0
        self._engine_fault_last_logged = ""
        # v3.5.7: keep a lightweight view of SAB's *real* server/socket state.
        # v3.5.5 rendered configured connection capacity as if every socket were
        # active, which hid the exact failure mode where SAB had a Downloading
        # queue entry but zero live NNTP connections.
        self._provider_health_cache: dict[str, Any] = {}
        self._provider_health_ts = 0.0
        self._provider_health_success_ts = 0.0
        self._provider_unblock_after: dict[str, float] = {}
        self._zero_socket_since = 0.0
        self._last_stall_repair_ts = 0.0
        # v3.5.9: SAB can legitimately drop to zero live sockets for a few seconds
        # while it rolls between files/articles or reconnects a provider socket.
        # Recovery must be driven by sustained *lack of queue progress*, not a
        # single zero-socket sample, otherwise NewzDeck's own repair routine can
        # interrupt an otherwise healthy transfer.
        self._last_queue_remaining: int | None = None
        self._last_queue_progress_ts = time.time()
        self._provider_probe_fail_count = 0
        self._provider_sync_errors: list[str] = []
        # v3.5.7: distinguish three different provider states: settings saved in
        # SAB's config, a runtime Downloader server actually loaded, and a provider
        # credential/connection test that can open a real NNTP session. v3.5.6 only
        # inspected the runtime status list, so an empty/missing runtime server could
        # produce zero sockets with no useful error text.
        self._provider_probe_cache: dict[str, Any] = {}
        self._provider_probe_ts = 0.0
        self._last_forced_restart_ts = 0.0
        self._engine_recovery_lock = threading.Lock()
        # v3.5.10 presentation telemetry: SAB's instantaneous kbpersec and live
        # socket count legitimately touch zero during article/file handoffs. Keep a
        # short rolling transfer estimate based on actual remaining-byte progress so
        # the NewzDeck UI reports a useful speed/ETA instead of flashing blank.
        self._telemetry_last_sample_ts = 0.0
        self._telemetry_last_remaining: int | None = None
        self._telemetry_smoothed_bps = 0.0
        self._telemetry_last_positive_ts = 0.0
        self._telemetry_last_live_connections = 0
        self._telemetry_last_live_connections_ts = 0.0
        self._telemetry_active_until = 0.0
        self._provisioning = False
        self._download_progress: dict[str, Any] = {"active": False, "bytes": 0, "total": 0, "started": 0.0}
        self._engine_thread = None
        self._completion_thread = None
        self._background_threads_lock = threading.Lock()
        self._import_kick_lock = threading.Lock()
        self._import_kick_inflight: set[str] = set()
        if start_threads:
            self.start_background_threads()

    def start_background_threads(self) -> None:
        """Start SAB coordination workers once, after the local HTTP server is ready.

        v3.5.34 decouples localhost/UI readiness from SAB identity probing and
        completion reconciliation. These workers remain asynchronous exactly as
        before; only their start point moves out of module import.
        """
        with self._background_threads_lock:
            if self.shutdown_event.is_set():
                return
            if self._engine_thread is None or not self._engine_thread.is_alive():
                self._engine_thread = threading.Thread(target=self._engine_loop, name="newzdeck-sab-engine", daemon=True)
                self._engine_thread.start()
            if self._completion_thread is None or not self._completion_thread.is_alive():
                self._completion_thread = threading.Thread(target=self._completion_loop, name="newzdeck-sab-completion", daemon=True)
                self._completion_thread.start()

    def _event(self, level: str, message: str, **details: Any) -> None:
        try:
            if self.diagnostics is not None:
                self.diagnostics.event(level, "sab-engine", message, **details)
        except Exception:
            pass

    def _cleanup_stale_identity_temps(self) -> None:
        cutoff = time.time() - 30.0
        removed = 0
        for pattern in ("engine.json.tmp-*", "engine-identities.json.tmp-*", "engine.json.*.tmp", "engine-identities.json.*.tmp"):
            try:
                candidates = list(self.root.glob(pattern))
            except OSError:
                candidates = []
            for temp in candidates:
                try:
                    if temp.stat().st_mtime > cutoff:
                        continue
                    temp.unlink()
                    removed += 1
                except OSError:
                    pass
        if removed:
            self._event("info", f"Cleaned {removed} stale SAB identity temp file(s)")

    @contextlib.contextmanager
    def _identity_file_guard(self):
        self.identity_lock_file.parent.mkdir(parents=True, exist_ok=True)
        fh = self.identity_lock_file.open("a+b")
        try:
            fh.seek(0, os.SEEK_END)
            if fh.tell() <= 0:
                fh.write(b"0")
                fh.flush()
            fh.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()

    @contextlib.contextmanager
    def _state_file_guard(self):
        """Cross-process lock for the SAB/NewzDeck tracking ledger."""
        self.state_lock_file.parent.mkdir(parents=True, exist_ok=True)
        fh = self.state_lock_file.open("a+b")
        try:
            fh.seek(0, os.SEEK_END)
            if fh.tell() <= 0:
                fh.write(b"0")
                fh.flush()
            fh.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()

    @staticmethod
    def _normalize_state_value(raw: Any) -> dict[str, Any]:
        out = dict(raw) if isinstance(raw, dict) else {}
        out.setdefault("version", ENGINE_STATE_VERSION)
        out["jobs"] = dict(out.get("jobs") or {}) if isinstance(out.get("jobs"), dict) else {}
        out["statistics"] = dict(out.get("statistics") or {}) if isinstance(out.get("statistics"), dict) else {}
        out["completed_imports"] = dict(out.get("completed_imports") or {}) if isinstance(out.get("completed_imports"), dict) else {}
        out["removed_jobs"] = dict(out.get("removed_jobs") or {}) if isinstance(out.get("removed_jobs"), dict) else {}
        out["removed_job_reasons"] = dict(out.get("removed_job_reasons") or {}) if isinstance(out.get("removed_job_reasons"), dict) else {}
        out["paused"] = bool(out.get("paused", False))
        out["_paused_updated_ts"] = float(out.get("_paused_updated_ts") or 0.0)
        return out

    @staticmethod
    def _job_state_stamp(rec: Any) -> float:
        if not isinstance(rec, dict):
            return 0.0
        return max(
            _num(rec.get("_updated_ts"), 0),
            _num(rec.get("import_claim_ts"), 0),
            _num(rec.get("created_ts"), 0),
        )

    def _merge_shared_states(self, disk_raw: Any, memory_raw: Any) -> dict[str, Any]:
        disk = self._normalize_state_value(disk_raw)
        memory = self._normalize_state_value(memory_raw)
        merged = dict(disk)

        jobs: dict[str, Any] = {}
        all_ids = set(disk["jobs"]) | set(memory["jobs"])
        for nzo_id in all_ids:
            a = disk["jobs"].get(nzo_id)
            b = memory["jobs"].get(nzo_id)
            if a is None:
                chosen = b
            elif b is None:
                chosen = a
            else:
                sa, sb = self._job_state_stamp(a), self._job_state_stamp(b)
                if sb > sa:
                    chosen = b
                elif sa > sb:
                    chosen = a
                else:
                    score_a = int(bool((a or {}).get("automation_context"))) + int(bool((a or {}).get("import_status"))) + len(a or {})
                    score_b = int(bool((b or {}).get("automation_context"))) + int(bool((b or {}).get("import_status"))) + len(b or {})
                    chosen = b if score_b >= score_a else a
            if isinstance(chosen, dict):
                jobs[str(nzo_id)] = dict(chosen)

        removed: dict[str, float] = {}
        for src in (disk.get("removed_jobs", {}), memory.get("removed_jobs", {})):
            for nzo_id, ts in src.items():
                removed[str(nzo_id)] = max(float(removed.get(str(nzo_id), 0.0) or 0.0), _num(ts, 0))
        cutoff = time.time() - 7 * 86400
        removed = {k: v for k, v in removed.items() if v >= cutoff}
        removed_reasons: dict[str, str] = {}
        for src in (disk.get("removed_job_reasons", {}), memory.get("removed_job_reasons", {})):
            if not isinstance(src, dict):
                continue
            for nzo_id, reason in src.items():
                text = str(reason or "").strip()
                if text:
                    removed_reasons[str(nzo_id)] = text
        for nzo_id, ts in list(removed.items()):
            rec = jobs.get(nzo_id)
            if rec is None:
                continue
            stamp = self._job_state_stamp(rec)
            if ts >= stamp:
                jobs.pop(nzo_id, None)
            else:
                # A newer real ownership record supersedes an older tombstone. This is
                # important when v3.6.13 recovers a job that an older build incorrectly
                # auto-pruned while SAB was still downloading it.
                removed.pop(nzo_id, None)
                removed_reasons.pop(nzo_id, None)

        merged["jobs"] = jobs
        merged["removed_jobs"] = removed
        merged["removed_job_reasons"] = {k: v for k, v in removed_reasons.items() if k in removed}

        if float(memory.get("_paused_updated_ts") or 0) >= float(disk.get("_paused_updated_ts") or 0):
            merged["paused"] = bool(memory.get("paused", False))
            merged["_paused_updated_ts"] = float(memory.get("_paused_updated_ts") or 0)
        else:
            merged["paused"] = bool(disk.get("paused", False))
            merged["_paused_updated_ts"] = float(disk.get("_paused_updated_ts") or 0)

        stats = dict(disk.get("statistics") or {})
        for key, val in (memory.get("statistics") or {}).items():
            if isinstance(val, (int, float)) and isinstance(stats.get(key), (int, float)):
                stats[key] = max(stats[key], val)
            elif key not in stats:
                stats[key] = val
        merged["statistics"] = stats
        merged["completed_imports"] = {**dict(disk.get("completed_imports") or {}), **dict(memory.get("completed_imports") or {})}
        merged["version"] = max(int(disk.get("version") or ENGINE_STATE_VERSION), int(memory.get("version") or ENGINE_STATE_VERSION))
        return merged

    def _refresh_shared_state(self) -> None:
        """Refresh this process from the canonical cross-process tracking ledger."""
        with self.lock:
            with self._state_file_guard():
                disk = _json_read(self.state_file, {})
                self.state = self._merge_shared_states(disk, self.state)

    def _save_state(self) -> None:
        """Merge and save without allowing another NewzDeck runtime to clobber jobs."""
        with self.lock:
            with self._state_file_guard():
                disk = _json_read(self.state_file, {})
                merged = self._merge_shared_states(disk, self.state)
                _atomic_json_write(self.state_file, merged)
                self.state = merged

    def _mark_removed_locked(self, nzo_id: str, reason: str = "user") -> None:
        removed = self.state.setdefault("removed_jobs", {})
        removed[str(nzo_id)] = time.time()
        reasons = self.state.setdefault("removed_job_reasons", {})
        reasons[str(nzo_id)] = str(reason or "user")

    @staticmethod
    def _sab_mutation_accepted(result: Any) -> bool:
        """Treat an explicit SAB status=false response as a failed mutation."""
        if not isinstance(result, dict):
            return True
        status = result.get("status")
        if status is False or str(status).strip().casefold() in {"false", "0", "no"}:
            return False
        return not bool(result.get("error"))

    @staticmethod
    def _slot_ids(slots: list[dict[str, Any]]) -> set[str]:
        return {
            str(x.get("nzo_id") or x.get("id") or "")
            for x in slots if isinstance(x, dict) and str(x.get("nzo_id") or x.get("id") or "")
        }

    def _delete_sab_job_verified(self, nzo_id: str, *, delete_files: bool = True) -> tuple[bool, str]:
        """Stop/delete one SAB job and prove a live transfer is gone before hiding it.

        v3.6.20 hardens terminal-history removal as well as live queue removal:
        transient localhost API reads are retried, a terminal Failed/Completed
        history record can prove that the job is no longer transferring when Queue
        itself is briefly unreadable, and history cleanup remains secondary to the
        safety invariant that a live queue job must not be hidden.
        """
        nzo_id = str(nzo_id or "").strip()
        if not nzo_id:
            return False, "Missing SAB job id"

        # A busy SAB localhost API can briefly miss one ping while downloads remain
        # healthy. Give verified user control a small retry window before failing.
        ready = False
        for attempt in range(3):
            if self._ping(timeout=0.9):
                ready = True
                break
            if attempt < 2:
                time.sleep(0.12 * (attempt + 1))
        if not ready:
            self.sync_event.set()
            return False, "Built-in download engine is reconnecting; the download was not removed"

        def read_slots(mode: str, attempts: int = 3) -> tuple[list[dict[str, Any]] | None, str]:
            last_error = ""
            for attempt in range(max(1, attempts)):
                try:
                    payload = self._api(mode, start=0, limit=500, timeout=2.2)
                    if mode == "queue":
                        _root, slots = self._queue_slots(payload)
                    else:
                        _root, slots = self._history_slots(payload)
                    return list(slots or []), ""
                except Exception as exc:
                    last_error = str(exc)
                    if attempt + 1 < max(1, attempts):
                        time.sleep(0.12 * (attempt + 1))
            return None, last_error

        qslots, queue_error = read_slots("queue", attempts=3)
        hslots, history_error = read_slots("history", attempts=2)
        history_slot = next(
            (x for x in (hslots or []) if str(x.get("nzo_id") or x.get("id") or "") == nzo_id),
            None,
        )
        history_status = str((history_slot or {}).get("status") or "").strip().casefold()
        terminal_history_proof = history_status in {"failed", "completed", "cancelled"}

        if qslots is None:
            # For a terminal SAB History entry, SAB itself has already declared the
            # transfer finished. That is sufficient safety proof to let the user
            # remove the failed/completed card even if Queue had one transient read
            # failure. Never use this shortcut for non-terminal state.
            if not terminal_history_proof:
                detail = f": {queue_error}" if queue_error else ""
                return False, f"Could not verify the SAB queue before removal{detail}"
            queue_present = False
            self._event(
                "warning",
                "Used terminal SAB history state to verify removal while Queue was temporarily unreadable",
                nzo_id=nzo_id,
                history_status=history_status,
                queue_error=queue_error[:300],
            )
        else:
            queue_present = nzo_id in self._slot_ids(qslots)

        if queue_present:
            last_error = ""
            for attempt in range(3):
                try:
                    result = self._api(
                        "queue", name="delete", value=nzo_id,
                        del_files=1 if delete_files else 0, timeout=4,
                    )
                    if not self._sab_mutation_accepted(result):
                        last_error = str(result.get("error") or result.get("status") or "SAB rejected queue deletion")
                    else:
                        last_error = ""
                except Exception as exc:
                    last_error = str(exc)

                deadline = time.monotonic() + 3.0
                while time.monotonic() < deadline:
                    verify_slots, verify_error = read_slots("queue", attempts=2)
                    if verify_slots is not None:
                        if nzo_id not in self._slot_ids(verify_slots):
                            queue_present = False
                            break
                    elif verify_error:
                        last_error = verify_error
                    time.sleep(0.18)
                if not queue_present:
                    break
                if attempt < 2:
                    time.sleep(0.20 * (attempt + 1))

            if queue_present:
                detail = f": {last_error}" if last_error else ""
                return False, f"SAB is still transferring this download after the remove request{detail}"

        # The live-transfer safety invariant is satisfied. History is presentation
        # state only, so cleanup is best-effort; a tombstone prevents an old history
        # row from being re-adopted if SAB rejects or delays that cleanup.
        if hslots is None and not terminal_history_proof:
            hslots, history_error = read_slots("history", attempts=2)
            history_slot = next(
                (x for x in (hslots or []) if str(x.get("nzo_id") or x.get("id") or "") == nzo_id),
                None,
            )

        if history_slot is not None:
            try:
                result = self._api(
                    "history", name="delete", value=nzo_id, archive=0,
                    del_files=1 if delete_files else 0, timeout=4,
                )
                if not self._sab_mutation_accepted(result):
                    self._event(
                        "warning", "SAB history cleanup was rejected after transfer stopped",
                        nzo_id=nzo_id,
                        error=str(result.get("error") or result.get("status") or "")[:300],
                    )
            except Exception as exc:
                self._event(
                    "warning", "SAB history cleanup failed after transfer stopped",
                    nzo_id=nzo_id, error=str(exc),
                )
        elif history_error:
            self._event(
                "warning", "Could not refresh SAB history during removal; live transfer was already proven absent",
                nzo_id=nzo_id, error=history_error[:300],
            )

        return True, ""

    def _enforce_removed_tombstones(self, qslots: list[dict[str, Any]]) -> list[str]:
        """Re-issue delete for legacy/user tombstones that SAB still exposes live.

        This repairs the pre-r3 failure mode on first poll: a card that was hidden by
        an older unverified Remove remains explicit user intent, so r3 stops the
        underlying SAB transfer instead of resurrecting the card and redownloading it.
        """
        live_ids = self._slot_ids(qslots)
        if not live_ids:
            return []
        now = time.time()
        with self.lock:
            removed = {
                str(k): _num(v, 0) for k, v in (self.state.get("removed_jobs") or {}).items()
                if _num(v, 0) >= now - 7 * 86400
            }
            reasons = {str(k): str(v or "") for k, v in (self.state.get("removed_job_reasons") or {}).items()}
        candidates = [
            nzo for nzo in live_ids
            if nzo in removed and reasons.get(nzo) and now - self._removed_cleanup_attempt_ts.get(nzo, 0.0) >= 4.0
        ]
        attempted: list[str] = []
        for nzo in candidates:
            self._removed_cleanup_attempt_ts[nzo] = now
            attempted.append(nzo)
            try:
                result = self._api("queue", name="delete", value=nzo, del_files=1, timeout=4)
                if not self._sab_mutation_accepted(result):
                    self._event("warning", "SAB rejected cleanup of a previously removed live job", nzo_id=nzo)
                    continue
                self._event("info", "Reissued stop for hidden SAB transfer left by an older unverified Remove/Cancel", nzo_id=nzo)
            except Exception as exc:
                self._event("warning", "Could not stop hidden SAB transfer for a removed job", nzo_id=nzo, error=str(exc))
        return attempted

    def _touch_job_locked(self, rec: dict[str, Any]) -> None:
        rec["_updated_ts"] = time.time()

    def set_media_automation(self, engine: Any) -> None:
        self.media_automation = engine

    def request_sync(self) -> None:
        self._last_sync_signature = ""
        self.sync_event.set()

    def _port_available(self, port: int) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(0.2)
            return sock.connect_ex(("127.0.0.1", int(port))) != 0
        finally:
            sock.close()

    def _config_identity_from(self, path: Path) -> dict[str, Any]:
        """Read a private SAB identity from one config or config backup."""
        try:
            path = Path(path)
            if not path.exists() or not path.is_file() or path.stat().st_size <= 0:
                return {}
            cfg = configparser.ConfigParser(interpolation=None)
            cfg.optionxform = str
            cfg.read(path, encoding="utf-8")
            misc = cfg["misc"] if cfg.has_section("misc") else {}
            port = _clamp_int(misc.get("port"), 1025, 65535, 0)
            return {
                "port": port,
                "api_key": str(misc.get("api_key") or "").strip(),
                "nzb_key": str(misc.get("nzb_key") or "").strip(),
                "config_file": str(path),
                "source": "sab-config",
            }
        except Exception:
            return {}

    def _config_identity(self) -> dict[str, Any]:
        return self._config_identity_from(self.config_file)

    @staticmethod
    def _canonical_config_path(path: Path) -> Path:
        """Map sabnzbd.ini backup names back to the config file the process used."""
        path = Path(path)
        if path.name.casefold() != "sabnzbd.ini":
            candidate = path.parent / "sabnzbd.ini"
            if candidate.exists():
                return candidate
        return path

    def _identity_candidates(self) -> list[dict[str, Any]]:
        """Collect every private SAB identity NewzDeck has ever had enough data to prove.

        v3.5.2 could overwrite sabnzbd.ini with a new key while an older private SAB
        process was still running with the previous key in memory. SAB commonly leaves
        config backups, so those backups are valuable recovery credentials and must not
        be ignored during portable-version migration.
        """
        rows: list[dict[str, Any]] = []
        raw = _json_read(self.engine_state_file, {})
        if isinstance(raw, dict):
            rec = dict(raw)
            rec["source"] = "engine.json"
            if not rec.get("config_file"):
                rec["config_file"] = str(self.config_file)
            rows.append(rec)

        # Current config plus every SAB config backup in all NewzDeck-owned admin generations.
        paths: list[Path] = [self.config_file]
        try:
            for admin in sorted(self.root.glob("admin*")):
                if admin.is_dir():
                    paths.extend(sorted(x for x in admin.glob("sabnzbd.ini*") if x.is_file()))
        except OSError:
            pass
        seen_paths: set[str] = set()
        for cfg_path in paths:
            key = str(cfg_path).casefold()
            if key in seen_paths:
                continue
            seen_paths.add(key)
            rec = self._config_identity_from(cfg_path)
            if rec:
                rec["config_file"] = str(self._canonical_config_path(cfg_path))
                rec["source"] = f"config:{cfg_path.name}"
                rows.append(rec)

        hist = _json_read(self.identity_history_file, [])
        if isinstance(hist, list):
            for item in reversed(hist[-24:]):
                if isinstance(item, dict):
                    rec = dict(item)
                    rec["source"] = str(rec.get("source") or "identity-history")
                    rows.append(rec)

        out: list[dict[str, Any]] = []
        seen: set[tuple[int, str, str]] = set()
        for rec in rows:
            port = _clamp_int(rec.get("port"), 1025, 65535, 0)
            api_key = str(rec.get("api_key") or "").strip()
            nzb_key = str(rec.get("nzb_key") or "").strip()
            if not port:
                continue
            token = (port, api_key, nzb_key)
            if token in seen:
                continue
            seen.add(token)
            rec["port"] = port
            rec["api_key"] = api_key
            rec["nzb_key"] = nzb_key
            out.append(rec)
        return out


    def _authoritative_identity_candidates(self) -> list[dict[str, Any]]:
        """Return credentials belonging only to the current engine generation.

        Historical admin-vN folders are evidence for retiring stale NewzDeck SAB
        processes, not candidates for normal adoption. This is the key split-brain
        boundary: current control calls may repair the API key for the *current*
        generation, but must never jump to another generation or localhost port.
        """
        current = _json_read(self.engine_state_file, {})
        if not isinstance(current, dict):
            current = {}
        config_value = str(current.get("config_file") or self.config_file)
        try:
            current_cfg = self._canonical_config_path(Path(config_value))
        except Exception:
            current_cfg = self.config_file

        rows: list[dict[str, Any]] = []
        if current:
            rec = dict(current)
            rec["source"] = "engine.json"
            rec["config_file"] = str(current_cfg)
            rows.append(rec)

        try:
            candidates = [current_cfg]
            candidates.extend(sorted(x for x in current_cfg.parent.glob("sabnzbd.ini*") if x.is_file()))
        except OSError:
            candidates = [current_cfg]

        for cfg_path in candidates:
            rec = self._config_identity_from(cfg_path)
            if not rec:
                continue
            rec["config_file"] = str(current_cfg)
            rec["source"] = f"current-generation:{cfg_path.name}"
            rows.append(rec)

        current_port = _clamp_int(current.get("port"), 1025, 65535, 0)
        if not current_port:
            try:
                current_port = int(self._load_engine_identity()["port"])
            except Exception:
                current_port = 0

        out: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        for rec in rows:
            api_key = str(rec.get("api_key") or "").strip()
            if not api_key or api_key in seen_keys:
                continue
            if current_port:
                rec["port"] = current_port
            seen_keys.add(api_key)
            out.append(rec)
        return out

    def _historical_authenticated_identity_on_port(
        self,
        port: int,
        *,
        timeout: float = 0.7,
    ) -> tuple[dict[str, Any] | None, str]:
        """Prove a historical NewzDeck-owned SAB on one port without adopting it."""
        port = int(port or 0)
        if port <= 0 or not self._probe_version(port, timeout=timeout):
            return None, ""
        current = _json_read(self.engine_state_file, {})
        current_cfg = str((current or {}).get("config_file") or self.config_file).casefold()
        current_key = str((current or {}).get("api_key") or "")
        seen: set[str] = set()
        for rec in self._identity_candidates():
            if int(rec.get("port") or 0) != port:
                continue
            key = str(rec.get("api_key") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            rec_cfg = str(rec.get("config_file") or "").casefold()
            # Current-generation credentials belong to authoritative reconciliation,
            # not stale-engine quarantine.
            if key == current_key and (not rec_cfg or rec_cfg == current_cfg):
                continue
            if self._auth_kind(port, key, timeout=timeout) == "apikey":
                return dict(rec), key
        return None, ""

    def _quarantine_known_engine_on_port(
        self,
        port: int,
        *,
        reason: str,
        timeout: float = 0.8,
    ) -> dict[str, Any]:
        """Pause/shutdown a proven *historical* NewzDeck SAB without adopting it.

        If it still has queue work, Pause preserves the queue and incomplete bytes
        for forensic/manual recovery while stopping hidden duplicate transfers. If
        its queue is empty, shutdown releases the stale localhost port.
        """
        rec, key = self._historical_authenticated_identity_on_port(port, timeout=timeout)
        if not rec or not key:
            return {"authenticated": False, "port": int(port or 0), "slots": 0, "action": ""}

        slots: list[dict[str, Any]] = []
        try:
            payload = self._raw_api(int(port), "queue", timeout=1.8, api_key=key, start=0, limit=500)
            _root, slots = self._queue_slots(payload)
        except Exception as exc:
            self._event(
                "warning",
                "Authenticated stale NewzDeck SAB but could not inspect its queue",
                port=int(port), reason=reason, error=str(exc),
            )
            return {"authenticated": True, "port": int(port), "slots": -1, "action": "inspect-failed"}

        slot_count = len(slots)
        self._stale_engine_ports_seen += 1
        self._stale_engine_last_port = int(port)
        self._stale_engine_last_slots = slot_count
        names = [
            str(x.get("filename") or x.get("name") or "")[:180]
            for x in slots[:5] if isinstance(x, dict)
        ]
        if slot_count:
            try:
                self._raw_api(int(port), "pause", timeout=2.5, api_key=key)
                self._stale_engine_live_slots_paused += slot_count
                self._event(
                    "warning",
                    "Quarantined stale NewzDeck SAB with hidden queue work",
                    port=int(port), slots=slot_count, reason=reason, jobs=names,
                )
                return {"authenticated": True, "port": int(port), "slots": slot_count, "action": "paused"}
            except Exception as exc:
                self._event(
                    "warning",
                    "Could not pause stale NewzDeck SAB",
                    port=int(port), slots=slot_count, reason=reason, error=str(exc),
                )
                return {"authenticated": True, "port": int(port), "slots": slot_count, "action": "pause-failed"}

        try:
            self._raw_api(int(port), "shutdown", timeout=2.5, api_key=key)
            self._stale_engines_shutdown += 1
            self._event("warning", "Shut down empty stale NewzDeck SAB", port=int(port), reason=reason)
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline and not self._port_available(int(port)):
                time.sleep(0.15)
            return {"authenticated": True, "port": int(port), "slots": 0, "action": "shutdown"}
        except Exception as exc:
            self._event(
                "warning",
                "Could not shut down empty stale NewzDeck SAB",
                port=int(port), reason=reason, error=str(exc),
            )
            return {"authenticated": True, "port": int(port), "slots": 0, "action": "shutdown-failed"}

    def _quarantine_stale_private_engines(self, *, force: bool = False) -> None:
        """Pause hidden historical SAB queues and retire empty old engines.

        This runs at a low cadence after the authoritative engine is healthy. It
        never changes engine.json and never adopts historical credentials.
        """
        now = time.time()
        if not force and now - self._stale_engine_quarantine_last_ts < 60.0:
            return
        self._stale_engine_quarantine_last_ts = now
        try:
            current = self._load_engine_identity()
            current_port = int(current.get("port") or 0)
        except Exception:
            return

        ports: list[int] = []
        for rec in self._identity_candidates():
            port = _clamp_int(rec.get("port"), 1025, 65535, 0)
            if port and port != current_port and port not in ports:
                ports.append(port)
        for port in ports:
            if self.shutdown_event.is_set():
                return
            self._quarantine_known_engine_on_port(port, reason="historical private SAB identity")

    def _load_engine_identity(self) -> dict[str, Any]:
        """Load SAB identity without rotating credentials because of a transient file-read failure."""
        with self._identity_lock:
            with self._identity_file_guard():
                raw = _json_read_retry(self.engine_state_file, {}, strict_existing=True)
                if not isinstance(raw, dict):
                    raw = {}
                original = dict(raw)
                config_value = str(raw.get("config_file") or "").strip()
                if config_value:
                    try:
                        candidate = Path(config_value)
                        if candidate.resolve().is_relative_to(self.root.resolve()):
                            self.config_file = candidate
                            self.admin_dir = candidate.parent
                    except Exception:
                        pass
                config_ident = self._config_identity()
                if not raw.get("api_key") and config_ident.get("api_key"):
                    raw["api_key"] = config_ident["api_key"]
                if not raw.get("nzb_key") and config_ident.get("nzb_key"):
                    raw["nzb_key"] = config_ident["nzb_key"]
                if not raw.get("api_key"):
                    raw["api_key"] = uuid.uuid4().hex
                if not raw.get("nzb_key"):
                    raw["nzb_key"] = uuid.uuid4().hex
                port = _clamp_int(raw.get("port"), 1025, 65535, 0)
                if not port:
                    port = _clamp_int(config_ident.get("port"), 1025, 65535, 0)
                if not port:
                    for candidate in range(65433, 65520):
                        if self._port_available(candidate):
                            port = candidate
                            break
                if not port:
                    raise RuntimeError("NewzDeck could not reserve a private localhost port for its download engine")
                raw.update({
                    "version": SAB_VERSION,
                    "port": port,
                    "url": f"http://127.0.0.1:{port}",
                    "api_key": str(raw["api_key"]),
                    "nzb_key": str(raw["nzb_key"]),
                    "config_file": str(self.config_file),
                })
                if raw != original or not self.engine_state_file.exists():
                    _atomic_json_write(self.engine_state_file, raw)
                return raw

    def _record_identity(self, ident: dict[str, Any], source: str = "save") -> None:
        rec = {
            "port": _clamp_int(ident.get("port"), 1025, 65535, 0),
            "api_key": str(ident.get("api_key") or ""),
            "nzb_key": str(ident.get("nzb_key") or ""),
            "config_file": str(ident.get("config_file") or self.config_file),
            "source": str(source or "save"),
            "saved_ts": time.time(),
        }
        if not rec["port"]:
            return
        with self._identity_lock:
            with self._identity_file_guard():
                hist = _json_read_retry(self.identity_history_file, [], strict_existing=True)
                if not isinstance(hist, list):
                    hist = []
                hist = [x for x in hist if not (isinstance(x, dict) and int(x.get("port") or 0) == rec["port"]
                                                and str(x.get("api_key") or "") == rec["api_key"])]
                hist.append(rec)
                _atomic_json_write(self.identity_history_file, hist[-24:])

    def _save_engine_identity(self, ident: dict[str, Any], *, source: str = "save") -> dict[str, Any]:
        with self._identity_lock:
            normalized = dict(ident)
            port = _clamp_int(normalized.get("port"), 1025, 65535, 0)
            if not port:
                raise RuntimeError("Invalid private download-engine port")
            normalized.update({
                "version": SAB_VERSION,
                "port": port,
                "url": f"http://127.0.0.1:{port}",
                "config_file": str(normalized.get("config_file") or self.config_file),
            })
            with self._identity_file_guard():
                current = _json_read_retry(self.engine_state_file, {}, strict_existing=True)
                if not isinstance(current, dict) or current != normalized:
                    _atomic_json_write(self.engine_state_file, normalized)
            self._record_identity(normalized, source=source)
            return normalized

    def _api_base(self) -> tuple[str, str]:
        ident = self._load_engine_identity()
        return str(ident["url"]).rstrip("/") + "/api", str(ident["api_key"])

    @staticmethod
    def _decode_api_payload(raw: bytes) -> dict[str, Any]:
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {"value": data}

    # The localhost SAB HTTP listener port must not be named ``port`` here.
    # SAB server configuration also has a query parameter named ``port``
    # (the provider NNTP port). Using the same Python argument name made
    # calls such as set_config(..., port=563) fail before any HTTP request.
    def _api_url(self, api_port: int, mode: str, *, api_key: str = "", include_key: bool = True, **params: Any) -> str:
        query: dict[str, Any] = {"mode": mode, "output": "json"}
        if include_key and api_key:
            query["apikey"] = api_key
        for k, v in params.items():
            if v is not None:
                query[k] = v
        return f"http://127.0.0.1:{int(api_port)}/api?" + urllib.parse.urlencode(query, doseq=True)

    def _raw_api(self, api_port: int, mode: str, *, timeout: float = 1.0, api_key: str = "",
                 include_key: bool = True, **params: Any) -> dict[str, Any]:
        url = self._api_url(api_port, mode, api_key=api_key, include_key=include_key, **params)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "NewzDeck/3.6.20", "Connection": "close"},
        )
        # SAB's own anonymized log showed one healthy process and successful NNTP
        # transfers while NewzDeck was receiving 10054 on localhost API calls. Keep
        # NewzDeck's control traffic single-filed so snapshot/completion/provider
        # threads cannot concurrently churn CherryPy/Cheroot connections.
        with self._sab_transport_lock:
            with urllib.request.urlopen(req, timeout=max(0.35, float(timeout))) as response:
                data = self._decode_api_payload(response.read())
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(str(data.get("error")))
        return data

    def _probe_version(self, port: int, timeout: float = 0.6) -> str:
        """Fingerprint SAB without credentials. SAB documents version as key-free."""
        try:
            data = self._raw_api(port, "version", timeout=timeout, include_key=False)
            return str(data.get("version") or data.get("value") or "").strip()
        except Exception:
            return ""

    def _auth_kind(self, port: int, candidate: str, timeout: float = 0.6) -> str:
        """Validate a candidate API/NZB key using SAB's key-free auth endpoint."""
        if not candidate:
            return ""
        try:
            data = self._raw_api(port, "auth", timeout=timeout, include_key=False, key=candidate)
            return str(data.get("auth") or data.get("value") or "").strip().casefold()
        except Exception:
            return ""

    def _adopt_identity(self, *, port: int, api_key: str, nzb_key: str = "", config_file: str = "", source: str = "reconcile") -> dict[str, Any]:
        current = _json_read(self.engine_state_file, {})
        if not isinstance(current, dict):
            current = {}
        if config_file:
            try:
                cfg_path = self._canonical_config_path(Path(config_file))
                if cfg_path.resolve().is_relative_to(self.root.resolve()):
                    self.config_file = cfg_path
                    self.admin_dir = cfg_path.parent
            except Exception:
                pass
        current["port"] = int(port)
        current["api_key"] = str(api_key)
        if nzb_key:
            current["nzb_key"] = str(nzb_key)
        if not current.get("nzb_key"):
            current["nzb_key"] = uuid.uuid4().hex
        current["config_file"] = str(self.config_file)
        adopted = self._save_engine_identity(current, source=source)
        self._last_error = ""
        self._event("info", "Reconciled private SAB API identity", port=int(port), source=source)
        return adopted

    def _reconcile_live_identity(self, *, timeout: float = 0.7) -> bool:
        """Repair only the authoritative current SAB generation.

        v3.6.19 and older scanned every admin-vN/history credential and could adopt
        any SAB they authenticated on any old localhost port. With multiple orphaned
        private SAB processes, a transient auth/control error could therefore switch
        the running adapter to a different queue. Historical identities are now
        retirement credentials only.
        """
        try:
            current = self._load_engine_identity()
        except Exception:
            return False
        port = int(current.get("port") or 0)
        if not port:
            return False
        version = self._probe_version(port, timeout=timeout)
        if not version:
            return False

        candidates = self._authoritative_identity_candidates()
        current_key = str(current.get("api_key") or "").strip()
        current_cfg = str(current.get("config_file") or self.config_file)
        for rec in candidates:
            key = str(rec.get("api_key") or "").strip()
            if not key:
                continue
            if self._auth_kind(port, key, timeout=timeout) != "apikey":
                continue
            if key != current_key:
                repaired = dict(current)
                repaired["api_key"] = key
                nzb_key = str(rec.get("nzb_key") or "").strip()
                if nzb_key:
                    repaired["nzb_key"] = nzb_key
                repaired["config_file"] = current_cfg
                self._save_engine_identity(repaired, source="authoritative-key-repair")
                self._identity_authoritative_key_repairs += 1
                self._event(
                    "info",
                    "Repaired authoritative private SAB API key without changing engine generation",
                    port=port,
                )
            self._last_ready_ts = time.time()
            self._last_error = ""
            return True

        # Explicitly do NOT scan/adopt another port here.
        self._identity_cross_adoptions_blocked += 1
        self._last_error = (
            f"SABnzbd {version} is reachable on authoritative localhost:{port}, "
            "but the current generation API identity does not authenticate"
        )
        return False


    def _api(self, mode: str, *, timeout: float = 4.0, include_key: bool = True, _retry_auth: bool = True, **params: Any) -> dict[str, Any]:
        ident = self._load_engine_identity()
        port = int(ident["port"])
        key = str(ident.get("api_key") or "")
        try:
            result = self._raw_api(port, mode, timeout=timeout, api_key=key, include_key=include_key, **params)
            self._last_api_success_ts = time.time()
            self._last_ready_ts = self._last_api_success_ts
            return result
        except urllib.error.HTTPError as exc:
            # A stale identity should heal itself instead of surfacing raw 403 errors.
            if exc.code in {401, 403} and include_key and _retry_auth and self._reconcile_live_identity(timeout=0.8):
                return self._api(mode, timeout=timeout, include_key=include_key, _retry_auth=False, **params)
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace").strip()
            except Exception:
                pass
            detail = body[:240] if body else str(exc.reason or "Forbidden")
            raise RuntimeError(f"Built-in SABnzbd API rejected {mode}: HTTP {exc.code} {detail}") from exc
        except RuntimeError as exc:
            # SAB normally reports a missing/incorrect API key as a JSON error with
            # HTTP 200, not necessarily 401/403. Treat that semantic error exactly
            # like an HTTP auth failure and reconcile historical identities once.
            message = str(exc)
            if include_key and _retry_auth and "api key" in message.casefold() and self._reconcile_live_identity(timeout=0.8):
                return self._api(mode, timeout=timeout, include_key=include_key, _retry_auth=False, **params)
            raise

    def _ping(self, timeout: float = 0.8) -> bool:
        """Prove both SAB identity and a full API credential without mutating config."""
        try:
            ident = self._load_engine_identity()
            port = int(ident["port"])
            key = str(ident.get("api_key") or "")
            if self._probe_version(port, timeout=timeout) and key and self._auth_kind(port, key, timeout=timeout) == "apikey":
                self._last_ready_ts = time.time()
                self._last_error = ""
                return True
        except Exception:
            pass
        if self._reconcile_live_identity(timeout=timeout):
            self._last_ready_ts = time.time()
            self._last_error = ""
            return True
        return False

    def _engine_exe(self) -> Path | None:
        direct = self.engine_dir / "SABnzbd.exe"
        if direct.exists():
            return direct
        try:
            for p in self.engine_dir.rglob("SABnzbd.exe"):
                if p.is_file():
                    return p
        except OSError:
            pass
        return None

    def _acquire_bootstrap_lock(self) -> bool:
        try:
            if self.bootstrap_lock_file.exists() and time.time() - self.bootstrap_lock_file.stat().st_mtime > 300:
                self.bootstrap_lock_file.unlink(missing_ok=True)
            fd = os.open(str(self.bootstrap_lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()}\n".encode("ascii"))
            os.close(fd)
            return True
        except FileExistsError:
            return False

    def _release_bootstrap_lock(self) -> None:
        try:
            self.bootstrap_lock_file.unlink(missing_ok=True)
        except OSError:
            pass

    def _try_kernel_file_lock(self, path: Path):
        """Return a held one-byte OS lock, or None without waiting.

        Unlike the old create/delete launch marker, the operating system owns this
        lock. It cannot survive a crashed process and it does not require PID, token,
        mtime or heartbeat recovery heuristics.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        fh = path.open("a+b")
        try:
            fh.seek(0, os.SEEK_END)
            if fh.tell() <= 0:
                fh.write(b"0")
                fh.flush()
            fh.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fh
        except (OSError, BlockingIOError):
            fh.close()
            return None

    @staticmethod
    def _release_kernel_file_lock(fh) -> None:
        if fh is None:
            return
        try:
            fh.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            try:
                fh.close()
            except OSError:
                pass

    def _acquire_launch_lock(self) -> bool:
        """Cross-process guard used by desktop/service/tray startup races."""
        try:
            if self.launch_lock_file.exists() and time.time() - self.launch_lock_file.stat().st_mtime > 90:
                self.launch_lock_file.unlink(missing_ok=True)
            fd = os.open(str(self.launch_lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()}\n".encode("ascii"))
            os.close(fd)
            return True
        except FileExistsError:
            return False

    def _release_launch_lock(self) -> None:
        try:
            self.launch_lock_file.unlink(missing_ok=True)
        except OSError:
            pass

    def _wait_for_engine(self, seconds: float) -> bool:
        deadline = time.monotonic() + max(0.0, float(seconds))
        while time.monotonic() < deadline and not self.shutdown_event.is_set():
            if self._ping(timeout=0.6):
                return True
            time.sleep(0.5)
        return self._ping(timeout=0.7)

    def _fresh_engine_generation(self, *, reason: str = "private engine identity conflict") -> dict[str, Any]:
        """Create a clean SAB admin generation without touching an inaccessible old process."""
        old = _json_read(self.engine_state_file, {})
        if not isinstance(old, dict):
            old = {}
        try:
            self._record_identity(old, source="pre-generation-rotation")
        except Exception:
            pass

        chosen_dir: Path | None = None
        for generation in range(2, 50):
            candidate = self.root / f"admin-v{generation}"
            if not candidate.exists():
                chosen_dir = candidate
                break
        if chosen_dir is None:
            chosen_dir = self.root / f"admin-v{int(time.time())}"
        chosen_dir.mkdir(parents=True, exist_ok=True)
        self.admin_dir = chosen_dir
        self.config_file = chosen_dir / "sabnzbd.ini"

        port = 0
        for candidate in range(65433, 65520):
            if self._port_available(candidate):
                port = candidate
                break
        if not port:
            raise RuntimeError("NewzDeck could not find a free private localhost port for a fresh download engine")

        ident = {
            "version": SAB_VERSION,
            "port": port,
            "api_key": uuid.uuid4().hex,
            "nzb_key": uuid.uuid4().hex,
            "config_file": str(self.config_file),
            "generation_reason": str(reason),
            "generation_ts": time.time(),
        }
        ident = self._save_engine_identity(ident, source="fresh-engine-generation")
        self._last_sync_signature = ""
        self._event("warning", "Started a fresh isolated SAB engine generation", reason=reason, port=port,
                    config_file=str(self.config_file))
        return ident

    def _select_free_engine_port(self) -> dict[str, Any]:
        # Kept for callers, but an occupied port now gets a separate admin generation
        # too, so an inaccessible old SAB process can never overwrite the new config.
        return self._fresh_engine_generation(reason="saved SAB port was already occupied")

    def _download_official_engine(self, target: Path) -> None:
        temp = target.with_suffix(".download")
        temp.unlink(missing_ok=True)
        h = hashlib.sha256()
        total = 0
        self._download_progress = {"active": True, "bytes": 0, "total": 0, "started": time.time()}
        req = urllib.request.Request(SAB_WINDOWS_X64_URL, headers={"User-Agent": "NewzDeck/3.6.20 (+embedded SAB engine provisioner)"})
        try:
            with urllib.request.urlopen(req, timeout=30) as response, temp.open("wb") as out:
                try:
                    total = max(0, int(response.headers.get("Content-Length") or 0))
                except ValueError:
                    total = 0
                self._download_progress["total"] = total
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    h.update(chunk)
                    self._download_progress["bytes"] = int(self._download_progress.get("bytes", 0)) + len(chunk)
                out.flush()
                os.fsync(out.fileno())
            digest = h.hexdigest().lower()
            if digest != SAB_WINDOWS_X64_SHA256:
                temp.unlink(missing_ok=True)
                raise RuntimeError(f"SABnzbd engine checksum verification failed (received {digest})")
            os.replace(temp, target)
        finally:
            self._download_progress["active"] = False

    def _provision_engine(self) -> Path:
        existing = self._engine_exe()
        if existing:
            return existing
        if not self._acquire_bootstrap_lock():
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline and not self.shutdown_event.is_set():
                existing = self._engine_exe()
                if existing:
                    return existing
                time.sleep(0.5)
            raise RuntimeError("Timed out waiting for the NewzDeck download engine to finish provisioning")
        self._provisioning = True
        try:
            self._event("info", f"Provisioning SABnzbd {SAB_VERSION} download engine")
            package = self.root / f"SABnzbd-{SAB_VERSION}-win64-bin.zip"
            if package.exists():
                try:
                    digest = hashlib.sha256(package.read_bytes()).hexdigest().lower()
                except OSError:
                    digest = ""
                if digest != SAB_WINDOWS_X64_SHA256:
                    package.unlink(missing_ok=True)
            if not package.exists():
                self._download_official_engine(package)
            staging = self.root / f".{SAB_VERSION}-extract-{os.getpid()}-{uuid.uuid4().hex[:8]}"
            shutil.rmtree(staging, ignore_errors=True)
            staging.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(package, "r") as zf:
                bad = zf.testzip()
                if bad:
                    raise RuntimeError(f"SABnzbd engine archive failed CRC validation at {bad}")
                for member in zf.infolist():
                    rel = Path(member.filename)
                    if rel.is_absolute() or ".." in rel.parts:
                        raise RuntimeError("SABnzbd engine archive contains an unsafe path")
                zf.extractall(staging)
            candidates = list(staging.rglob("SABnzbd.exe"))
            if not candidates:
                raise RuntimeError("Official SABnzbd portable archive did not contain SABnzbd.exe")
            src_root = candidates[0].parent
            if self.engine_dir.exists():
                shutil.rmtree(self.engine_dir, ignore_errors=True)
            try:
                os.replace(src_root, self.engine_dir)
            except OSError:
                shutil.copytree(src_root, self.engine_dir, dirs_exist_ok=True)
            shutil.rmtree(staging, ignore_errors=True)
            exe = self._engine_exe()
            if not exe:
                raise RuntimeError("SABnzbd engine provisioning completed without an executable")
            self._event("info", f"SABnzbd {SAB_VERSION} download engine provisioned", sha256=SAB_WINDOWS_X64_SHA256)
            return exe
        finally:
            self._provisioning = False
            self._release_bootstrap_lock()

    def _write_initial_config(self) -> None:
        """Create/reconcile the config only after the final engine identity is known."""
        ident = self._load_engine_identity()
        self.admin_dir = self.config_file.parent
        self.admin_dir.mkdir(parents=True, exist_ok=True)
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.optionxform = str
        if self.config_file.exists() and self.config_file.stat().st_size > 0:
            try:
                cfg.read(self.config_file, encoding="utf-8")
            except Exception:
                cfg = configparser.ConfigParser(interpolation=None)
                cfg.optionxform = str
        if not cfg.has_section("misc"):
            cfg.add_section("misc")
        misc = cfg["misc"]
        enforced = {
            "host": "127.0.0.1", "port": str(ident["port"]),
            "api_key": str(ident["api_key"]), "nzb_key": str(ident["nzb_key"]),
            "auto_browser": "0", "inet_exposure": "0", "enable_https": "0",
            "enable_broadcast": "0", "tray_icon": "0", "disable_api_key": "0",
        }
        for key, value in enforced.items():
            misc[key] = value
        settings = self.settings_getter() or {}
        defaults = {
            "username": "", "password": "", "language": "en", "web_dir": "Glitter",
            "check_new_rel": "0", "config_lock": "0", "start_paused": "0",
        }
        for key, value in defaults.items():
            if key not in misc:
                misc[key] = value
        # These are NewzDeck-owned runtime settings. They are written while SAB is
        # offline so the first live sync does not need to mutate them and recycle
        # the localhost control listener.
        misc["download_dir"] = str(self.incomplete_dir)
        misc["complete_dir"] = str(self.download_dir_getter())
        misc["direct_unpack"] = "1" if str(settings.get("direct_unpack_mode", "auto")).lower() != "off" else "0"
        misc["pause_on_post_processing"] = "0"
        if not cfg.has_section("acenter"):
            cfg.add_section("acenter")
        cfg["acenter"]["acenter_enable"] = "0"
        if not cfg.has_section("servers"):
            cfg.add_section("servers")
        with self.config_file.open("w", encoding="utf-8", newline="\n") as f:
            cfg.write(f)
        self._bootstrap_misc_authoritative = True

    def _launch(self) -> None:
        """Start/adopt the private SAB engine with one clean-generation recovery.

        v3.5.47 keeps the proven v3.5.39 identity/adoption ordering, but fixes the
        persistent-state failure mode exposed after the v3.5.41-v3.5.45 acceptance
        cycle: a damaged sabnzbd.ini/admin generation could make every subsequent
        launch fail forever even after NewzDeck itself was downgraded/restored.

        The first launch attempt always uses the existing identity/config exactly as
        before.  Only if a SAB process that *we just launched* exits or never exposes
        a valid authenticated API do we preserve that generation, allocate a fresh
        admin directory/localhost port, and try once more.  NewzDeck's job ledger,
        incoming NZBs, incomplete data, statistics and provider settings are outside
        the rotated SAB admin generation and are therefore preserved.
        """
        # Never write sabnzbd.ini until we know whether the saved port belongs to an
        # already-running private engine. This ordering prevents the v3.5.2 key split.
        if self._ping(timeout=0.8):
            self._event("info", f"Adopted existing SABnzbd {SAB_VERSION} engine", port=self._load_engine_identity()["port"])
            return

        if not self._acquire_launch_lock():
            if self._wait_for_engine(12.0):
                self._event("info", f"Adopted SABnzbd {SAB_VERSION} engine started by another NewzDeck process",
                            port=self._load_engine_identity()["port"])
                return
            try:
                if self.launch_lock_file.exists() and time.time() - self.launch_lock_file.stat().st_mtime > 12:
                    self.launch_lock_file.unlink(missing_ok=True)
            except OSError:
                pass
            if not self._acquire_launch_lock():
                raise RuntimeError("Another NewzDeck runtime still owns the private SAB startup guard")

        def stop_spawned_process() -> None:
            proc = self._process
            if proc is None or proc.poll() is not None:
                return
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            finally:
                self._process = None

        def start_current_generation(*, recovery: bool) -> tuple[bool, str]:
            exe = self._provision_engine()
            ident = self._load_engine_identity()
            port = int(ident["port"])

            # Resolve occupancy BEFORE writing any SAB config. If a previous NewzDeck
            # SAB is alive and we know any historical key, reconcile/adopt it. If it is
            # SAB but the old key is irrecoverable, isolate a fresh admin generation
            # and free port rather than modifying the config underneath the old process.
            if not self._port_available(port):
                if self._reconcile_live_identity(timeout=0.9):
                    self._event("info", f"Adopted authoritative existing SABnzbd {SAB_VERSION} engine after port probe",
                                port=self._load_engine_identity()["port"])
                    return True, ""

                quarantined = self._quarantine_known_engine_on_port(
                    port, reason="authoritative localhost port occupied by historical NewzDeck SAB",
                )
                # An empty authenticated stale process may have shut down and freed
                # the desired authoritative port. A stale engine with queue work is
                # paused/preserved, so allocate a new generation on another port.
                if not self._port_available(port):
                    version = self._probe_version(port, timeout=0.7)
                    if quarantined.get("authenticated"):
                        reason = (
                            f"quarantined stale NewzDeck SAB on localhost:{port} "
                            f"with {int(quarantined.get('slots') or 0)} preserved queue slot(s)"
                        )
                    else:
                        reason = (f"unrecoverable legacy SAB {version} identity on localhost:{port}"
                                  if version else f"another process occupies localhost:{port}")
                    self._fresh_engine_generation(reason=reason)
                    ident = self._load_engine_identity()
                    port = int(ident["port"])

            self._write_initial_config()
            ident = self._load_engine_identity()
            pid_file = self.admin_dir / "sabnzbd.pid"
            try:
                if self._port_available(int(ident["port"])):
                    pid_file.unlink(missing_ok=True)
            except OSError:
                pass
            args = [str(exe), "-f", str(self.config_file), "-s", f"127.0.0.1:{ident['port']}",
                    "-b", "0", "--inet_exposure", "0", "--pidfile", str(pid_file)]
            creationflags = 0
            startupinfo = None
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                try:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                except Exception:
                    startupinfo = None

            # Keep a small persistent startup log.  Previous builds sent stdout/stderr
            # to DEVNULL, which made a real SAB startup failure indistinguishable from
            # a generic "reconnecting" state in the UI.
            startup_log = self.root / "sab-startup.log"
            try:
                with startup_log.open("ab") as log:
                    stamp = f"\n--- NewzDeck 3.6.20 SAB startup {time.strftime('%Y-%m-%d %H:%M:%S')} recovery={int(recovery)} config={self.config_file} port={ident['port']} service_mode={int(os.environ.get('NEWZDECK_SERVICE') == '1')} ---\n"
                    log.write(stamp.encode("utf-8", errors="replace"))
                    log.flush()
                    if os.name == "nt" and os.environ.get("NEWZDECK_SERVICE") == "1":
                        if not self.process_launcher:
                            return False, "NewzDeck background service has no signed-in user-session SAB launcher"
                        result = self.process_launcher(exe, args[1:], exe.parent, startup_log)
                        pid = int((result or {}).get("pid") or 0)
                        if pid <= 0:
                            return False, "NewzDeck tray did not return a valid private SAB process id"
                        self._process = _ExternalWindowsProcess(pid)
                    else:
                        self._process = subprocess.Popen(args, cwd=str(exe.parent), stdin=subprocess.DEVNULL,
                                                         stdout=log, stderr=subprocess.STDOUT,
                                                         creationflags=creationflags, startupinfo=startupinfo)
            except Exception as exc:
                return False, f"Could not start the built-in SABnzbd engine: {exc}"

            deadline = time.monotonic() + (22.0 if recovery else 16.0)
            while time.monotonic() < deadline and not self.shutdown_event.is_set():
                if self._ping(timeout=0.8):
                    self._event("info", f"SABnzbd {SAB_VERSION} engine ready",
                                port=self._load_engine_identity()["port"], recovery_generation=bool(recovery))
                    return True, ""
                if self._process and self._process.poll() is not None:
                    code = self._process.returncode
                    self._process = None
                    return False, f"Built-in SABnzbd engine exited during startup (code {code})"
                time.sleep(0.35)
            stop_spawned_process()
            return False, "Built-in SABnzbd engine did not expose a healthy localhost API before the startup deadline"

        try:
            if self._ping(timeout=0.8):
                return

            ok, first_error = start_current_generation(recovery=False)
            if ok:
                return

            # Preserve the failed admin generation in place and rotate engine.json to
            # a brand-new admin-vN + port.  This is deliberately a one-shot recovery:
            # if a clean generation cannot start either, the real error is surfaced
            # rather than creating endless admin generations every three seconds.
            current_ident = self._load_engine_identity()
            previous_recovery = str(current_ident.get("generation_reason") or "").startswith("automatic startup recovery:")
            previous_recovery_ts = float(current_ident.get("generation_ts") or 0.0)
            if previous_recovery and time.time() - previous_recovery_ts < 600.0:
                raise RuntimeError(f"Private SAB startup still failing after the recent clean-generation recovery ({first_error})")

            self._event("warning", "Private SAB admin generation failed; retrying with a clean generation",
                        error=first_error, config_file=str(self.config_file))
            self._fresh_engine_generation(reason=f"automatic startup recovery: {first_error}")
            ok, recovery_error = start_current_generation(recovery=True)
            if ok:
                self._last_error = ""
                return
            raise RuntimeError(f"Private SAB startup failed ({first_error}); clean-generation recovery also failed ({recovery_error})")
        finally:
            self._release_launch_lock()

    def wait_ready_for_submit(self, timeout: float = 4.0) -> bool:
        """Compatibility helper retained for diagnostics; user Grabs are queued locally first."""
        try:
            return bool(self.ensure_running(blocking=True))
        except Exception:
            return False

    def _recent_transfer_work(self) -> bool:
        snap = self._last_snapshot if isinstance(self._last_snapshot, dict) else {}
        counts = snap.get("counts") if isinstance(snap.get("counts"), dict) else {}
        return bool(
            self._live_queue_ids
            or int(snap.get("remaining_bytes", 0) or 0) > 0
            or any(int(counts.get(k, 0) or 0) > 0 for k in ("downloading", "queued", "retry_wait", "cancelling"))
        )

    def ensure_running(self, *, blocking: bool = True) -> bool:
        """Keep SAB available without turning a transient HTTP miss into a restart.

        Previous builds reacted to one failed 0.8-second localhost ping by entering
        _launch() and then force-rewriting SAB/provider configuration. Those config
        writes can recycle SAB's HTTP listener and NNTP workers, creating the very
        reconnect/pause/zero-socket windows NewzDeck then tried to repair.

        Any recent successful SAB API call proves the process/control plane is alive.
        If a real probe fails, wait non-destructively first. Only a sustained outage
        is allowed to enter launch recovery, and even then normal persisted config is
        reused unless a fresh generation explicitly invalidated the sync signature.
        """
        now = time.time()
        if self._last_api_success_ts > 0 and now - self._last_api_success_ts <= 5.0:
            self._ensure_probe_miss_since = 0.0
            self._ensure_probe_miss_count = 0
            return True

        if self._ping(timeout=0.9):
            self._last_api_success_ts = time.time()
            self._ensure_probe_miss_since = 0.0
            self._ensure_probe_miss_count = 0
            return True

        self._ensure_transient_probe_misses += 1
        self._ensure_probe_miss_count += 1
        if self._ensure_probe_miss_since <= 0:
            self._ensure_probe_miss_since = now

        if not blocking:
            self.sync_event.set()
            return False

        # Give SAB several seconds to finish a file/history/config handoff with no
        # mutation whatsoever.
        if self._wait_for_engine(4.0):
            self._last_api_success_ts = time.time()
            self._ensure_probe_miss_since = 0.0
            self._ensure_probe_miss_count = 0
            return True

        miss_age = max(0.0, time.time() - self._ensure_probe_miss_since)
        recently_healthy = bool(
            (self._last_ready_ts and time.time() - self._last_ready_ts <= 20.0)
            or self._recent_transfer_work()
        )
        if recently_healthy and miss_age < 15.0:
            self._ensure_recovery_deferred += 1
            raise RuntimeError(
                "Private SAB control channel is temporarily unavailable; "
                "NewzDeck is deferring disruptive engine recovery"
            )

        self._ensure_launch_recoveries += 1
        self._launch()

        # Never force a full config rewrite merely because the control plane was
        # temporarily unavailable. A genuine fresh admin generation clears
        # _last_sync_signature itself, so normal sync still runs when actually needed.
        self._sync_configuration(force=False)
        self._ensure_probe_miss_since = 0.0
        self._ensure_probe_miss_count = 0
        return True

    def _provider_signature(self) -> str:
        providers = []
        for p in self.providers_getter():
            if not isinstance(p, dict):
                continue
            providers.append({k: p.get(k) for k in ("id", "name", "host", "port", "ssl", "username", "password_protected", "connections", "enabled", "role", "priority", "use_downloads", "use_browsing")})
        settings = self.settings_getter() or {}
        payload = {
            "providers": providers,
            "complete": str(self.download_dir_getter()),
            "direct_unpack": str(settings.get("direct_unpack_mode", "auto")),
            "cleanup": bool(settings.get("cleanup_archives", False)),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()

    def _managed_server_expectations(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for index, provider in enumerate(self.providers_getter()):
            if not isinstance(provider, dict) or not provider.get("host"):
                continue
            name = "NewzDeck-" + str(provider.get("id") or index)
            configured = _clamp_int(provider.get("connections"), 1, 100, 20)
            reserve = min(3, max(0, configured - 1)) if provider.get("use_browsing", True) else 0
            out[name] = {
                "enabled": bool(provider.get("enabled", True) and provider.get("use_downloads", True)),
                "display_name": str(provider.get("name") or provider.get("host") or name),
                "host": str(provider.get("host") or ""),
                "connections": max(1, configured - reserve),
            }
        return out

    @staticmethod
    def _status_root(payload: dict[str, Any]) -> dict[str, Any]:
        wrapped = payload.get("status") if isinstance(payload, dict) else None
        return wrapped if isinstance(wrapped, dict) else (payload if isinstance(payload, dict) else {})

    @staticmethod
    def _config_servers_root(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize SAB get_config(section=servers) across API wrapper shapes.

        SAB 5.x commonly returns the server collection as a list of singleton
        dictionaries, e.g. ``[{"server-name": {...}}]``. Older NewzDeck
        parsing treated that wrapper itself as the server record, so the runtime
        worker could be present while Diagnostics incorrectly reported 0 configured
        providers. Flatten both that shape and the direct list/dict variants.
        """
        if not isinstance(payload, dict):
            return []
        raw: Any = payload.get("config")
        if not isinstance(raw, (dict, list)):
            raw = payload.get("value")
        if not isinstance(raw, (dict, list)):
            raw = payload
        if isinstance(raw, dict):
            raw = raw.get("servers", raw.get("server", raw))

        out: list[dict[str, Any]] = []
        if isinstance(raw, list):
            for entry in raw:
                if not isinstance(entry, dict):
                    continue
                # Direct server record.
                if any(k in entry for k in ("name", "servername", "displayname", "host", "serverhost")):
                    out.append(dict(entry))
                    continue
                # SAB 5.x nested shape: [{"server-name": {server fields...}}].
                for name, value in entry.items():
                    if not isinstance(value, dict):
                        continue
                    item = dict(value)
                    item.setdefault("name", str(name))
                    out.append(item)
            return out
        if isinstance(raw, dict):
            for name, value in raw.items():
                if not isinstance(value, dict):
                    continue
                item = dict(value)
                item.setdefault("name", str(name))
                out.append(item)
        return out

    def _configured_managed_servers(self, *, timeout: float = 2.5) -> dict[str, dict[str, Any]]:
        try:
            payload = self._read_api_retry("get_config", section="servers", timeout=timeout)
        except Exception:
            return {}
        out: dict[str, dict[str, Any]] = {}
        for item in self._config_servers_root(payload):
            name = str(item.get("name") or item.get("servername") or item.get("displayname") or "").strip()
            if name.startswith("NewzDeck-"):
                out[name] = dict(item)
        return out

    def _active_warnings(self, *, timeout: float = 1.5) -> list[str]:
        try:
            payload = self._api("warnings", timeout=timeout)
            raw = payload.get("warnings") if isinstance(payload, dict) else []
            if not isinstance(raw, list):
                return []
            out = [str(x.get("text") if isinstance(x, dict) else x).strip() for x in raw]
            return [x for x in out if x]
        except Exception:
            return []

    def _provider_health(self, *, force: bool = False, timeout: float = 2.0) -> dict[str, Any]:
        """Read configured + runtime SAB NNTP state and always explain zero-worker states."""
        now = time.time()
        if not force and self._provider_health_cache and now - self._provider_health_ts < 3.0:
            return dict(self._provider_health_cache)
        expectations = self._managed_server_expectations()
        enabled_expected = {name: value for name, value in expectations.items() if value.get("enabled")}
        configured = self._configured_managed_servers(timeout=max(1.0, timeout))
        try:
            payload = self._api("status", skip_dashboard=1, timeout=timeout)
            root = self._status_root(payload)
            raw_servers = root.get("servers") if isinstance(root.get("servers"), list) else []
            servers: list[dict[str, Any]] = []
            active_connections = 0
            reported_capacity = 0
            errors: list[str] = []
            matched_names: set[str] = set()

            # Match exact managed name first. If SAB reports a display name instead,
            # fall back to the unique configured host so useful telemetry is not lost.
            host_to_name: dict[str, str] = {}
            for expected_name, expected in expectations.items():
                host = str(expected.get("host") or "").strip().casefold()
                if host and host not in host_to_name:
                    host_to_name[host] = expected_name

            for raw in raw_servers:
                if not isinstance(raw, dict):
                    continue
                reported_name = str(raw.get("servername") or raw.get("name") or raw.get("displayname") or "").strip()
                expected_name = reported_name if reported_name in expectations else ""
                if not expected_name:
                    raw_host = str(raw.get("host") or raw.get("serverhost") or "").strip().casefold()
                    expected_name = host_to_name.get(raw_host, "")
                if not expected_name:
                    continue
                expected = expectations[expected_name]
                matched_names.add(expected_name)
                conn_list = raw.get("serverconnections") if isinstance(raw.get("serverconnections"), list) else []
                active = max(_clamp_int(raw.get("serveractiveconn"), 0, 1000, 0), len(conn_list))
                capacity = max(_clamp_int(raw.get("servertotalconn"), 0, 1000, 0), int(expected.get("connections") or 0))
                error = str(raw.get("servererror") or "").strip()
                enabled = bool(expected.get("enabled"))
                server_active = bool(raw.get("serveractive", enabled))
                if enabled:
                    active_connections += active
                    reported_capacity += capacity
                    if error:
                        errors.append(f"{expected.get('display_name')}: {error}")
                    elif not server_active:
                        errors.append(f"{expected.get('display_name')}: server is inactive in SABnzbd")
                servers.append({
                    "name": expected_name,
                    "reported_name": reported_name,
                    "display_name": str(expected.get("display_name") or expected_name),
                    "host": str(expected.get("host") or ""),
                    "enabled": enabled,
                    "server_active": server_active,
                    "active_connections": active,
                    "capacity": capacity,
                    "error": error,
                })

            missing_config = [name for name in enabled_expected if name not in configured]
            missing_runtime = [name for name in enabled_expected if name not in matched_names]
            warnings = root.get("warnings") if isinstance(root.get("warnings"), list) else []
            warning_text = [str(x.get("text") if isinstance(x, dict) else x).strip() for x in warnings]
            warning_text = [x for x in warning_text if x]
            if not warning_text:
                warning_text = self._active_warnings(timeout=1.2)

            summary = errors[0] if errors else (warning_text[0] if warning_text else "")
            if not summary and enabled_expected and missing_config:
                names = ", ".join(str(enabled_expected[x].get("display_name") or x) for x in missing_config[:2])
                summary = f"SABnzbd does not have the NewzDeck provider configuration loaded ({names})."
            elif not summary and enabled_expected and missing_runtime:
                names = ", ".join(str(enabled_expected[x].get("display_name") or x) for x in missing_runtime[:2])
                summary = f"SABnzbd has no runtime NNTP worker loaded for {names}."
            elif not summary and not enabled_expected:
                summary = "No enabled NewzDeck provider is configured for downloads."

            result = {
                "available": True,
                "active_connections": active_connections,
                "capacity": reported_capacity or sum(int(x.get("connections") or 0) for x in enabled_expected.values()),
                "servers": servers,
                "errors": errors,
                "warnings": warning_text,
                "summary": summary,
                "expected_servers": len(enabled_expected),
                "configured_servers": len([x for x in enabled_expected if x in configured]),
                "runtime_servers": len([x for x in enabled_expected if x in matched_names]),
                "runtime_state_known": True,
                "control_degraded": False,
                "control_error": "",
                "missing_config": missing_config,
                "missing_runtime": missing_runtime,
            }
            self._provider_health_success_ts = now
        except Exception as exc:
            # A failed localhost status request does not mean SAB lost its NNTP
            # runtime server. The r2 evidence showed all 52 Easynews connections
            # successfully established while this exact fallback reported 0/1
            # runtime. Preserve recent proven provider state or mark runtime UNKNOWN.
            if (self._is_transient_control_error(exc) and self._provider_health_cache
                    and now - self._provider_health_success_ts <= 15.0
                    and bool(self._provider_health_cache.get("available"))):
                result = dict(self._provider_health_cache)
                result["control_degraded"] = True
                result["control_error"] = str(exc)
                result["runtime_state_known"] = False
            else:
                result = {
                    "available": False,
                    "control_degraded": self._is_transient_control_error(exc),
                    "control_error": str(exc),
                    "runtime_state_known": False,
                    "active_connections": 0,
                    "capacity": sum(int(x.get("connections") or 0) for x in enabled_expected.values()),
                    "servers": [], "errors": [], "warnings": [],
                    "summary": "SAB status temporarily unavailable" if self._is_transient_control_error(exc) else str(exc),
                    "expected_servers": len(enabled_expected), "configured_servers": len(configured),
                    "runtime_servers": -1, "missing_config": [x for x in enabled_expected if x not in configured],
                    "missing_runtime": [],
                }
        # Keep the latest real connection-test result available to the Downloads
        # UI, but do not automatically promote a one-off diagnostic socket failure
        # into the provider summary. A provider can reset an individual TCP session
        # while SAB is already reconnecting normally; stall recovery decides whether
        # a failed probe is persistent enough to surface as an actual fault.
        if self._provider_probe_cache and now - self._provider_probe_ts < 45.0:
            probe = dict(self._provider_probe_cache)
            result["provider_test"] = probe
            result["provider_test_ok"] = bool(probe.get("ok"))
        self._provider_health_cache = dict(result)
        self._provider_health_ts = now
        return result

    def _test_managed_providers(self, *, force: bool = False) -> dict[str, Any]:
        """Ask SAB to open a real one-off connection using NewzDeck's provider values."""
        now = time.time()
        if not force and self._provider_probe_cache and now - self._provider_probe_ts < 12.0:
            return dict(self._provider_probe_cache)
        results: list[dict[str, Any]] = []
        failures: list[str] = []
        for index, provider in enumerate(self.providers_getter()):
            if not isinstance(provider, dict) or not provider.get("host"):
                continue
            if not bool(provider.get("enabled", True) and provider.get("use_downloads", True)):
                continue
            label = str(provider.get("name") or provider.get("host") or f"Provider {index + 1}")
            protected = str(provider.get("password_protected") or "")
            password = ""
            if protected:
                try:
                    password = self.secret_unprotect(protected)
                    if not password:
                        raise RuntimeError("saved password decrypted to an empty value")
                except Exception as exc:
                    message = f"{label}: NewzDeck could not decrypt the saved provider password ({exc})"
                    failures.append(message)
                    results.append({"name": label, "ok": False, "message": message})
                    continue
            args = {
                "host": str(provider.get("host") or ""),
                "port": str(_clamp_int(provider.get("port"), 1, 65535, 563)),
                "username": str(provider.get("username") or ""),
                "password": password,
                "connections": "1",
                "ssl": "1" if provider.get("ssl", True) else "0",
                "ssl_verify": "3",
            }
            try:
                payload = self._api("config", name="test_server", timeout=12, **args)
                value = payload.get("value") if isinstance(payload, dict) else None
                if not isinstance(value, dict):
                    value = payload if isinstance(payload, dict) else {}
                ok = bool(value.get("result", value.get("status", False)))
                message = str(value.get("message") or payload.get("error") or ("Connection successful" if ok else "Connection test failed")).strip()
                results.append({"name": label, "ok": ok, "message": message})
                if not ok:
                    failures.append(f"{label}: {message}")
            except Exception as exc:
                message = f"{label}: {exc}"
                failures.append(message)
                results.append({"name": label, "ok": False, "message": str(exc)})

        ok = bool(results) and not failures
        result = {
            "tested": bool(results),
            "ok": ok,
            "results": results,
            "summary": failures[0] if failures else (results[0].get("message", "") if results else "No enabled download provider could be tested."),
        }
        self._provider_probe_cache = dict(result)
        self._provider_probe_ts = now
        return result

    def _restart_private_engine_for_provider_recovery(self) -> bool:
        """Restart SAB once so persisted server config is rebuilt into Downloader workers."""
        if not self._engine_recovery_lock.acquire(blocking=False):
            return False
        try:
            self._event("warning", "Restarting built-in SABnzbd to reload Usenet provider workers")
            try:
                self._api("restart", timeout=3)
            except Exception as exc:
                # The HTTP socket can close while SAB accepts the restart. Log it and
                # still wait for the process to return before deciding it failed.
                self._event("info", f"SAB restart request returned while engine recycled: {exc}")
            deadline = time.monotonic() + 30.0
            saw_down = False
            while time.monotonic() < deadline and not self.shutdown_event.is_set():
                alive = self._ping(timeout=0.45)
                if not alive:
                    saw_down = True
                elif saw_down or time.monotonic() > deadline - 24.0:
                    self._provider_health_ts = 0.0
                    self._provider_probe_ts = 0.0
                    self._last_sync_signature = ""
                    self._sync_configuration(force=True)
                    if not bool(self.state.get("paused")):
                        try:
                            self._api("resume", timeout=3)
                        except Exception:
                            pass
                    self._event("info", "Built-in SABnzbd restarted and provider configuration reloaded")
                    return True
                time.sleep(0.5)
            self._event("warning", "Built-in SABnzbd did not return after provider recovery restart")
            return False
        finally:
            self._engine_recovery_lock.release()

    def _unblock_managed_servers(self, health: dict[str, Any] | None = None, *, force: bool = False) -> int:
        """Clear SAB's temporary server block after NewzDeck reapplies valid settings."""
        health = health or self._provider_health(force=True)
        now = time.time()
        unblocked = 0
        for server in health.get("servers") or []:
            if not isinstance(server, dict) or not server.get("enabled"):
                continue
            name = str(server.get("name") or "")
            error = str(server.get("error") or "").strip()
            if not name or not error:
                continue
            if not force and now < float(self._provider_unblock_after.get(name, 0.0) or 0.0):
                continue
            self._provider_unblock_after[name] = now + 20.0
            try:
                self._api("status", name="unblock_server", value=name, timeout=3)
                unblocked += 1
                self._event("info", "Requested SAB provider unblock", server=name, error=error)
            except Exception as exc:
                self._event("warning", f"Could not unblock SAB provider {name}: {exc}")
        if unblocked:
            self._provider_health_ts = 0.0
        return unblocked

    @staticmethod
    def _is_transient_control_error(exc: Exception) -> bool:
        """Return True for short-lived localhost SAB control-channel resets.

        SAB can recycle its HTTP listener while reloading configuration. On Windows
        that often surfaces as WinError 10054 even though the engine is healthy a
        fraction of a second later. These control-plane hiccups must not be presented
        as provider/download failures.
        """
        text = str(exc or "").casefold()
        markers = (
            "winerror 10054", "errno 10054", "forcibly closed", "connection reset",
            "connection aborted", "broken pipe", "remote end closed connection",
            "connection refused", "timed out", "timeout",
        )
        return isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, TimeoutError)) or any(x in text for x in markers)

    def _config_api(self, mode: str, *, attempts: int = 3, timeout: float = 4.0, **params: Any) -> dict[str, Any]:
        """Run an idempotent SAB configuration call with bounded reconnect retry.

        A SAB config mutation can recycle its localhost HTTP listener. On Windows
        the request that *successfully applied* the setting can therefore end with
        WinError 10054. Give the listener time to come back before retrying instead
        of immediately stacking more config mutations onto the recycle window.
        """
        last: Exception | None = None
        for attempt in range(max(1, int(attempts))):
            try:
                return self._api(mode, timeout=timeout, **params)
            except Exception as exc:
                last = exc
                if not self._is_transient_control_error(exc) or attempt + 1 >= attempts:
                    raise
                time.sleep(0.35 * (attempt + 1))
                try:
                    self._wait_for_engine(min(3.5, 1.5 + attempt))
                except Exception:
                    pass
        if last is not None:
            raise last
        return {}

    @staticmethod
    def _tag_sab_payload(payload: dict[str, Any], section: str, *, fresh: bool, age: float = 0.0, error: str = "") -> dict[str, Any]:
        """Attach NewzDeck-only freshness metadata without mutating cached SAB data."""
        base = dict(payload or {})
        if isinstance(base.get(section), dict):
            root = dict(base.get(section) or {})
            root["_newzdeck_fresh"] = bool(fresh)
            root["_newzdeck_age_seconds"] = max(0.0, float(age or 0.0))
            root["_newzdeck_control_error"] = str(error or "")[:300]
            base[section] = root
            return base
        base["_newzdeck_fresh"] = bool(fresh)
        base["_newzdeck_age_seconds"] = max(0.0, float(age or 0.0))
        base["_newzdeck_control_error"] = str(error or "")[:300]
        return base

    def _read_api_retry(self, mode: str, *, attempts: int = 6, timeout: float = 4.0, **params: Any) -> dict[str, Any]:
        """Retry read-only SAB API calls through a serialized localhost transport.

        The r2 anonymized SAB log proved SAB stayed alive and its NNTP downloader was
        healthy while individual NewzDeck HTTP reads saw WinError 10054. Reads are
        idempotent, so absorb several short resets before declaring the control plane
        unavailable.
        """
        last: Exception | None = None
        for attempt in range(max(1, int(attempts))):
            try:
                return self._api(mode, timeout=timeout, **params)
            except Exception as exc:
                last = exc
                if not self._is_transient_control_error(exc) or attempt + 1 >= attempts:
                    raise
                self._sab_read_resets += 1
                time.sleep(min(0.8, 0.12 * (attempt + 1)))
        if last is not None:
            raise last
        return {}

    def _sync_configuration(self, force: bool = False) -> None:
        if not self._ping():
            return
        signature = self._provider_signature()
        now = time.time()
        if not force and signature == self._last_sync_signature:
            return
        if not force and now < float(getattr(self, "_config_sync_retry_after", 0.0) or 0.0):
            return
        self._config_sync_attempts += 1
        settings = self.settings_getter() or {}
        complete = Path(self.download_dir_getter())
        complete.mkdir(parents=True, exist_ok=True)
        self.incomplete_dir.mkdir(parents=True, exist_ok=True)
        sync_errors: list[str] = []

        # Provider configuration is the critical path. Apply it before any optional
        # live misc mutation so a listener recycle cannot strand a fresh SAB
        # generation with no NNTP server loaded.
        desired_names: set[str] = set()
        for index, provider in enumerate(self.providers_getter()):
            if not isinstance(provider, dict) or not provider.get("host"):
                continue
            name = "NewzDeck-" + str(provider.get("id") or index)
            desired_names.add(name)
            enabled = bool(provider.get("enabled", True) and provider.get("use_downloads", True))
            protected = str(provider.get("password_protected") or "")
            password: str | None = ""
            if protected:
                try:
                    password = self.secret_unprotect(protected)
                    if password == "":
                        raise RuntimeError("saved provider password decrypted to an empty value")
                except Exception as exc:
                    password = None
                    message = f"Could not decrypt provider password for {provider.get('name') or provider.get('host')}: {exc}"
                    sync_errors.append(message)
                    self._event("warning", message)
            role = str(provider.get("role") or "primary").lower()
            role_base = {"primary": 0, "backup": 33, "recovery": 66}.get(role, 0)
            configured_priority = _clamp_int(provider.get("priority"), 1, 99, 10)
            sab_priority = min(99, role_base + min(32, configured_priority))
            configured_connections = _clamp_int(provider.get("connections"), 1, 100, 20)
            reserve = min(3, max(0, configured_connections - 1)) if provider.get("use_browsing", True) else 0
            args: dict[str, Any] = {
                "section": "servers", "name": name,
                "host": str(provider.get("host") or ""),
                "port": str(_clamp_int(provider.get("port"), 1, 65535, 563)),
                "username": str(provider.get("username") or ""),
                "connections": str(max(1, configured_connections - reserve)),
                "ssl": "1" if provider.get("ssl", True) else "0",
                "enable": "1" if enabled else "0",
                "priority": str(sab_priority),
                "optional": "1" if role == "recovery" else "0",
            }
            if password is not None:
                args["password"] = password
            try:
                self._config_api("set_config", timeout=5, **args)
            except Exception as exc:
                message = f"Could not sync provider {provider.get('name') or provider.get('host')}: {exc}"
                sync_errors.append(message)
                self._event("warning", message)

        # Verify server persistence using the SAB 5.x nested response parser.
        missing: list[str] = []
        try:
            cfg = self._read_api_retry("get_config", section="servers", timeout=4)
            servers = self._config_servers_root(cfg)
            persisted_names: set[str] = set()
            for item in servers:
                name = str(item.get("name") or item.get("servername") or item.get("displayname") or "")
                if name.startswith("NewzDeck-"):
                    persisted_names.add(name)
                    if name not in desired_names:
                        try:
                            self._config_api("del_config", section="servers", keyword=name, timeout=3, attempts=2)
                        except Exception:
                            pass
            expected_enabled = set(self._managed_server_expectations()) & desired_names
            missing = [name for name in expected_enabled if name not in persisted_names]
            if missing:
                message = "SABnzbd did not persist managed provider configuration: " + ", ".join(missing[:3])
                sync_errors.append(message)
                self._event("warning", message)
        except Exception as exc:
            message = f"Could not verify SAB provider configuration: {exc}"
            sync_errors.append(message)
            self._event("warning", message)

        # A process that NewzDeck just launched already received these values in
        # sabnzbd.ini before startup. Do not immediately reapply them through the
        # live API: direct_unpack/pause_on_post_processing can recycle SAB's HTTP
        # listener and were the source of the r1 startup 10054 loop. Live changes
        # later in the session still flow through this block normally.
        bootstrap_misc_ready = bool(getattr(self, "_bootstrap_misc_authoritative", False))
        if bootstrap_misc_ready:
            self._bootstrap_misc_authoritative = False
        else:
            misc = {
                "download_dir": str(self.incomplete_dir),
                "complete_dir": str(complete),
                "direct_unpack": "1" if str(settings.get("direct_unpack_mode", "auto")).lower() != "off" else "0",
                "pause_on_post_processing": "0",
            }
            for keyword, value in misc.items():
                try:
                    self._config_api("set_config", section="misc", keyword=keyword, value=value, timeout=4, attempts=2)
                except Exception as exc:
                    message = f"Could not sync SAB setting {keyword}: {exc}"
                    sync_errors.append(message)
                    self._event("warning", message)
            try:
                self._config_api("set_config", section="acenter", keyword="acenter_enable", value="0", timeout=4, attempts=2)
            except Exception as exc:
                message = f"Could not disable SAB Windows notifications: {exc}"
                sync_errors.append(message)
                self._event("warning", message)

        self._provider_sync_errors = sync_errors[-8:]
        provider_persisted = not missing
        if sync_errors:
            self._config_sync_failures += 1
            self._config_sync_last_error_ts = time.time()
            # Missing provider persistence gets a bounded retry after the listener
            # has had time to settle. Do not enter the old three-second rewrite storm.
            if not provider_persisted:
                self._config_sync_retry_after = time.time() + 15.0
                self._last_sync_signature = ""
            else:
                self._config_sync_retry_after = 0.0
                self._last_sync_signature = signature
            self._config_retry_storms_suppressed += 1
            self._event(
                "warning",
                "SAB configuration reconciliation completed with non-fatal control errors",
                provider_persisted=provider_persisted, errors=sync_errors[-3:],
            )
        else:
            self._config_sync_retry_after = 0.0
            self._last_sync_signature = signature

        self._provider_health_ts = 0.0
        health = self._provider_health(force=True)
        self._unblock_managed_servers(health, force=True)
        if provider_persisted:
            self._event("info", "SABnzbd configuration synchronized", providers=len(desired_names), complete_dir=str(complete),
                        errors=len(sync_errors), active_connections=int(health.get("active_connections", 0) or 0))

    def _presentation_transfer_telemetry(self, *, raw_speed_bps: int, remaining_bytes: int,
                                         queue_active: bool, queue_paused: bool,
                                         live_connections: int) -> dict[str, Any]:
        """Return stable *presentation* speed/connection telemetry.

        SAB's queue API reports instantaneous values. It can briefly publish
        ``kbpersec=0`` and zero live sockets at an article/file boundary even though
        the remaining byte count keeps falling. NewzDeck should preserve that truth
        rather than making the page flash between transferring and blank.
        """
        now = time.time()
        raw_speed = max(0, int(raw_speed_bps or 0))
        remaining = max(0, int(remaining_bytes or 0))
        live = max(0, int(live_connections or 0))

        if queue_active and not queue_paused and remaining > 0:
            self._telemetry_active_until = now + 12.0
        presentation_active = bool(queue_active or (not queue_paused and remaining > 0 and now < self._telemetry_active_until))
        if not presentation_active or queue_paused or remaining <= 0:
            self._telemetry_last_sample_ts = now
            self._telemetry_last_remaining = remaining if remaining > 0 else None
            self._telemetry_smoothed_bps = 0.0
            self._telemetry_last_positive_ts = 0.0
            self._telemetry_active_until = 0.0
            return {"speed_bps": raw_speed, "connections": live, "estimated": False, "progress_bps": 0}

        progress_bps = 0.0
        if self._telemetry_last_sample_ts > 0 and self._telemetry_last_remaining is not None:
            dt = now - self._telemetry_last_sample_ts
            delta = self._telemetry_last_remaining - remaining
            if 0.35 <= dt <= 8.0 and delta > 0:
                candidate = float(delta) / dt
                # Reject impossible/coarse-poll spikes while allowing very fast LAN
                # or multi-gigabit Usenet connections.
                if 16 * 1024 <= candidate <= 2 * 1024 * 1024 * 1024:
                    progress_bps = candidate

        self._telemetry_last_sample_ts = now
        self._telemetry_last_remaining = remaining

        positive_sample = 0.0
        if raw_speed > 0 and progress_bps > 0:
            # SAB's own meter is responsive; byte progress damps one-poll drops/spikes.
            positive_sample = raw_speed * 0.65 + progress_bps * 0.35
        elif raw_speed > 0:
            positive_sample = float(raw_speed)
        elif progress_bps > 0:
            positive_sample = progress_bps

        if positive_sample > 0:
            if self._telemetry_smoothed_bps <= 0:
                self._telemetry_smoothed_bps = positive_sample
            else:
                self._telemetry_smoothed_bps = self._telemetry_smoothed_bps * 0.72 + positive_sample * 0.28
            self._telemetry_last_positive_ts = now
        elif self._telemetry_last_positive_ts and now - self._telemetry_last_positive_ts > 12.0:
            # A real extended idle should eventually show as idle rather than hiding
            # a genuine stall forever.
            self._telemetry_smoothed_bps = 0.0

        display_speed = raw_speed
        estimated = False
        if self._telemetry_smoothed_bps > 0 and (raw_speed > 0 or now - self._telemetry_last_positive_ts <= 12.0):
            display_speed = max(1, int(self._telemetry_smoothed_bps))
            estimated = raw_speed <= 0

        if live > 0:
            self._telemetry_last_live_connections = live
            self._telemetry_last_live_connections_ts = now
            display_connections = live
        elif (self._telemetry_last_live_connections > 0
              and now - self._telemetry_last_live_connections_ts <= 12.0
              and (display_speed > 0 or progress_bps > 0)):
            display_connections = self._telemetry_last_live_connections
        else:
            display_connections = 0

        return {
            "speed_bps": display_speed,
            "connections": display_connections,
            "estimated": estimated,
            "progress_bps": int(progress_bps),
        }

    @staticmethod
    def _transient_provider_reset(message: str) -> bool:
        low = str(message or "").casefold()
        return any(token in low for token in (
            "winerror 10054", "errno 10054", "connection reset", "forcibly closed by the remote host",
            "remote host closed", "connection aborted", "eof occurred in violation of protocol",
        ))

    def _recover_zero_socket_transfer(self, *, queue_active: bool, queue_paused: bool, total_speed: int,
                                      remaining_bytes: int = 0) -> dict[str, Any]:
        """Recover only a *sustained no-progress* SAB stall.

        SAB normally reconnects individual NNTP sockets itself. Short zero-socket
        gaps happen at file/article boundaries and after a provider resets one TCP
        session. v3.5.7/v3.5.8 reacted after only three seconds and even issued SAB's
        global ``disconnect`` API, which could create the stop/start behavior it was
        trying to repair. v3.5.9+ leaves transient reconnects entirely to SAB and only
        intervenes after the queue has made no progress for a meaningful interval.
        """
        now = time.time()
        health = self._provider_health(force=False)
        active_connections = int(health.get("active_connections", 0) or 0)
        remaining = max(0, int(remaining_bytes or 0))

        # Track real progress independently of SAB's instantaneous speed/socket
        # counters. mbleft decreasing is the strongest evidence that the transfer is
        # healthy even if one status poll lands during a reconnect window.
        if self._last_queue_remaining is None:
            self._last_queue_remaining = remaining if remaining > 0 else None
            self._last_queue_progress_ts = now
        elif remaining > 0 and self._last_queue_remaining > 0 and remaining < self._last_queue_remaining:
            self._last_queue_progress_ts = now
            self._last_queue_remaining = remaining
            self._provider_probe_fail_count = 0
            if self._provider_probe_cache and not bool(self._provider_probe_cache.get("ok")):
                self._provider_probe_cache = {}
                self._provider_probe_ts = 0.0
        elif remaining > 0:
            self._last_queue_remaining = remaining

        if not queue_active or queue_paused:
            self._zero_socket_since = 0.0
            self._last_queue_remaining = remaining if remaining > 0 else None
            self._last_queue_progress_ts = now
            health["stalled"] = False
            health["transient_idle"] = False
            return health

        # Any live traffic or socket activity proves SAB is doing useful work. Do
        # not run connection tests, resync the server, or disconnect/restart it.
        if total_speed > 0 or active_connections > 0:
            self._last_queue_progress_ts = now
            self._zero_socket_since = 0.0
            self._provider_probe_fail_count = 0
            if self._provider_probe_cache and not bool(self._provider_probe_cache.get("ok")):
                self._provider_probe_cache = {}
                self._provider_probe_ts = 0.0
            health["stalled"] = False
            health["transient_idle"] = False
            health["zero_socket_seconds"] = 0.0
            health["no_progress_seconds"] = 0.0
            return health

        if self._zero_socket_since <= 0:
            self._zero_socket_since = now
        zero_for = max(0.0, now - self._zero_socket_since)
        no_progress_for = max(0.0, now - self._last_queue_progress_ts)
        health["zero_socket_seconds"] = round(zero_for, 1)
        health["no_progress_seconds"] = round(no_progress_for, 1)

        # Twenty seconds is deliberately much longer than a normal SAB reconnect or
        # file-boundary handoff. During this grace period the UI stays calm and SAB
        # owns its reconnect policy. In particular, do NOT call the global disconnect
        # API and do NOT open an extra test_server connection.
        if no_progress_for < 20.0:
            health["stalled"] = False
            health["transient_idle"] = True
            if (int(health.get("configured_servers", 0) or 0) >= int(health.get("expected_servers", 0) or 0)
                    and not health.get("errors")):
                health["summary"] = ""
            return health

        health["stalled"] = True
        health["transient_idle"] = False

        # Stage 1 (20s): wake/unblock SAB. Only rewrite provider configuration if
        # SAB actually lost the persisted server entry. Reapplying a healthy server
        # configuration during an active transfer can itself recycle worker sockets.
        if now - self._last_stall_repair_ts >= 20.0:
            self._last_stall_repair_ts = now
            self._event("warning", "SAB queue has made no progress; beginning non-disruptive provider recovery",
                        stalled_seconds=round(no_progress_for, 1), provider_error=str(health.get("summary") or ""))
            expected = int(health.get("expected_servers", 0) or 0)
            configured = int(health.get("configured_servers", 0) or 0)
            if expected and configured < expected:
                try:
                    self._sync_configuration(force=True)
                except Exception as exc:
                    self._event("warning", f"Automatic SAB provider resync failed: {exc}")
            try:
                if not bool(self.state.get("paused")):
                    self._api("resume", timeout=3)
            except Exception:
                pass
            health = self._provider_health(force=True)
            self._unblock_managed_servers(health, force=True)
            health = self._provider_health(force=True)
            health["stalled"] = True
            health["zero_socket_seconds"] = round(zero_for, 1)
            health["no_progress_seconds"] = round(no_progress_for, 1)

        # Stage 2 (35s): only now run a real provider login test. A single TCP reset
        # (WinError 10054) is treated as transient because the remote host can close
        # one diagnostic session while SAB is concurrently reconnecting its pool.
        probe: dict[str, Any] | None = None
        if no_progress_for >= 35.0:
            probe = self._test_managed_providers(force=(now - self._provider_probe_ts >= 12.0))
            health["provider_test"] = probe
            health["provider_test_ok"] = bool(probe.get("ok"))
            if probe.get("ok"):
                self._provider_probe_fail_count = 0
            else:
                self._provider_probe_fail_count += 1
                probe_summary = str(probe.get("summary") or "Unknown provider error")
                if self._transient_provider_reset(probe_summary) and self._provider_probe_fail_count < 2 and no_progress_for < 60.0:
                    health["summary"] = "Provider reset a diagnostic connection; SABnzbd is being allowed to reconnect normally."
                    health["provider_test_transient"] = True
                    self._provider_health_cache = dict(health)
                    self._provider_health_ts = time.time()
                    return health
                health["summary"] = "Provider test failed: " + probe_summary
                self._provider_health_cache = dict(health)
                self._provider_health_ts = time.time()
                return health

        # Stage 3 (90s+): do *not* recycle SAB while a real queue item is active.
        # v3.5.9 could still restart the private engine after a long-looking status
        # gap even though the download later proved healthy, which produced the
        # visible 0/0 + "reconnecting" periods. SAB owns socket reconnects; NewzDeck
        # limits itself to wake/unblock/test operations that preserve the process.
        if no_progress_for >= 90.0:
            probe = probe or self._test_managed_providers(force=False)
            if probe.get("ok") and int(health.get("active_connections", 0) or 0) <= 0:
                health["summary"] = "SABnzbd has not reported transfer progress, but the provider test succeeds. The engine is being left intact so completed data is preserved."
                health["non_disruptive_stall"] = True
                self._provider_health_cache = dict(health)
                self._provider_health_ts = time.time()
        return health

    def _engine_loop(self) -> None:
        # Provision asynchronously so NewzDeck UI startup is never blocked by a first-run download.
        while not self.shutdown_event.is_set():
            try:
                self.ensure_running(blocking=True)
                self._sync_configuration()
                self._quarantine_stale_private_engines()
                if self._resume_intent_event.is_set():
                    self._resume_intent_event.clear()
                    self._refresh_shared_state()
                    provider_fault = str((self._provider_health_cache or {}).get("summary") or "")
                    disk_fault = "disk error" in provider_fault.casefold()
                    if disk_fault:
                        self._engine_fault = provider_fault
                        self._engine_fault_last_ts = time.time()
                        if provider_fault != self._engine_fault_last_logged:
                            self._engine_fault_last_logged = provider_fault
                            self._event(
                                "error",
                                "Private SAB queue is paused by a disk error; automatic Resume suppressed",
                                error=provider_fault,
                            )
                    elif not bool(self.state.get("paused", False)):
                        try:
                            self._api("resume", timeout=3)
                            self._event("info", "Reasserted NewzDeck running queue intent after sustained SAB Pause")
                        except Exception as resume_exc:
                            self._event("warning", f"Could not reassert SAB queue running state: {resume_exc}")
                self._flush_pending_submissions(max_items=3)
                self.sync_event.wait(3.0)
                self.sync_event.clear()
            except Exception as exc:
                message = str(exc)
                self._last_error = message
                if "deferring disruptive engine recovery" not in message:
                    self._event("warning", f"Download engine unavailable: {exc}")
                self.sync_event.wait(3.0)
                self.sync_event.clear()

    def engine_status(self) -> dict[str, Any]:
        exe = self._engine_exe()
        now = time.time()
        if self._engine_status_cache and now - self._engine_status_ts < 1.0:
            return dict(self._engine_status_cache)
        recent_api = bool(self._last_api_success_ts and now - self._last_api_success_ts <= 3.0)
        probe_ready = recent_api or self._ping(timeout=0.7)
        if probe_ready:
            if not recent_api:
                self._last_api_success_ts = time.time()
            self._engine_unready_since = 0.0
            ready = True
        else:
            if self._engine_unready_since <= 0:
                self._engine_unready_since = now
            # SAB's localhost API can miss one short probe while it rotates files,
            # writes history, or performs post-processing. Treat that as a degraded
            # heartbeat, not an engine restart. snapshot() will validate the queue
            # API next and fall back to the last coherent snapshot if needed.
            ready = bool(self._last_ready_ts and now - self._last_ready_ts <= self._engine_probe_grace_seconds)
        progress = dict(self._download_progress)
        try:
            ident = self._load_engine_identity()
            port = int(ident.get("port") or 0)
            config_name = Path(str(ident.get("config_file") or self.config_file)).parent.name
        except Exception:
            port = 0
            config_name = ""
        result = {
            "name": "SABnzbd",
            "version": SAB_VERSION,
            "adapter_version": "3.6.21",
            "mode": "built-in",
            "ready": ready,
            "probe_ready": probe_ready,
            "heartbeat_degraded": bool(ready and not probe_ready),
            "heartbeat_gap_seconds": max(0.0, now - self._engine_unready_since) if self._engine_unready_since > 0 else 0.0,
            "provisioned": bool(exe),
            "provisioning": bool(self._provisioning or progress.get("active")),
            "provision_bytes": int(progress.get("bytes", 0) or 0),
            "provision_total": int(progress.get("total", 0) or 0),
            "last_error": self._last_error,
            "localhost_only": True,
            "port": port,
            "config_generation": config_name,
            "official_sha256": SAB_WINDOWS_X64_SHA256,
        }
        self._engine_status_cache = dict(result)
        self._engine_status_ts = now
        return result

    def _tracked(self) -> dict[str, dict[str, Any]]:
        jobs = self.state.get("jobs")
        if not isinstance(jobs, dict):
            jobs = {}
            self.state["jobs"] = jobs
        return jobs

    def _track_add(self, nzo_id: str, *, name: str, source_name: str, provider_id: str,
                   expected_bytes: int, file_count: int, automation_context: dict[str, Any] | None,
                   priority: str = "normal", browser_flat_images: bool = False,
                   browser_flat_filenames: list[str] | None = None, browser_flat_staging_name: str = "") -> None:
        self._refresh_shared_state()
        with self.lock:
            tracked = self._tracked()
            tracked[nzo_id] = {
                "id": nzo_id,
                "name": _safe_name(name),
                "source_name": source_name,
                "provider_id": provider_id,
                "expected_bytes": max(0, int(expected_bytes)),
                "file_count": max(1, int(file_count or 1)),
                "automation_context": dict(automation_context or {}),
                "priority": priority if priority in {"high", "normal", "low"} else "normal",
                "created_ts": time.time(),
                "import_status": "",
                "import_message": "",
                "import_progress": 0,
                "imported": False,
                # Expected SAB completed-output location.  SAB can occasionally
                # report an empty/stale history ``storage`` field for direct-media
                # jobs, so keep NewzDeck's own deterministic hint as a second
                # source of truth for Smart Import.
                "output_hint": str(self.download_dir_getter() if browser_flat_images else self.download_dir_getter() / _safe_name(name)),
                "browser_flat_images": bool(browser_flat_images),
                "browser_flat_filenames": [Path(str(x)).name for x in (browser_flat_filenames or []) if Path(str(x)).name],
                "browser_flat_staging_name": _safe_name(browser_flat_staging_name, "") if browser_flat_staging_name else "",
                "browser_flattened": False,
                "_updated_ts": time.time(),
            }
            self.state.setdefault("removed_jobs", {}).pop(str(nzo_id), None)
            self._save_state()

    @staticmethod
    def _browser_flat_destination(root: Path, filename: str, reserved: set[str]) -> Path:
        """Return a collision-safe file path directly under *root*."""
        base = Path(str(filename or "download.bin")).name or "download.bin"
        candidate = root / base
        stem, suffix = candidate.stem, candidate.suffix
        index = 2
        while candidate.exists() or str(candidate).casefold() in reserved:
            candidate = root / f"{stem} ({index}){suffix}"
            index += 1
        reserved.add(str(candidate).casefold())
        return candidate

    def _flatten_completed_browser_images(self, nzo_id: str, meta: dict[str, Any], slot: dict[str, Any]) -> bool:
        """Finalize a direct Newsgroups image job with no per-job output folder.

        SAB remains the authoritative transfer engine, so it necessarily stages an NZB
        in a job directory while it works. r2 gives new loose-image jobs a unique
        ``NewzDeck Images <token>`` SAB-only name, then uses the *fresh Completed*
        history storage path to move the finished payload into Download Folder itself.
        The visible NewzDeck job name remains the image name. Automation, imported
        NZBs, videos and All Posts/browser_set packages never receive this marker.
        """
        if not bool(meta.get("browser_flat_images")):
            return False
        root = Path(self.download_dir_getter()).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        if bool(meta.get("browser_flattened")):
            slot["storage"] = str(root)
            slot["path"] = str(root)
            return True

        expected = [Path(str(x)).name for x in (meta.get("browser_flat_filenames") or []) if Path(str(x)).name]
        if not expected:
            return False
        expected_folded = {x.casefold() for x in expected}
        staging_name = str(meta.get("browser_flat_staging_name") or "").strip()
        raw_storage = str(slot.get("storage") or slot.get("path") or "").strip()

        # Prefer the explicit r2 staging directory. SAB history occasionally reports
        # the complete root itself during the final rename window, so the internal
        # staging identity is the deterministic fallback rather than a guessed image
        # filename directory.
        source_candidates: list[Path] = []
        if staging_name:
            source_candidates.append(root / staging_name)
        if raw_storage:
            source_candidates.append(Path(raw_storage).expanduser())
        legacy_name = _safe_name(str(meta.get("name") or ""), "")
        if legacy_name:
            source_candidates.append(root / legacy_name)

        source: Path | None = None
        seen_paths: set[str] = set()
        for candidate in source_candidates:
            try:
                resolved = candidate.resolve()
                folded = str(resolved).casefold()
                if folded in seen_paths:
                    continue
                seen_paths.add(folded)
                resolved.relative_to(root)
            except (OSError, ValueError):
                continue
            if resolved.exists():
                source = resolved
                break
        if source is None:
            return False

        try:
            source.relative_to(root)
        except ValueError:
            self._event("warning", "Skipped loose-image flatten outside Download Folder", nzo_id=nzo_id, storage=str(source))
            return False

        image_suffixes = {
            ".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".gif", ".webp", ".bmp",
            ".tif", ".tiff", ".avif", ".heic", ".heif", ".jxl",
        }

        # SAB can return a single completed file directly in the root. That is already
        # the desired layout; only normalize NewzDeck's bookkeeping.
        if source.is_file() and source.parent == root:
            if source.name.casefold() not in expected_folded and source.suffix.casefold() not in image_suffixes:
                return False
            moved_names = [source.name]
        else:
            if not source.is_dir():
                return False
            all_files = [x for x in source.rglob("*") if x.is_file()]
            if not all_files:
                return False

            # Exact decoded/header names are preferred. If SAB normalized a decoded
            # image filename, a fresh history storage directory is still job-specific,
            # so image payloads in that directory are safe to flatten as a fallback.
            by_name: dict[str, list[Path]] = {}
            for candidate in all_files:
                by_name.setdefault(candidate.name.casefold(), []).append(candidate)
            selected: list[Path] = []
            remaining: dict[str, int] = {}
            for filename in expected:
                key = filename.casefold()
                remaining[key] = remaining.get(key, 0) + 1
            exact_ok = True
            for key, count in remaining.items():
                matches = by_name.get(key, [])
                if len(matches) < count:
                    exact_ok = False
                    break
                selected.extend(matches[:count])
            if not exact_ok:
                selected = [x for x in all_files if x.suffix.casefold() in image_suffixes]
                if not selected and len(all_files) == len(expected):
                    # Last-resort compatibility for an image format whose extension
                    # NewzDeck does not yet know; this directory came from the fresh
                    # SAB history slot for an explicitly image-only job.
                    selected = list(all_files)
            if not selected:
                return False

            trusted_r2_staging = bool(
                staging_name
                and staging_name.casefold().startswith("newzdeck images ")
                and source.parent == root
                and source.name.casefold() == staging_name.casefold()
            )

            # Stage before deleting/renaming anything. This handles the old r1 shape
            # Download\photo.jpg\photo.jpg and the r2 internal staging directory while
            # preserving collision-safe root naming.
            stage = root / f".newzdeck-flat-{uuid.uuid4().hex}"
            stage.mkdir(parents=False, exist_ok=False)
            staged: list[tuple[Path, Path]] = []
            try:
                for index, candidate in enumerate(selected):
                    temp = stage / f"{index:06d}-{candidate.name}"
                    shutil.move(str(candidate), str(temp))
                    staged.append((candidate, temp))
            except Exception as exc:
                for original, temp in reversed(staged):
                    if not temp.exists() or original.exists():
                        continue
                    try:
                        original.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(temp), str(original))
                    except Exception:
                        pass
                shutil.rmtree(stage, ignore_errors=True)
                self._event("warning", "Could not stage completed loose-image job", nzo_id=nzo_id, error=str(exc))
                return False

            # r2's uniquely named directory is NewzDeck-owned staging for this exact
            # image-only job. Once its payload has been staged, remove it completely so
            # no empty/image-named/engine-residue folder is left behind. Legacy r1 jobs
            # use conservative empty-directory cleanup only.
            try:
                if trusted_r2_staging:
                    shutil.rmtree(source)
                else:
                    dirs = sorted((x for x in source.rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True)
                    for directory in dirs:
                        try:
                            directory.rmdir()
                        except OSError:
                            pass
                    try:
                        source.rmdir()
                    except OSError:
                        pass
            except OSError as exc:
                # Files are still safely staged; continue to root finalization and let
                # the next completion pass retry directory cleanup if needed.
                self._event("warning", "Loose-image staging directory cleanup deferred", nzo_id=nzo_id, error=str(exc))

            reserved: set[str] = set()
            final_plan: list[tuple[Path, Path, Path]] = []
            for original, temp in staged:
                final_plan.append((original, temp, self._browser_flat_destination(root, original.name, reserved)))

            finalized: list[tuple[Path, Path, Path]] = []
            try:
                for original, temp, dest in final_plan:
                    shutil.move(str(temp), str(dest))
                    finalized.append((original, temp, dest))
            except Exception as exc:
                for original, temp, dest in reversed(finalized):
                    if not dest.exists() or original.exists():
                        continue
                    try:
                        original.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(dest), str(original))
                    except Exception:
                        pass
                for original, temp in staged:
                    if not temp.exists() or original.exists():
                        continue
                    try:
                        original.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(temp), str(original))
                    except Exception:
                        pass
                shutil.rmtree(stage, ignore_errors=True)
                self._event("warning", "Could not flatten completed loose-image job", nzo_id=nzo_id, error=str(exc))
                return False
            shutil.rmtree(stage, ignore_errors=True)
            moved_names = [dest.name for _, _, dest in final_plan]

            # If a transient Windows lock prevented deleting the r2 staging folder,
            # don't mark the cleanup final yet. Files are already flat, and the next
            # fresh Completed pass can remove the now-payload-free directory.
            if trusted_r2_staging and source.exists():
                try:
                    shutil.rmtree(source)
                except OSError:
                    return False

        with self.lock:
            live = self._tracked().get(str(nzo_id))
            if isinstance(live, dict):
                live["browser_flattened"] = True
                live["browser_flattened_files"] = list(moved_names)
                live["resolved_output"] = str(root)
                live["output_hint"] = str(root)
                self._touch_job_locked(live)
                meta.update(live)
                self._save_state()
        slot["storage"] = str(root)
        slot["path"] = str(root)
        self._event("info", "Placed completed Newsgroups images directly in Download Folder", nzo_id=nzo_id, files=len(moved_names))
        return True

    def _priority_value(self, priority: str) -> int:
        return {"high": 1, "normal": 0, "low": -1}.get(str(priority).lower(), 0)

    @staticmethod
    def _sab_slot_name(slot: dict[str, Any]) -> str:
        return str(slot.get("filename") or slot.get("name") or slot.get("nzb_name") or "").strip()

    def _sab_ids_for_name(self, name: str, *, timeout: float = 2.0) -> set[str] | None:
        """Return SAB queue/history IDs matching *name*, or None when SAB cannot be queried.

        This is used only around addlocalfile's ambiguous failure window.  A successful
        before/after comparison lets NewzDeck prove whether SAB accepted an NZB even
        when its localhost HTTP response was reset before urllib received it.
        """
        wanted = _safe_name(name).casefold()
        found: set[str] = set()
        try:
            queue_data = self._api("queue", start=0, limit=200, timeout=timeout)
            history_data = self._api("history", start=0, limit=200, timeout=timeout)
            _, qslots = self._queue_slots(queue_data)
            _, hslots = self._history_slots(history_data)
            for slot in qslots + hslots:
                if _safe_name(self._sab_slot_name(slot)).casefold() != wanted:
                    continue
                nzo_id = str(slot.get("nzo_id") or slot.get("id") or "").strip()
                if nzo_id:
                    found.add(nzo_id)
            return found
        except Exception:
            return None

    def _confirm_new_sab_submission(self, name: str, before: set[str] | None, *, wait_seconds: float = 2.4) -> str:
        if before is None:
            return ""
        deadline = time.time() + max(0.4, float(wait_seconds))
        while time.time() < deadline:
            current = self._sab_ids_for_name(name, timeout=1.2)
            if current is not None:
                added = sorted(current - before)
                if added:
                    return str(added[0])
            time.sleep(0.2)
        return ""

    @staticmethod
    def _friendly_submit_error(exc: Exception) -> str:
        text = str(exc or "").casefold()
        if any(x in text for x in ("winerror 10054", "errno 10054", "forcibly closed", "connection reset", "remote end closed", "connection aborted", "broken pipe")):
            return "The built-in download engine briefly reset its local connection while queueing this release."
        if any(x in text for x in ("winerror 10061", "errno 10061", "connection refused", "timed out", "timeout")):
            return "The built-in download engine was temporarily unavailable while queueing this release."
        return "The built-in download engine could not queue this release."

    def queue_nzb(self, provider_id: str, source_name: str, raw: bytes, automation_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Commit an NZB to NewzDeck immediately and hand it to SAB asynchronously.

        Interactive/Automation Grabs must never block an HTTP request on SAB startup.
        Persist the NZB and its Smart Import identity first, expose it as Queued, then
        let the normal background engine worker perform the SAB addlocalfile handoff.
        """
        parsed = self.parse_nzb(raw, source_name)
        files = list(parsed.get("files") or [])
        expected = sum(max(0, int(x.get("bytes", 0) or 0)) for x in files if isinstance(x, dict))
        passwords = list(parsed.get("passwords") or [])
        job_name = str(parsed.get("name") or Path(source_name).stem)
        if isinstance(automation_context, dict):
            release_name = str(automation_context.get("release_title") or "").strip()
            if release_name:
                job_name = release_name
        ticket = "pending-" + uuid.uuid4().hex
        pending_path = self.incoming_dir / f"{ticket}.nzb"
        pending_path.write_bytes(raw)
        now = time.time()
        self._refresh_shared_state()
        with self.lock:
            self._tracked()[ticket] = {
                "id": ticket, "name": _safe_name(job_name), "source_name": source_name,
                "provider_id": provider_id, "expected_bytes": max(0, int(expected)),
                "file_count": max(1, len(files)), "automation_context": dict(automation_context or {}),
                "priority": "normal", "created_ts": now, "import_status": "", "import_message": "",
                "import_progress": 0, "imported": False, "pending_submit": True,
                "pending_path": str(pending_path), "pending_password": str(passwords[0]) if passwords else "",
                "pending_attempts": 0, "pending_next_ts": 0.0, "pending_last_error": "",
                "pending_before_ids": [], "pending_before_ids_known": False, "pending_ambiguous_since": 0.0,
                "output_hint": str(self.download_dir_getter() / _safe_name(job_name)), "_updated_ts": now,
            }
            self.state.setdefault("removed_jobs", {}).pop(ticket, None)
            self._save_state()
        self._last_snapshot_ts = 0.0
        self.start_background_threads()
        self.sync_event.set()
        self._event("info", f"Queued {job_name} for immediate SAB handoff", pending_id=ticket)
        return {
            "ok": True, "collection_id": ticket, "collection_name": _safe_name(job_name),
            "files": max(1, len(files)), "added": [{"id": ticket, "filename": _safe_name(job_name), "collection_id": ticket}],
            "duplicates": [], "skipped": [], "warnings": [],
            "folder": str(self.download_dir_getter() / _safe_name(job_name)),
            "engine": "SABnzbd", "engine_version": SAB_VERSION, "pending_engine_handoff": True,
        }

    def _flush_pending_submissions(self, max_items: int = 3) -> int:
        """Submit already-committed Grab tickets after SAB is ready.

        A per-ticket kernel lock prevents desktop and service runtimes from submitting
        the same NZB. Failures in the localhost control path remain queued and retry
        without asking the user to click Grab again.
        """
        self._refresh_shared_state()
        now = time.time()
        with self.lock:
            pending = [(str(k), dict(v)) for k, v in self._tracked().items()
                       if isinstance(v, dict) and v.get("pending_submit") and not v.get("terminal_status")
                       and float(v.get("pending_next_ts") or 0) <= now]
        pending.sort(key=lambda kv: float(kv[1].get("created_ts") or 0))
        completed = 0
        for ticket, meta in pending[:max(1, int(max_items))]:
            claim_path = self.incoming_dir / f".{ticket}.submit.lock"
            claim = self._try_kernel_file_lock(claim_path)
            if claim is None:
                continue
            try:
                self._refresh_shared_state()
                with self.lock:
                    live = self._tracked().get(ticket)
                    if not isinstance(live, dict) or not live.get("pending_submit"):
                        continue
                    meta = dict(live)

                # Record the matching SAB ids that existed before the first attempt.
                # If addlocalfile ever returns an ambiguous connection reset, this
                # baseline lets a later pass prove whether SAB accepted a new job
                # before NewzDeck considers another submission.
                if not bool(meta.get("pending_before_ids_known")):
                    before = self._sab_ids_for_name(str(meta.get("name") or ""), timeout=1.0)
                    if before is not None:
                        with self.lock:
                            live = self._tracked().get(ticket)
                            if isinstance(live, dict):
                                live["pending_before_ids"] = sorted(before)
                                live["pending_before_ids_known"] = True
                                self._touch_job_locked(live)
                                self._save_state()
                                meta = dict(live)

                ambiguous_since = float(meta.get("pending_ambiguous_since") or 0.0)
                if ambiguous_since > 0:
                    current = self._sab_ids_for_name(str(meta.get("name") or ""), timeout=1.2)
                    if current is None or not bool(meta.get("pending_before_ids_known")):
                        with self.lock:
                            live = self._tracked().get(ticket)
                            if isinstance(live, dict):
                                live["pending_next_ts"] = time.time() + 2.0
                                self._touch_job_locked(live)
                                self._save_state()
                        continue
                    before = {str(x) for x in (meta.get("pending_before_ids") or [])}
                    added = sorted(set(current) - before)
                    if added:
                        real_id = str(added[0])
                        self._track_add(
                            real_id, name=str(meta.get("name") or "NZB package"),
                            source_name=str(meta.get("source_name") or "Queued Grab.nzb"),
                            provider_id=str(meta.get("provider_id") or ""),
                            expected_bytes=int(meta.get("expected_bytes") or 0),
                            file_count=int(meta.get("file_count") or 1),
                            automation_context=dict(meta.get("automation_context") or {}),
                            priority=str(meta.get("priority") or "normal"),
                        )
                        self._refresh_shared_state()
                        with self.lock:
                            self._tracked().pop(ticket, None)
                            self._mark_removed_locked(ticket, "handoff")
                            self._save_state()
                        try:
                            Path(str(meta.get("pending_path") or "")).unlink(missing_ok=True)
                        except OSError:
                            pass
                        self._last_snapshot_ts = 0.0
                        completed += 1
                        self._event("warning", "Recovered ambiguous queued SAB handoff without duplicate submission", pending_id=ticket, nzo_id=real_id)
                        continue
                    if time.time() - ambiguous_since < 8.0:
                        with self.lock:
                            live = self._tracked().get(ticket)
                            if isinstance(live, dict):
                                live["pending_next_ts"] = time.time() + 1.5
                                self._touch_job_locked(live)
                                self._save_state()
                        continue
                    # SAB has been queryable for multiple seconds and no id beyond
                    # the pre-submit baseline exists. A retry is now proven safe.
                    with self.lock:
                        live = self._tracked().get(ticket)
                        if isinstance(live, dict):
                            live["pending_ambiguous_since"] = 0.0
                            live["pending_next_ts"] = 0.0
                            self._touch_job_locked(live)
                            self._save_state()
                            meta = dict(live)

                path = Path(str(meta.get("pending_path") or ""))
                if not path.exists():
                    with self.lock:
                        live = self._tracked().get(ticket)
                        if isinstance(live, dict):
                            live["pending_submit"] = False
                            live["terminal_status"] = "failed"
                            live["pending_last_error"] = "The queued NZB staging file is missing."
                            self._touch_job_locked(live)
                            self._save_state()
                    continue
                raw = path.read_bytes()
                try:
                    result = self._submit_nzb(
                        str(meta.get("provider_id") or ""), str(meta.get("source_name") or path.name), raw,
                        name=str(meta.get("name") or path.stem), expected_bytes=int(meta.get("expected_bytes") or 0),
                        file_count=int(meta.get("file_count") or 1),
                        automation_context=dict(meta.get("automation_context") or {}),
                        priority=str(meta.get("priority") or "normal"), password=str(meta.get("pending_password") or ""),
                    )
                    real_id = str(result.get("collection_id") or "")
                    self._refresh_shared_state()
                    with self.lock:
                        self._tracked().pop(ticket, None)
                        self._mark_removed_locked(ticket, "handoff")
                        self._save_state()
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
                    self._last_snapshot_ts = 0.0
                    completed += 1
                    self._event("info", "Completed queued SAB handoff", pending_id=ticket, nzo_id=real_id)
                except Exception as exc:
                    attempts = int(meta.get("pending_attempts") or 0) + 1
                    low = str(exc or "").casefold()
                    ambiguous = "could not safely confirm whether sab accepted" in low
                    delay = 1.5 if ambiguous else min(15.0, 0.75 * (2 ** min(attempts - 1, 4)))
                    with self.lock:
                        live = self._tracked().get(ticket)
                        if isinstance(live, dict):
                            live["pending_attempts"] = attempts
                            live["pending_next_ts"] = time.time() + delay
                            live["pending_last_error"] = str(exc)[:500]
                            if ambiguous and not float(live.get("pending_ambiguous_since") or 0.0):
                                live["pending_ambiguous_since"] = time.time()
                            self._touch_job_locked(live)
                            self._save_state()
                    self._last_snapshot_ts = 0.0
                    self._event("warning", "Queued SAB handoff will reconcile before retry" if ambiguous else "Queued SAB handoff will retry", pending_id=ticket, attempt=attempts, error=str(exc))
                    # Engine/control errors are shared across queued tickets; let the
                    # next engine-loop pass recover before trying additional entries.
                    break
            finally:
                self._release_kernel_file_lock(claim)
                try:
                    claim_path.unlink(missing_ok=True)
                except OSError:
                    pass
        return completed

    def _submit_nzb(self, provider_id: str, source_name: str, raw: bytes, *, name: str,
                    expected_bytes: int, file_count: int, automation_context: dict[str, Any] | None = None,
                    priority: str = "normal", password: str = "", browser_flat_images: bool = False,
                    browser_flat_filenames: list[str] | None = None) -> dict[str, Any]:
        # Synchronous callers (ordinary NZB imports) may still ensure SAB is ready.
        # Interactive/Automation Grabs use queue_nzb() and therefore never block the
        # browser request on this startup/control path.
        self.start_background_threads()
        self.sync_event.set()
        self.ensure_running(blocking=True)

        safe_source = _safe_name(Path(source_name).stem, "NewzDeck") + ".nzb"
        path = self.incoming_dir / f"{int(time.time())}-{uuid.uuid4().hex[:10]}-{safe_source}"
        path.write_bytes(raw)
        settings = self.settings_getter() or {}
        # SAB pp=3 means +Repair/+Unpack/Delete; pp=2 retains archive parts.
        cleanup = bool(settings.get("cleanup_archives", False) or automation_context)
        pp = 3 if cleanup else 2

        # Direct loose-image selections need SAB for the proven transfer engine, but
        # SAB always completes an NZB inside a job-named directory. Give those jobs a
        # unique NewzDeck-owned internal name so completion cleanup can identify the
        # staging directory unambiguously without depending on decoded filenames.
        sab_job_name = _safe_name(name)
        if browser_flat_images:
            sab_job_name = _safe_name(f"NewzDeck Images {uuid.uuid4().hex[:12]}")

        before_ids = self._sab_ids_for_name(sab_job_name, timeout=1.6)
        result: dict[str, Any] = {}
        try:
            result = self._api("addlocalfile", name=str(path), nzbname=sab_job_name, cat="*", script="Default",
                               priority=self._priority_value(priority), pp=pp, password=password or None, timeout=12)
        except Exception as exc:
            if not self._is_transient_control_error(exc):
                raise

            # addlocalfile is not blindly retried: the reset may have happened *after*
            # SAB accepted the NZB. First prove whether a new matching queue/history
            # ID appeared. This prevents duplicate jobs after an ambiguous HTTP reset.
            confirmed = self._confirm_new_sab_submission(sab_job_name, before_ids)
            if confirmed:
                result = {"nzo_ids": [confirmed]}
                self._event("warning", "Recovered SAB addlocalfile response after localhost connection reset", nzo_id=confirmed)
            else:
                # If SAB can now be queried successfully and no new job exists, one
                # retry is safe. If its state remains unknowable, fail closed with a
                # human message rather than risking a duplicate submission.
                current_ids = self._sab_ids_for_name(sab_job_name, timeout=1.6)
                if before_ids is not None and current_ids is not None and not (current_ids - before_ids):
                    time.sleep(0.25)
                    try:
                        result = self._api("addlocalfile", name=str(path), nzbname=sab_job_name, cat="*", script="Default",
                                           priority=self._priority_value(priority), pp=pp, password=password or None, timeout=12)
                    except Exception as retry_exc:
                        if self._is_transient_control_error(retry_exc):
                            confirmed = self._confirm_new_sab_submission(sab_job_name, before_ids)
                            if confirmed:
                                result = {"nzo_ids": [confirmed]}
                            else:
                                raise RuntimeError(self._friendly_submit_error(retry_exc) + " No duplicate was submitted; try Grab again in a moment.") from retry_exc
                        else:
                            raise
                else:
                    raise RuntimeError(self._friendly_submit_error(exc) + " NewzDeck could not safely confirm whether SAB accepted it, so it did not retry automatically. Check Downloads before trying Grab again.") from exc

        ids = result.get("nzo_ids") if isinstance(result.get("nzo_ids"), list) else []
        if not ids:
            # Some versions wrap this in result.
            wrapped = result.get("result") if isinstance(result.get("result"), dict) else {}
            ids = wrapped.get("nzo_ids") if isinstance(wrapped.get("nzo_ids"), list) else []
        if not ids:
            confirmed = self._confirm_new_sab_submission(sab_job_name, before_ids, wait_seconds=1.2)
            if confirmed:
                ids = [confirmed]
        if not ids:
            raise RuntimeError(str(result.get("error") or "SABnzbd did not return a queue job ID"))
        nzo_id = str(ids[0])
        self._track_add(nzo_id, name=name, source_name=source_name, provider_id=provider_id,
                        expected_bytes=expected_bytes, file_count=file_count, automation_context=automation_context,
                        priority=priority, browser_flat_images=browser_flat_images,
                        browser_flat_filenames=browser_flat_filenames,
                        browser_flat_staging_name=sab_job_name if browser_flat_images else "")
        # Explicitly wake SAB after addlocalfile. This is idempotent when the queue is
        # already running and avoids leaving a newly-added job behind a stale internal
        # downloader pause after a service/engine hand-off.
        if not bool(self.state.get("paused")):
            try:
                self._api("resume", timeout=3)
            except Exception:
                pass
        self.sync_event.set()
        self._event("info", f"Submitted {name} to built-in SABnzbd", nzo_id=nzo_id)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return {"ok": True, "collection_id": nzo_id, "collection_name": _safe_name(name),
                "files": file_count, "added": [{"id": nzo_id, "filename": _safe_name(name), "collection_id": nzo_id}],
                "duplicates": [], "skipped": [], "warnings": [],
                "folder": str(self.download_dir_getter() if browser_flat_images else self.download_dir_getter() / _safe_name(name)),
                "engine": "SABnzbd", "engine_version": SAB_VERSION}

    def add_nzb(self, provider_id: str, source_name: str, raw: bytes, automation_context: dict[str, Any] | None = None) -> dict[str, Any]:
        parsed = self.parse_nzb(raw, source_name)
        files = list(parsed.get("files") or [])
        expected = sum(max(0, int(x.get("bytes", 0) or 0)) for x in files if isinstance(x, dict))
        passwords = list(parsed.get("passwords") or [])
        # Automation owns the human/release identity.  Some indexers deliberately
        # put an opaque payload filename in the NZB subject and parse_nzb() quite
        # reasonably exposes that as the package name.  Do not let that opaque name
        # become SAB's completed-folder identity: use the preserved indexer release
        # title for Automation jobs while leaving ordinary NZB imports unchanged.
        job_name = str(parsed.get("name") or Path(source_name).stem)
        if isinstance(automation_context, dict):
            release_name = str(automation_context.get("release_title") or "").strip()
            if release_name:
                job_name = release_name
        return self._submit_nzb(provider_id, source_name, raw, name=job_name,
                                expected_bytes=expected, file_count=max(1, len(files)), automation_context=automation_context,
                                password=str(passwords[0]) if passwords else "")

    def add_nzb_selection(self, provider_id: str, parsed: dict[str, Any], selected_indices: list[int] | None = None, collection_name: str = "") -> dict[str, Any]:
        files = list(parsed.get("files") or [])
        if selected_indices is None:
            selected = list(range(len(files)))
        else:
            selected = sorted({int(i) for i in selected_indices if str(i).isdigit() and 0 <= int(i) < len(files)})
        if not selected:
            raise ValueError("Select at least one NZB file")
        entries = [files[i] for i in selected]
        name = _safe_name(collection_name or str(parsed.get("name") or "Imported NZB"))
        passwords = list(parsed.get("passwords") or [])
        raw = build_nzb_bytes(name, entries, str(passwords[0]) if passwords else "")
        expected = sum(max(0, int(x.get("bytes", 0) or 0)) for x in entries if isinstance(x, dict))
        return self._submit_nzb(provider_id, str(parsed.get("source_name") or name + ".nzb"), raw, name=name,
                                expected_bytes=expected, file_count=len(entries), automation_context=parsed.get("automation_context") if isinstance(parsed.get("automation_context"), dict) else None,
                                password=str(passwords[0]) if passwords else "")

    def add(self, provider_id: str, group: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        if not items:
            raise ValueError("Select at least one media item")
        name = _safe_name(str((items[0].get("media") or {}).get("filename") or items[0].get("subject") or "NewzDeck Download"))
        raw = build_nzb_bytes(name, items)
        expected = sum(max(0, int(x.get("bytes", 0) or sum(int(s.get("bytes", 0) or 0) for s in (x.get("segments") or [])))) for x in items if isinstance(x, dict))
        loose_images = bool(items) and all(
            isinstance(x, dict)
            and str((x.get("media") or {}).get("kind") or "").casefold() == "image"
            and str(x.get("source") or "").casefold() != "browser_set"
            and not str(x.get("collection_id") or "").strip()
            for x in items
        )
        flat_filenames = [Path(str((x.get("media") or {}).get("filename") or "")).name for x in items] if loose_images else []
        return self._submit_nzb(provider_id, name + ".nzb", raw, name=name, expected_bytes=expected,
                                file_count=len(items), automation_context=None,
                                browser_flat_images=loose_images, browser_flat_filenames=flat_filenames)

    def _queue_and_history(self, *, live: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
        """Read one coherent SAB Queue/History pair through a shared reader.

        Snapshot polling and the Automation completion monitor used to issue their
        own concurrent Queue/History requests. The SAB log from the real r2 failure
        showed SAB itself remained alive, opened all 52 Easynews connections and
        processed jobs while NewzDeck saw localhost 10054 errors. Serialize these
        reads, share recent results, and explicitly mark short cached fallbacks stale
        so they can never drive Pause recovery as if they were current engine truth.
        """
        with self._queue_history_lock:
            now = time.time()
            queue_fresh = True
            queue_error = ""
            try:
                queue_data = self._read_api_retry(
                    "queue", start=0, limit=200,
                    timeout=2.0 if live else 4.0, attempts=6,
                )
                self._last_good_queue_payload = dict(queue_data)
                self._last_good_queue_ts = time.time()
            except Exception as exc:
                queue_error = str(exc)
                age = now - float(self._last_good_queue_ts or 0.0)
                if self._last_good_queue_payload is None or age > 1.75:
                    raise
                queue_data = dict(self._last_good_queue_payload)
                queue_fresh = False
                self._sab_read_stale_uses += 1

            queue_age = 0.0 if queue_fresh else max(0.0, now - self._last_good_queue_ts)
            queue_data = self._tag_sab_payload(
                queue_data, "queue", fresh=queue_fresh, age=queue_age, error=queue_error
            )
            _qroot, qslots = self._queue_slots(queue_data)
            current_ids = {
                str(x.get("nzo_id") or x.get("id") or "")
                for x in qslots if str(x.get("nzo_id") or x.get("id") or "")
            }

            # History is allowed a slightly longer fallback because it is terminal
            # state rather than live transfer telemetry. Queue->History handoffs still
            # force a fresh read whenever possible.
            queue_handoff = bool(self._live_queue_ids - current_ids) if queue_fresh else False
            cached_history_root, _cached_history_slots = self._history_slots(self._live_history_payload or {})
            cached_pp_active = int(_num(cached_history_root.get("ppslots"), 0) or 0) > 0
            history_interval = 0.5 if cached_pp_active else 1.0
            history_due = (
                not live
                or self._live_history_payload is None
                or now - self._live_history_fetch_ts >= history_interval
                or queue_handoff
            )

            history_fresh = True
            history_error = ""
            if history_due:
                try:
                    history_data = self._read_api_retry(
                        "history", start=0, limit=200,
                        timeout=2.5 if live else 4.0, attempts=6,
                    )
                    self._live_history_payload = dict(history_data)
                    self._live_history_fetch_ts = time.time()
                    self._last_good_history_payload = dict(history_data)
                    self._last_good_history_ts = time.time()
                except Exception as exc:
                    history_error = str(exc)
                    age = now - float(self._last_good_history_ts or 0.0)
                    if self._last_good_history_payload is None or age > 8.0:
                        raise
                    history_data = dict(self._last_good_history_payload)
                    history_fresh = False
                    self._sab_read_stale_uses += 1
            else:
                history_data = dict(self._live_history_payload or self._last_good_history_payload or {})
                history_fresh = False

            history_age = 0.0 if history_fresh else max(0.0, now - float(self._last_good_history_ts or 0.0))
            history_data = self._tag_sab_payload(
                history_data, "history", fresh=history_fresh, age=history_age, error=history_error
            )

            if queue_fresh:
                self._live_queue_ids = current_ids
            return queue_data, history_data

    @staticmethod
    def _queue_slots(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        q = payload.get("queue") if isinstance(payload.get("queue"), dict) else payload
        slots = q.get("slots") if isinstance(q, dict) and isinstance(q.get("slots"), list) else []
        return q if isinstance(q, dict) else {}, [x for x in slots if isinstance(x, dict)]

    @staticmethod
    def _history_slots(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        h = payload.get("history") if isinstance(payload.get("history"), dict) else payload
        raw_slots = h.get("slots") if isinstance(h, dict) and isinstance(h.get("slots"), list) else []
        slots: list[dict[str, Any]] = []
        for rank, raw in enumerate(raw_slots):
            if not isinstance(raw, dict):
                continue
            slot = dict(raw)
            # SAB history is returned newest-first. Preserve that ordering only as
            # a fallback for old entries lacking the Unix ``completed`` timestamp.
            slot["_newzdeck_history_rank"] = rank
            slots.append(slot)
        return h if isinstance(h, dict) else {}, slots

    def _recover_automation_context_for_slot(self, nzo_id: str, slot: dict[str, Any]) -> dict[str, Any]:
        engine = self.media_automation
        if engine is None:
            return {}
        try:
            recover = getattr(engine, "recover_download_context", None)
            if recover is None:
                return {}
            name = str(slot.get("filename") or slot.get("name") or "")
            value = recover(str(nzo_id), name)
            return dict(value) if isinstance(value, dict) else {}
        except Exception as exc:
            self._event("warning", f"Could not recover Automation context for SAB job {nzo_id}: {exc}")
            return {}

    def _cleanup_proven_stale_queue_duplicates(self, queue_slots: list[dict[str, Any]]) -> set[str]:
        """Remove only queue entries that are *provably* stale duplicates.

        Safe cases:
        1. the exact SAB NZO id is already terminal=completed and imported in the
           NewzDeck ledger; or
        2. the SAB id is completely untracked and its exact normalized release name
           matches a completed/imported NewzDeck job.

        A tracked non-terminal re-download is never removed merely because its name
        matches an older completion.
        """
        self._refresh_shared_state()
        with self.lock:
            tracked = dict(self._tracked())

        terminal_ids: set[str] = set()
        completed_names: set[str] = set()
        for job_id, meta in tracked.items():
            if not isinstance(meta, dict):
                continue
            terminal = str(meta.get("terminal_status") or "").casefold()
            if terminal == "completed" and bool(meta.get("imported")):
                terminal_ids.add(str(job_id))
                name = _safe_name(str(meta.get("name") or "")).casefold()
                if name:
                    completed_names.add(name)

        cleaned: set[str] = set()
        for slot in queue_slots:
            if not isinstance(slot, dict):
                continue
            nzo_id = str(slot.get("nzo_id") or slot.get("id") or "").strip()
            if not nzo_id:
                continue
            slot_name = _safe_name(str(slot.get("filename") or slot.get("name") or "")).casefold()
            reason = ""
            delete_files = False
            if nzo_id in terminal_ids:
                reason = "completed/imported SAB job id reappeared in live Queue"
                delete_files = False
            elif nzo_id not in tracked and slot_name and slot_name in completed_names:
                reason = "untracked live Queue entry exactly duplicates an imported release"
                delete_files = True
            if not reason:
                continue
            try:
                result = self._api(
                    "queue", name="delete", value=nzo_id,
                    del_files=1 if delete_files else 0, timeout=4,
                )
                if not self._sab_mutation_accepted(result):
                    raise RuntimeError(str(result.get("error") or result.get("status") or "SAB rejected deletion"))
                cleaned.add(nzo_id)
                self._stale_duplicate_queue_cleanups += 1
                self._stale_duplicate_queue_last_ts = time.time()
                if nzo_id not in tracked:
                    with self.lock:
                        self._mark_removed_locked(nzo_id, "stale_duplicate")
                        self._save_state()
                self._event(
                    "warning",
                    "Removed proven stale duplicate from authoritative SAB Queue",
                    nzo_id=nzo_id,
                    reason=reason,
                    name=str(slot.get("filename") or slot.get("name") or "")[:240],
                )
            except Exception as exc:
                self._event(
                    "warning",
                    "Could not remove proven stale duplicate from authoritative SAB Queue",
                    nzo_id=nzo_id, reason=reason, error=str(exc),
                )
        return cleaned

    def _adopt_untracked_slots(self, queue_slots: list[dict[str, Any]], history_slots: list[dict[str, Any]]) -> int:
        """Adopt SAB jobs created by another NewzDeck runtime into the shared ledger.

        SAB is a single private engine, but a desktop process and Windows service can
        overlap briefly. The process serving the UI must still display/import a job
        submitted by its sibling instead of showing only aggregate speed/remaining.
        """
        self._refresh_shared_state()
        additions: list[tuple[str, dict[str, Any], dict[str, Any], bool]] = []
        repairs: list[tuple[str, dict[str, Any]]] = []
        with self.lock:
            tracked_snapshot = dict(self._tracked())
            known = set(tracked_snapshot)
            # A Cancel/Remove action leaves a seven-day tombstone in the shared
            # ledger. SAB history can outlive the local card (especially when the
            # engine was reconnecting during deletion), so adoption must honor the
            # tombstone instead of resurrecting that exact NZO ID as post-processing.
            removed_snapshot = {
                str(k): _num(v, 0) for k, v in (self.state.get("removed_jobs") or {}).items()
                if _num(v, 0) >= time.time() - 7 * 86400
            }
            removed_reasons = {str(k): str(v or "") for k, v in (self.state.get("removed_job_reasons") or {}).items()}
        legacy_recovered: set[str] = set()
        for slot in queue_slots:
            nzo_id = str(slot.get("nzo_id") or slot.get("id") or "")
            if not nzo_id:
                continue
            if nzo_id in removed_snapshot:
                # v3.6.10 and older used the same tombstone for explicit Remove/Cancel
                # and for an automatic 12-second missing-slot prune. New reasoned
                # tombstones preserve explicit user intent; legacy reasonless tombstones
                # may be recovered when SAB proves the job is still in its live queue.
                if removed_reasons.get(nzo_id):
                    continue
                legacy_recovered.add(nzo_id)
            if nzo_id in known:
                existing = tracked_snapshot.get(nzo_id) or {}
                if not isinstance(existing.get("automation_context"), dict) or not existing.get("automation_context"):
                    ctx = self._recover_automation_context_for_slot(nzo_id, slot)
                    if ctx: repairs.append((nzo_id, ctx))
                continue
            ctx = self._recover_automation_context_for_slot(nzo_id, slot)
            additions.append((nzo_id, slot, ctx, False))
            known.add(nzo_id)
        for slot in history_slots:
            nzo_id = str(slot.get("nzo_id") or slot.get("id") or "")
            if not nzo_id:
                continue
            if str(slot.get("status") or "").casefold() != "completed":
                continue
            completed_ts = _num(slot.get("completed"), 0)
            if completed_ts > 0 and time.time() - completed_ts > 48 * 3600:
                continue
            legacy_history_context: dict[str, Any] = {}
            if nzo_id in removed_snapshot:
                if removed_reasons.get(nzo_id):
                    continue
                # Only revive an old reasonless tombstone from completed history when
                # Automation can independently recover the target and completion occurred
                # after the tombstone. This repairs the historical auto-prune bug without
                # broadly resurrecting old manually-cleared history.
                legacy_history_context = self._recover_automation_context_for_slot(nzo_id, slot)
                if not legacy_history_context or completed_ts <= removed_snapshot.get(nzo_id, 0):
                    continue
                legacy_recovered.add(nzo_id)
            if nzo_id in known:
                existing = tracked_snapshot.get(nzo_id) or {}
                if not isinstance(existing.get("automation_context"), dict) or not existing.get("automation_context"):
                    ctx = self._recover_automation_context_for_slot(nzo_id, slot)
                    if ctx: repairs.append((nzo_id, ctx))
                continue
            ctx = legacy_history_context or self._recover_automation_context_for_slot(nzo_id, slot)
            if not ctx:
                continue
            additions.append((nzo_id, slot, ctx, True))
            known.add(nzo_id)
        if not additions and not repairs:
            return 0
        now = time.time()
        with self.lock:
            tracked = self._tracked()
            for nzo_id, context in repairs:
                live = tracked.get(nzo_id)
                if isinstance(live, dict) and not live.get("automation_context"):
                    live["automation_context"] = dict(context)
                    live["context_recovered_ts"] = now
                    self._touch_job_locked(live)
            for nzo_id, slot, context, history in additions:
                expected = max(_mb_to_bytes(slot.get("mb")), _mb_to_bytes(slot.get("mbleft")))
                name = _safe_name(str(slot.get("filename") or slot.get("name") or "Recovered SAB download"))
                tracked[nzo_id] = {
                    "id": nzo_id,
                    "name": name,
                    "source_name": name + ".nzb",
                    "provider_id": str(context.get("provider_id") or ""),
                    "expected_bytes": expected,
                    "file_count": max(1, _clamp_int(slot.get("nrof") or slot.get("files"), 1, 100000, 1)),
                    "automation_context": dict(context),
                    "priority": "normal",
                    "created_ts": _num(slot.get("time_added"), now),
                    "import_status": "",
                    "import_message": "",
                    "import_progress": 0,
                    "imported": False,
                    "output_hint": str(slot.get("storage") or slot.get("path") or (self.download_dir_getter() / name)),
                    "_updated_ts": now,
                    "adopted_from_sab": True,
                }
                # Do not clear a removal tombstone here. Only a genuinely new NZO ID
                # should be adopted, and tombstones deliberately suppress stale SAB history.
            self._save_state()
        for nzo_id, context in repairs:
            self._event("info", "Recovered Automation context for shared SAB job",
                        nzo_id=nzo_id, target_key=str(context.get("target_key") or ""))
        for nzo_id, slot, context, history in additions:
            message = "Recovered SAB job from legacy automatic-prune tombstone" if nzo_id in legacy_recovered else "Reconciled SAB job after submission/runtime handoff"
            self._event("info", message,
                        nzo_id=nzo_id, automation=bool(context), history=history,
                        name=str(slot.get("filename") or slot.get("name") or ""))
        self._last_snapshot_ts = 0
        return len(additions) + len(repairs)

    def _bridge_unexpected_sab_pause(
        self,
        qroot: dict[str, Any],
        engine: dict[str, Any],
        now: float,
        *,
        has_transfer_work: bool,
    ) -> dict[str, Any] | None:
        """Hold the last coherent live view through a transient SAB global pause.

        NewzDeck is the user-facing owner of Pause/Resume. If NewzDeck's durable
        state says the queue is running, but SAB briefly reports aggregate Paused
        immediately after a proven live snapshot, treat that first bounded interval
        as an internal engine handoff rather than a user pause. A real NewzDeck pause
        still wins immediately because ``self.state['paused']`` is set before the
        control response is rendered.

        After the grace window expires, the raw SAB pause is accepted so genuine
        engine/disk/provider problems are never hidden indefinitely.
        """
        local_paused = bool(self.state.get("paused", False))
        aggregate_status = str((qroot or {}).get("status") or "").strip().casefold()
        raw_paused = bool((qroot or {}).get("paused", False)) or aggregate_status == "paused"
        prior = self._last_snapshot if isinstance(self._last_snapshot, dict) else None
        prior_counts = (prior or {}).get("counts") if isinstance((prior or {}).get("counts"), dict) else {}
        prior_active = int(prior_counts.get("downloading", 0) or 0)
        prior_age = max(0.0, now - float(self._last_snapshot_ts or 0.0))

        if local_paused or not raw_paused or not has_transfer_work or prior_active <= 0 or prior is None:
            self._unexpected_sab_pause_since = 0.0
            self._unexpected_sab_pause_bridge_open = False
            return None

        # Do not bridge a very old remembered snapshot after a real idle/restart.
        if prior_age > max(20.0, self._active_continuity_seconds):
            self._unexpected_sab_pause_since = 0.0
            self._unexpected_sab_pause_bridge_open = False
            return None

        if self._unexpected_sab_pause_since <= 0:
            self._unexpected_sab_pause_since = now
        pause_age = max(0.0, now - self._unexpected_sab_pause_since)
        if pause_age > self._unexpected_sab_pause_grace_seconds:
            self._unexpected_sab_pause_bridge_open = False
            return None

        if not self._unexpected_sab_pause_bridge_open:
            self._unexpected_sab_pause_bridge_open = True
            self._unexpected_sab_pause_bridges += 1
            self._unexpected_sab_pause_last_ts = now
            self._event(
                "warning",
                "Bridging transient SAB global Pause while NewzDeck queue intent is running",
                active_jobs=prior_active,
                pause_age_seconds=round(pause_age, 2),
            )

        # Ask the background coordinator to reassert NewzDeck's running intent.
        # Never mutate SAB directly from the UI snapshot thread.
        if now - self._unexpected_sab_pause_last_resume_request_ts >= 2.5:
            self._unexpected_sab_pause_last_resume_request_ts = now
            self._resume_intent_event.set()
            self.sync_event.set()

        stale = dict(prior)
        stale["paused"] = False
        stale_engine = dict(stale.get("engine") or {})
        stale_engine.update({
            **dict(engine or {}),
            "unexpected_pause_bridge": True,
            "unexpected_pause_seconds": round(pause_age, 2),
        })
        stale["engine"] = stale_engine
        telemetry = dict(stale.get("telemetry") or {})
        telemetry["unexpected_sab_pause_bridges"] = int(self._unexpected_sab_pause_bridges)
        telemetry["unexpected_sab_pause_last_ts"] = float(self._unexpected_sab_pause_last_ts)
        telemetry["unexpected_sab_pause_active"] = True
        stale["telemetry"] = telemetry
        return stale

    def _observe_engine_pause_intent(
        self,
        qroot: dict[str, Any],
        now: float,
        *,
        has_transfer_work: bool,
    ) -> bool:
        """Expose/recover only a sustained SAB pause while real work is waiting."""
        local_paused = bool(self.state.get("paused", False))
        raw_status = str((qroot or {}).get("status") or "").strip().casefold()
        raw_paused = bool((qroot or {}).get("paused", False)) or raw_status == "paused"

        if not has_transfer_work or local_paused or not raw_paused:
            self._engine_pause_mismatch_since = 0.0
            return False

        if self._engine_pause_mismatch_since <= 0:
            self._engine_pause_mismatch_since = now
        pause_age = max(0.0, now - self._engine_pause_mismatch_since)

        # SAB can flip its aggregate queue state at file/article boundaries. Do not
        # flash the UI or mutate the engine for those short transitions.
        visible_mismatch = pause_age >= 4.0

        if pause_age >= 8.0 and now - self._unexpected_sab_pause_last_resume_request_ts >= 15.0:
            self._unexpected_sab_pause_last_resume_request_ts = now
            self._engine_pause_reassert_count += 1
            self._engine_pause_reassert_last_ts = now
            self._resume_intent_event.set()
            self.sync_event.set()

        return visible_mismatch

    def _active_continuity_allowed(self, nzo_id: str, now: float, *, prior_status: str,
                                   queue_paused: bool, foreground_id: str = "",
                                   slot_status: str = "") -> bool:
        """Keep a proven live SAB owner Active through bounded presentation gaps.

        This is intentionally stricter than an ordinary time-based card cache. The
        lease starts only after SAB positively identifies the job as downloading,
        fetching, foreground, or making byte progress. Explicit pause/propagation, a
        competing foreground job, or a terminal history record still wins immediately.
        """
        if str(prior_status or "").casefold() != "downloading" or queue_paused:
            return False
        if str(slot_status or "").casefold() in {"paused", "propagating"}:
            return False
        if foreground_id and foreground_id != nzo_id:
            return False
        confirmed = float(self._job_active_confirmed_ts.get(nzo_id, 0.0) or 0.0)
        return bool(confirmed > 0 and now - confirmed <= self._active_continuity_seconds)

    def _mark_active_bridge(self, nzo_id: str, now: float) -> None:
        if nzo_id not in self._active_bridge_open:
            self._active_bridge_open.add(nzo_id)
            self._active_continuity_bridges += 1
            self._active_continuity_last_ts = now

    def _confirm_active_owner(self, nzo_id: str, now: float) -> None:
        self._job_active_confirmed_ts[nzo_id] = now
        self._active_bridge_open.discard(nzo_id)

    def _status_for_queue(self, status: str) -> tuple[str, str]:
        raw = str(status or "Queued")
        low = raw.casefold()
        if low == "downloading": return "downloading", ""
        if low == "paused": return "queued", ""
        if low == "propagating": return "retry_wait", ""
        if low == "fetching": return "downloading", "repairing"
        return "queued", ""

    def _status_for_history(self, status: str) -> tuple[str, str]:
        low = str(status or "").casefold()
        if low == "completed": return "completed", "completed"
        if low == "failed": return "failed", "failed"
        stages = {"queued": "queued", "quickcheck": "verifying", "verifying": "verifying", "repairing": "repairing",
                  "fetching": "repairing", "extracting": "extracting", "moving": "importing", "running": "importing"}
        return "completed", stages.get(low, "queued")

    def _job_from_slot(self, nzo_id: str, meta: dict[str, Any], slot: dict[str, Any], *, history: bool) -> dict[str, Any]:
        expected = max(int(meta.get("expected_bytes", 0) or 0), _mb_to_bytes(slot.get("mb")))
        remaining = _mb_to_bytes(slot.get("mbleft"))
        if history:
            status, post = self._status_for_history(str(slot.get("status") or ""))
            downloaded = expected if status == "completed" else max(0, expected - remaining)
            speed = 0
        else:
            status, post = self._status_for_queue(str(slot.get("status") or ""))
            downloaded = max(0, expected - remaining) if expected else _mb_to_bytes(slot.get("mb") or 0) - remaining
            speed = _kb_to_bps(slot.get("kbpersec"))
        paused = str(slot.get("status") or "").casefold() == "paused"
        pct = max(0.0, min(100.0, _num(slot.get("percentage"), 0)))
        if expected and downloaded <= 0 and pct > 0:
            downloaded = int(expected * pct / 100.0)
        storage = str(slot.get("storage") or slot.get("path") or "")
        pp = str(slot.get("status") or "")
        sab_post_stage, sab_post_progress, sab_post_progress_known, sab_post_message = _sab_post_progress(slot, post)
        if sab_post_stage:
            post = sab_post_stage
        import_status = str(meta.get("import_status") or "")
        import_heartbeat_ts = _num(meta.get("import_heartbeat_ts"), _num(meta.get("import_claim_ts"), 0))
        import_heartbeat_age = max(0.0, time.time() - import_heartbeat_ts) if import_status == "importing" and import_heartbeat_ts > 0 else 0.0
        import_stalled = bool(import_status == "importing" and import_heartbeat_age >= 90.0)
        if import_status in {"queued", "waiting", "importing", "failed", "completed"}:
            post = import_status if import_status != "completed" else "completed"
            pp = str(meta.get("import_message") or pp)
            if import_stalled:
                pp = (pp + f" • no import progress for {int(import_heartbeat_age)}s").strip(" •")
        automation_context = dict(meta.get("automation_context") or {})
        automation_label, automation_release_title, automation_destination = _automation_identity(automation_context)
        created = _num(slot.get("time_added"), _num(meta.get("created_ts"), time.time()))
        completed_ts = max(_num(slot.get("completed"), 0), _num(meta.get("completed_ts"), 0))
        history_rank = int(_num(slot.get("_newzdeck_history_rank"), 10**9)) if history else 10**9
        eta_seconds = 0 if history else _duration_seconds(slot.get("timeleft"))
        if eta_seconds <= 0 and not history and speed > 0 and expected > downloaded:
            eta_seconds = int((expected - downloaded) / speed)
        return {
            "id": nzo_id, "identity": nzo_id, "collection_id": nzo_id, "collection_name": str(meta.get("name") or slot.get("filename") or "NZB"),
            "provider_id": str(meta.get("provider_id") or ""), "provider_name": "SABnzbd engine", "origin_provider_id": str(meta.get("provider_id") or ""),
            "group": "", "filename": str(slot.get("filename") or meta.get("name") or "NZB package"), "kind": "file",
            "status": status, "expected_bytes": expected, "downloaded_bytes": max(0, downloaded), "actual_size": expected if status == "completed" else 0,
            "current_part": int(round(pct)), "processed_parts": int(round(pct)), "successful_parts": int(round(pct)), "failed_parts": 0,
            "total_parts": 100, "speed_bps": speed, "eta_seconds": eta_seconds, "connections_used": 0, "path": storage, "partial_path": str(slot.get("path") or ""),
            "error": str(slot.get("fail_message") or "") if status == "failed" else "", "created_ts": created, "started_ts": _num(meta.get("started_ts"), created),
            "completed_ts": completed_ts, "history_rank": history_rank, "recovered_parts": 0, "retry_count": 0, "priority": str(meta.get("priority") or "normal"), "paused": paused,
            "queue_order": _num(slot.get("index"), 0), "status_detail": sab_post_message or _sab_text(slot.get("stage_log")) or str(slot.get("status") or ""), "transfer_phase": "sabnzbd",
            "integrity_status": "healthy" if status == "completed" else "unknown", "post_status": post,
            "post_progress": int(meta.get("import_progress", 0) or 0) if import_status in {"queued", "waiting", "importing", "failed", "completed"} else sab_post_progress,
            "post_progress_known": bool(import_status == "importing" or (not import_status and sab_post_progress_known)),
            "post_indeterminate": bool(post in {"queued", "verifying", "repairing", "extracting", "importing"} and not (import_status == "importing" or (not import_status and sab_post_progress_known))),
            "post_message": str(meta.get("import_message") or sab_post_message or pp), "automation_context": automation_context, "source": "nzb",
            "automation_label": automation_label, "automation_release_title": automation_release_title,
            "automation_destination": automation_destination, "display_name": automation_label or str(slot.get("filename") or meta.get("name") or "NZB package"),
            "source_filename": str(slot.get("filename") or ""), "import_status": import_status,
            "imported": bool(meta.get("imported")),
            "import_heartbeat_age_seconds": float(import_heartbeat_age),
            "import_stalled": bool(import_stalled),
            "release_failure_recorded": bool(meta.get("failure_feedback_recorded")),
            "release_failure_reason": str(meta.get("failure_reason") or ""),
            "collection_role": "payload", "is_auxiliary": False, "optional_missing": False, "missing_bytes": 0, "resumed_parts": 0,
        }

    def _collection_from_job(self, job: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
        status = str(job.get("status") or "queued")
        post = str(job.get("post_status") or "")
        if status == "completed" and post in {"queued", "verifying", "repairing", "extracting", "importing"}:
            package_status = "completed"
        else:
            package_status = status
        file_count = max(1, int(meta.get("file_count", 1) or 1))
        expected = max(0, int(job.get("expected_bytes", 0) or 0))
        downloaded = max(0, int(job.get("downloaded_bytes", 0) or 0))
        automation_context = dict(meta.get("automation_context") or {})
        automation_label, automation_release_title, automation_destination = _automation_identity(automation_context)
        package_name = str(meta.get("name") or job.get("collection_name") or "NZB package")
        return {
            "id": str(job["id"]), "name": package_name, "display_name": automation_label or package_name, "status": package_status,
            "priority": str(meta.get("priority") or "normal"), "category": ("One-time Media" if str(automation_context.get("source") or "")=="manual_media_grab" else "Automation" if automation_context else ""),
            "automation_context": automation_context, "automation_source": str(automation_context.get("source") or ""),
            "automation_label": automation_label, "automation_release_title": automation_release_title,
            "automation_destination": automation_destination, "source_filename": str(job.get("source_filename") or job.get("filename") or ""),
            "job_ids": [str(job["id"])],
            "files": file_count, "payload_files": file_count, "optional_files": 0, "optional_skipped_files": 0, "recovery_files": 0,
            "completed_files": file_count if status == "completed" else 0, "failed_files": file_count if status == "failed" else 0,
            "queued_files": file_count if status == "queued" else 0, "active_files": file_count if status in {"downloading", "retry_wait"} else 0,
            "expected_bytes": expected, "downloaded_bytes": downloaded, "speed_bps": int(job.get("speed_bps", 0) or 0), "eta_seconds": int(job.get("eta_seconds", 0) or 0), "peak_speed_bps": 0,
            "connections_used": int(job.get("connections_used", 0) or 0), "retry_count": 0, "recovered_parts": 0, "failed_parts": 0,
            "post_status": str(job.get("post_status") or ""), "post_progress": int(job.get("post_progress", 0) or 0),
            "post_progress_known": bool(job.get("post_progress_known")), "post_indeterminate": bool(job.get("post_indeterminate")),
            "post_message": str(job.get("post_message") or ""),
            "import_status": str(job.get("import_status") or ""),
            "imported": bool(job.get("imported")),
            "import_heartbeat_age_seconds": float(job.get("import_heartbeat_age_seconds", 0) or 0),
            "import_stalled": bool(job.get("import_stalled")),
            "release_failure_recorded": bool(job.get("release_failure_recorded")),
            "release_failure_reason": str(job.get("release_failure_reason") or ""),
            "health": {"state": "needs_attention" if str(job.get("import_status") or "")=="failed" else ("healthy" if status not in {"failed"} else "incomplete"), "label": "Import needs attention" if str(job.get("import_status") or "")=="failed" else ("✓ HEALTHY" if status not in {"failed"} else "Needs attention"), "missing_articles": 0,
                       "missing_bytes": 0, "recovery_blocks_available": 0, "recovery_blocks_queued": 0, "recovery_blocks_deferred": 0},
            "created_ts": _num(job.get("created_ts"), time.time()), "started_ts": _num(job.get("started_ts"), 0), "completed_ts": _num(job.get("completed_ts"), 0),
            "history_rank": int(_num(job.get("history_rank"), 10**9)),
            "average_speed_bps": 0, "duration_seconds": 0, "folder": str(job.get("path") or self.download_dir_getter()),
            "deferred_recovery_files": 0, "direct_unpack_status": "active" if str(job.get("post_status")) == "extracting" else "", "direct_unpack_progress": int(job.get("post_progress", 0) or 0),
        }

    def _statistics(self, history_root: dict[str, Any]) -> dict[str, Any]:
        stats = self.state.get("statistics") if isinstance(self.state.get("statistics"), dict) else {}
        legacy_stats = self.legacy_statistics
        tracking = _num(stats.get("tracking_since_ts"), _num(legacy_stats.get("tracking_since_ts"), time.time()))
        total = max(int(stats.get("total_downloaded_bytes", 0) or 0), int(legacy_stats.get("total_downloaded_bytes", 0) or 0))
        completed = max(int(stats.get("completed_files", 0) or 0), int(legacy_stats.get("completed_files", 0) or 0))
        transfer = max(_num(stats.get("transfer_seconds"), 0), _num(legacy_stats.get("transfer_seconds"), 0))
        peak = max(int(stats.get("peak_speed_bps", 0) or 0), int(legacy_stats.get("peak_speed_bps", 0) or 0))
        # SAB exposes aggregate downloaded bytes in some history builds. Treat it as additive only when larger.
        for key in ("total_size", "total_downloaded"):
            if history_root.get(key) is not None:
                candidate = _mb_to_bytes(history_root.get(key))
                if candidate > total:
                    total = candidate
        return {"tracking_since_ts": tracking, "total_downloaded_bytes": total, "completed_files": completed,
                "transfer_seconds": transfer, "peak_speed_bps": peak, "recovered_blocks": int(legacy_stats.get("recovered_blocks", 0) or 0),
                "average_speed_bps": int(total / transfer) if transfer > 0 else 0}

    @staticmethod
    def _display_order_key(item: dict[str, Any]) -> tuple[Any, ...]:
        """Keep live queue order intact while ordering terminal history newest-first."""
        status = str(item.get("status") or "queued")
        priority_rank = {"high": 0, "normal": 1, "low": 2}
        if status in {"downloading", "queued", "retry_wait", "cancelling", "post_processing", "repair_needed"}:
            queue_order = _num(item.get("queue_order"), _num(item.get("created_ts"), 0))
            return (0, priority_rank.get(str(item.get("priority") or "normal"), 1), queue_order)
        completed = _num(item.get("completed_ts"), 0)
        created = _num(item.get("created_ts"), 0)
        started = _num(item.get("started_ts"), 0)
        history_rank = int(_num(item.get("history_rank"), 10**9))
        if completed > 0:
            return (1, 0, -completed, -created, str(item.get("id") or ""))
        if history_rank < 10**9:
            return (1, 1, history_rank, -created, str(item.get("id") or ""))
        terminal_hint = max(started, created)
        return (1, 2, -terminal_hint, -created, str(item.get("id") or ""))

    def snapshot(self) -> dict[str, Any]:
        now = time.time()
        if self._last_snapshot is not None and now - self._last_snapshot_ts < self._snapshot_cache_seconds:
            return self._last_snapshot
        with self._snapshot_lock:
            now = time.time()
            if self._last_snapshot is not None and now - self._last_snapshot_ts < self._snapshot_cache_seconds:
                return self._last_snapshot
            result = self._snapshot_uncached()
            # Sequence/timestamp let the browser reject genuinely older state even
            # if a slow HTTP response arrives after a newer request.
            decorated = dict(result)
            self._snapshot_sequence += 1
            decorated["snapshot_seq"] = self._snapshot_sequence
            decorated["snapshot_generated_ts"] = time.time()
            self._last_snapshot = decorated
            self._last_snapshot_ts = time.time()
            return decorated

    def _offline_job_from_meta(self, nzo_id: str, meta: dict[str, Any], now: float) -> dict[str, Any]:
        """Reconstruct one persisted job while SAB is temporarily unavailable.

        A process restart clears the in-memory last-view cache, but the shared ledger
        survives.  Terminal jobs must remain terminal during that reconnect window;
        otherwise old completed/imported downloads are falsely presented as a live
        Queue and can consume Automation queue depth until SAB responds again.
        """
        prior = self._job_last_view.get(nzo_id)
        if prior is not None:
            job = dict(prior)
            if str(job.get("status") or "") not in {"completed", "failed", "cancelled"}:
                job["speed_bps"] = 0
                job["connections_used"] = 0
                job["status_detail"] = "Download engine reconnecting…"
            return job

        expected = max(0, int(meta.get("expected_bytes", 0) or 0))
        completed_ts = _num(meta.get("completed_ts"), 0)
        terminal_status = str(meta.get("terminal_status") or "").casefold()
        import_status = str(meta.get("import_status") or "").casefold()
        transfer_complete = bool(
            terminal_status in {"completed", "failed", "cancelled"}
            or completed_ts > 0
            or meta.get("imported")
            or import_status in {"queued", "waiting", "importing", "failed", "completed"}
        )
        if transfer_complete:
            sab_status = "Failed" if terminal_status == "failed" else "Completed"
            slot = {
                "nzo_id": nzo_id,
                "status": sab_status,
                "filename": str(meta.get("name") or "NZB package"),
                "time_added": _num(meta.get("created_ts"), now),
                "completed": completed_ts or _num(meta.get("_updated_ts"), now),
                "mb": expected / (1024 * 1024) if expected else 0,
                "mbleft": 0,
                "percentage": 100,
                "storage": str(meta.get("resolved_output") or meta.get("output_hint") or ""),
                "stage_log": "Download engine reconnecting…",
            }
            job = self._job_from_slot(nzo_id, meta, slot, history=True)
            job["speed_bps"] = 0
            job["connections_used"] = 0
            job["status_detail"] = "Download complete • download engine reconnecting…" if job.get("status") == "completed" else "Download engine reconnecting…"
            return job

        created = _num(meta.get("created_ts"), now)
        return {
            "id": nzo_id, "identity": nzo_id, "collection_id": nzo_id,
            "collection_name": str(meta.get("name") or "NZB package"),
            "provider_id": str(meta.get("provider_id") or ""), "provider_name": "SABnzbd engine",
            "origin_provider_id": str(meta.get("provider_id") or ""), "group": "",
            "filename": str(meta.get("name") or "NZB package"), "kind": "file",
            "status": "queued", "expected_bytes": expected, "downloaded_bytes": 0, "actual_size": 0,
            "current_part": 0, "processed_parts": 0, "successful_parts": 0, "failed_parts": 0, "total_parts": 100,
            "speed_bps": 0, "eta_seconds": 0, "connections_used": 0, "path": "", "partial_path": "", "error": "",
            "created_ts": created, "started_ts": 0, "completed_ts": 0, "recovered_parts": 0, "retry_count": 0,
            "priority": str(meta.get("priority") or "normal"), "paused": bool(self.state.get("paused")),
            "queue_order": 0, "status_detail": "Waiting for built-in download engine",
            "transfer_phase": "sabnzbd", "integrity_status": "unknown", "post_status": "", "post_progress": 0,
            "post_message": "", "automation_context": dict(meta.get("automation_context") or {}),
            "source": "nzb", "collection_role": "payload", "is_auxiliary": False,
            "optional_missing": False, "missing_bytes": 0, "resumed_parts": 0,
        }

    def _control_degraded_snapshot(self, engine: dict[str, Any], now: float, error: str) -> dict[str, Any]:
        """Render durable NewzDeck state when SAB Queue/History cannot be read.

        Never renew an old raw SAB snapshot indefinitely. The r2 failure showed a
        job had already failed in SAB while NewzDeck kept presenting an old Queued
        snapshot as if it were fresh, which also fed the false engine-pause warning.
        During a sustained localhost read outage, show durable jobs explicitly as
        control-state unknown and suppress transfer KPIs until a fresh Queue read
        returns.
        """
        self._sab_control_degraded_snapshots += 1
        with self.lock:
            tracked = dict(self._tracked())
        jobs: list[dict[str, Any]] = []
        collections: list[dict[str, Any]] = []
        counts = {"queued": 0, "downloading": 0, "retry_wait": 0, "cancelling": 0,
                  "completed": 0, "failed": 0, "cancelled": 0}
        for nzo_id, meta in tracked.items():
            job = self._offline_job_from_meta(str(nzo_id), meta, now)
            status = str(job.get("status") or "queued")
            if status not in {"completed", "failed", "cancelled"}:
                job["status"] = "queued"
                job["speed_bps"] = 0
                job["eta_seconds"] = 0
                job["connections_used"] = 0
                job["status_detail"] = "SAB control channel refreshing • transfer state temporarily unknown"
                status = "queued"
            jobs.append(job)
            collections.append(self._collection_from_job(job, meta))
            counts[status if status in counts else "queued"] += 1
        jobs.sort(key=self._display_order_key)
        collections.sort(key=self._display_order_key)
        configured_capacity = sum(
            max(1, _clamp_int(p.get("connections"), 1, 100, 20)
                - (min(3, max(0, _clamp_int(p.get("connections"), 1, 100, 20) - 1)) if p.get("use_browsing", True) else 0))
            for p in self.providers_getter()
            if isinstance(p, dict) and p.get("enabled", True) and p.get("use_downloads", True)
        )
        telemetry = {
            "engine_label": f"SABnzbd {SAB_VERSION} • adapter 3.6.21 • control channel refreshing",
            "network_rate_bps": 0, "decode_rate_bps": 0, "disk_rate_bps": 0,
            "soft_misses": 0, "native_parts": 0, "slot_utilization_pct": 0,
            "sab_control_degraded": True, "sab_control_error": str(error or "")[:300],
            "sab_read_resets": int(self._sab_read_resets),
            "sab_read_stale_uses": int(self._sab_read_stale_uses),
            "sab_control_degraded_snapshots": int(self._sab_control_degraded_snapshots),
            "sab_stale_snapshot_suppressed": int(self._sab_stale_snapshot_suppressed),
            "engine_pause_mismatch": False, "engine_idle_paused": False,
            "active_card_continuity_bridges": int(self._active_continuity_bridges),
            "active_card_continuity_last_ts": float(self._active_continuity_last_ts),
            "bandwidth": {"enabled": False, "active": False},
        }
        return {
            "paused": bool(self.state.get("paused", False)),
            "jobs": jobs, "collections": collections, "counts": counts,
            "concurrent_downloads": 1, "folder": str(self.download_dir_getter()),
            "total_speed_bps": 0, "average_speed_bps": 0,
            "remaining_bytes": 0, "remaining_unknown": True, "queue_eta_seconds": 0,
            "post_processing_active": 0,
            "connections": {"active": 0, "live_active": 0, "open": 0,
                            "effective_capacity": configured_capacity, "capacity": configured_capacity,
                            "configured": configured_capacity, "pools": [],
                            "yenc": {"available": True, "workers": 0}},
            "telemetry": telemetry, "statistics": self._statistics({}),
            "engine": {**dict(engine or {}), "last_error": str(error or ""), "control_degraded": True},
        }

    def _snapshot_uncached(self) -> dict[str, Any]:
        now = time.time()
        self._refresh_shared_state()
        engine = self.engine_status()
        if not engine.get("ready"):
            # Never show a queue badge with an empty Downloads page. If the private
            # engine is provisioning/reconnecting, render tracked NewzDeck jobs from
            # their last known view (or a queued placeholder) until SAB is reachable.
            with self.lock:
                tracked = dict(self._tracked())
            jobs: list[dict[str, Any]] = []
            collections: list[dict[str, Any]] = []
            counts = {"queued": 0, "downloading": 0, "retry_wait": 0, "cancelling": 0, "completed": 0, "failed": 0, "cancelled": 0}
            for nzo_id, meta in tracked.items():
                # Reconstruct from durable ledger state.  A fresh process has no
                # _job_last_view yet, so completed/imported records must not fall
                # through to a synthetic Queued placeholder while SAB reconnects.
                job = self._offline_job_from_meta(nzo_id, meta, now)
                jobs.append(job)
                collections.append(self._collection_from_job(job, meta))
                status = str(job.get("status") or "queued")
                counts[status if status in counts else "queued"] += 1
            jobs.sort(key=self._display_order_key)
            collections.sort(key=self._display_order_key)
            configured_capacity = sum(max(1, _clamp_int(p.get("connections"), 1, 100, 20) - (min(3, max(0, _clamp_int(p.get("connections"), 1, 100, 20) - 1)) if p.get("use_browsing", True) else 0)) for p in self.providers_getter() if isinstance(p, dict) and p.get("enabled", True) and p.get("use_downloads", True))
            result = {"paused": bool(self.state.get("paused")), "jobs": jobs, "counts": counts, "concurrent_downloads": 1,
                      "folder": str(self.download_dir_getter()), "total_speed_bps": 0, "average_speed_bps": 0,
                      "remaining_bytes": sum(max(0, int(j.get("expected_bytes", 0) or 0) - int(j.get("downloaded_bytes", 0) or 0)) for j in jobs if j.get("status") in {"queued", "downloading", "retry_wait"}),
                      "queue_eta_seconds": 0, "post_processing_active": 0,
                      "connections": {"active": 0, "live_active": 0, "open": 0, "effective_capacity": configured_capacity, "capacity": configured_capacity, "configured": configured_capacity, "pools": [], "yenc": {"available": True, "workers": 0}},
                      "collections": collections, "telemetry": {"engine_label": f"SABnzbd {SAB_VERSION} • adapter 3.6.21 • {'provisioning' if engine.get('provisioning') else 'reconnecting'}", "network_rate_bps": 0, "decode_rate_bps": 0, "disk_rate_bps": 0, "soft_misses": 0, "native_parts": 0, "slot_utilization_pct": 0, "active_card_continuity_bridges": int(self._active_continuity_bridges), "active_card_continuity_last_ts": float(self._active_continuity_last_ts), "unexpected_sab_pause_bridges": int(self._unexpected_sab_pause_bridges), "unexpected_sab_pause_last_ts": float(self._unexpected_sab_pause_last_ts), "unexpected_sab_pause_active": bool(self._unexpected_sab_pause_bridge_open), "removed_orphan_cleanup_count": int(self._orphan_removed_cleanup_count), "removed_orphan_cleanup_last_ts": float(self._orphan_removed_cleanup_last_ts), "bandwidth": {"enabled": False, "active": False}},
                      "statistics": self._statistics({}), "engine": engine}
            self._last_snapshot, self._last_snapshot_ts = result, now
            return result
        try:
            queue_payload, history_payload = self._queue_and_history(live=True)
            qroot, qslots = self._queue_slots(queue_payload)
            hroot, hslots = self._history_slots(history_payload)
            queue_read_fresh = bool(qroot.get("_newzdeck_fresh", True))
            history_read_fresh = bool(hroot.get("_newzdeck_fresh", True))

            # Never perform destructive reconciliation from a short cached Queue
            # fallback. Only a fresh SAB Queue response may prove a live job exists.
            if queue_read_fresh:
                cleanup_ids = self._enforce_removed_tombstones(qslots)
                if cleanup_ids:
                    queue_payload, history_payload = self._queue_and_history(live=False)
                    qroot, qslots = self._queue_slots(queue_payload)
                    hroot, hslots = self._history_slots(history_payload)
                    queue_read_fresh = bool(qroot.get("_newzdeck_fresh", True))
                    history_read_fresh = bool(hroot.get("_newzdeck_fresh", True))
                    remaining_live=self._slot_ids(qslots)
                    for cleaned_id in cleanup_ids:
                        if cleaned_id not in remaining_live:
                            self._orphan_removed_cleanup_count += 1
                            self._orphan_removed_cleanup_last_ts = time.time()
                            self._event("warning", "Stopped hidden SAB transfer left by an older unverified Remove/Cancel", nzo_id=cleaned_id)
                        else:
                            self._event("warning", "Hidden removed SAB transfer is still live after cleanup request", nzo_id=cleaned_id)
                stale_duplicate_ids = self._cleanup_proven_stale_queue_duplicates(qslots)
                if stale_duplicate_ids:
                    queue_payload, history_payload = self._queue_and_history(live=False)
                    qroot, qslots = self._queue_slots(queue_payload)
                    hroot, hslots = self._history_slots(history_payload)
                    queue_read_fresh = bool(qroot.get("_newzdeck_fresh", True))
                    history_read_fresh = bool(hroot.get("_newzdeck_fresh", True))

            self._adopt_untracked_slots(qslots, hslots)
            if history_read_fresh:
                self._kick_completed_automation_imports(qslots, hslots)

            bridge_remaining_hint = _mb_to_bytes(qroot.get("mbleft"))
            if bridge_remaining_hint <= 0:
                bridge_remaining_hint = sum(
                    _mb_to_bytes(x.get("mbleft")) for x in qslots if isinstance(x, dict)
                )
            # Cached queue data is presentation fallback only. It must never drive
            # Resume/engine-pause recovery as though it were current engine truth.
            if queue_read_fresh:
                bridged_pause = self._bridge_unexpected_sab_pause(
                    qroot, engine, now,
                    has_transfer_work=bool(qslots) or bridge_remaining_hint > 0,
                )
                if bridged_pause is not None:
                    return bridged_pause
                self._last_coherent_sab_snapshot_ts = now
        except Exception as exc:
            self._last_error = str(exc)
            coherent_age = now - float(self._last_coherent_sab_snapshot_ts or 0.0)
            if self._last_snapshot is not None and coherent_age <= 1.5:
                self._sab_read_stale_uses += 1
                stale = dict(self._last_snapshot)
                stale["paused"] = bool(self.state.get("paused", False))
                stale["engine"] = {**engine, "last_error": str(exc), "control_degraded": True}
                stale_tel = dict(stale.get("telemetry") or {})
                stale_tel["sab_control_degraded"] = True
                stale_tel["sab_control_error"] = str(exc)[:300]
                stale_tel["engine_pause_mismatch"] = False
                stale_tel["unexpected_sab_pause_active"] = False
                stale["telemetry"] = stale_tel
                return stale
            self._sab_stale_snapshot_suppressed += 1
            return self._control_degraded_snapshot(engine, now, str(exc))
        queue_by = {str(x.get("nzo_id") or x.get("id") or ""): x for x in qslots}
        hist_by = {str(x.get("nzo_id") or x.get("id") or ""): x for x in hslots}
        total_speed = _kb_to_bps(qroot.get("kbpersec"))
        aggregate_status = str(qroot.get("status") or "").casefold()
        queue_paused = bool(qroot.get("paused", False)) or aggregate_status == "paused"

        # SAB exposes both an aggregate queue state and per-slot state. During a
        # healthy transfer the aggregate queue can remain Downloading while the
        # foreground slot transiently says Queued between internal article/file
        # transitions. Resolve a single foreground package from the aggregate
        # signal so NewzDeck's Active tab stays stable.
        explicit_active_slots = sorted(
            [
                x for x in qslots
                if str(x.get("status") or "").casefold() in {"downloading", "fetching"}
                and str(x.get("nzo_id") or x.get("id") or "")
            ],
            key=lambda x: _num(x.get("index"), 10**9),
        )
        explicit_active_ids = [str(x.get("nzo_id") or x.get("id") or "") for x in explicit_active_slots]
        foreground_id = explicit_active_ids[0] if explicit_active_ids else ""
        if len(explicit_active_ids) > 1:
            self._multiple_active_slot_corrections += 1
            self._multiple_active_slot_last_ts = now
        # Keep SAB's aggregate Downloading state as a recovery signal, but do not use
        # that aggregate flag alone to promote an arbitrary Queued slot to Active.
        # v3.5.6 could therefore render a false Active package with 0 B/s / 0 sockets.
        queue_active_signal = bool(foreground_id) or (not queue_paused and aggregate_status in {"downloading", "fetching"})
        queue_remaining_hint = _mb_to_bytes(qroot.get("mbleft"))
        if queue_remaining_hint <= 0:
            queue_remaining_hint = sum(_mb_to_bytes(x.get("mbleft")) for x in qslots if isinstance(x, dict))
        has_engine_transfer_work = bool(queue_read_fresh and (qslots or queue_remaining_hint > 0))
        engine_pause_mismatch = self._observe_engine_pause_intent(
            qroot, now, has_transfer_work=has_engine_transfer_work,
        )
        if queue_read_fresh:
            provider_health = self._recover_zero_socket_transfer(
                queue_active=queue_active_signal, queue_paused=queue_paused, total_speed=total_speed,
                remaining_bytes=queue_remaining_hint,
            )
        else:
            # A cached Queue sample cannot prove a provider stall. Read cached health
            # only and wait for fresh Queue truth before any recovery decision.
            provider_health = self._provider_health(force=False)
        actual_active_connections = int(provider_health.get("active_connections", 0) or 0)
        provider_summary = str(provider_health.get("summary") or "").strip()
        disk_fault = bool("disk error" in provider_summary.casefold())
        if disk_fault:
            self._engine_fault = provider_summary
            self._engine_fault_last_ts = now
            self._resume_intent_event.clear()
            engine_pause_mismatch = False
        elif self._engine_fault and now - self._engine_fault_last_ts > 15.0:
            self._engine_fault = ""
        presentation = self._presentation_transfer_telemetry(
            raw_speed_bps=total_speed, remaining_bytes=queue_remaining_hint,
            queue_active=queue_active_signal, queue_paused=queue_paused,
            live_connections=actual_active_connections,
        )
        display_speed = int(presentation.get("speed_bps", 0) or 0)
        display_connections = int(presentation.get("connections", 0) or 0)
        if not foreground_id and not queue_paused and (display_speed > 0 or display_connections > 0):
            ordered = sorted(qslots, key=lambda x: _num(x.get("index"), 10**9))
            for candidate in ordered:
                candidate_status = str(candidate.get("status") or "").casefold()
                candidate_id = str(candidate.get("nzo_id") or candidate.get("id") or "")
                if candidate_id and candidate_status not in {"paused", "propagating"}:
                    foreground_id = candidate_id
                    break

        jobs: list[dict[str, Any]] = []
        collections: list[dict[str, Any]] = []
        counts = {"queued": 0, "downloading": 0, "retry_wait": 0, "cancelling": 0, "completed": 0, "failed": 0, "cancelled": 0}
        with self.lock:
            tracked = dict(self._tracked())

        # SAB can occasionally expose aggregate Downloading/speed/remaining while its
        # per-job slots list is temporarily empty during internal queue reshaping.
        # Choose one durable foreground owner from the last coherent NewzDeck view so
        # that aggregate activity never turns into "0 active" or destroys ownership.
        aggregate_live_signal = bool(
            not queue_paused and (
                aggregate_status in {"downloading", "fetching"}
                or total_speed > 0 or display_speed > 0
                or actual_active_connections > 0 or display_connections > 0
            )
        )
        aggregate_owner_id = str(foreground_id or "")
        if aggregate_live_signal and not aggregate_owner_id:
            candidates: list[tuple[tuple[Any, ...], str]] = []
            for candidate_id, candidate_meta in tracked.items():
                if not isinstance(candidate_meta, dict) or candidate_meta.get("pending_submit"):
                    continue
                if str(candidate_meta.get("terminal_status") or "").casefold() in {"completed", "failed", "cancelled"}:
                    continue
                prior = self._job_last_view.get(candidate_id) or {}
                prior_status = str(prior.get("status") or "").casefold()
                if prior_status in {"completed", "failed", "cancelled"}:
                    continue
                score = (
                    1 if prior_status == "downloading" else 0,
                    1 if self._active_latch_until.get(candidate_id, 0.0) > now else 0,
                    self._job_last_seen_ts.get(candidate_id, 0.0),
                    -_num(candidate_meta.get("created_ts"), now),
                )
                candidates.append((score, str(candidate_id)))
            if candidates:
                candidates.sort(reverse=True)
                aggregate_owner_id = candidates[0][1]

        for nzo_id, meta in tracked.items():
            if bool(meta.get("pending_submit")):
                job = self._offline_job_from_meta(nzo_id, meta, now)
                job["status"] = "queued"
                job["status_detail"] = "Queued • handing off to built-in download engine"
                jobs.append(job)
                collections.append(self._collection_from_job(job, meta))
                counts["queued"] += 1
                continue
            queue_slot = queue_by.get(nzo_id)
            history_slot = hist_by.get(nzo_id)
            history_status = str((history_slot or {}).get("status") or "").casefold()
            prior_status = str((self._job_last_view.get(nzo_id) or {}).get("status") or "").casefold()

            # Completion is monotonic for a SAB NZO id. During SAB's queue→history
            # handoff the same id can transiently appear in both feeds, or a stale
            # queue slot can be observed one poll after history already says Completed.
            # Prefer terminal completion so the UI never resurrects it as Queued.
            meta_terminal = str(meta.get("terminal_status") or "").casefold()
            if queue_slot is not None and meta_terminal == "completed" and bool(meta.get("imported")):
                # This should have been removed by _cleanup_proven_stale_queue_duplicates.
                # If SAB rejected deletion, never hide live transfer bytes behind a
                # Completed card. Surface it as a stopping/corrupt duplicate.
                slot = queue_slot
                history = False
            elif history_slot is not None and history_status == "completed":
                slot = history_slot
                history = True
            elif prior_status == "completed" and history_slot is None:
                # If history itself is briefly omitted, keep the last completed view
                # rather than trusting a stale non-terminal queue echo for the same id.
                prior = self._job_last_view.get(nzo_id)
                if prior is not None:
                    job = dict(prior)
                    self._job_missing_since.pop(nzo_id, None)
                    jobs.append(job)
                    collections.append(self._collection_from_job(job, meta))
                    counts["completed"] += 1
                    continue
                slot = queue_slot
                history = False
            elif queue_slot is not None:
                slot = queue_slot
                history = False
            else:
                slot = history_slot
                history = slot is not None
            if slot is None:
                missing_since = self._job_missing_since.setdefault(nzo_id, now)
                # A slot can disappear from SAB while aggregate transfer telemetry keeps
                # proving that the queue is active. Never convert that observation gap
                # into lost ownership. Bridge the selected foreground package from the
                # last coherent view (or durable metadata) until SAB exposes its slot again.
                last_seen = self._job_last_seen_ts.get(nzo_id, 0.0)
                prior = self._job_last_view.get(nzo_id)
                prior_status = str((prior or {}).get("status") or "")
                aggregate_bridge = bool(aggregate_live_signal and nzo_id == aggregate_owner_id)
                continuity_bridge = self._active_continuity_allowed(
                    nzo_id, now, prior_status=prior_status, queue_paused=queue_paused,
                    foreground_id=foreground_id, slot_status="",
                )
                if aggregate_bridge or continuity_bridge:
                    job = dict(prior) if prior is not None else self._offline_job_from_meta(nzo_id, meta, now)
                    if str(job.get("status") or "").casefold() not in {"completed", "failed", "cancelled"}:
                        job["status"] = "downloading"
                        if continuity_bridge and not aggregate_bridge:
                            job["status_detail"] = "Downloading • holding Active through SAB queue handoff"
                            self._mark_active_bridge(nzo_id, now)
                        else:
                            job["status_detail"] = "Downloading • SAB is refreshing queue details"
                            # Aggregate speed/socket/Downloading telemetry is positive
                            # evidence that the selected durable owner is still live.
                            # Refresh the continuity lease so a long slot omission does
                            # not expire merely because SAB kept exposing only aggregate data.
                            self._confirm_active_owner(nzo_id, now)
                        if display_speed > 0:
                            job["speed_bps"] = display_speed
                        if display_connections > 0:
                            job["connections_used"] = display_connections
                        expected_for_job = max(0, int(job.get("expected_bytes", 0) or 0))
                        if expected_for_job > 0 and queue_remaining_hint > 0:
                            aggregate_done = max(0, expected_for_job - min(expected_for_job, queue_remaining_hint))
                            job["downloaded_bytes"] = max(int(job.get("downloaded_bytes", 0) or 0), aggregate_done)
                            if display_speed > 0:
                                job["eta_seconds"] = int(min(expected_for_job, queue_remaining_hint) / display_speed)
                        self._active_latch_until[nzo_id] = now + 8.0
                        self._job_last_seen_ts[nzo_id] = now
                        self._job_last_view[nzo_id] = dict(job)
                    jobs.append(job)
                    collections.append(self._collection_from_job(job, meta))
                    counts[job["status"] if job["status"] in counts else "queued"] += 1
                    continue

                # Short non-active omissions are also presentation noise. Keep the last
                # real view briefly, but do not manufacture a removal tombstone if the
                # slot stays absent. Tombstones are reserved for explicit user intent.
                preserve_seconds = 8.0 if prior_status == "downloading" else 3.0
                if prior is not None and now - last_seen <= preserve_seconds and prior_status not in {"completed", "failed", "cancelled"}:
                    job = dict(prior)
                    jobs.append(job)
                    collections.append(self._collection_from_job(job, meta))
                    counts[job["status"] if job["status"] in counts else "queued"] += 1
                    continue

                context = meta.get("automation_context") if isinstance(meta.get("automation_context"), dict) else {}
                retain_seconds = 48 * 3600 if _is_smart_import_context(context) else 120.0
                if not aggregate_live_signal and now - missing_since > retain_seconds:
                    with self.lock:
                        self._tracked().pop(nzo_id, None)
                        self._job_last_view.pop(nzo_id, None)
                        self._job_last_seen_ts.pop(nzo_id, None)
                        self._active_latch_until.pop(nzo_id, None)
                        self._job_active_confirmed_ts.pop(nzo_id, None)
                        self._active_bridge_open.discard(nzo_id)
                        self._job_queued_observations.pop(nzo_id, None)
                        self._save_state()
                    self._event("warning", "Released stale SAB ownership record without removal tombstone",
                                nzo_id=nzo_id, automation=bool(context), missing_seconds=int(now - missing_since))
                continue
            self._job_missing_since.pop(nzo_id, None)
            if history and str(slot.get('status') or '').casefold()=='failed':
                self._remember_failed_automation_release(nzo_id,meta,slot)
            if history and history_read_fresh and str(slot.get('status') or '').casefold() == 'completed' and bool(meta.get('browser_flat_images')):
                self._flatten_completed_browser_images(nzo_id, meta, slot)
            job = self._job_from_slot(nzo_id, meta, slot, history=history)
            if not history and str(meta.get("terminal_status") or "").casefold() == "completed" and bool(meta.get("imported")):
                job["status"] = "cancelling"
                job["status_detail"] = "Stopping stale duplicate • this release was already imported"
                job["speed_bps"] = 0
                job["eta_seconds"] = 0
            if not history:
                slot_status = str(slot.get("status") or "").casefold()
                prior = self._job_last_view.get(nzo_id) or {}
                prior_was_active = str(prior.get("status") or "").casefold() == "downloading"
                prior_done = max(0, int(prior.get("downloaded_bytes", 0) or 0))
                current_done = max(0, int(job.get("downloaded_bytes", 0) or 0))
                expected_now = max(0, int(job.get("expected_bytes", 0) or 0))
                if prior_done > current_done and prior_was_active:
                    corrected_done = min(expected_now, prior_done) if expected_now > 0 else prior_done
                    if corrected_done > current_done:
                        job["downloaded_bytes"] = corrected_done
                        current_done = corrected_done
                        if expected_now > 0:
                            corrected_pct = max(0, min(100, int(round(corrected_done * 100.0 / expected_now))))
                            job["current_part"] = max(int(job.get("current_part", 0) or 0), corrected_pct)
                            job["processed_parts"] = max(int(job.get("processed_parts", 0) or 0), corrected_pct)
                            job["successful_parts"] = max(int(job.get("successful_parts", 0) or 0), corrected_pct)
                        self._progress_regression_corrections += 1
                        self._progress_regression_last_ts = now
                progress_advanced = current_done > prior_done
                # Queue mode is one package at a time. SAB can briefly echo multiple
                # slots as Downloading around internal handoffs; only the selected
                # queue-order foreground owner is Active. If SAB exposes no explicit
                # foreground, actual byte progress may identify one.
                direct_active = (nzo_id == foreground_id) or (not foreground_id and progress_advanced)
                if slot_status in {"downloading", "fetching"} and foreground_id and nzo_id != foreground_id:
                    job["status"] = "queued"
                    job["speed_bps"] = 0
                    job["eta_seconds"] = 0
                    job["connections_used"] = 0
                    job["status_detail"] = "Queued • waiting behind foreground package"
                continuity_active = False
                genuinely_active = direct_active
                if direct_active:
                    self._confirm_active_owner(nzo_id, now)
                    self._active_latch_until[nzo_id] = now + 8.0
                    self._job_queued_observations[nzo_id] = 0
                elif (job.get("status") == "queued" and prior_was_active and not queue_paused
                      and slot_status not in {"paused", "propagating"}
                      and (not foreground_id or foreground_id == nzo_id)):
                    observations = self._job_queued_observations.get(nzo_id, 0) + 1
                    self._job_queued_observations[nzo_id] = observations
                    continuity_active = self._active_continuity_allowed(
                        nzo_id, now, prior_status="downloading", queue_paused=queue_paused,
                        foreground_id=foreground_id, slot_status=slot_status,
                    )
                    # The original observation/latch gate remains as the fast path. The
                    # continuity lease handles the longer SAB file-boundary gaps that can
                    # outlive 8 seconds while the underlying transfer keeps progressing.
                    if observations < 4 or self._active_latch_until.get(nzo_id, 0.0) > now or continuity_active:
                        genuinely_active = True
                        if continuity_active:
                            self._mark_active_bridge(nzo_id, now)
                else:
                    self._job_queued_observations[nzo_id] = 0
                if genuinely_active and job.get("status") == "queued":
                    job["status"] = "downloading"
                    job["status_detail"] = (
                        "Downloading • holding Active through SAB queue handoff"
                        if continuity_active else str(slot.get("stage_log") or slot.get("status") or "Downloading")
                    )
                    if nzo_id == foreground_id and display_speed > 0:
                        job["speed_bps"] = display_speed
                    elif continuity_active and display_speed <= 0:
                        prior_speed = max(0, int(prior.get("speed_bps", 0) or 0))
                        confirmed = float(self._job_active_confirmed_ts.get(nzo_id, 0.0) or 0.0)
                        if prior_speed > 0 and now - confirmed <= 12.0:
                            job["speed_bps"] = prior_speed
                            remaining_for_job = max(0, int(job.get("expected_bytes", 0) or 0) - int(job.get("downloaded_bytes", 0) or 0))
                            if remaining_for_job > 0:
                                job["eta_seconds"] = int(remaining_for_job / prior_speed)
                if genuinely_active and nzo_id == foreground_id:
                    job["connections_used"] = display_connections
                    if display_speed > 0:
                        job["speed_bps"] = display_speed
                        remaining_for_job = max(0, int(job.get("expected_bytes", 0) or 0) - int(job.get("downloaded_bytes", 0) or 0))
                        if remaining_for_job > 0:
                            job["eta_seconds"] = int(remaining_for_job / display_speed)
                    if total_speed <= 0 and actual_active_connections <= 0:
                        if self._provider_sync_errors:
                            job["status_detail"] = self._provider_sync_errors[-1]
                        elif provider_summary:
                            job["status_detail"] = "Provider connection: " + provider_summary
                        elif bool(provider_health.get("transient_idle", False)):
                            job["status_detail"] = "Reconnecting to Usenet provider…"
                        else:
                            job["status_detail"] = "Connecting to Usenet provider…"
            else:
                self._active_latch_until.pop(nzo_id, None)
                self._job_active_confirmed_ts.pop(nzo_id, None)
                self._active_bridge_open.discard(nzo_id)
                self._job_queued_observations.pop(nzo_id, None)
            self._job_last_seen_ts[nzo_id] = now
            self._job_last_view[nzo_id] = dict(job)
            if history and str(job.get("status") or "") in {"completed", "failed", "cancelled"}:
                # Persist terminal classification, not only the timestamp. This makes
                # restart/reconnect reconstruction monotonic even before SAB history
                # is reachable in the new process.
                with self.lock:
                    live_meta = self._tracked().get(nzo_id)
                    if isinstance(live_meta, dict):
                        changed_terminal = False
                        terminal = str(job.get("status") or "")
                        if str(live_meta.get("terminal_status") or "") != terminal:
                            live_meta["terminal_status"] = terminal
                            changed_terminal = True
                        completed_value = _num(job.get("completed_ts"), 0)
                        if completed_value > 0 and _num(live_meta.get("completed_ts"), 0) <= 0:
                            live_meta["completed_ts"] = completed_value
                            changed_terminal = True
                        if changed_terminal:
                            self._touch_job_locked(live_meta)
                            self._save_state()
            jobs.append(job)
            collections.append(self._collection_from_job(job, meta))
            counts[job["status"] if job["status"] in counts else "queued"] += 1
        # Fundamental Downloads invariant: every live SAB Queue slot must have a
        # NewzDeck-visible card. Normally _adopt_untracked_slots() makes this true.
        # If a cross-runtime race, explicit removal tombstone, or ledger problem
        # prevents adoption, surface a temporary card rather than hiding a live
        # transfer behind SAB aggregate Remaining/speed counters.
        represented_ids = {str(j.get("id") or "") for j in jobs}
        with self.lock:
            removed_reason_snapshot = {
                str(k): str(v or "") for k, v in (self.state.get("removed_job_reasons") or {}).items()
            }
        for raw_slot in qslots:
            orphan_id = str(raw_slot.get("nzo_id") or raw_slot.get("id") or "")
            if not orphan_id or orphan_id in represented_ids:
                continue
            synthetic_meta = {
                "name": str(raw_slot.get("filename") or raw_slot.get("name") or "SAB download"),
                "expected_bytes": max(_mb_to_bytes(raw_slot.get("mb")), _mb_to_bytes(raw_slot.get("mbleft"))),
                "file_count": max(1, _clamp_int(raw_slot.get("nrof") or raw_slot.get("files"), 1, 100000, 1)),
                "priority": "normal",
                "created_ts": _num(raw_slot.get("time_added"), now),
                "automation_context": self._recover_automation_context_for_slot(orphan_id, raw_slot),
            }
            orphan_job = self._job_from_slot(orphan_id, synthetic_meta, raw_slot, history=False)
            if removed_reason_snapshot.get(orphan_id):
                orphan_job["status"] = "cancelling"
                orphan_job["status_detail"] = "Stopping previously removed download • SAB still exposes the live job"
            else:
                orphan_job["status_detail"] = "Recovering NewzDeck ownership from the live SAB queue"
            self._job_last_seen_ts[orphan_id] = now
            self._job_last_view[orphan_id] = dict(orphan_job)
            jobs.append(orphan_job)
            collections.append(self._collection_from_job(orphan_job, synthetic_meta))
            represented_ids.add(orphan_id)
            self._snapshot_consistency_mismatches += 1
            self._snapshot_consistency_last_ts = now
            self._event(
                "warning",
                "Surfaced SAB Queue job that was missing from the NewzDeck ledger",
                nzo_id=orphan_id,
                tombstoned=bool(removed_reason_snapshot.get(orphan_id)),
                status=str(raw_slot.get("status") or ""),
            )

        # Product invariant: queue mode is one package at a time. If transient SAB
        # state/continuity reconstruction still produced multiple Active cards, keep
        # exactly one foreground owner and demote the rest to Queued presentation.
        active_jobs_now = [j for j in jobs if str(j.get("status") or "") == "downloading"]
        if len(active_jobs_now) > 1:
            keep_id = str(foreground_id or "")
            if not keep_id or not any(str(j.get("id") or "") == keep_id for j in active_jobs_now):
                active_jobs_now.sort(key=lambda j: _num(j.get("queue_order"), _num(j.get("created_ts"), 10**9)))
                keep_id = str(active_jobs_now[0].get("id") or "")
            collection_by_id = {str(c.get("id") or ""): c for c in collections}
            for visible_job in active_jobs_now:
                visible_id = str(visible_job.get("id") or "")
                if visible_id == keep_id:
                    continue
                visible_job["status"] = "queued"
                visible_job["speed_bps"] = 0
                visible_job["eta_seconds"] = 0
                visible_job["connections_used"] = 0
                visible_job["status_detail"] = "Queued • waiting behind foreground package"
                c = collection_by_id.get(visible_id)
                if isinstance(c, dict):
                    c["status"] = "queued"
                    c["active_files"] = 0
                    c["queued_files"] = max(1, int(c.get("files", 1) or 1))
                    c["speed_bps"] = 0
                    c["eta_seconds"] = 0
                    c["connections_used"] = 0
            self._multiple_active_slot_corrections += 1
            self._multiple_active_slot_last_ts = now

        # Completed history must be deterministic and reverse-chronological. SAB's
        # queue/history responses and NewzDeck's tracked dictionary are not a stable
        # user-facing history order, so normalize them before returning the snapshot.
        jobs.sort(key=self._display_order_key)
        collections.sort(key=self._display_order_key)

        # Canonicalize every KPI from the *same visible job set* used by the cards.
        # SAB's aggregate mbleft is diagnostic input only; it must never create a
        # "94 GB remaining / 0 Active / 0 Queued" contradiction.
        counts = {"queued": 0, "downloading": 0, "retry_wait": 0, "cancelling": 0, "completed": 0, "failed": 0, "cancelled": 0}
        for visible_job in jobs:
            visible_status = str(visible_job.get("status") or "queued")
            counts[visible_status if visible_status in counts else "queued"] += 1

        transfer_statuses = {"queued", "downloading", "retry_wait", "cancelling"}
        remaining = sum(
            max(0, int(j.get("expected_bytes", 0) or 0) - int(j.get("downloaded_bytes", 0) or 0))
            for j in jobs if str(j.get("status") or "") in transfer_statuses
        )
        total_speed = (
            display_speed or sum(int(j.get("speed_bps", 0) or 0) for j in jobs if str(j.get("status") or "") == "downloading")
        ) if counts.get("downloading", 0) > 0 else 0

        engine_remaining_gap = max(0, int(queue_remaining_hint or 0) - int(remaining or 0))
        if engine_remaining_gap >= 16 * 1024 * 1024:
            if now - self._snapshot_consistency_last_ts >= 5.0:
                self._snapshot_consistency_mismatches += 1
                self._snapshot_consistency_last_ts = now
                self._event(
                    "warning",
                    "Ignored SAB aggregate Remaining that was not represented by visible queue jobs",
                    engine_remaining_bytes=int(queue_remaining_hint or 0),
                    visible_remaining_bytes=int(remaining or 0),
                    gap_bytes=int(engine_remaining_gap),
                    queue_slots=len(qslots),
                    visible_transfer_jobs=sum(1 for j in jobs if str(j.get("status") or "") in transfer_statuses),
                )
        sab_eta = _duration_seconds(qroot.get("timeleft"))
        if sab_eta <= 0 and foreground_id:
            foreground_slot = queue_by.get(foreground_id) or {}
            sab_eta = _duration_seconds(foreground_slot.get("timeleft"))
        eta = sab_eta if sab_eta > 0 else (int(remaining / total_speed) if total_speed > 0 else 0)
        configured = sum(max(1, _clamp_int(p.get("connections"), 1, 100, 20) - (min(3, max(0, _clamp_int(p.get("connections"), 1, 100, 20) - 1)) if p.get("use_browsing", True) else 0)) for p in self.providers_getter() if isinstance(p, dict) and p.get("enabled", True) and p.get("use_downloads", True))
        active_dl = counts.get("downloading", 0)
        reported_capacity = int(provider_health.get("capacity", 0) or 0)
        connection_capacity = max(configured, reported_capacity)
        connections = {"active": display_connections, "open": display_connections,
                       "live_active": actual_active_connections,
                       "effective_capacity": connection_capacity, "capacity": configured, "configured": configured,
                       "engine_reported_capacity": reported_capacity,
                       "provider_stalled": bool(provider_health.get("stalled", False)),
                       "provider_transient_idle": bool(provider_health.get("transient_idle", False)),
                       "provider_zero_socket_seconds": float(provider_health.get("zero_socket_seconds", 0.0) or 0.0),
                       "provider_no_progress_seconds": float(provider_health.get("no_progress_seconds", 0.0) or 0.0),
                       "provider_summary": provider_summary,
                       "provider_test": dict(provider_health.get("provider_test") or {}),
                       "expected_servers": int(provider_health.get("expected_servers", 0) or 0),
                       "configured_servers": int(provider_health.get("configured_servers", 0) or 0),
                       "runtime_servers": int(provider_health.get("runtime_servers", 0) or 0),
                       "runtime_state_known": bool(provider_health.get("runtime_state_known", True)),
                       "provider_control_degraded": bool(provider_health.get("control_degraded", False)),
                       "provider_control_error": str(provider_health.get("control_error") or ""),
                       "server_errors": list(provider_health.get("errors") or []),
                       "servers": list(provider_health.get("servers") or []),
                       "pools": [{"name": "SABnzbd", "pipeline_depth": 1, "pipeline_enabled": False}] if configured else [],
                       "yenc": {"available": True, "workers": 0, "engine": "SABnzbd"}}
        statistics = self._statistics(hroot)
        statistics["peak_speed_bps"] = max(int(statistics.get("peak_speed_bps", 0) or 0), total_speed)
        post_active = sum(1 for j in jobs if str(j.get("post_status") or "") in {"queued", "verifying", "repairing", "extracting", "importing"})
        result = {"paused": bool(self.state.get("paused", False)), "jobs": jobs, "counts": counts, "concurrent_downloads": 1,
                  "folder": str(self.download_dir_getter()), "total_speed_bps": total_speed, "average_speed_bps": total_speed,
                  "remaining_bytes": remaining, "queue_eta_seconds": eta, "post_processing_active": post_active,
                  "connections": connections, "collections": collections,
                  "telemetry": {"engine_label": f"SABnzbd {SAB_VERSION} built-in engine • adapter 3.6.21", "network_rate_bps": total_speed,
                                "raw_network_rate_bps": _kb_to_bps(qroot.get("kbpersec")),
                                "speed_estimated": bool(presentation.get("estimated", False)),
                                "progress_rate_bps": int(presentation.get("progress_bps", 0) or 0),
                                "decode_rate_bps": 0, "disk_rate_bps": 0, "soft_misses": 0, "native_parts": 0,
                                "active_card_continuity_bridges": int(self._active_continuity_bridges),
                                "active_card_continuity_last_ts": float(self._active_continuity_last_ts),
                                "unexpected_sab_pause_bridges": int(self._unexpected_sab_pause_bridges),
                                "unexpected_sab_pause_last_ts": float(self._unexpected_sab_pause_last_ts),
                                "unexpected_sab_pause_active": bool(self._unexpected_sab_pause_bridge_open),
                                "sab_queue_fresh": bool(queue_read_fresh),
                                "sab_queue_age_seconds": float(qroot.get("_newzdeck_age_seconds", 0.0) or 0.0),
                                "sab_history_fresh": bool(history_read_fresh),
                                "sab_history_age_seconds": float(hroot.get("_newzdeck_age_seconds", 0.0) or 0.0),
                                "sab_control_degraded": not bool(queue_read_fresh),
                                "sab_read_resets": int(self._sab_read_resets),
                                "sab_read_stale_uses": int(self._sab_read_stale_uses),
                                "sab_control_degraded_snapshots": int(self._sab_control_degraded_snapshots),
                                "sab_stale_snapshot_suppressed": int(self._sab_stale_snapshot_suppressed),
                                "engine_queue_paused_raw": bool(queue_paused),
                                "engine_has_transfer_work": bool(has_engine_transfer_work),
                                "engine_idle_paused": bool(
                                    queue_paused
                                    and not has_engine_transfer_work
                                    and not self.state.get("paused", False)
                                ),
                                "engine_pause_mismatch": bool(engine_pause_mismatch),
                                "engine_pause_mismatch_seconds": max(0.0, now - self._engine_pause_mismatch_since) if self._engine_pause_mismatch_since > 0 else 0.0,
                                "engine_pause_reassert_count": int(self._engine_pause_reassert_count),
                                "engine_pause_reassert_last_ts": float(self._engine_pause_reassert_last_ts),
                                "engine_remaining_bytes_raw": int(queue_remaining_hint or 0),
                                "visible_remaining_bytes": int(remaining or 0),
                                "remaining_mismatch_bytes": int(engine_remaining_gap or 0),
                                "snapshot_consistency_mismatches": int(self._snapshot_consistency_mismatches),
                                "snapshot_consistency_last_ts": float(self._snapshot_consistency_last_ts),
                                "import_dead_owner_reclaims": int(self._import_dead_owner_reclaims),
                                "import_dead_owner_last_ts": float(self._import_dead_owner_last_ts),
                                "sab_api_success_age_seconds": max(0.0, now - self._last_api_success_ts) if self._last_api_success_ts > 0 else 0.0,
                                "engine_transient_probe_misses": int(self._ensure_transient_probe_misses),
                                "engine_recovery_deferred": int(self._ensure_recovery_deferred),
                                "engine_launch_recoveries": int(self._ensure_launch_recoveries),
                                "config_sync_attempts": int(self._config_sync_attempts),
                                "config_sync_failures": int(self._config_sync_failures),
                                "config_retry_storms_suppressed": int(self._config_retry_storms_suppressed),
                                "config_sync_last_error_ts": float(self._config_sync_last_error_ts),
                                "multiple_active_slot_corrections": int(self._multiple_active_slot_corrections),
                                "multiple_active_slot_last_ts": float(self._multiple_active_slot_last_ts),
                                "progress_regression_corrections": int(self._progress_regression_corrections),
                                "progress_regression_last_ts": float(self._progress_regression_last_ts),
                                "identity_cross_adoptions_blocked": int(self._identity_cross_adoptions_blocked),
                                "identity_authoritative_key_repairs": int(self._identity_authoritative_key_repairs),
                                "stale_engine_ports_seen": int(self._stale_engine_ports_seen),
                                "stale_engine_live_slots_paused": int(self._stale_engine_live_slots_paused),
                                "stale_engines_shutdown": int(self._stale_engines_shutdown),
                                "stale_engine_last_port": int(self._stale_engine_last_port),
                                "stale_engine_last_slots": int(self._stale_engine_last_slots),
                                "stale_duplicate_queue_cleanups": int(self._stale_duplicate_queue_cleanups),
                                "stale_duplicate_queue_last_ts": float(self._stale_duplicate_queue_last_ts),
                                "completion_control_failures": int(self._completion_control_failures),
                                "completion_backoff_seconds": float(self._completion_backoff_seconds),
                                "engine_fault": str(self._engine_fault or ""),
                                "engine_fault_last_ts": float(self._engine_fault_last_ts),
                                "removed_orphan_cleanup_count": int(self._orphan_removed_cleanup_count),
                                "removed_orphan_cleanup_last_ts": float(self._orphan_removed_cleanup_last_ts),
                                "slot_utilization_pct": (100.0 * actual_active_connections / configured) if active_dl and configured else 0, "inflight_articles": 0,
                                "rar_lanes_active": 0, "rar_lanes_target": 0, "bandwidth": {"enabled": False, "active": False}},
                  "statistics": statistics, "engine": engine}
        self._last_snapshot, self._last_snapshot_ts = result, now
        return result

    def _ids(self, job_id: str, job_ids: list[str] | None) -> list[str]:
        ids = [str(x) for x in (job_ids or []) if str(x)]
        if job_id and job_id not in ids:
            ids.append(job_id)
        return ids

    def control(self, action: str, job_id: str = "", value: Any = None, job_ids: list[str] | None = None) -> dict[str, Any]:
        self._refresh_shared_state()
        ids = self._ids(job_id, job_ids)

        # r3: Remove is authoritative stop+delete, not a best-effort local hide.
        # Do not create a tombstone until SAB queue absence proves the transfer ended.
        if action == "remove":
            if not ids:
                raise ValueError("No downloads were selected")
            succeeded: list[str] = []
            failures: list[str] = []
            for nzo in ids:
                ok, message = self._delete_sab_job_verified(nzo, delete_files=True)
                if ok:
                    succeeded.append(nzo)
                else:
                    failures.append(f"{nzo}: {message}")
            if succeeded:
                with self.lock:
                    for nzo in succeeded:
                        self._tracked().pop(nzo, None)
                        self._mark_removed_locked(nzo, reason="remove")
                        self._job_last_view.pop(nzo, None)
                        self._job_last_seen_ts.pop(nzo, None)
                        self._active_latch_until.pop(nzo, None)
                        self._job_active_confirmed_ts.pop(nzo, None)
                        self._active_bridge_open.discard(nzo)
                        self._job_missing_since.pop(nzo, None)
                        self._job_queued_observations.pop(nzo, None)
                    self._save_state()
            self._last_snapshot = None
            self._last_snapshot_ts = 0
            if failures:
                self._event("warning", "Remove could not be fully verified", failures=failures[:3])
                raise ValueError("Remove was not confirmed; NewzDeck kept the download visible. " + " | ".join(failures[:3]))
            return self.snapshot()

        # Cancel uses the same verified stop invariant. It may be presented differently
        # by the UI, but it must never create a hidden continuing SAB transfer.
        if action == "cancel":
            if not ids:
                raise ValueError("No downloads were selected")
            succeeded: list[str] = []
            failures: list[str] = []
            for nzo in ids:
                ok, message = self._delete_sab_job_verified(nzo, delete_files=True)
                if ok:
                    succeeded.append(nzo)
                else:
                    failures.append(f"{nzo}: {message}")
            if succeeded:
                with self.lock:
                    for nzo in succeeded:
                        self._tracked().pop(nzo, None)
                        self._mark_removed_locked(nzo, reason="cancel")
                        self._job_last_view.pop(nzo, None)
                        self._job_last_seen_ts.pop(nzo, None)
                        self._active_latch_until.pop(nzo, None)
                        self._job_active_confirmed_ts.pop(nzo, None)
                        self._active_bridge_open.discard(nzo)
                        self._job_missing_since.pop(nzo, None)
                        self._job_queued_observations.pop(nzo, None)
                    self._save_state()
            self._last_snapshot = None
            self._last_snapshot_ts = 0
            if failures:
                self._event("warning", "Cancel could not be fully verified", failures=failures[:3])
                raise ValueError("Cancel was not confirmed; NewzDeck kept the download visible. " + " | ".join(failures[:3]))
            return self.snapshot()

        # Local Stop All must remain usable during an engine reconnect.
        if action == "hard_stop_all" and not self._ping(timeout=0.5):
            self.state["paused"] = True
            self.state["_paused_updated_ts"] = time.time()
            self._save_state()
            self._last_snapshot_ts = 0
            return self.snapshot()

        self.ensure_running(blocking=True)
        if action == "pause_all":
            self._unexpected_sab_pause_since = 0.0
            self._unexpected_sab_pause_bridge_open = False
            self._resume_intent_event.clear()
            self._api("pause", timeout=4)
            self.state["paused"] = True; self.state["_paused_updated_ts"] = time.time(); self._save_state()
        elif action == "resume_all":
            self._unexpected_sab_pause_since = 0.0
            self._unexpected_sab_pause_bridge_open = False
            self._resume_intent_event.clear()
            self._api("resume", timeout=4)
            self.state["paused"] = False; self.state["_paused_updated_ts"] = time.time(); self._save_state()
        elif action in {"pause", "resume"}:
            for nzo in ids:
                self._api("queue", name=action, value=nzo, timeout=4)
        elif action == "retry":
            for nzo in ids:
                self._api("retry", value=nzo, timeout=8)
        elif action == "priority":
            priority = str(value or "normal").lower()
            if priority not in {"high", "normal", "low"}:
                raise ValueError("Priority must be High, Normal, or Low")
            for nzo in ids:
                self._api("queue", name="priority", value=nzo, value2=self._priority_value(priority), timeout=4)
                with self.lock:
                    if nzo in self._tracked():
                        self._tracked()[nzo]["priority"] = priority
                        self._touch_job_locked(self._tracked()[nzo])
            self._save_state()
        elif action in {"move_top", "move_bottom"}:
            q, _ = self._queue_and_history()
            _, slots = self._queue_slots(q)
            position = 0 if action == "move_top" else max(0, len(slots) - 1)
            for nzo in ids:
                self._api("switch", value=nzo, value2=position, timeout=4)
        elif action == "hard_stop_all":
            self._api("pause", timeout=4)
            self.state["paused"] = True; self.state["_paused_updated_ts"] = time.time(); self._save_state()
        elif action in {"fetch_recovery", "password"}:
            raise ValueError("SABnzbd manages PAR2 recovery and archive passwords automatically for Download Engine v2")
        else:
            raise ValueError("Unknown download action")
        self._last_snapshot_ts = 0
        return self.snapshot()

    def _remember_failed_automation_release(self, nzo_id: str, meta: dict[str, Any], slot: dict[str, Any]) -> None:
        """Persist exact-release failure feedback as soon as SAB marks a job Failed.

        Some bad/expired posts can move from addlocalfile to SAB history in less than
        one UI poll. The completion thread normally records that failure, but the
        Downloads snapshot can observe it first. Either path may call this helper; a
        per-job persisted flag plus Automation's collection-id de-duplication makes it
        safe and gives Interactive Search deterministic failed-post feedback.
        """
        nzo_id=str(nzo_id or '')
        if not nzo_id or self.media_automation is None:
            return
        if nzo_id in self._failed_release_feedback_seen or bool(meta.get('failure_feedback_recorded')):
            return
        context=meta.get('automation_context') if isinstance(meta.get('automation_context'),dict) else {}
        if not context or str(context.get('source') or '')!='automation_grab':
            return
        reason=str(slot.get('fail_message') or slot.get('stage_log') or slot.get('status') or 'SABnzbd could not complete this release')
        try:
            self.media_automation.record_release_failure(dict(context),reason,collection_id=nzo_id)
        except Exception as exc:
            self._event('warning',f'Could not remember failed Automation release: {exc}',nzo_id=nzo_id)
            return
        self._failed_release_feedback_seen.add(nzo_id)
        with self.lock:
            live=self._tracked().get(nzo_id)
            if isinstance(live,dict):
                live['failure_feedback_recorded']=True
                live['failure_reason']=reason[:600]
                self._touch_job_locked(live)
        self._save_state()
        self._event('info','Remembered failed Automation release for Interactive Search',nzo_id=nzo_id,reason=reason[:240])

    @staticmethod
    def _automation_import_rank(meta: dict[str, Any]) -> tuple[int, int, float]:
        context = meta.get("automation_context") if isinstance(meta.get("automation_context"), dict) else {}
        score = int(_num(context.get("release_score"), 0))
        quality = str(context.get("release_quality") or context.get("release_title") or "").casefold()
        resolution = 0
        for value in (4320, 2160, 1440, 1080, 720, 576, 480):
            if str(value) in quality:
                resolution = value
                break
        return score, resolution, _num(meta.get("created_ts"), 0)

    def _completed_automation_candidates(self, queue_slots: list[dict[str, Any]],
                                         history_slots: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
        queue_by = {str(x.get("nzo_id") or x.get("id") or ""): x for x in queue_slots if isinstance(x, dict)}
        hist_by = {str(x.get("nzo_id") or x.get("id") or ""): x for x in history_slots if isinstance(x, dict)}
        with self.lock:
            tracked = dict(self._tracked())
        groups: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        for nzo_id, meta in tracked.items():
            context = meta.get("automation_context") if isinstance(meta.get("automation_context"), dict) else {}
            if not _is_smart_import_context(context) or meta.get("imported"):
                continue
            target = str(context.get("target_key") or "").strip() or f"job:{nzo_id}"
            groups.setdefault(target, []).append((str(nzo_id), meta))
        selected: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        for rows in groups.values():
            completed = []
            active = []
            for nzo_id, meta in rows:
                hslot = hist_by.get(nzo_id)
                qslot = queue_by.get(nzo_id)
                if hslot is not None and str(hslot.get("status") or "").casefold() == "completed":
                    completed.append((self._automation_import_rank(meta), nzo_id, meta, hslot))
                elif qslot is not None and str(qslot.get("status") or "").casefold() not in {"failed", "completed"}:
                    active.append((self._automation_import_rank(meta), nzo_id, meta, qslot))
            if not completed:
                continue
            completed.sort(key=lambda x: x[0], reverse=True)
            best = completed[0]
            if active:
                active.sort(key=lambda x: x[0], reverse=True)
                if active[0][0] > best[0]:
                    continue
            selected.append((best[1], best[2], best[3]))
        return selected

    def _process_completed_automation_slots(self, queue_slots: list[dict[str, Any]],
                                            history_slots: list[dict[str, Any]]) -> None:
        for nzo_id, meta, slot in self._completed_automation_candidates(queue_slots, history_slots):
            self._run_automation_import(nzo_id, meta, slot)

    def _kick_completed_automation_imports(self, queue_slots: list[dict[str, Any]],
                                           history_slots: list[dict[str, Any]]) -> None:
        if self.media_automation is None:
            return
        candidates = self._completed_automation_candidates(queue_slots, history_slots)
        if not candidates:
            return
        with self._import_kick_lock:
            chosen = [row for row in candidates if row[0] not in self._import_kick_inflight]
            for nzo_id, _meta, _slot in chosen:
                self._import_kick_inflight.add(nzo_id)
        if not chosen:
            return
        def worker(rows: list[tuple[str, dict[str, Any], dict[str, Any]]]) -> None:
            try:
                for nzo_id, meta, slot in rows:
                    try:
                        self._run_automation_import(nzo_id, meta, slot)
                    finally:
                        with self._import_kick_lock:
                            self._import_kick_inflight.discard(nzo_id)
            finally:
                self._last_snapshot_ts = 0
        threading.Thread(target=worker, args=(chosen,), name="newzdeck-sab-import-kick", daemon=True).start()

    def _completion_loop(self) -> None:
        delay = 2.0
        while not self.shutdown_event.wait(delay):
            try:
                queue_payload, history_payload = self._queue_and_history()
                _, qslots = self._queue_slots(queue_payload)
                hroot, hslots = self._history_slots(history_payload)
                self._adopt_untracked_slots(qslots, hslots)
                self._refresh_shared_state()
                by_id = {str(x.get("nzo_id") or x.get("id") or ""): x for x in hslots}
                with self.lock:
                    tracked = dict(self._tracked())
                if bool(hroot.get("_newzdeck_fresh", True)):
                    for nzo_id, meta in tracked.items():
                        slot = by_id.get(nzo_id)
                        if slot is not None and str(slot.get("status") or "").casefold() == "completed" and bool(meta.get("browser_flat_images")):
                            self._flatten_completed_browser_images(nzo_id, meta, slot)
                if self.media_automation is not None:
                    for nzo_id, meta in tracked.items():
                        context = meta.get("automation_context") if isinstance(meta.get("automation_context"), dict) else {}
                        if not _is_smart_import_context(context) or meta.get("imported"):
                            continue
                        slot = by_id.get(nzo_id)
                        if slot is not None and str(slot.get("status") or "").casefold() == "failed":
                            self._remember_failed_automation_release(nzo_id, meta, slot)
                    self._process_completed_automation_slots(qslots, hslots)
                    self._retry_pending_automation_cleanups()
                delay = 2.0
                self._completion_backoff_seconds = delay
            except Exception as exc:
                self._completion_control_failures += 1
                if self._is_transient_control_error(exc):
                    delay = min(30.0, max(4.0, delay * 1.8))
                else:
                    delay = min(15.0, max(3.0, delay * 1.4))
                self._completion_backoff_seconds = delay
                now = time.time()
                if now - self._completion_last_warning_ts >= max(15.0, delay):
                    self._completion_last_warning_ts = now
                    self._event(
                        "warning",
                        f"SAB completion monitor failed; backing off {delay:.0f}s: {exc}",
                    )


    @staticmethod
    def _pid_is_alive(pid: int) -> bool:
        """Return whether a persisted import-owner PID still exists.

        Smart Import claims survive service/update handoffs. A dead owner must not
        strand a package in IMPORTING until the old ten-minute lease expires.
        """
        pid = int(pid or 0)
        if pid <= 0:
            return False
        if pid == os.getpid():
            return True
        if os.name == "nt":
            try:
                return _ExternalWindowsProcess(pid).poll() is None
            except Exception:
                return False
        try:
            os.kill(pid, 0)
            return True
        except PermissionError:
            return True
        except (ProcessLookupError, OSError):
            return False

    def _claim_automation_import(self, nzo_id: str) -> dict[str, Any] | None:
        """Atomically claim one completed Automation import across all runtimes.

        A live owner retains the claim. A dead runtime owner is reclaimed
        immediately rather than waiting for the historical 10-minute lease.
        """
        self._refresh_shared_state()
        now = time.time()
        with self.lock:
            with self._state_file_guard():
                disk = self._normalize_state_value(_json_read(self.state_file, {}))
                live = disk.get("jobs", {}).get(str(nzo_id))
                if not isinstance(live, dict):
                    return None
                if live.get("imported"):
                    self.state = self._merge_shared_states(disk, self.state)
                    return None
                retry_after = _num(live.get("import_retry_after"), 0)
                if retry_after > now:
                    self.state = self._merge_shared_states(disk, self.state)
                    return None
                status = str(live.get("import_status") or "")
                claim_ts = _num(live.get("import_claim_ts"), 0)
                claim_pid = int(_num(live.get("import_claim_pid"), 0))
                heartbeat_ts = _num(live.get("import_heartbeat_ts"), claim_ts)
                owner_alive = self._pid_is_alive(claim_pid)
                if status == "importing" and claim_ts > now - 600 and owner_alive:
                    self.state = self._merge_shared_states(disk, self.state)
                    return None
                if status == "importing" and claim_pid > 0 and not owner_alive:
                    self._import_dead_owner_reclaims += 1
                    self._import_dead_owner_last_ts = now
                    self._event(
                        "warning",
                        "Reclaiming Smart Import from a dead NewzDeck runtime",
                        nzo_id=str(nzo_id),
                        dead_pid=claim_pid,
                        last_progress_age_seconds=round(max(0.0, now - heartbeat_ts), 1) if heartbeat_ts else 0,
                    )
                live["import_status"] = "importing"
                live["import_progress"] = max(0, min(100, int(live.get("import_progress", 0) or 0))) if status == "importing" else 0
                live["import_message"] = "Smart Import • recovering interrupted import" if status == "importing" else "Smart Import • inspecting SABnzbd output"
                live["import_claim_ts"] = now
                live["import_heartbeat_ts"] = now
                live["import_claim_pid"] = os.getpid()
                live["_updated_ts"] = now
                disk["jobs"][str(nzo_id)] = live
                _atomic_json_write(self.state_file, disk)
                self.state = self._merge_shared_states(disk, self.state)
                return dict(live)

    @staticmethod
    def _output_alias(value: Any) -> str:
        """Normalize a SAB/job path or name for conservative output matching."""
        text = str(value or "").strip().replace("\\", "/").rstrip("/")
        if not text:
            return ""
        name = text.rsplit("/", 1)[-1]
        # Treat an NZB/media extension as decoration, not part of folder identity.
        low = name.casefold()
        for ext in (".nzb", ".mkv", ".mp4", ".m4v", ".avi", ".mov", ".wmv", ".ts", ".m2ts", ".webm", ".mpg", ".mpeg"):
            if low.endswith(ext):
                name = name[:-len(ext)]
                break
        return "".join(ch.casefold() for ch in name if ch.isalnum())

    @staticmethod
    def _media_under(path: Path, *, max_depth: int = 4, max_files: int = 800) -> list[Path]:
        """Return media under one candidate SAB output without wandering the drive."""
        try:
            if path.is_file():
                return [path] if path.suffix.casefold() in AUTOMATION_MEDIA_EXTS else []
            if not path.is_dir():
                return []
        except OSError:
            return []
        base_depth = len(path.parts)
        out: list[Path] = []
        seen = 0
        try:
            for root, dirs, files in os.walk(path):
                root_path = Path(root)
                depth = len(root_path.parts) - base_depth
                if depth >= max_depth:
                    dirs[:] = []
                for name in files:
                    seen += 1
                    if seen > max_files:
                        return out
                    candidate = root_path / name
                    if candidate.suffix.casefold() in AUTOMATION_MEDIA_EXTS:
                        out.append(candidate)
        except OSError:
            pass
        return out

    def _resolve_automation_output(self, nzo_id: str, meta: dict[str, Any], slot: dict[str, Any]) -> tuple[list[Path], Path | None, str]:
        """Locate SAB's completed media even when history.storage is stale/empty.

        The v3.5.30 Import Inspector already knows how to rename an opaque feature
        safely from exact Automation context.  The remaining real-world failure was
        one layer earlier: SAB history can occasionally expose a blank, stale, or
        differently-normalized ``storage`` path for direct-media/obfuscated jobs.
        Smart Import then received *zero files* forever and could never reach the
        working identity/rename logic.

        Resolution is deliberately scoped to the configured Completed Download
        Folder and to this one SAB job.  We first trust explicit SAB/NewzDeck paths,
        then exact job/release aliases, and only then use a bounded recent-output
        fallback for an exact Automation target.
        """
        complete = Path(self.download_dir_getter()).expanduser()
        context = dict(meta.get("automation_context") or {})
        raw_paths = [slot.get("storage"), slot.get("path"), meta.get("output_hint")]
        aliases = {
            self._output_alias(x) for x in (
                meta.get("name"), meta.get("source_name"), meta.get("output_hint"),
                slot.get("filename"), slot.get("name"), slot.get("nzb_name"),
                slot.get("storage"), slot.get("path"), context.get("release_title"),
            ) if self._output_alias(x)
        }

        explicit: list[Path] = []
        seen_paths: set[str] = set()
        for raw in raw_paths:
            text = str(raw or "").strip()
            if not text:
                continue
            p = Path(text).expanduser()
            if not p.is_absolute():
                p = complete / p
            key = str(p).casefold()
            if key not in seen_paths:
                explicit.append(p); seen_paths.add(key)
        for p in explicit:
            files = self._media_under(p)
            if files:
                stage = p if p.is_dir() else p.parent
                return files, stage, f"SAB history/output path: {p}"

        # SAB may sanitize/drop an extension when turning the NZB job name into its
        # completed folder.  Match only exact normalized aliases at the top level.
        exact_groups: list[tuple[Path, list[Path]]] = []
        try:
            if complete.is_dir():
                for child in complete.iterdir():
                    if self._output_alias(child.name) not in aliases:
                        continue
                    media = self._media_under(child)
                    if media:
                        exact_groups.append((child, media))
        except OSError:
            pass
        if len(exact_groups) == 1:
            group, files = exact_groups[0]
            return files, (group if group.is_dir() else group.parent), f"Matched SAB job/release folder: {group}"
        if len(exact_groups) > 1:
            # Prefer the group whose total media size most closely resembles this job.
            expected = max(int(meta.get("expected_bytes", 0) or 0), int(context.get("release_size", 0) or 0))
            if expected > 0:
                ranked = []
                for group, files in exact_groups:
                    total = 0
                    for f in files:
                        try: total += int(f.stat().st_size)
                        except OSError: pass
                    ranked.append((abs(total - expected), group, files))
                ranked.sort(key=lambda x: x[0])
                if len(ranked) == 1 or ranked[0][0] + max(64 * 1024 * 1024, int(expected * 0.08)) < ranked[1][0]:
                    _, group, files = ranked[0]
                    return files, (group if group.is_dir() else group.parent), f"Matched closest SAB job/release folder: {group}"

        # Final fallback: an exact Automation target may use a completely opaque
        # job/file name.  Because NewzDeck intentionally runs one top-level package
        # at a time, select only a *clear* recent completed-output group.  Never scan
        # outside the configured Completed Download Folder and never guess between
        # multiple similarly plausible groups.
        exact_target = bool(
            _is_smart_import_context(context) and (
                (str(context.get("kind") or "") == "tv" and context.get("season") is not None and context.get("episode") is not None and not bool(context.get("season_pack")))
                or str(context.get("kind") or "") == "movie"
            )
        )
        if not exact_target:
            return [], next((p for p in explicit if p.exists() and p.is_dir()), None), "No exact SAB output path was available"

        created = float(meta.get("created_ts", 0) or slot.get("time_added") or 0)
        completed = float(slot.get("completed", 0) or time.time())
        expected = max(int(meta.get("expected_bytes", 0) or 0), int(context.get("release_size", 0) or 0))
        recent: list[tuple[float, Path, list[Path]]] = []
        lower = (created - 15 * 60) if created else (completed - 6 * 3600)
        upper = (completed + 15 * 60) if completed else (time.time() + 15 * 60)
        try:
            if complete.is_dir():
                for child in complete.iterdir():
                    try:
                        stat = child.stat(); mtime = float(stat.st_mtime)
                    except OSError:
                        continue
                    # A folder can retain an older mtime on some Windows/storage
                    # combinations, so media mtimes below get the final say too.
                    media = self._media_under(child, max_depth=3, max_files=500)
                    if not media:
                        continue
                    mtimes=[]; total=0; feature_count=0
                    for f in media:
                        try:
                            st=f.stat(); total += int(st.st_size); mtimes.append(float(st.st_mtime))
                            if int(st.st_size) >= 128 * 1024 * 1024: feature_count += 1
                        except OSError:
                            pass
                    newest=max(mtimes or [mtime])
                    if newest < lower or newest > upper:
                        continue
                    score=0.0
                    if self._output_alias(child.name) in aliases: score += 120.0
                    # Completion-time proximity is a strong job-ownership signal.
                    if completed:
                        delta=abs(newest-completed)
                        if delta <= 90: score += 45
                        elif delta <= 300: score += 30
                        elif delta <= 900: score += 15
                    if expected > 0 and total > 0:
                        ratio=total/float(expected)
                        if 0.75 <= ratio <= 1.25: score += 45
                        elif 0.50 <= ratio <= 1.60: score += 25
                        elif 0.25 <= ratio <= 2.25: score += 10
                    if feature_count == 1: score += 12
                    recent.append((score, child, media))
        except OSError:
            pass
        recent.sort(key=lambda x: x[0], reverse=True)
        if recent:
            best = recent[0]
            second = recent[1] if len(recent) > 1 else None
            # A single recent group is enough; with competition require a clear lead.
            if second is None or (best[0] >= 35 and best[0] >= second[0] + 18):
                group, files = best[1], best[2]
                return files, (group if group.is_dir() else group.parent), f"Recovered completed media from recent SAB output: {group}"

        return [], next((p for p in explicit if p.exists() and p.is_dir()), None), "SAB completed the job but its media output could not yet be located safely"

    def _cleanup_automation_output(self, nzo_id: str, staging_dir: Path | str | None, *, attempts: int = 6) -> tuple[bool, str]:
        """Remove one verified Automation job's completed SAB folder safely.

        v3.5.38 closes a long-standing split between the native post-processor and
        the private SAB engine path. Smart Import moves/keeps the media file, but
        SAB can legitimately leave .nfo/.sfv/.srr/.par2/artwork and other sidecars
        in its completed job directory. The previous SAB path only tried rmdir(),
        which can never remove those files, so raw release folders accumulated.

        Cleanup is allowed only for a child of NewzDeck's configured Completed
        Download Folder; the Completed Download Folder itself is never recursively
        removed. A few short retries absorb transient Windows Defender/Explorer/SAB
        file handles without turning a momentary sharing violation into permanent
        debris.
        """
        if not staging_dir:
            return False, "No completed job folder was available for cleanup"
        try:
            complete = Path(self.download_dir_getter()).expanduser().resolve()
            stage = Path(staging_dir).expanduser().resolve()
        except OSError as exc:
            return False, f"Could not resolve completed job folder: {exc}"
        try:
            relative = stage.relative_to(complete)
        except ValueError:
            return False, f"Refused cleanup outside the Completed Download Folder: {stage}"
        if not relative.parts:
            # Direct-media jobs can occasionally resolve to a file directly in the
            # Completed Download Folder. The media file itself is already moved by
            # Smart Import, but recursively deleting the shared root is forbidden.
            return False, "Completed media was stored directly in the shared Download Folder; root cleanup was intentionally skipped"

        # _resolve_automation_output is bounded to one job. If SAB/history points at
        # a nested media directory, remove the top-level job folder, not only the
        # innermost directory, so release sidecars beside that nested directory are
        # cleaned as well.
        owned = complete / relative.parts[0]
        delay = 0.15
        last_error = ""
        for attempt in range(max(1, int(attempts))):
            try:
                shutil.rmtree(owned)
                return True, f"Removed completed media staging folder: {owned}"
            except FileNotFoundError:
                return True, f"Completed media staging folder was already removed: {owned}"
            except OSError as exc:
                last_error = str(exc)
                if attempt + 1 >= max(1, int(attempts)):
                    break
                time.sleep(delay)
                delay = min(1.5, delay * 1.8)
        return False, f"Could not completely remove {owned}: {last_error or 'folder is still in use'}"

    def _retry_pending_automation_cleanups(self) -> None:
        """Retry successful imports whose SAB source folder hit a transient lock."""
        now = time.time()
        with self.lock:
            rows = []
            for nzo_id, meta in self._tracked().items():
                if not isinstance(meta, dict) or not meta.get("imported") or meta.get("source_cleaned") or meta.get("cleanup_abandoned"):
                    continue
                # Adopt successful v3.5.37 imports too. That release persisted
                # resolved_output + "Smart Import complete" but had no recursive
                # SAB-source cleanup state, which is why old .nfo/.sfv folders can
                # still be present when v3.5.38 first starts.
                context = meta.get("automation_context") if isinstance(meta.get("automation_context"), dict) else {}
                legacy_exact_target = bool(str(context.get("kind") or "") == "movie" or (str(context.get("kind") or "") == "tv" and context.get("season") is not None and context.get("episode") is not None and not bool(context.get("season_pack"))))
                legacy_success = legacy_exact_target and str(meta.get("import_status") or "") == "completed" and str(meta.get("import_message") or "").startswith("Smart Import complete")
                if not meta.get("cleanup_pending") and not legacy_success:
                    continue
                if _num(meta.get("cleanup_retry_after"), 0) > now:
                    continue
                stage = str(meta.get("resolved_output") or "").strip()
                if stage:
                    rows.append((str(nzo_id), stage))
        changed = False
        for nzo_id, stage in rows[:4]:
            cleaned, detail = self._cleanup_automation_output(nzo_id, stage, attempts=2)
            with self.lock:
                live = self._tracked().get(nzo_id)
                if not isinstance(live, dict):
                    continue
                count = int(live.get("cleanup_retry_count", 0) or 0) + 1
                live["cleanup_retry_count"] = count
                live["cleanup_message"] = detail[:500]
                terminal = ("intentionally skipped" in detail or "outside the Completed Download Folder" in detail or "No completed job folder" in detail)
                live["cleanup_retry_after"] = 0 if (cleaned or terminal) else time.time() + min(60.0, 5.0 + count * 2.0)
                live["cleanup_pending"] = not cleaned and not terminal
                live["cleanup_abandoned"] = bool(terminal)
                live["source_cleaned"] = bool(cleaned)
                self._touch_job_locked(live)
                changed = True
                if cleaned:
                    self._event("info", "Removed deferred media staging folder", nzo_id=nzo_id, path=stage)
            if cleaned:
                self._last_snapshot_ts = 0
        if changed:
            self._save_state()

    def _run_automation_import(self, nzo_id: str, meta: dict[str, Any], slot: dict[str, Any]) -> None:
        claimed = self._claim_automation_import(nzo_id)
        if not claimed:
            return
        meta = claimed
        candidates, staging_dir, resolution = self._resolve_automation_output(nzo_id, meta, slot)
        with self.lock:
            live = self._tracked().get(nzo_id)
            if live:
                live["output_resolution"] = resolution[:500]
                live["resolved_output"] = str(staging_dir or "")
                self._touch_job_locked(live)
                self._save_state()
        def progress(pct: float, message: str) -> None:
            with self.lock:
                live = self._tracked().get(nzo_id)
                if not live: return
                live["import_progress"] = max(0, min(100, int(pct)))
                live["import_message"] = str(message)[:500]
                live["import_heartbeat_ts"] = time.time()
                self._touch_job_locked(live)
                self._save_state()
                self._last_snapshot_ts = 0
        try:
            result = self.media_automation.import_completed_download(dict(meta.get("automation_context") or {}), candidates,
                                                                     staging_dir=staging_dir,
                                                                     progress_callback=progress)
            ok = bool(result.get("ok")) if isinstance(result, dict) else False
            skipped = bool(result.get("skipped")) if isinstance(result, dict) else False
            retryable = bool(result.get("retryable")) if isinstance(result, dict) else False
            # v3.5.38 Movie imports are not allowed to finish silently unless the
            # reconciled final/kept-existing library file actually exists. This turns
            # any remaining Movie-specific path problem into an explicit Import needs
            # attention state while preserving the SAB output for diagnosis/retry.
            context = meta.get("automation_context") if isinstance(meta.get("automation_context"), dict) else {}
            if ok and str(context.get("kind") or "") == "movie":
                destination = str((result or {}).get("destination") or "").strip()
                if not destination or not Path(destination).is_file():
                    result = dict(result or {})
                    result.update({"ok": False, "needs_attention": True, "cleanup_safe": False, "reason": "Movie Smart Import did not produce or reconcile a verified library file; the completed SAB output was preserved for Retry Import."})
                    ok = False
                    skipped = False
                    retryable = False
            cleanup_safe = bool((result or {}).get("cleanup_safe", True)) if isinstance(result, dict) else False
            cleanup_attempted = bool(ok and cleanup_safe and staging_dir)
            cleanup_done = False
            cleanup_detail = ""
            if cleanup_attempted:
                cleanup_done, cleanup_detail = self._cleanup_automation_output(nzo_id, staging_dir, attempts=6)
                if isinstance(result, dict):
                    result = dict(result)
                    result["source_cleaned"] = bool(cleanup_done)
                    result["cleanup_message"] = cleanup_detail
            with self.lock:
                live = self._tracked().get(nzo_id)
                if live:
                    if retryable and not ok:
                        retry_count = int(live.get("import_retry_count", 0) or 0) + 1
                        live["import_retry_count"] = retry_count
                        live["imported"] = False
                        if retry_count >= 24:
                            live["import_status"] = "failed"
                            live["import_progress"] = 0
                            live["import_retry_after"] = 0
                        else:
                            live["import_status"] = "waiting"
                            live["import_progress"] = 0
                            live["import_retry_after"] = time.time() + 5.0
                    else:
                        live["import_retry_count"] = 0
                        live["imported"] = bool(ok or skipped)
                        live["import_status"] = "completed" if (ok or skipped) else "failed"
                        live["import_progress"] = 100 if (ok or skipped) else int(live.get("import_progress", 0) or 0)
                        live["import_retry_after"] = 0
                    if cleanup_attempted:
                        cleanup_terminal = ("intentionally skipped" in cleanup_detail or "outside the Completed Download Folder" in cleanup_detail or "No completed job folder" in cleanup_detail)
                        live["source_cleaned"] = bool(cleanup_done)
                        live["cleanup_pending"] = not bool(cleanup_done) and not cleanup_terminal
                        live["cleanup_abandoned"] = bool(cleanup_terminal)
                        live["cleanup_message"] = str(cleanup_detail)[:500]
                        live["cleanup_retry_count"] = 0
                        live["cleanup_retry_after"] = 0 if (cleanup_done or cleanup_terminal) else time.time() + 5.0
                    elif ok and not cleanup_safe:
                        live["source_cleaned"] = False
                        live["cleanup_pending"] = False
                        live["cleanup_message"] = "Source folder preserved because Import Inspector still has unresolved media"
                    if isinstance(result, dict):
                        live["import_destination"] = str(result.get("destination") or "")[:1000]
                        live["imported_count"] = int(result.get("imported_count", 0) or 0)
                        live["kept_existing_count"] = int(result.get("kept_existing", 0) or 0)
                    live["import_claim_pid"] = 0
                    live["import_claim_ts"] = 0
                    live["import_heartbeat_ts"] = 0
                    if retryable and not ok and int(live.get("import_retry_count", 0) or 0) >= 24:
                        message = f"Smart Import could not locate SAB's completed media after repeated checks. {resolution}. Download is preserved; use Retry Import after verifying the output folder."
                    elif retryable and not ok:
                        message = f"Smart Import is locating completed media • {resolution}"
                    else:
                        if ok:
                            dest = str((result or {}).get("destination") or "")
                            message = "Smart Import complete" + (f" • {dest}" if dest else "")
                            if cleanup_attempted:
                                message += " • source cleaned" if cleanup_done else " • source cleanup pending"
                        else:
                            message = str((result or {}).get("reason") or "Smart Import requires attention")
                    live["import_message"] = message[:500]
                    self._touch_job_locked(live)
                    self._save_state()
            self._event("info" if (ok or skipped or retryable) else "warning", f"Smart Import {'completed' if ok else ('deferred' if retryable else 'finished')} for {meta.get('name')}", result=result)
        except Exception as exc:
            with self.lock:
                live = self._tracked().get(nzo_id)
                if live:
                    live["import_status"] = "failed"
                    live["import_message"] = f"Smart Import failed: {exc}"[:500]
                    live["import_claim_pid"] = 0
                    live["import_claim_ts"] = 0
                    live["import_heartbeat_ts"] = 0
                    self._touch_job_locked(live)
                    self._save_state()
            self._event("error", f"Smart Import failed for {meta.get('name')}: {exc}")
        finally:
            self._last_snapshot_ts = 0

    def retry_automation_import(self, collection_id: str) -> dict[str, Any]:
        nzo_id = str(collection_id or "")
        self._refresh_shared_state()
        with self.lock:
            meta = self._tracked().get(nzo_id)
            if not meta:
                raise ValueError("Download package was not found")
            meta["imported"] = False
            meta["import_status"] = ""
            meta["import_message"] = ""
            meta["import_progress"] = 0
            meta["import_retry_after"] = 0
            meta["import_retry_count"] = 0
            meta["import_claim_pid"] = 0
            meta["import_claim_ts"] = 0
            meta["import_heartbeat_ts"] = 0
            self._touch_job_locked(meta)
            self._save_state()
        return self.snapshot()

    def stop(self) -> None:
        self.shutdown_event.set()
        self.sync_event.set()
        # Keep the engine alive only when NewzDeck's Windows background service is
        # actually available to own it. Otherwise a normal desktop exit should not
        # leave an invisible SAB process orphaned on the machine.
        keep_running = False
        try:
            keep_running = bool(self.keep_engine_running())
        except Exception:
            keep_running = False
        if not keep_running and self._ping(timeout=0.35):
            try:
                self._api("shutdown", timeout=2.0)
            except Exception:
                pass
