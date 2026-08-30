from __future__ import annotations

import base64
import binascii
import ctypes
import ctypes.wintypes
import email.header
import email.utils
import fnmatch
import functools
import hashlib
import html
import io
import json
import math
import mimetypes
import os
import queue
import shutil
import re
import secrets
import socket
import subprocess
import ssl
import struct
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
import zlib
import traceback
import zipfile
import xml.etree.ElementTree as ET
from collections import deque, OrderedDict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable

def safe_print(*args, **kwargs):
    """Print when a console/log stream exists; pythonw.exe may expose none."""
    try:
        if sys.stdout is not None:
            print(*args, **kwargs)
    except Exception:
        pass

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

# v3.6.10 source-freshness rule: NewzDeck ships deterministic source timestamps,
# so an adjacent timestamp-based .pyc from an older same-size source file can
# otherwise survive an in-place upgrade and be accepted as current. The main
# server is executed directly from source; remove only NewzDeck's adjacent app
# bytecode cache before loading sibling modules and do not recreate it.
sys.dont_write_bytecode = True
try:
    shutil.rmtree(APP_DIR / "__pycache__", ignore_errors=True)
except Exception:
    pass

def _load_app_source_module(module_name: str, module_path: Path):
    """Load one NewzDeck-owned sibling module from the current source bytes.

    Deliberately bypass SourceFileLoader.exec_module(), whose normal timestamp/size
    bytecode validation can accept an older deterministic-build .pyc after an
    in-place update. Module metadata is still created from a normal import spec,
    but the code object always comes from the installed .py file bytes.
    """
    import importlib.util
    module_path = Path(module_path)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Cannot create module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        source_bytes = module_path.read_bytes()
        code = compile(source_bytes, str(module_path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module

def user_data_root() -> Path:
    """Return NewzDeck's version-independent per-user storage directory."""
    override = os.environ.get("NEWZDECK_USER_ROOT", "").strip()
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        return base / "NewzDeck"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "NewzDeck"
    base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return base / "newzdeck"

def legacy_user_data_root() -> Path:
    """Return the pre-v1.0 Usenet Browser data root for one-time rebrand migration."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        return base / "Usenet Browser"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Usenet Browser"
    base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return base / "usenet-browser"

def _merge_rebrand_tree(source: Path, target: Path) -> None:
    """Move legacy data into NewzDeck without overwriting newer files."""
    if not source.exists() or source == target:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        try:
            source.replace(target)
            return
        except OSError:
            pass
    target.mkdir(parents=True, exist_ok=True)
    try:
        children = list(source.iterdir())
    except OSError:
        return
    for child in children:
        destination = target / child.name
        try:
            if child.is_dir() and destination.is_dir():
                _merge_rebrand_tree(child, destination)
            elif not destination.exists():
                shutil.move(str(child), str(destination))
        except OSError:
            continue
    try:
        source.rmdir()
    except OSError:
        pass

USER_ROOT = user_data_root()
_merge_rebrand_tree(legacy_user_data_root(), USER_ROOT)
DATA_DIR = USER_ROOT / "data"
BACKEND_STARTUP_LOG_FILE = DATA_DIR / "backend-startup.log"

def _backend_startup_excepthook(exc_type, exc_value, exc_tb):
    """Persist uncaught backend-startup failures even when the GUI launcher hides stderr."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with BACKEND_STARTUP_LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] Uncaught backend exception\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=handle)
    except Exception:
        pass
    try:
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    except Exception:
        pass

sys.excepthook = _backend_startup_excepthook
CACHE_DIR = USER_ROOT / "preview-cache"
THUMB_CACHE_DIR = USER_ROOT / "thumbnail-cache"
DOWNLOAD_TEMP_DIR = USER_ROOT / "download-temp"
UPDATE_DIR = USER_ROOT / "updates"
UPDATE_FEED_CACHE_FILE = DATA_DIR / "update-feed.json"
UPDATE_FEED_URL = os.environ.get(
    "NEWZDECK_UPDATE_FEED_URL",
    "https://api.github.com/repos/newzdeckadmin/NewzDeck/releases/latest",
).strip()
UPDATE_FEED_TTL_SECONDS = 15 * 60
UPDATE_MAX_PACKAGE_BYTES = 200 * 1024 * 1024
TRAY_REQUEST_FILE = USER_ROOT / "tray-request.json"
TRAY_REPLY_DIR = USER_ROOT / "tray-replies"
TRAY_HEARTBEAT_FILE = USER_ROOT / "tray-heartbeat.txt"
TRAY_AUTOSTART_FILE = USER_ROOT / "tray-autostart.enabled"
SERVICE_STATE_FILE = DATA_DIR / "service-state.json"
SERVICE_NAME = "NewzDeckService"
SERVICE_HELPER_EXE = APP_DIR / "NewzDeckService.exe"
TRAY_HELPER_EXE = APP_DIR / "NewzDeckTray.exe"
PICKER_HELPER_EXE = APP_DIR / "NewzDeckPicker.exe"
PICKER_REPLY_DIR = USER_ROOT / "picker-replies"
PROVIDERS_FILE = DATA_DIR / "providers.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
DOWNLOADS_FILE = DATA_DIR / "downloads.json"
SAVED_SEARCHES_FILE = DATA_DIR / "saved-searches.json"
DIAGNOSTICS_LOG_FILE = DATA_DIR / "diagnostics.log"
NAME_RESOLUTION_CACHE_FILE = DATA_DIR / "name-resolution-cache.json"
HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_GROUP_PAGE_SIZE = 1000
MAX_GROUP_PAGE_SIZE = 5000
DEFAULT_ARTICLE_LIMIT = 300
DEFAULT_PREVIEW_LIMIT_MB = 512
VIDEO_THUMB_SAMPLE_MB = 24
PREVIEW_WORKER_COUNT = 80
PREVIEW_SOCKET_TIMEOUT = 7.0
BROWSE_HEADER_POOL_SIZE = 2
BROWSE_HEADER_IDLE_CLOSE_SECONDS = 10.0
SMART_BROWSE_WORKER_COUNT = 2
PREVIEW_CONNECTION_IDLE_CLOSE_SECONDS = 3.0
NAME_RESOLUTION_WORKER_COUNT = 3
NAME_RESOLUTION_PROBE_BYTES = 96 * 1024
NAME_RESOLUTION_SOCKET_TIMEOUT = 4.5
NAME_RESOLUTION_METADATA_MAX_BYTES = 4 * 1024 * 1024
NAME_RESOLUTION_ARCHIVE_PROBE_BYTES = 512 * 1024
NAME_RESOLUTION_ARCHIVE_WIRE_MAX_BYTES = 768 * 1024
DEFAULT_THUMB_CACHE_GB = 2
MAX_CONCURRENT_DOWNLOADS = 6
PACKAGE_QUEUE_CONCURRENCY = 1
# Multipart RAR downloads use a two-file rolling window. One top-level NZB still
# owns the network, but only the current volume plus one read-ahead volume may be
# active. The lead volume keeps most provider sockets while the read-ahead lane
# gets a small reserved share. This avoids fragmenting a 40-100 connection pool
# across 5-6 independent file coordinators while still preventing volume-boundary
# tail drain.
RAR_COLLECTION_FAST_LANE_MAX = 2
RAR_COLLECTION_MIN_CONNECTIONS_FOR_READ_AHEAD = 12
RAR_READ_AHEAD_SHARE = 0.20
RAR_READ_AHEAD_MIN_CONNECTIONS = 4
RAR_READ_AHEAD_MAX_CONNECTIONS = 12
# High-throughput queue defaults. The cache ceiling is adjusted again at runtime
# from physical RAM so fast SSD/NVMe systems do not stall the network while the
# coordinator performs small writes.
DOWNLOAD_ARTICLE_CACHE_MIN_PER_JOB_MB = 64
DOWNLOAD_PROGRESS_PERSIST_INTERVAL = 3.0
NNTP_PIPELINE_TARGET_INFLIGHT = 120
NNTP_PIPELINE_MAX_DEPTH = 10
# High-connection providers are treated as a ceiling, not a command to keep every
# socket busy. v3.3.1's proven fast path kept roughly 120 BODY requests in flight;
# v3.4.11 accidentally reduced that target to 80, which changed a 55-connection
# provider from pipeline depth 3 to depth 2. Start large pools at 32 sockets, keep
# the proven ~120 in-flight window, and ramp only while measured wire throughput
# improves. This avoids both under-pipelining and blind max-connection saturation.
NNTP_AUTOTUNE_START_CONNECTIONS = 32
NNTP_AUTOTUNE_STEP_CONNECTIONS = 8
NNTP_AUTOTUNE_SAMPLE_SECONDS = 4.0
NNTP_AUTOTUNE_MIN_GAIN = 0.06
NNTP_AUTOTUNE_REGRESSION = 0.10
NNTP_AUTOTUNE_RESET_SECONDS = 30.0
DOWNLOAD_DECODE_BACKLOG_WAVES = 2
DOWNLOAD_JOURNAL_FLUSH_INTERVAL = 2.0
# Missing-article recovery policy. A 423/430 is a definitive result for one
# provider connection, so NewzDeck only performs one fresh same-provider probe
# before moving on to recovery providers. Delayed whole-file rechecks are also
# bounded; widespread missing data bypasses delayed loops and proceeds directly
# to PAR2 recovery (when possible) or a terminal failed state.
NZB_MISSING_PROVIDER_ATTEMPTS = 2
NZB_SOFT_MISSING_MAX_RECHECKS = 2
NZB_SOFT_MISSING_RECHECK_DELAYS = (15, 45)
NZB_PROPAGATION_MAX_RECHECKS = 5
NZB_PROPAGATION_RECHECK_DELAYS = (15, 30, 60, 120, 180)
NZB_BULK_MISSING_MIN_BLOCKS = 8
NZB_BULK_MISSING_RATIO = 0.50
DIRECT_UNPACK_AUTO_READ_AHEAD_VOLUMES = 2
DIRECT_UNPACK_ALL_COMPLETE_GRACE_SECONDS = 300
DEFAULT_THUMBNAIL_SIZE = "medium"
DEFAULT_CONTINUOUS_BROWSE = True
DEFAULT_VIEW_MODE = "gallery"
DEFAULT_CONTENT_FILTER = "images"
DEFAULT_DOWNLOAD_ORGANIZATION = "flat"
DEFAULT_GROUP_RELATED_MEDIA = False
DEFAULT_GROUP_BINARY_SETS = True
DEFAULT_POST_PROCESSING = True
DEFAULT_AUTO_REPAIR = True
DEFAULT_AUTO_FETCH_PAR2 = True
DEFAULT_AUTO_EXTRACT = True
DEFAULT_CLEANUP_ARCHIVES = False
DEFAULT_EXTRACT_SUBFOLDER = True
DEFAULT_DIRECT_UNPACK_MODE = "auto"
DEFAULT_AUTOMATION_MEDIA_CLEANUP = True
DEFAULT_WATCH_FOLDER_ENABLED = False
DEFAULT_WATCH_FOLDER = str(USER_ROOT / "watch-nzb")
DEFAULT_WATCH_ARCHIVE_PROCESSED = True
DEFAULT_SMART_CATEGORIES = False
DEFAULT_BANDWIDTH_SCHEDULE_ENABLED = False
DEFAULT_BANDWIDTH_SCHEDULE_START = "18:00"
DEFAULT_BANDWIDTH_SCHEDULE_END = "23:00"
DEFAULT_BANDWIDTH_SCHEDULE_LIMIT_MB_S = 25.0
DEFAULT_COMPLETION_NOTIFICATION = False
DEFAULT_COMPLETION_OPEN_FOLDER = False
APP_VERSION = "3.6.15"
BACKEND_PROCESS_STARTED_AT = time.monotonic()
DEFAULT_DOWNLOAD_DIR = Path(os.environ.get("NEWZDECK_DEFAULT_DOWNLOAD_DIR", "").strip() or (Path.home() / "Downloads" / "NewzDeck"))
DOWNLOAD_DIR = DEFAULT_DOWNLOAD_DIR

UNRAR_MANAGED_VERSION = "7.23"
UNRAR_MANAGED_URL = "https://www.rarlab.com/rar/unrarw64.exe"

UNRAR_MANAGED_SHA256 = "ca630e4d4eff213076def6690cc82ead81abb739158da7ead3fd263ff9d104e5"
UNRAR_MANAGED_DIR = DATA_DIR / "tools" / f"unrar-{UNRAR_MANAGED_VERSION}"
UNRAR_MANAGED_EXE = UNRAR_MANAGED_DIR / "UnRAR.exe"
UNRAR_TOOL_STATUS_FILE = DATA_DIR / "unrar-tool-status.json"

PAR2_MANAGED_VERSION = "1.5.0"
PAR2_MANAGED_URL = "https://github.com/animetosho/par2cmdline-turbo/releases/download/v1.5.0/par2cmdline-turbo-1.5.0-win-x64.zip"
PAR2_MANAGED_SHA256 = "873a6f25822415f432224cc6f734407ca2732004184e002960fc68ed1e99c5d7"
PAR2_MANAGED_DIR = DATA_DIR / "tools" / f"par2cmdline-turbo-{PAR2_MANAGED_VERSION}"
PAR2_MANAGED_EXE = PAR2_MANAGED_DIR / "par2.exe"
PAR2_TOOL_STATUS_FILE = DATA_DIR / "par2-tool-status.json"

SERVICE_MODE = os.environ.get("NEWZDECK_SERVICE") == "1"
DESKTOP_MODE = (os.environ.get("NEWZDECK_DESKTOP") == "1" or os.environ.get("USENET_BROWSER_DESKTOP") == "1") and not SERVICE_MODE
_desktop_heartbeat_lock = threading.Lock()
_desktop_last_heartbeat = time.monotonic()
_desktop_heartbeat_seen = False

def desktop_heartbeat() -> None:
    global _desktop_last_heartbeat, _desktop_heartbeat_seen
    with _desktop_heartbeat_lock:
        _desktop_last_heartbeat = time.monotonic()
        _desktop_heartbeat_seen = True

def desktop_heartbeat_state() -> tuple[float, bool]:
    with _desktop_heartbeat_lock:
        return _desktop_last_heartbeat, _desktop_heartbeat_seen

DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
THUMB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_TEMP_DIR.mkdir(parents=True, exist_ok=True)
UPDATE_DIR.mkdir(parents=True, exist_ok=True)
TRAY_REPLY_DIR.mkdir(parents=True, exist_ok=True)
PICKER_REPLY_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

try:
    (DATA_DIR / "library.json").unlink(missing_ok=True)
except OSError:
    pass

class DiagnosticsRegistry:
    """Thread-safe lightweight operational telemetry kept local to this PC."""
    def __init__(self):
        self.lock = threading.RLock()
        self.started = time.time()
        self.events = deque(maxlen=200)
        self.providers: dict[str, dict[str, Any]] = {}

    @staticmethod
    def provider_key(host: str, port: int) -> str:
        return f"{str(host).casefold()}:{int(port)}"

    def event(self, level: str, area: str, message: str, **details: Any) -> None:
        item = {"ts": time.time(), "level": str(level), "area": str(area), "message": str(message)[:1000], "details": details}
        with self.lock:
            self.events.appendleft(item)
        if level in {"warning", "error"}:
            try:
                line = json.dumps(item, ensure_ascii=False, default=str) + "\n"
                if DIAGNOSTICS_LOG_FILE.exists() and DIAGNOSTICS_LOG_FILE.stat().st_size > 2_000_000:
                    rotated = DIAGNOSTICS_LOG_FILE.with_suffix('.log.1')
                    rotated.unlink(missing_ok=True)
                    DIAGNOSTICS_LOG_FILE.replace(rotated)
                with DIAGNOSTICS_LOG_FILE.open('a', encoding='utf-8') as f:
                    f.write(line)
            except OSError:
                pass

    def provider_result(self, host: str, port: int, *, ok: bool, latency_ms: float = 0, bytes_count: int = 0, reconnect: bool = False, error: str = '') -> None:
        key = self.provider_key(host, port)
        with self.lock:
            m = self.providers.setdefault(key, {"successes": 0, "failures": 0, "reconnects": 0, "bytes": 0, "last_latency_ms": 0.0, "latency_sum": 0.0, "latency_samples": 0, "last_ok": 0.0, "last_error": "", "last_error_ts": 0.0})
            if ok:
                m["successes"] += 1; m["last_ok"] = time.time()
                if latency_ms > 0:
                    m["last_latency_ms"] = round(float(latency_ms), 1); m["latency_sum"] += float(latency_ms); m["latency_samples"] += 1
            else:
                m["failures"] += 1; m["last_error"] = str(error)[:500]; m["last_error_ts"] = time.time()
            if reconnect: m["reconnects"] += 1
            m["bytes"] += max(0, int(bytes_count or 0))

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {"started": self.started, "providers": json.loads(json.dumps(self.providers)), "events": list(self.events)}

DIAGNOSTICS = DiagnosticsRegistry()

# Distribution privacy rule:
# User state lives only under USER_ROOT. NewzDeck intentionally does NOT scan the
# application directory, Downloads, or old portable-build folders for providers or
# settings. The only automatic legacy migration is the explicit per-user rebrand
# move performed above from LOCALAPPDATA\"Usenet Browser\" to LOCALAPPDATA\NewzDeck.
# This prevents distributable installers from ever inheriting copied/synced build
# data or developer configuration on a fresh machine.

GROUP_CACHE: dict[str, dict[str, Any]] = {}
GROUP_CACHE_LOCK = threading.Lock()
GROUP_CACHE_DIR = DATA_DIR / "group-cache"
GROUP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
THUMB_STATS_FILE = DATA_DIR / "thumbnail-cache-stats.json"

ARTICLE_PAGE_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}
ARTICLE_PAGE_CACHE_LOCK = threading.Lock()
ARTICLE_PAGE_CACHE_TTL_SECONDS = 600.0
ARTICLE_PAGE_CACHE_MAX_ENTRIES = 300

def _article_page_cache_article_budget() -> int:
    """Bound recent-page RAM by both page count and approximate article objects."""
    try:
        ram_gb = _physical_memory_bytes() / (1024 ** 3)
    except Exception:
        ram_gb = 8.0
    if ram_gb <= 8:
        return 60000
    if ram_gb <= 16:
        return 100000
    if ram_gb <= 32:
        return 160000
    if ram_gb <= 64:
        return 220000
    return 300000

def _trim_article_page_cache_locked() -> None:
    total_articles = sum(len((entry.get("payload") or {}).get("articles") or []) for entry in ARTICLE_PAGE_CACHE.values())
    article_budget = _article_page_cache_article_budget()
    if len(ARTICLE_PAGE_CACHE) <= ARTICLE_PAGE_CACHE_MAX_ENTRIES and total_articles <= article_budget:
        return
    ordered = sorted(ARTICLE_PAGE_CACHE.items(), key=lambda kv: float(kv[1].get("cached_at", 0) or 0))
    for key, entry in ordered:
        if len(ARTICLE_PAGE_CACHE) <= ARTICLE_PAGE_CACHE_MAX_ENTRIES and total_articles <= article_budget:
            break
        removed = ARTICLE_PAGE_CACHE.pop(key, None)
        if removed is not None:
            total_articles -= len((removed.get("payload") or {}).get("articles") or [])

# v3.6.7 browsing-session registry. Thumbnail/full-preview requests carry a
# short-lived browser-session token so work from a group/view that the user has
# already left can be interrupted inside BODY streaming instead of continuing to
# consume provider sockets in the background.
_BROWSE_SESSION_LOCK = threading.RLock()
_BROWSE_SESSIONS: dict[str, dict[str, Any]] = {}
SMART_BROWSE_EXECUTOR = ThreadPoolExecutor(max_workers=SMART_BROWSE_WORKER_COUNT, thread_name_prefix="usenet-browse-smart")

class BrowseSessionCancelled(RuntimeError):
    pass

def register_browse_session(provider_id: str, group: str, token: str) -> dict[str, Any]:
    provider_id = str(provider_id or "").strip()
    group = str(group or "").strip()
    token = str(token or "").strip()[:160]
    if not provider_id or not group or not token:
        raise ValueError("Provider, newsgroup, and browsing session are required")
    with _BROWSE_SESSION_LOCK:
        _BROWSE_SESSIONS[provider_id] = {"token": token, "group": group, "updated": time.monotonic()}
    return {"ok": True, "provider_id": provider_id, "group": group, "browse_session": token}

def browse_session_cancel_check(provider_id: str, group: str, token: str):
    token = str(token or "").strip()
    if not token:
        return None
    provider_id = str(provider_id or "").strip(); group = str(group or "").strip()
    def check() -> None:
        with _BROWSE_SESSION_LOCK:
            current = _BROWSE_SESSIONS.get(provider_id)
        if not current or current.get("token") != token or current.get("group") != group:
            raise BrowseSessionCancelled("Browsing request superseded by a newer newsgroup session")
    return check

_THUMB_STATS_LOCK = threading.Lock()
_THUMB_STATS_CACHE: dict[str, Any] | None = None
_THUMB_STATS_CACHE_TS = 0.0
_THUMB_STATS_DIRTY = True
_THUMB_CLEANUP_LAST = 0.0
_THUMB_CLEANUP_RUNNING = False
THUMB_STATS_TTL_SECONDS = 15.0
THUMB_CLEANUP_INTERVAL_SECONDS = 60.0

_PREVIEW_CLEANUP_LOCK = threading.Lock()
_PREVIEW_CLEANUP_LAST = 0.0
_PREVIEW_CLEANUP_RUNNING = False
PREVIEW_CLEANUP_INTERVAL_SECONDS = 300.0

def _provider_group_cache_signature(provider: dict[str, Any]) -> str:
    raw = json.dumps({
        "host": str(provider.get("host", "")).casefold(),
        "port": int(provider.get("port", 563)),
        "ssl": bool(provider.get("ssl", True)),
        "username": str(provider.get("username", "")).casefold(),
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]

def _provider_group_cache_path(provider_id: str) -> Path:
    safe = hashlib.sha256(str(provider_id).encode("utf-8")).hexdigest()[:24]
    return GROUP_CACHE_DIR / f"{safe}.json"

def _load_persistent_group_cache(provider_id: str, provider: dict[str, Any]) -> dict[str, Any] | None:
    path = _provider_group_cache_path(provider_id)
    data = json_read(path, None)
    if not isinstance(data, dict):
        return None
    if data.get("signature") != _provider_group_cache_signature(provider):
        return None
    groups = data.get("groups")
    if not isinstance(groups, list):
        return None
    return {"groups": groups, "loaded_at": float(data.get("loaded_at", 0) or 0), "source": "disk"}

def _save_persistent_group_cache(provider_id: str, provider: dict[str, Any], cached: dict[str, Any]) -> None:
    path = _provider_group_cache_path(provider_id)
    try:
        json_write(path, {
            "signature": _provider_group_cache_signature(provider),
            "loaded_at": float(cached.get("loaded_at", time.time()) or time.time()),
            "groups": list(cached.get("groups", [])),
        })
    except OSError:
        pass

def _drop_persistent_group_cache(provider_id: str) -> None:
    try:
        _provider_group_cache_path(provider_id).unlink(missing_ok=True)
    except OSError:
        pass

def _sorted_group_view(cached: dict[str, Any], sort: str) -> list[dict[str, Any]]:
    """Return a cached in-memory sort order for a provider's active groups."""
    with GROUP_CACHE_LOCK:
        sort_cache = cached.setdefault("_sorted", {})
        ready = sort_cache.get(sort)
    if isinstance(ready, list):
        return ready

    groups = list(cached.get("groups", []))
    if sort == "name_asc":
        groups.sort(key=lambda g: g["name"].lower())
    elif sort == "name_desc":
        groups.sort(key=lambda g: g["name"].lower(), reverse=True)
    elif sort == "articles_asc":
        groups.sort(key=lambda g: (g.get("articles", 0), g["name"].lower()))
    else:
        groups.sort(key=lambda g: (g.get("articles", 0), g["name"].lower()), reverse=True)

    with GROUP_CACHE_LOCK:
        sort_cache = cached.setdefault("_sorted", {})
        existing = sort_cache.get(sort)
        if isinstance(existing, list):
            return existing
        sort_cache[sort] = groups
    return groups

def json_read(path: Path, default: Any) -> Any:
    """Read NewzDeck JSON state, accepting standard UTF-8 and UTF-8 with BOM.

    Windows PowerShell 5.1 writes a UTF-8 BOM when scripts use ``-Encoding UTF8``.
    User-state files produced or repaired by Windows tooling must therefore be read
    with ``utf-8-sig`` semantics; it is identical to UTF-8 when no BOM is present
    and strips a leading BOM when one exists.
    """
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError, OSError):
        return default

def _atomic_text_write(path: Path, text: str) -> None:
    """Atomically replace a text file without cross-thread temp-name collisions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.{secrets.token_hex(3)}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass

def json_write(path: Path, value: Any) -> None:
    _atomic_text_write(path, json.dumps(value, indent=2, ensure_ascii=False))

def json_write_compact(path: Path, value: Any) -> None:
    """Atomic compact JSON writer for high-churn internal state files."""
    _atomic_text_write(path, json.dumps(value, ensure_ascii=False, separators=(",", ":")))

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

def _win_blob(data: bytes) -> tuple[DATA_BLOB, Any]:
    buf = ctypes.create_string_buffer(data)
    blob = DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))
    return blob, buf

def _load_download_dir_setting() -> Path:
    try:
        raw = json_read(SETTINGS_FILE, {})
        configured = str(raw.get("download_folder", "") or "").strip() if isinstance(raw, dict) else ""
        p = Path(configured).expanduser() if configured else DEFAULT_DOWNLOAD_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        DEFAULT_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_DOWNLOAD_DIR

DOWNLOAD_DIR = _load_download_dir_setting()

def protect_secret(secret: str, machine_scope: bool | None = None) -> str:
    if not secret:
        return ""
    raw = secret.encode("utf-8")
    if sys.platform == "win32":
        if machine_scope is None:
            machine_scope = SERVICE_MODE
        in_blob, in_buf = _win_blob(raw)
        out_blob = DATA_BLOB()
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        flags = 0x4 if machine_scope else 0
        if not crypt32.CryptProtectData(ctypes.byref(in_blob), "NewzDeck", None, None, None, flags, ctypes.byref(out_blob)):
            raise ctypes.WinError()
        try:
            protected = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return ("dpapim:" if machine_scope else "dpapi:") + base64.b64encode(protected).decode("ascii")
        finally:
            kernel32.LocalFree(out_blob.pbData)
    return "local:" + base64.b64encode(raw).decode("ascii")

def unprotect_secret(value: str) -> str:
    if not value:
        return ""
    if (value.startswith("dpapi:") or value.startswith("dpapim:")) and sys.platform == "win32":
        prefix_len = 7 if value.startswith("dpapim:") else 6
        protected = base64.b64decode(value[prefix_len:])
        in_blob, in_buf = _win_blob(protected)
        out_blob = DATA_BLOB()
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        if not crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
            raise ctypes.WinError()
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData).decode("utf-8")
        finally:
            kernel32.LocalFree(out_blob.pbData)
    if value.startswith("local:"):
        return base64.b64decode(value[6:]).decode("utf-8")
    return ""

def migrate_provider_secrets_machine_scope() -> int:
    """Reprotect existing provider passwords so the Windows service can decrypt them."""
    if sys.platform != "win32":
        return 0
    providers = get_providers()
    changed = 0
    for provider in providers:
        value = str(provider.get("password_protected") or "")
        if not value or value.startswith("dpapim:"):
            continue
        password = unprotect_secret(value)
        provider["password_protected"] = protect_secret(password, machine_scope=True)
        changed += 1
    if changed:
        save_providers(providers)
    return changed

_tray_helper_lock = threading.Lock()

def tray_helper_request(action: str, *, path: str = "", initial: str = "", title: str = "", text: str = "", enabled: bool | None = None, args: list[str] | None = None, working_dir: str = "", log_path: str = "", timeout: float = 125.0) -> dict[str, Any]:
    """Ask the logged-in tray process to perform an interactive desktop action."""
    if sys.platform != "win32":
        raise ValueError("This action is only available on Windows")
    try:
        if not TRAY_HEARTBEAT_FILE.exists() or time.time() - TRAY_HEARTBEAT_FILE.stat().st_mtime > 10:
            raise ValueError("The NewzDeck tray helper is not running. Use Settings > Background > Show Tray Icon and try again.")
    except OSError:
        raise ValueError("The NewzDeck tray helper is not running. Use Settings > Background > Show Tray Icon and try again.")
    req_id = uuid.uuid4().hex
    reply = TRAY_REPLY_DIR / f"{req_id}.json"
    request = {"id": req_id, "action": action, "path": path, "initial": initial, "title": title, "text": text, "enabled": enabled, "args": list(args or []), "working_dir": working_dir, "log_path": log_path}
    with _tray_helper_lock:

        deadline = time.monotonic() + min(timeout, 10.0)
        while TRAY_REQUEST_FILE.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        if TRAY_REQUEST_FILE.exists():
            raise ValueError("The NewzDeck tray helper is busy. Try again in a moment.")
        tmp = TRAY_REQUEST_FILE.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(request), encoding='utf-8')
        tmp.replace(TRAY_REQUEST_FILE)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if reply.exists():
            result = json_read(reply, {})
            reply.unlink(missing_ok=True)
            if isinstance(result, dict):
                if result.get('ok') is False:
                    raise ValueError(str(result.get('error') or 'Tray helper action failed'))
                return result
            break
        time.sleep(0.15)
    try:
        if TRAY_REQUEST_FILE.exists() and json_read(TRAY_REQUEST_FILE, {}).get('id') == req_id:
            TRAY_REQUEST_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    raise ValueError("The NewzDeck tray helper is not responding. Start the tray icon and try again.")

def _version_tuple(value: str) -> tuple[int, ...]:
    nums = [int(x) for x in re.findall(r"\d+", str(value or ""))[:4]]
    return tuple((nums + [0, 0, 0, 0])[:4])

def _release_http(url: str, *, timeout: float = 8.0, accept: str = "application/vnd.github+json"):
    req = urllib.request.Request(
        str(url),
        headers={
            "User-Agent": f"NewzDeck/{APP_VERSION} (+https://newzdeck.com)",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    return urllib.request.urlopen(req, timeout=timeout)

def _release_checksum_value(text: str, filename: str) -> str:
    target = Path(str(filename or "")).name.casefold()
    generic = ""
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^([0-9a-fA-F]{64})\s+[* ]?(.+?)\s*$", line)
        if m:
            digest, name = m.group(1).lower(), Path(m.group(2).strip()).name.casefold()
            if name == target:
                return digest
            if not generic:
                generic = digest
            continue
        m = re.match(r"^SHA256\s*\((.+)\)\s*=\s*([0-9a-fA-F]{64})$", line, re.I)
        if m:
            name, digest = Path(m.group(1).strip()).name.casefold(), m.group(2).lower()
            if name == target:
                return digest
            if not generic:
                generic = digest

    m = re.fullmatch(r"\s*([0-9a-fA-F]{64})\s*", str(text or ""))
    if m:
        return m.group(1).lower()
    return generic if target and len(str(text or "").splitlines()) == 1 else ""

def _select_online_update_assets(assets: list[dict[str, Any]], latest_version: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Choose the canonical Setup/checksum pair for a GitHub release.

    NewzDeck's public release naming is versioned (for example
    ``NewzDeck_v3.6.2_Setup.exe`` and ``NewzDeck_v3.6.2_SHA256.txt``).  Keep a
    conservative legacy fallback for older packages, but never pair a versioned
    installer with a checksum belonging to a different release.
    """
    latest = re.sub(r"^[vV]", "", str(latest_version or "").strip())
    canonical_installer = f"NewzDeck_v{latest}_Setup.exe".casefold() if latest else ""
    canonical_checksum = f"NewzDeck_v{latest}_SHA256.txt".casefold() if latest else ""
    by_name = {str(x.get("name") or "").casefold(): x for x in assets if isinstance(x, dict)}

    installer = by_name.get(canonical_installer) if canonical_installer else None
    if installer is None:
        legacy = [x for x in assets if re.match(r"^NewzDeckSetup.*\.exe$", str(x.get("name") or ""), re.I)]
        installer = legacy[0] if legacy else None

    checksum = by_name.get(canonical_checksum) if canonical_checksum else None
    if checksum is None and installer:
        iname = str(installer.get("name") or "")
        exact = (iname + ".sha256").casefold()
        for asset in assets:
            name = str(asset.get("name") or "")
            low = name.casefold()
            if low == exact or low in {"sha256sums.txt", "sha256sum.txt", "checksums.txt", "checksums.sha256"}:
                checksum = asset
                if low == exact:
                    break
    return installer, checksum


def online_update_status(force: bool = False) -> dict[str, Any]:
    cached = json_read(UPDATE_FEED_CACHE_FILE, {})
    if not isinstance(cached, dict):
        cached = {}
    now = time.time()
    if not force and cached.get("checked_at") and now - float(cached.get("checked_at") or 0) < UPDATE_FEED_TTL_SECONDS:
        return {**cached, "cached": True}
    base = {
        "online_feed": True,
        "feed_url": UPDATE_FEED_URL,
        "current_version": APP_VERSION,
        "latest_version": APP_VERSION,
        "update_available": False,
        "verified_download": False,
        "installer_name": "",
        "installer_url": "",
        "installer_size": 0,
        "checksum_url": "",
        "release_url": "",
        "release_notes": "",
        "published_at": "",
        "checked_at": now,
        "cached": False,
    }
    if not UPDATE_FEED_URL:
        return {**base, "online_feed": False, "feed_error": "Online update feed is disabled"}
    try:
        with _release_http(UPDATE_FEED_URL, timeout=8) as resp:
            raw = resp.read(4 * 1024 * 1024)
        release = json.loads(raw.decode("utf-8", "replace"))
        tag = str(release.get("tag_name") or release.get("name") or "").strip()
        latest = re.sub(r"^[vV]", "", tag).strip() or APP_VERSION
        assets = [x for x in (release.get("assets") or []) if isinstance(x, dict)]
        installer, checksum = _select_online_update_assets(assets, latest)
        result = {
            **base,
            "latest_version": latest,
            "update_available": _version_tuple(latest) > _version_tuple(APP_VERSION),
            "installer_name": str((installer or {}).get("name") or ""),
            "installer_url": str((installer or {}).get("browser_download_url") or ""),
            "installer_size": int((installer or {}).get("size") or 0),
            "checksum_url": str((checksum or {}).get("browser_download_url") or ""),
            "verified_download": bool(installer and checksum),
            "release_url": str(release.get("html_url") or ""),
            "release_notes": str(release.get("body") or "")[:12000],
            "published_at": str(release.get("published_at") or release.get("created_at") or ""),
            "checked_at": now,
        }
        json_write(UPDATE_FEED_CACHE_FILE, result)
        return result
    except Exception as exc:

        if cached.get("latest_version"):
            return {**cached, "cached": True, "feed_error": str(exc), "checked_at": float(cached.get("checked_at") or 0)}
        return {**base, "feed_error": str(exc)}

def _launch_update_handoff(staged: Path, *, target_version: str = "") -> None:
    """Start a short-lived user-session coordinator that owns the whole update handoff.

    NewzDeck.exe launches the Chromium app window detached, so Inno Restart Manager
    cannot close the visible UI by targeting NewzDeck.exe. Copy the native Picker
    helper outside {app}, let it close NewzDeck's app/tray windows, wait for Setup,
    then restore the service/tray/app after Setup exits. The copied coordinator
    survives replacement of the installed NewzDeckPicker.exe during the update.
    """
    if sys.platform != "win32":
        raise ValueError("In-app installation is currently available on Windows only")
    if not PICKER_HELPER_EXE.exists():
        raise ValueError("NewzDeckPicker.exe is missing. Reinstall NewzDeck to repair the update handoff helper.")
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    for old in UPDATE_DIR.glob("NewzDeckUpdateHandoff-*.exe"):
        try:
            if time.time() - old.stat().st_mtime > 3600:
                old.unlink(missing_ok=True)
        except OSError:
            pass
    handoff = UPDATE_DIR / f"NewzDeckUpdateHandoff-{int(time.time())}-{os.getpid()}.exe"
    shutil.copy2(PICKER_HELPER_EXE, handoff)
    service_installed = _service_query_status() != "not_installed"
    tray_recent = False
    try:
        tray_recent = TRAY_HEARTBEAT_FILE.exists() and time.time() - TRAY_HEARTBEAT_FILE.stat().st_mtime <= 15
    except OSError:
        tray_recent = False
    restore_tray = bool(service_installed or tray_recent or _tray_autostart_enabled())
    args = [
        "--update-handoff",
        "--setup", str(staged),
        "--app-dir", str(APP_DIR),
        "--user-root", str(USER_ROOT),
        "--version", str(target_version or APP_VERSION),
        "--restore-service", "1" if service_installed else "0",
        "--restore-tray", "1" if restore_tray else "0",
    ]
    launched = False
    if SERVICE_MODE:
        launched = _launch_process_in_active_user_session(str(handoff), subprocess.list2cmdline(args))
    else:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
        subprocess.Popen([str(handoff)] + args, cwd=str(UPDATE_DIR), creationflags=flags)
        launched = True
    if not launched:
        try:
            handoff.unlink(missing_ok=True)
        except OSError:
            pass
        raise ValueError("Windows could not launch the NewzDeck update handoff in the signed-in desktop session")

def _schedule_update_handoff(staged: Path, *, target_version: str, server_obj=None) -> None:
    def run():
        # Return the API response first so the browser can paint the handoff state.
        time.sleep(0.8)
        try:
            _launch_update_handoff(staged, target_version=target_version)
            if not SERVICE_MODE and server_obj is not None:
                time.sleep(1.4)
                try:
                    server_obj.shutdown()
                except Exception:
                    pass
        except Exception as exc:
            safe_print("Update handoff failed:", repr(exc))
    threading.Thread(target=run, name="newzdeck-update-handoff", daemon=True).start()

def download_verified_online_update() -> dict[str, Any]:
    status = online_update_status(force=True)
    if not status.get("update_available"):
        return {"ok": True, "update_available": False, "message": "NewzDeck is already up to date.", "status": status}
    installer_url = str(status.get("installer_url") or "")
    checksum_url = str(status.get("checksum_url") or "")
    installer_name = Path(str(status.get("installer_name") or "NewzDeckSetup.exe")).name
    if not installer_url:
        raise ValueError("The latest release does not contain a NewzDeck Setup installer")
    if not checksum_url:
        raise ValueError("The latest release does not contain a SHA-256 checksum. NewzDeck will not run an unverified online update.")
    with _release_http(checksum_url, timeout=10, accept="text/plain, application/octet-stream") as resp:
        checksum_text = resp.read(1024 * 1024).decode("utf-8", "replace")
    expected = _release_checksum_value(checksum_text, installer_name)
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("The release checksum file does not contain a SHA-256 value for the NewzDeck installer")
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    staged = UPDATE_DIR / installer_name
    part = staged.with_suffix(staged.suffix + ".part")
    h = hashlib.sha256(); total = 0; first = b""
    try:
        with _release_http(installer_url, timeout=30, accept="application/octet-stream") as resp, open(part, "wb") as out:
            declared = int(resp.headers.get("Content-Length", "0") or 0)
            if declared and declared > UPDATE_MAX_PACKAGE_BYTES:
                raise ValueError("The update package is larger than NewzDeck's safety limit")
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                if not first:
                    first = chunk[:2]
                total += len(chunk)
                if total > UPDATE_MAX_PACKAGE_BYTES:
                    raise ValueError("The update package exceeded NewzDeck's safety limit")
                h.update(chunk); out.write(chunk)
        if total <= 0 or first != b"MZ":
            raise ValueError("The downloaded update is not a valid Windows executable package")
        actual = h.hexdigest().lower()
        if not secrets.compare_digest(actual, expected):
            raise ValueError("SHA-256 verification failed. The downloaded update was deleted and will not be run.")
        os.replace(part, staged)
    except Exception:
        try: part.unlink(missing_ok=True)
        except OSError: pass
        raise
    return {"ok": True, "update_available": True, "version": status.get("latest_version"), "sha256": expected, "path": str(staged), "message": f"NewzDeck v{status.get('latest_version')} verified and ready for managed update handoff."}

def _service_query_status() -> str:
    if sys.platform != 'win32':
        return 'unsupported'
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    proc = subprocess.run(['sc.exe','query',SERVICE_NAME], capture_output=True, text=True, creationflags=flags)
    if proc.returncode != 0:
        return 'not_installed'
    text = (proc.stdout or '').upper()
    for token, status in [('RUNNING','running'),('START_PENDING','starting'),('STOP_PENDING','stopping'),('STOPPED','stopped')]:
        if token in text:
            return status
    return 'installed'

def _tray_command_parts() -> tuple[str, list[str]]:
    if not TRAY_HELPER_EXE.exists():
        raise ValueError('NewzDeckTray.exe is missing. Reinstall NewzDeck to repair the system-tray helper.')
    return str(TRAY_HELPER_EXE), ['--app-dir', str(APP_DIR), '--user-root', str(USER_ROOT), '--version', APP_VERSION]

def _tray_registry_command() -> str:
    exe, args = _tray_command_parts()
    def q(v: str) -> str:
        return '"' + str(v).replace('"', '\\"') + '"' if (' ' in str(v) or '\t' in str(v) or '"' in str(v)) else str(v)
    return ' '.join([q(exe)] + [q(x) for x in args])

def _tray_autostart_enabled() -> bool:
    if sys.platform != 'win32':
        return False
    if SERVICE_MODE:
        return TRAY_AUTOSTART_FILE.exists()
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
            value, _ = winreg.QueryValueEx(key, 'NewzDeckTray')
            enabled = bool(str(value).strip())
            if enabled:
                TRAY_AUTOSTART_FILE.write_text('1', encoding='utf-8')
            return enabled
    except Exception:
        return TRAY_AUTOSTART_FILE.exists()

def _set_tray_autostart(enabled: bool) -> None:
    if sys.platform != 'win32':
        return
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        if enabled:
            winreg.SetValueEx(key, 'NewzDeckTray', 0, winreg.REG_SZ, _tray_registry_command())
            TRAY_AUTOSTART_FILE.write_text('1', encoding='utf-8')
        else:
            try: winreg.DeleteValue(key, 'NewzDeckTray')
            except FileNotFoundError: pass
            TRAY_AUTOSTART_FILE.unlink(missing_ok=True)

def _launch_process_in_active_user_session(executable: str, arguments: str = '') -> bool:
    """Launch a GUI helper in the active interactive session from the LocalSystem service."""
    if sys.platform != 'win32':
        return False
    try:
        kernel32 = ctypes.windll.kernel32
        wtsapi32 = ctypes.windll.wtsapi32
        advapi32 = ctypes.windll.advapi32
        userenv = ctypes.windll.userenv
        session_id = int(kernel32.WTSGetActiveConsoleSessionId())
        if session_id == 0xFFFFFFFF:
            return False
        token = ctypes.wintypes.HANDLE()
        if not wtsapi32.WTSQueryUserToken(ctypes.wintypes.ULONG(session_id), ctypes.byref(token)):
            return False
        env = ctypes.c_void_p()
        class STARTUPINFOW(ctypes.Structure):
            _fields_ = [
                ('cb', ctypes.wintypes.DWORD), ('lpReserved', ctypes.wintypes.LPWSTR),
                ('lpDesktop', ctypes.wintypes.LPWSTR), ('lpTitle', ctypes.wintypes.LPWSTR),
                ('dwX', ctypes.wintypes.DWORD), ('dwY', ctypes.wintypes.DWORD),
                ('dwXSize', ctypes.wintypes.DWORD), ('dwYSize', ctypes.wintypes.DWORD),
                ('dwXCountChars', ctypes.wintypes.DWORD), ('dwYCountChars', ctypes.wintypes.DWORD),
                ('dwFillAttribute', ctypes.wintypes.DWORD), ('dwFlags', ctypes.wintypes.DWORD),
                ('wShowWindow', ctypes.wintypes.WORD), ('cbReserved2', ctypes.wintypes.WORD),
                ('lpReserved2', ctypes.POINTER(ctypes.c_byte)),
                ('hStdInput', ctypes.wintypes.HANDLE), ('hStdOutput', ctypes.wintypes.HANDLE),
                ('hStdError', ctypes.wintypes.HANDLE),
            ]
        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [('hProcess', ctypes.wintypes.HANDLE), ('hThread', ctypes.wintypes.HANDLE),
                        ('dwProcessId', ctypes.wintypes.DWORD), ('dwThreadId', ctypes.wintypes.DWORD)]
        si = STARTUPINFOW(); si.cb = ctypes.sizeof(si); si.lpDesktop = 'winsta0\\default'
        pi = PROCESS_INFORMATION()
        created_env = bool(userenv.CreateEnvironmentBlock(ctypes.byref(env), token, False))
        cmd = f'"{executable}"' + (f' {arguments}' if arguments else '')
        cmd_buf = ctypes.create_unicode_buffer(cmd)
        flags = 0x00000400 | 0x08000000
        ok = bool(advapi32.CreateProcessAsUserW(token, None, cmd_buf, None, None, False, flags,
                                                env if created_env else None, str(APP_DIR), ctypes.byref(si), ctypes.byref(pi)))
        if created_env:
            userenv.DestroyEnvironmentBlock(env)
        kernel32.CloseHandle(token)
        if ok:
            kernel32.CloseHandle(pi.hThread); kernel32.CloseHandle(pi.hProcess)
        return ok
    except Exception:
        return False

_taskbar_identity_lock = threading.Lock()
_taskbar_identity_last_launch = 0.0

def _launch_taskbar_identity() -> bool:
    """Compatibility no-op for the retired picker-based taskbar helper.

    NewzDeck v3.6.5+ assigns taskbar identity from NewzDeck.exe itself. Keeping
    NewzDeckPicker.exe alive in --taskbar-fix mode created a file lock that could
    block verified in-app upgrades, so v3.6.10 deliberately stops launching it.
    """
    return False

def _native_folder_picker(initial_path: str, title: str, timeout: float = 125.0) -> dict[str, Any]:
    """Open NewzDeck's native Windows folder picker in the signed-in desktop session.

    The picker is a small native GUI helper shipped with NewzDeck. In background-
    service mode the service launches that EXE in the active user's session; in
    desktop mode it is launched normally. No PowerShell scripts, temp-script ACLs,
    or tray-helper round trips are involved.
    """
    if sys.platform != 'win32':
        raise ValueError('The folder picker is currently available in the Windows desktop app')
    if not PICKER_HELPER_EXE.exists():
        raise ValueError('NewzDeckPicker.exe is missing. Reinstall NewzDeck to repair the folder picker.')

    req_id = uuid.uuid4().hex
    PICKER_REPLY_DIR.mkdir(parents=True, exist_ok=True)
    result_file = PICKER_REPLY_DIR / f'{req_id}.json'
    started_file = PICKER_REPLY_DIR / f'{req_id}.started'
    for item in (result_file, started_file, Path(str(result_file) + '.tmp'), Path(str(started_file) + '.tmp')):
        try:
            item.unlink(missing_ok=True)
        except OSError:
            pass

    args = [
        '--result-file', str(result_file),
        '--started-file', str(started_file),
        '--initial', str(initial_path or ''),
        '--title', str(title or 'Choose a NewzDeck folder'),
    ]
    launched = False
    if SERVICE_MODE:
        launched = _launch_process_in_active_user_session(str(PICKER_HELPER_EXE), subprocess.list2cmdline(args))
    else:
        try:
            subprocess.Popen([str(PICKER_HELPER_EXE)] + args, cwd=str(APP_DIR),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            launched = True
        except OSError:
            launched = False
    if not launched:
        raise ValueError('Windows could not start NewzDeck\'s native folder picker.')

    startup_deadline = time.monotonic() + 5.0
    while time.monotonic() < startup_deadline:
        if started_file.exists() or result_file.exists():
            break
        time.sleep(0.05)
    if not started_file.exists() and not result_file.exists():
        raise ValueError('The native folder picker did not start in your Windows desktop session.')

    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            if result_file.exists():
                raw = result_file.read_text(encoding='utf-8', errors='replace')
                status, _, value = raw.partition('\n')
                status = status.strip().upper()
                value = value.strip()
                if status == 'OK':
                    return {'ok': True, 'cancelled': False, 'folder': value}
                if status == 'CANCEL':
                    return {'ok': True, 'cancelled': True, 'folder': ''}
                if status == 'ERROR':
                    raise ValueError(value or 'The native folder picker failed.')
                raise ValueError('The native folder picker returned an invalid result.')
            time.sleep(0.08)
    finally:
        for item in (result_file, started_file, Path(str(result_file) + '.tmp'), Path(str(started_file) + '.tmp')):
            try:
                item.unlink(missing_ok=True)
            except OSError:
                pass
    raise ValueError('The folder picker did not return a result.')

def _launch_tray() -> bool:
    if sys.platform != 'win32':
        return False
    exe, args = _tray_command_parts()
    if SERVICE_MODE:
        def winquote(v: str) -> str:
            return subprocess.list2cmdline([str(v)])
        return _launch_process_in_active_user_session(exe, ' '.join(winquote(x) for x in args))
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    try:
        subprocess.Popen([exe] + args, cwd=str(APP_DIR), creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def _ensure_tray_running(timeout: float = 8.0) -> None:
    try:
        if TRAY_HEARTBEAT_FILE.exists() and time.time() - TRAY_HEARTBEAT_FILE.stat().st_mtime <= 10:
            return
    except OSError:
        pass
    if not _launch_tray():
        raise ValueError('NewzDeck could not start the tray helper in the signed-in Windows session.')
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if TRAY_HEARTBEAT_FILE.exists() and time.time() - TRAY_HEARTBEAT_FILE.stat().st_mtime <= 10:
                return
        except OSError:
            pass
        time.sleep(0.2)
    raise ValueError('The NewzDeck tray helper did not become ready.')

def _service_helper_args(action: str, result_file: Path | None = None, delay_ms: int = 0) -> list[str]:
    args = [str(action)]
    if action in {'install', 'repair'}:
        args += ['--user-root', str(USER_ROOT), '--default-download-dir', str(DEFAULT_DOWNLOAD_DIR)]
    if result_file is not None:
        args += ['--result-file', str(result_file)]
    if delay_ms > 0:
        args += ['--delay-ms', str(int(delay_ms))]
    return args

def _run_service_helper(action: str, *, elevated: bool, wait: bool = True, delay_ms: int = 0, timeout: float = 65.0) -> dict[str, Any]:
    if sys.platform != 'win32':
        raise ValueError('Background service controls are only available on Windows')
    if not SERVICE_HELPER_EXE.exists():
        raise ValueError('NewzDeckService.exe is missing. Reinstall NewzDeck to repair the background service files.')
    result_file = DATA_DIR / f'service-helper-{uuid.uuid4().hex}.json' if wait else None
    args = _service_helper_args(action, result_file, delay_ms)
    if elevated:
        params = subprocess.list2cmdline(args)
        result = ctypes.windll.shell32.ShellExecuteW(None, 'runas', str(SERVICE_HELPER_EXE), params, str(APP_DIR), 0)
        if int(result) <= 32:
            raise ValueError('Windows did not start the elevated NewzDeck service helper. The UAC prompt may have been cancelled.')
    else:
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        subprocess.Popen([str(SERVICE_HELPER_EXE)] + args, cwd=str(APP_DIR), creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not wait or result_file is None:
        return {'ok': True, 'elevation_started': bool(elevated)}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if result_file.exists():
            try:
                data = json.loads(result_file.read_text(encoding='utf-8'))
            finally:
                result_file.unlink(missing_ok=True)
            if not data.get('ok'):
                raise ValueError(str(data.get('error') or f'Background service {action} failed.'))
            return data
        time.sleep(0.2)
    raise ValueError(f'Timed out waiting for Windows to {action} the NewzDeck service.')

def service_status_snapshot() -> dict[str, Any]:
    status = _service_query_status()
    state = json_read(SERVICE_STATE_FILE, {})
    if not isinstance(state, dict): state = {}
    port = 0
    port_file = USER_ROOT / 'newzdeck.port'
    try: port = int(port_file.read_text(encoding='utf-8').strip())
    except Exception: port = 0
    service_ready = False
    if sys.platform == 'win32' and status == 'running' and port:
        if SERVICE_MODE:
            service_ready = True
        else:
            try:
                import urllib.request
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=0.6) as resp:
                    health = json.loads(resp.read().decode('utf-8'))
                service_ready = bool(health.get('service_mode'))
            except Exception:
                service_ready = False
    return {
        'ok': True, 'supported': sys.platform == 'win32', 'installed': sys.platform == 'win32' and status != 'not_installed',
        'status': status, 'service_mode': SERVICE_MODE, 'service_ready': service_ready,
        'service_url': f'http://127.0.0.1:{port}' if service_ready and port else '',
        'tray_autostart': _tray_autostart_enabled(), 'port': port,
        'worker_status': str(state.get('status') or ''), 'worker_detail': str(state.get('detail') or ''),
        'worker_pid': int(state.get('pid') or 0), 'restarts': int(state.get('restarts') or 0),
    }

_PROVIDERS_CACHE_LOCK = threading.RLock()
_PROVIDERS_CACHE_MTIME_NS = -1
_PROVIDERS_CACHE: list[dict[str, Any]] = []

def _provider_file_mtime_ns() -> int:
    try:
        return int(PROVIDERS_FILE.stat().st_mtime_ns)
    except OSError:
        return -1

def _normalize_provider_records(raw: Any) -> tuple[list[dict[str, Any]], bool]:
    """Accept the canonical provider array plus safe legacy/single-provider shapes.

    A few recovery/older tooling paths could leave a valid single provider object at
    the JSON root.  Treating that as an empty provider list makes the profile appear
    deleted even though all credentials are still present on disk.  Normalize only
    unambiguous shapes and migrate them back to the canonical list format.
    """
    migrated = False
    if isinstance(raw, list):
        source = raw
    elif isinstance(raw, dict) and isinstance(raw.get("providers"), list):
        source = raw.get("providers") or []
        migrated = True
    elif isinstance(raw, dict) and str(raw.get("host") or "").strip():
        source = [raw]
        migrated = True
    else:
        source = []
    return [dict(p) for p in source if isinstance(p, dict) and str(p.get("host") or "").strip()], migrated

def get_providers() -> list[dict[str, Any]]:
    """Return provider settings without reparsing providers.json on every request."""
    global _PROVIDERS_CACHE_MTIME_NS, _PROVIDERS_CACHE
    mtime_ns = _provider_file_mtime_ns()
    with _PROVIDERS_CACHE_LOCK:
        if mtime_ns != _PROVIDERS_CACHE_MTIME_NS:
            raw = json_read(PROVIDERS_FILE, [])
            normalized, migrated = _normalize_provider_records(raw)
            _PROVIDERS_CACHE = normalized
            if migrated and normalized:
                try:
                    # Canonicalize in place without changing any provider fields or secrets.
                    json_write(PROVIDERS_FILE, normalized)
                    mtime_ns = _provider_file_mtime_ns()
                except Exception:
                    pass
            _PROVIDERS_CACHE_MTIME_NS = mtime_ns
        return [dict(p) for p in _PROVIDERS_CACHE]

def save_providers(providers: list[dict[str, Any]]) -> None:
    global _PROVIDERS_CACHE_MTIME_NS, _PROVIDERS_CACHE
    normalized = [dict(p) for p in providers if isinstance(p, dict)]
    json_write(PROVIDERS_FILE, normalized)
    with _PROVIDERS_CACHE_LOCK:
        _PROVIDERS_CACHE = [dict(p) for p in normalized]
        _PROVIDERS_CACHE_MTIME_NS = _provider_file_mtime_ns()

PROVIDER_ROLE_ORDER = {"primary": 0, "backup": 1, "recovery": 2}

def _provider_role(provider: dict[str, Any]) -> str:
    role = str(provider.get("role", "primary") or "primary").lower()
    return role if role in PROVIDER_ROLE_ORDER else "primary"

def provider_enabled_for(provider: dict[str, Any], purpose: str) -> bool:
    if not bool(provider.get("enabled", True)):
        return False
    defaults = {"browsing": True, "previews": True, "downloads": True, "recovery": True}
    return bool(provider.get(f"use_{purpose}", defaults.get(purpose, True)))

def providers_for_purpose(purpose: str, exclude_id: str = "") -> list[dict[str, Any]]:
    source = get_providers()
    indexed = [(i, p) for i, p in enumerate(source) if str(p.get("id", "")) != str(exclude_id) and provider_enabled_for(p, purpose)]
    if purpose == "recovery":
        role_order = {"backup": 0, "recovery": 1, "primary": 2}
    else:
        role_order = PROVIDER_ROLE_ORDER
    indexed.sort(key=lambda item: (role_order.get(_provider_role(item[1]), 99), max(1, int(item[1].get("priority", 10) or 10)), item[0]))
    return [p for _, p in indexed]

def resolve_provider_for_purpose(origin_id: str, purpose: str) -> dict[str, Any]:
    origin = provider_by_id(origin_id)
    if provider_enabled_for(origin, purpose):
        return origin
    candidates = providers_for_purpose(purpose, exclude_id=origin_id)
    if candidates:
        return candidates[0]
    raise ValueError(f"No enabled provider is configured for {purpose}")

def public_provider(provider: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": provider.get("id"),
        "name": provider.get("name", "Provider"),
        "host": provider.get("host", ""),
        "port": provider.get("port", 563),
        "ssl": bool(provider.get("ssl", True)),
        "username": provider.get("username", ""),
        "has_password": bool(provider.get("password_protected")),
        "connections": int(provider.get("connections", 20)),
        "pipeline_depth": max(0, min(NNTP_PIPELINE_MAX_DEPTH, int(provider.get("pipeline_depth", 0) or 0))),
        "enabled": bool(provider.get("enabled", True)),
        "role": _provider_role(provider),
        "priority": max(1, int(provider.get("priority", 10) or 10)),
        "use_browsing": bool(provider.get("use_browsing", True)),
        "use_previews": bool(provider.get("use_previews", True)),
        "use_downloads": bool(provider.get("use_downloads", True)),
        "use_recovery": bool(provider.get("use_recovery", True)),
    }

def provider_by_id(provider_id: str) -> dict[str, Any]:
    for p in get_providers():
        if p.get("id") == provider_id:
            return p
    raise ValueError("Provider not found")

def decode_header_value(value: str) -> str:
    try:
        parts = email.header.decode_header(value)
        out = []
        for part, enc in parts:
            if isinstance(part, bytes):
                out.append(part.decode(enc or "utf-8", errors="replace"))
            else:
                out.append(part)
        return "".join(out)
    except Exception:
        return value

class NntpError(RuntimeError):
    pass

class SegmentFetchError(NntpError):
    """Structured failure for one article segment across one or more providers."""
    def __init__(self, message: str, *, code: str = "segment_failed", label: str = "Segment unavailable", retryable: bool = False, suggestion: str = "", attempts: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.code = code
        self.label = label
        self.retryable = bool(retryable)
        self.suggestion = suggestion
        self.attempts = list(attempts or [])

class DownloadIncompleteError(NntpError):
    """Raised after all possible blocks were processed but one or more remain unavailable."""
    def __init__(self, message: str, *, failures: list[dict[str, Any]], retryable: bool = False, code: str = "incomplete", label: str = "Download incomplete", suggestion: str = ""):
        super().__init__(message)
        self.failures = list(failures or [])
        self.retryable = bool(retryable)
        self.code = code
        self.label = label
        self.suggestion = suggestion

def classify_nntp_failure(exc: Exception) -> dict[str, Any]:
    """Translate raw socket/NNTP errors into user-facing categories and retry policy."""
    text = str(exc or "Unknown download error").strip() or "Unknown download error"
    low = text.casefold()
    status_match = re.search(r"(?:^|\s)(\d{3})(?:\s|$)", text)
    status = int(status_match.group(1)) if status_match else 0

    if isinstance(exc, ssl.SSLCertVerificationError) or "certificate verify failed" in low:
        return {"code":"tls_certificate","label":"TLS certificate problem","retryable":False,"suggestion":"Check the provider hostname, SSL setting, system clock, and certificate trust.","raw":text,"status":status}
    if "authentication failed" in low or status in {480, 481}:
        return {"code":"authentication","label":"Provider authentication failed","retryable":False,"suggestion":"Verify the provider username/password and that the account is active.","raw":text,"status":status}
    if "too many connections" in low or "connection limit" in low or "maximum connections" in low or "max connections" in low:
        return {"code":"connection_limit","label":"Provider connection limit reached","retryable":True,"suggestion":"The provider rejected an extra connection. Reduce Concurrent files or the provider connection setting if this repeats.","raw":text,"status":status}
    if "quota" in low or "bandwidth limit" in low or "download limit" in low or "account limit" in low:
        return {"code":"quota","label":"Provider account/quota limit reached","retryable":False,"suggestion":"Check the provider account for a bandwidth, block-account, or service limit before retrying.","raw":text,"status":status}
    if status == 411 or "no such newsgroup" in low:
        return {"code":"group_unavailable","label":"Newsgroup unavailable on provider","retryable":False,"suggestion":"This provider does not currently serve the requested newsgroup. Try another download/recovery provider.","raw":text,"status":status}
    if "connection refused" in low or "actively refused" in low:
        return {"code":"connection_refused","label":"Provider refused the connection","retryable":True,"suggestion":"Confirm the provider hostname/port and whether SSL is enabled. NewzDeck will retry transient refusals automatically.","raw":text,"status":status}
    if status == 502 or "permission denied" in low or "access denied" in low:
        return {"code":"permission","label":"Provider access denied","retryable":False,"suggestion":"The server denied access to this group/article. Check the provider account and server settings.","raw":text,"status":status}
    if status in {423, 430} or "no such article" in low or "article not found" in low or "unavailable by number or message-id" in low:
        return {"code":"article_missing","label":"Article block missing","retryable":False,"suggestion":"The block is not present on this provider. A recovery provider may have it; otherwise the post may be outside retention or removed.","raw":text,"status":status}
    if "crc mismatch" in low or "truncated" in low or "size mismatch" in low:
        return {"code":"integrity","label":"Corrupt article block","retryable":True,"suggestion":"NewzDeck will retry this block and can try a recovery provider. Repeated CRC failures usually mean a damaged post or provider copy.","raw":text,"status":status}
    if "no supported binary attachment" in low or "decode" in low or "encoding" in low or "yenc" in low:
        return {"code":"decode","label":"Binary decode failed","retryable":False,"suggestion":"The article body was received but could not be decoded as the expected binary data.","raw":text,"status":status}
    if isinstance(exc, socket.gaierror) or "name or service not known" in low or "getaddrinfo" in low or "nodename nor servname" in low:
        return {"code":"dns","label":"Provider DNS lookup failed","retryable":True,"suggestion":"Check the provider hostname and internet connection. NewzDeck can retry without discarding completed blocks.","raw":text,"status":status}
    if isinstance(exc, (socket.timeout, TimeoutError)) or "timed out" in low or "timeout" in low:
        return {"code":"timeout","label":"Provider timed out","retryable":True,"suggestion":"The provider did not respond in time. NewzDeck will retry automatically and preserve blocks already downloaded.","raw":text,"status":status}
    if isinstance(exc, ssl.SSLError) or "ssl" in low or "tls" in low:
        return {"code":"tls","label":"TLS/SSL connection failed","retryable":True,"suggestion":"The secure connection failed. Check SSL/port settings if the problem repeats.","raw":text,"status":status}
    if status in {400, 401, 403, 500, 503} or "connection" in low or "closed by server" in low or "reset by peer" in low or "broken pipe" in low:
        return {"code":"connection","label":"Provider connection interrupted","retryable":True,"suggestion":"The NNTP connection was interrupted. NewzDeck will retry automatically and preserve completed blocks.","raw":text,"status":status}
    if isinstance(exc, OSError):
        return {"code":"io","label":"Network or file I/O error","retryable":True,"suggestion":"A network or local I/O operation failed. Retry is safe because completed blocks are preserved.","raw":text,"status":status}
    return {"code":"segment_failed","label":"Article block failed","retryable":True,"suggestion":"Retry the missing block. NewzDeck will reuse blocks that were already downloaded successfully.","raw":text,"status":status}

def _parse_clock_minutes(value: str, fallback: str = "00:00") -> int:
    text = str(value or fallback).strip()
    try:
        hh, mm = text.split(":", 1)
        hour = max(0, min(23, int(hh))); minute = max(0, min(59, int(mm)))
        return hour * 60 + minute
    except Exception:
        return _parse_clock_minutes(fallback, "00:00") if text != fallback else 0

def _clock_window_active(start: str, end: str, now: datetime | None = None) -> bool:
    cur = now or datetime.now(); minute = cur.hour * 60 + cur.minute
    a = _parse_clock_minutes(start, "18:00"); b = _parse_clock_minutes(end, "23:00")
    if a == b: return True
    if a < b: return a <= minute < b
    return minute >= a or minute < b

def _split_keywords(value: Any) -> list[str]:
    raw = value if isinstance(value, list) else re.split(r'[,;\n]+', str(value or ''))
    return [str(x).strip().casefold() for x in raw if str(x).strip()][:100]

def automation_category_for(name: str, settings: dict[str, Any] | None = None) -> dict[str, str]:
    settings = settings if isinstance(settings, dict) else json_read(SETTINGS_FILE, {})
    if not bool(settings.get('smart_categories_enabled', DEFAULT_SMART_CATEGORIES)):
        return {'name':'', 'folder':'', 'priority':'normal'}
    text = str(name or '').casefold()
    if re.search(r'(?i)\bs\d{1,2}e\d{1,3}\b|\b\d{1,2}x\d{1,3}\b', text):
        return {'name':'TV', 'folder':safe_folder_name(str(settings.get('category_tv_folder') or 'TV')), 'priority':'normal'}
    rules = [
        ('TV', 'category_tv_keywords', 'category_tv_folder', 'TV'),
        ('Movies', 'category_movies_keywords', 'category_movies_folder', 'Movies'),
        ('Images', 'category_images_keywords', 'category_images_folder', 'Images'),
    ]
    for label, key, folder_key, default_folder in rules:
        words = _split_keywords(settings.get(key, ''))
        if words and any(word in text for word in words):
            return {'name':label, 'folder':safe_folder_name(str(settings.get(folder_key) or default_folder)), 'priority':'normal'}
    return {'name':'Other', 'folder':safe_folder_name(str(settings.get('category_other_folder') or 'Other')), 'priority':'normal'}

def recommended_nzb_indices(parsed: dict[str, Any]) -> list[int]:
    selected: list[int] = []
    for i, entry in enumerate(list(parsed.get('files') or [])):
        media = entry.get('media') or {}; filename = str(media.get('filename') or f'File {i+1}')
        ext = str(media.get('extension') or Path(filename).suffix.lstrip('.')).casefold()
        if bool(entry.get('is_par2_volume')) or ext in {'nfo','sfv','srr','txt'} or re.search(r'(?i)(sample|proof|screenshot)', filename):
            continue
        selected.append(i)
    return selected

class DownloadBandwidthLimiter:
    def __init__(self):
        self.lock = threading.Lock(); self.next_free = time.monotonic(); self._cache_ts = 0.0; self._cache: dict[str, Any] = {}
        # The BODY reader can be called once per TLS record (~16 KiB). Keep the
        # unlimited fast path essentially free instead of reparsing settings for
        # every record across dozens of NNTP threads.
        self._fast_rate_bps = 0
        self._fast_rate_ts = 0.0
    def _config(self) -> dict[str, Any]:
        now = time.monotonic()
        if now - self._cache_ts > 1.5:
            raw = json_read(SETTINGS_FILE, {}); self._cache = raw if isinstance(raw, dict) else {}; self._cache_ts = now
        return self._cache
    def current(self) -> dict[str, Any]:
        cfg = self._config(); enabled = bool(cfg.get('bandwidth_schedule_enabled', DEFAULT_BANDWIDTH_SCHEDULE_ENABLED))
        start = str(cfg.get('bandwidth_schedule_start', DEFAULT_BANDWIDTH_SCHEDULE_START) or DEFAULT_BANDWIDTH_SCHEDULE_START)
        end = str(cfg.get('bandwidth_schedule_end', DEFAULT_BANDWIDTH_SCHEDULE_END) or DEFAULT_BANDWIDTH_SCHEDULE_END)
        active = enabled and _clock_window_active(start, end)
        limit_mb = max(0.1, min(5000.0, float(cfg.get('bandwidth_schedule_limit_mb_s', DEFAULT_BANDWIDTH_SCHEDULE_LIMIT_MB_S) or DEFAULT_BANDWIDTH_SCHEDULE_LIMIT_MB_S)))
        return {'enabled':enabled, 'active':active, 'start':start, 'end':end, 'limit_mb_s':limit_mb, 'limit_bps':int(limit_mb*1024*1024) if active else 0}
    def consume(self, amount: int, cancel_check=None) -> None:
        if amount <= 0: return
        now = time.monotonic()
        # Refresh at most once per second. In the normal Unlimited case this
        # avoids thousands of Python dict/string/float operations per second.
        if now - self._fast_rate_ts >= 1.0:
            info = self.current()
            self._fast_rate_bps = int(info.get('limit_bps', 0) or 0)
            self._fast_rate_ts = now
        rate = self._fast_rate_bps
        if rate <= 0: return
        with self.lock:
            start = max(now, self.next_free); finish = start + amount / rate; self.next_free = finish; delay = finish - now
        while delay > 0:
            if cancel_check is not None: cancel_check()
            step = min(0.10, delay); time.sleep(step); delay -= step

DOWNLOAD_BANDWIDTH_LIMITER = DownloadBandwidthLimiter()

@functools.lru_cache(maxsize=1)
def _physical_memory_bytes() -> int:
    """Best-effort physical RAM size without adding a psutil dependency."""
    if sys.platform == "win32":
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            state = MEMORYSTATUSEX(); state.dwLength = ctypes.sizeof(state)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
                return int(state.ullTotalPhys)
        except Exception:
            pass
    try:
        return int(os.sysconf("SC_PHYS_PAGES")) * int(os.sysconf("SC_PAGE_SIZE"))
    except Exception:
        return 8 * 1024**3

def _enable_sparse_partial_file(fp) -> bool:
    """Mark a Windows partial file sparse before any full-size extension.

    Python's Windows file.truncate() ultimately extends a normal file with NUL
    bytes. On multi-gigabyte Usenet payloads that can turn the first Direct Write
    cache flush into gigabytes of needless disk I/O. NTFS sparse files make the
    advertised-size reservation metadata-only, matching the intended Direct Write
    behavior. On POSIX, extending a regular file with truncate is normally sparse.
    """
    if sys.platform != "win32":
        return True
    try:
        import msvcrt
        handle = msvcrt.get_osfhandle(fp.fileno())
        returned = ctypes.wintypes.DWORD(0)
        FSCTL_SET_SPARSE = 0x000900C4
        ok = ctypes.windll.kernel32.DeviceIoControl(
            ctypes.wintypes.HANDLE(handle), FSCTL_SET_SPARSE,
            None, 0, None, 0, ctypes.byref(returned), None,
        )
        return bool(ok)
    except Exception:
        return False

def _download_article_cache_budget_mb(active_jobs: int = 1) -> tuple[int, int]:
    """Return total and per-job decoded-article cache budgets.

    Use a meaningful RAM cache on fast lines so disk flushes do not repeatedly
    drain the socket queues. The global target is about one eighth of physical
    RAM, bounded from 512 MB to 2 GB, and divided among active file jobs.
    """
    ram_mb = max(1024, _physical_memory_bytes() // (1024 * 1024))
    total = max(512, min(2048, int(ram_mb // 8)))
    jobs = max(1, int(active_jobs or 1))
    per_job = max(DOWNLOAD_ARTICLE_CACHE_MIN_PER_JOB_MB, min(512, total // jobs))
    return total, per_job

class NntpClient:
    def __init__(self, host: str, port: int, use_ssl: bool, username: str = "", password: str = "", timeout: float = 20.0, probe_capabilities: bool = True):
        self.host = host
        self.port = int(port)
        self.use_ssl = use_ssl
        self.username = username
        self.password = password
        self.timeout = timeout
        self.sock: socket.socket | ssl.SSLSocket | None = None
        self.file = None
        # BODY pipelining can legally deliver bytes belonging to the next
        # response in the same SSL/TCP read. Keep those bytes here instead of
        # discarding them so status/body framing remains exact.
        self._read_ahead = bytearray()
        self.capabilities: list[str] = []
        self.probe_capabilities = probe_capabilities
        self._aborted = False
        self._state_lock = threading.RLock()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def connect(self):
        with self._state_lock:
            self._aborted = False
        raw = socket.create_connection((self.host, self.port), timeout=self.timeout)
        raw.settimeout(self.timeout)
        try:
            raw.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            raw.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)
            if hasattr(socket, "TCP_KEEPIDLE"): raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
            if hasattr(socket, "TCP_KEEPINTVL"): raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            if hasattr(socket, "TCP_KEEPCNT"): raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
        except OSError:
            pass
        if self.use_ssl:
            context = ssl.create_default_context()
            self.sock = context.wrap_socket(raw, server_hostname=self.host)
        else:
            self.sock = raw
        self.file = self.sock.makefile("rb", buffering=2 * 1024 * 1024)
        code, greeting = self._read_status()
        if code not in (200, 201):
            raise NntpError(f"Server rejected connection: {code} {greeting}")

        if self.username:
            code, msg = self.command(f"AUTHINFO USER {self.username}")
            if code == 381:
                code, msg = self.command(f"AUTHINFO PASS {self.password}")
            if code not in (281, 250):
                raise NntpError(f"Authentication failed: {code} {msg}")
        if self.probe_capabilities:
            try:
                code, msg, lines = self.command_multiline("CAPABILITIES")
                if code == 101:
                    self.capabilities = [line.decode("utf-8", errors="replace") for line in lines]
            except Exception:
                self.capabilities = []
        return self

    def close(self):
        """Gracefully close a connection from its owning worker thread."""
        try:
            if self.sock:
                try:
                    self._send("QUIT")
                except Exception:
                    pass
        finally:
            try:
                if self.file:
                    self.file.close()
            except Exception:
                pass
            finally:
                sock = self.sock
                self.file = None
                self.sock = None
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass

    def abort(self):
        """Immediately break a blocking NNTP read from another thread.

        Do not call file.close() here: BufferedReader.close() can block waiting for
        a concurrent readline() lock, which was the root cause of Stop All hanging.
        Shutting down the socket first wakes the owning worker; that worker later
        performs the normal close on its own thread.
        """
        with self._state_lock:
            self._aborted = True
            sock = self.sock
            self.sock = None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass

    def is_connected(self) -> bool:
        return bool(self.sock is not None and not self._aborted)

    def _send(self, command: str):
        if not self.sock:
            raise NntpError("Not connected")
        self.sock.sendall(command.encode("utf-8") + b"\r\n")

    def _readline(self) -> bytes:
        if not self.file:
            raise NntpError("Not connected")
        if self._read_ahead:
            nl = self._read_ahead.find(b"\n")
            if nl >= 0:
                line = bytes(self._read_ahead[:nl + 1])
                del self._read_ahead[:nl + 1]
            else:
                prefix = bytes(self._read_ahead)
                self._read_ahead.clear()
                tail = self.file.readline()
                line = prefix + tail
        else:
            line = self.file.readline()
        if not line:
            raise NntpError("Connection closed by server")
        return line.rstrip(b"\r\n")

    def _read_status(self) -> tuple[int, str]:
        line = self._readline()
        if len(line) < 3 or not line[:3].isdigit():
            raise NntpError("Invalid NNTP response")
        return int(line[:3]), line[4:].decode("utf-8", errors="replace") if len(line) > 4 else ""

    def _read_multiline(self) -> list[bytes]:
        lines = []
        while True:
            line = self._readline()
            if line == b".":
                break
            if line.startswith(b".."):
                line = line[1:]
            lines.append(line)
        return lines

    def command(self, command: str) -> tuple[int, str]:
        self._send(command)
        return self._read_status()

    def command_multiline(self, command: str) -> tuple[int, str, list[bytes]]:
        self._send(command)
        code, msg = self._read_status()
        if 100 <= code < 400:
            return code, msg, self._read_multiline()
        return code, msg, []

    def group(self, group_name: str) -> dict[str, int | str]:
        code, msg = self.command(f"GROUP {group_name}")
        if code != 211:
            raise NntpError(f"Unable to open group: {code} {msg}")
        parts = msg.split()
        if len(parts) < 4:
            raise NntpError("Unexpected GROUP response")
        return {"count": int(parts[0]), "low": int(parts[1]), "high": int(parts[2]), "group": parts[3]}

    def list_active(self, pattern: str | None = None) -> list[dict[str, Any]]:
        cmd = "LIST ACTIVE" + (f" {pattern}" if pattern else "")
        code, msg, lines = self.command_multiline(cmd)
        if code != 215:
            raise NntpError(f"Unable to list newsgroups: {code} {msg}")
        groups = []
        for raw in lines:
            parts = raw.decode("utf-8", errors="replace").split()
            if len(parts) >= 4:
                try:
                    high, low = int(parts[1]), int(parts[2])
                    estimate = max(0, high - low + 1)
                except ValueError:
                    estimate = 0
                groups.append({"name": parts[0], "high": parts[1], "low": parts[2], "status": parts[3], "articles": estimate})
        return groups

    def overview(self, start: int, end: int) -> list[dict[str, Any]]:
        if end < start:
            return []
        commands = [f"OVER {start}-{end}", f"XOVER {start}-{end}"]
        last_error = None
        for cmd in commands:
            try:
                code, msg, lines = self.command_multiline(cmd)
                if code in (224, 225):
                    return parse_overview(lines)
                last_error = f"{code} {msg}"
            except Exception as exc:
                last_error = str(exc)
        raise NntpError(f"Unable to load article overview: {last_error or 'unsupported'}")

    def body(self, article: int | str) -> list[bytes]:
        code, msg, lines = self.command_multiline(f"BODY {article}")
        if code != 222:
            raise NntpError(f"Unable to retrieve article body: {code} {msg}")
        return lines

    def body_iter(self, article: int | str):
        """Stream BODY response lines instead of buffering the whole article in RAM."""
        self._send(f"BODY {article}")
        code, msg = self._read_status()
        if code != 222:
            raise NntpError(f"Unable to retrieve article body: {code} {msg}")
        while True:
            line = self._readline()
            if line == b".":
                break
            if line.startswith(b".."):
                line = line[1:]
            yield line

    def body_control_prefix(self, article: int | str, *, max_bytes: int = NAME_RESOLUTION_PROBE_BYTES, max_lines: int = 80) -> list[bytes]:
        """Read only the beginning of BODY for low-bandwidth metadata inspection.

        Callers must discard this NNTP connection after returning because the
        remainder of the multiline BODY response intentionally remains unread.
        This makes yEnc name recovery cheap without downloading an entire binary
        segment merely to discover its filename.
        """
        self._send(f"BODY {article}")
        code, msg = self._read_status()
        if code != 222:
            raise NntpError(f"Unable to retrieve article body: {code} {msg}")
        lines: list[bytes] = []
        total = 0
        for _ in range(max(1, max_lines)):
            line = self._readline()
            if line == b".":
                break
            if line.startswith(b".."):
                line = line[1:]
            lines.append(line)
            total += len(line) + 2
            control = _control_view(line).lower()
            if control.startswith(b"=ybegin") or total >= max_bytes:
                break
        return lines

    def body_yenc_decoded_prefix(self, article: int | str, *, max_decoded: int = NAME_RESOLUTION_ARCHIVE_PROBE_BYTES, max_wire: int = NAME_RESOLUTION_ARCHIVE_WIRE_MAX_BYTES) -> tuple[bytes, dict[str, Any]]:
        """Decode only a bounded prefix of a yEnc BODY response.

        This is used by the Newsgroup name resolver to inspect archive headers
        without downloading a complete RAR/ZIP/7-Zip volume.  The caller must
        discard the connection afterwards because the BODY response normally
        remains intentionally unread.
        """
        self._send(f"BODY {article}")
        code, msg = self._read_status()
        if code != 222:
            raise NntpError(f"Unable to retrieve article body: {code} {msg}")
        decoded = bytearray()
        meta: dict[str, Any] = {"encoding": "yenc"}
        saw_begin = False
        wire = 0
        while wire < max(4096, int(max_wire)) and len(decoded) < max(1024, int(max_decoded)):
            line = self._readline()
            if line == b".":
                break
            if line.startswith(b".."):
                line = line[1:]
            wire += len(line) + 2
            control = _control_view(line)
            low = control.lower()
            if low.startswith(b"=ybegin"):
                _parse_yenc_begin(control, meta)
                saw_begin = True
                continue
            if not saw_begin:
                continue
            if low.startswith(b"=ypart"):
                _parse_ypart(control, meta)
                continue
            if low.startswith(b"=yend"):
                _parse_yenc_end(control, meta)
                break
            decoded.extend(_decode_yenc_data_line(line))
        return bytes(decoded[:max_decoded]), meta

    def _read_body_raw_response(self, *, cancel_check=None, progress_callback=None, max_bytes: int = 32 * 1024 * 1024) -> bytes:
        """Read one already-started multiline BODY response without line-by-line overhead.

        Any bytes that belong to a following pipelined response are preserved in
        ``_read_ahead``. This is the key framing primitive that allows multiple
        BODY commands to stay in flight on one commercial NNTP connection.
        """
        if not self.file:
            raise NntpError("Not connected")
        data = bytearray()
        marker = b"\r\n.\r\n"
        last_report = time.monotonic()
        last_report_bytes = 0
        search_from = 0
        while True:
            if cancel_check is not None:
                cancel_check()
            from_socket = not bool(self._read_ahead)
            if self._read_ahead:
                chunk = bytes(self._read_ahead)
                self._read_ahead.clear()
            else:
                try:
                    reader = getattr(self.file, "read1", None)
                    chunk = reader(2 * 1024 * 1024) if reader else self.file.read(2 * 1024 * 1024)
                except (OSError, ValueError) as exc:
                    raise NntpError(f"Connection interrupted while reading article body: {exc}") from exc
            if not chunk:
                raise NntpError("Connection closed by server while reading article body")
            if from_socket:
                DOWNLOAD_BANDWIDTH_LIMITER.consume(len(chunk), cancel_check)
            old_len = len(data)
            data.extend(chunk)
            if len(data) > max_bytes:
                raise NntpError(f"Article body exceeded {max_bytes // (1024*1024)} MB safety limit")

            if data.startswith(b".\r\n"):
                body_end, response_end = 0, 3
            else:
                idx = data.find(marker, max(0, min(search_from, old_len) - len(marker)))
                if idx >= 0:
                    body_end, response_end = idx, idx + len(marker)
                else:
                    body_end = response_end = -1
                    search_from = max(0, len(data) - len(marker) - 2)

            now = time.monotonic()
            if progress_callback is not None and (now - last_report >= 0.25 or len(data) - last_report_bytes >= 1024 * 1024):
                progress_callback(min(len(data), body_end if body_end >= 0 else len(data)))
                last_report = now
                last_report_bytes = len(data)

            if body_end >= 0:
                if response_end < len(data):
                    self._read_ahead.extend(data[response_end:])
                body = bytes(data[:body_end])
                break

        if progress_callback is not None:
            progress_callback(len(body))
        if body.startswith(b".."):
            body = b"." + body[2:]
        if b"\r\n.." in body:
            body = body.replace(b"\r\n..", b"\r\n.")
        return body

    def body_raw(self, article: int | str, *, cancel_check=None, progress_callback=None, max_bytes: int = 32 * 1024 * 1024) -> bytes:
        self._send(f"BODY {article}")
        code, msg = self._read_status()
        if code != 222:
            raise NntpError(f"Unable to retrieve article body: {code} {msg}")
        return self._read_body_raw_response(cancel_check=cancel_check, progress_callback=progress_callback, max_bytes=max_bytes)

    def body_raw_pipelined(self, articles: list[int | str], *, cancel_check=None, progress_callback=None, max_bytes: int = 32 * 1024 * 1024) -> list[dict[str, Any]]:
        """Issue several BODY commands at once and consume responses in order.

        RFC-compliant NNTP servers return responses in request order. Sending the
        next BODY before waiting for the previous article removes the RTT gap that
        otherwise leaves a fast connection idle between ~700 KB Usenet articles.
        """
        if not articles:
            return []
        if cancel_check is not None:
            cancel_check()
        if not self.sock:
            raise NntpError("Not connected")
        # One send call avoids a TLS record/syscall per article while preserving
        # normal NNTP command ordering. Responses are still consumed in order.
        commands = b"".join(f"BODY {article}\r\n".encode("utf-8") for article in articles)
        self.sock.sendall(commands)
        results: list[dict[str, Any]] = []
        for pos, article in enumerate(articles):
            if cancel_check is not None:
                cancel_check()
            code, msg = self._read_status()
            if code != 222:
                results.append({"ok": False, "article": article, "error": NntpError(f"Unable to retrieve article body: {code} {msg}")})
                continue
            cb = (lambda amount, p=pos: progress_callback(p, amount)) if progress_callback is not None else None
            raw = self._read_body_raw_response(cancel_check=cancel_check, progress_callback=cb, max_bytes=max_bytes)
            results.append({"ok": True, "article": article, "raw": raw})
        return results


class BrowseHeaderClientPool:
    """Small warm NNTP pool dedicated to interactive header browsing.

    Page loads used to reconnect/authenticate/select the group for every request.
    Two short-lived pooled connections remove that setup latency while still
    leaving the overwhelming majority of a high-connection account available to
    previews/downloads. Idle sessions are closed automatically after ten seconds.
    """
    def __init__(self, max_per_provider: int = BROWSE_HEADER_POOL_SIZE):
        self.max_per_provider = max(1, int(max_per_provider))
        self.cond = threading.Condition(threading.RLock())
        self.pools: dict[tuple[Any, ...], list[dict[str, Any]]] = {}

    @staticmethod
    def key(provider: dict[str, Any]) -> tuple[Any, ...]:
        return (
            provider.get("id") or provider.get("host", ""), str(provider.get("host", "")).casefold(),
            int(provider.get("port", 563)), bool(provider.get("ssl", True)), str(provider.get("username", "")),
        )

    def _close_holder(self, key: tuple[Any, ...], holder: dict[str, Any]) -> None:
        timer = holder.pop("idle_timer", None)
        if timer is not None:
            try: timer.cancel()
            except Exception: pass
        client = holder.get("client")
        holder["client"] = None; holder["closed"] = True
        try:
            if client: client.close()
        except Exception:
            pass
        with self.cond:
            pool = self.pools.get(key, [])
            if holder in pool: pool.remove(holder)
            if not pool: self.pools.pop(key, None)
            self.cond.notify_all()

    def _arm_idle_close(self, key: tuple[Any, ...], holder: dict[str, Any]) -> None:
        old = holder.pop("idle_timer", None)
        if old is not None:
            try: old.cancel()
            except Exception: pass
        marker = object(); holder["idle_marker"] = marker
        def expire() -> None:
            client = None
            with self.cond:
                if holder.get("busy") or holder.get("idle_marker") is not marker:
                    return
                idle = time.monotonic() - float(holder.get("last_used", 0.0))
                if idle < BROWSE_HEADER_IDLE_CLOSE_SECONDS - 0.05:
                    return
                holder["closed"] = True; holder["idle_timer"] = None; holder["idle_marker"] = None
                client = holder.get("client"); holder["client"] = None
                pool = self.pools.get(key, [])
                if holder in pool: pool.remove(holder)
                if not pool: self.pools.pop(key, None)
                self.cond.notify_all()
            try:
                if client: client.close()
            except Exception:
                pass
        timer = threading.Timer(BROWSE_HEADER_IDLE_CLOSE_SECONDS, expire)
        timer.daemon = True; holder["idle_timer"] = timer; timer.start()

    def acquire(self, provider: dict[str, Any], group: str) -> tuple[tuple[Any, ...], dict[str, Any], NntpClient]:
        key = self.key(provider); create = False; holder = None
        deadline = time.monotonic() + 8.0
        while holder is None:
            with self.cond:
                pool = self.pools.setdefault(key, [])
                for item in pool:
                    if not item.get("busy") and not item.get("closed") and item.get("client"):
                        holder = item; holder["busy"] = True
                        timer = holder.pop("idle_timer", None); holder["idle_marker"] = None
                        if timer is not None:
                            try: timer.cancel()
                            except Exception: pass
                        break
                if holder is None and len(pool) < self.max_per_provider:
                    holder = {"busy": True, "closed": False, "client": None, "group": "", "last_used": time.monotonic()}
                    pool.append(holder); create = True
                elif holder is None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("Timed out waiting for an interactive NNTP header connection")
                    self.cond.wait(timeout=min(0.25, remaining))
        try:
            if create:
                password = unprotect_secret(provider.get("password_protected", ""))
                client = NntpClient(provider["host"], provider["port"], bool(provider.get("ssl", True)), provider.get("username", ""), password, timeout=15.0, probe_capabilities=False)
                client.connect(); holder["client"] = client
            client = holder["client"]
            holder["last_used"] = time.monotonic()
            return key, holder, client
        except Exception:
            self._close_holder(key, holder)
            raise

    def release(self, key: tuple[Any, ...], holder: dict[str, Any], healthy: bool = True) -> None:
        if not healthy:
            self._close_holder(key, holder); return
        with self.cond:
            holder["busy"] = False; holder["last_used"] = time.monotonic(); self.cond.notify_all()
        self._arm_idle_close(key, holder)

    def lease(self, provider: dict[str, Any], group: str):
        pool = self
        class Lease:
            def __enter__(self_nonlocal):
                self_nonlocal.key, self_nonlocal.holder, self_nonlocal.client = pool.acquire(provider, group)
                return self_nonlocal.client
            def __exit__(self_nonlocal, exc_type, exc, tb):
                pool.release(self_nonlocal.key, self_nonlocal.holder, healthy=exc_type is None)
                return False
        return Lease()

BROWSE_HEADER_POOL = BrowseHeaderClientPool()

def parse_overview(lines: Iterable[bytes]) -> list[dict[str, Any]]:
    result = []
    for raw in lines:
        cols = raw.decode("utf-8", errors="replace").split("\t")
        if len(cols) < 5:
            continue
        try:
            article_no = int(cols[0])
        except ValueError:
            continue
        subject = decode_header_value(cols[1]) if len(cols) > 1 else ""
        sender = decode_header_value(cols[2]) if len(cols) > 2 else ""
        date = cols[3] if len(cols) > 3 else ""
        message_id = cols[4] if len(cols) > 4 else ""
        references = cols[5] if len(cols) > 5 else ""
        try:
            bytes_count = int(re.sub(r"\D", "", cols[6])) if len(cols) > 6 else 0
        except ValueError:
            bytes_count = 0
        try:
            lines_count = int(re.sub(r"\D", "", cols[7])) if len(cols) > 7 else 0
        except ValueError:
            lines_count = 0
        media = detect_media(subject)
        mp = multipart_info(subject)
        result.append({
            "article": article_no,
            "subject": subject,
            "from": sender,
            "date": date,
            "message_id": message_id,
            "references": references,
            "bytes": bytes_count,
            "lines": lines_count,
            "media": media,
            "multipart": mp,
        })
    return result

MEDIA_RE = re.compile(r'''(?i)(?:["']([^"'\r\n]+?\.(?:jpe?g|png|gif|webp|bmp|mp4|m4v|webm|mov|avi|mkv))["']|([^\s"'<>|]+?\.(?:jpe?g|png|gif|webp|bmp|mp4|m4v|webm|mov|avi|mkv)))''')
BINARY_FILE_RE = re.compile(r'''(?i)(?:["']([^"'\r\n]+?\.[a-z0-9]{1,8})["']|([^\s"'<>|]+?\.[a-z0-9]{1,8}))''')
COMMON_BINARY_EXTS = {
    'rar','zip','7z','par2','nzb','iso','img','bin','cue','tar','gz','bz2','xz','tgz','tbz','txz',
    'pdf','epub','mobi','azw','azw3','cbz','cbr','doc','docx','xls','xlsx','ppt','pptx','txt',
    'mp3','flac','wav','aac','m4a','ogg','opus','exe','msi','apk','dmg','pkg','deb','rpm'
}
PART_PATTERN = re.compile(r"(?i)(?:\(|\[)(\d{1,6})\s*(?:/|of)\s*(\d{1,6})(?:\)|\])|\b(\d{1,6})\s*/\s*(\d{1,6})\b")

def detect_media(subject: str) -> dict[str, Any] | None:
    matches = list(MEDIA_RE.finditer(subject))
    kind = ""
    if matches:
        m = matches[-1]
        filename = (m.group(1) or m.group(2) or "").strip('"\' ')
        filename = filename.replace("\\", "/").split("/")[-1]
        ext = Path(filename).suffix.lower().lstrip(".")
        kind = "image" if ext in {"jpg", "jpeg", "png", "gif", "webp", "bmp"} else "video"
    else:
        generic = list(BINARY_FILE_RE.finditer(subject))
        if not generic:
            return None
        m = generic[-1]
        filename = (m.group(1) or m.group(2) or "").strip('"\' ')
        filename = filename.replace("\\", "/").split("/")[-1]
        ext = Path(filename).suffix.lower().lstrip(".")
        if "yenc" not in subject.casefold() and ext not in COMMON_BINARY_EXTS and not re.fullmatch(r"r\d{2,3}", ext):
            return None
        kind = "file"
    mime = mimetypes.guess_type(filename)[0] or ("image/jpeg" if kind == "image" else "video/mp4" if kind == "video" else "application/octet-stream")
    return {"filename": filename, "extension": ext, "kind": kind, "mime": mime}

def multipart_info(subject: str) -> dict[str, int] | None:
    candidates: list[tuple[int, int, int]] = []
    for m in PART_PATTERN.finditer(subject):
        try:
            part = int(m.group(1) or m.group(3))
            total = int(m.group(2) or m.group(4))
        except (TypeError, ValueError):
            continue
        if 0 < part <= total <= 100000:
            candidates.append((m.start(), part, total))
    if not candidates:
        return None

    yenc_pos = subject.lower().rfind("yenc")
    after_yenc = [c for c in candidates if yenc_pos >= 0 and c[0] >= yenc_pos]
    if after_yenc:
        _, part, total = after_yenc[-1]
        return {"part": part, "total": total}

    media_matches = list(BINARY_FILE_RE.finditer(subject))
    if media_matches:
        media_end = media_matches[-1].end()
        after_filename = [c for c in candidates if c[0] >= media_end]
        if after_filename:
            _, part, total = after_filename[-1]
            return {"part": part, "total": total}
        return None

    _, part, total = candidates[-1]
    return {"part": part, "total": total}

def normalize_subject(subject: str) -> str:
    s = subject.lower()
    s = PART_PATTERN.sub("", s)
    s = re.sub(r"(?i)\byenc\b", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" -_[]()")

def _multipart_signature(article: dict[str, Any]) -> tuple[str, int] | None:
    mp = article.get("multipart") or {}
    try:
        total = int(mp.get("total", 0) or 0)
    except (TypeError, ValueError):
        return None
    if total <= 1 or "yenc" not in str(article.get("subject") or "").casefold():
        return None
    poster = str(article.get("from") or "").strip().casefold()
    return (poster, total) if poster else None

def _opaque_multipart_signatures(articles: list[dict[str, Any]]) -> set[tuple[str, int]]:
    """Identify multipart streams whose subject filenames cannot be trusted for grouping.

    Modern obfuscators commonly randomize the visible subject token on every yEnc
    segment.  Grouping only when detect_media() sees a filename therefore leaks every
    segment into the UI as an individual POST row.  A repeated poster/part-total stream
    with missing filenames or almost entirely unique filenames is a strong signal that
    the yEnc part counter is the useful identity instead.
    """
    buckets: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for article in articles:
        sig = _multipart_signature(article)
        if sig:
            buckets.setdefault(sig, []).append(article)
    opaque: set[tuple[str, int]] = set()
    for sig, items in buckets.items():
        if len(items) < 2:
            continue
        media_names = [str((x.get("media") or {}).get("filename") or "").strip().casefold() for x in items]
        missing = sum(1 for name in media_names if not name)
        known = [name for name in media_names if name]
        unique_ratio = (len(set(known)) / len(known)) if known else 1.0
        if missing or (len(known) >= 3 and unique_ratio >= 0.70):
            opaque.add(sig)
    return opaque

def _partition_opaque_multipart(items: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    ordered = sorted(items, key=lambda a: int(a.get("article", 0) or 0), reverse=True)
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    seen_parts: set[int] = set()
    previous_article = 0
    previous_ts: float | None = None

    def flush() -> None:
        nonlocal current, seen_parts, previous_article, previous_ts
        if current:
            groups.append(current)
        current = []
        seen_parts = set()
        previous_article = 0
        previous_ts = None

    for article in ordered:
        mp = article.get("multipart") or {}
        try:
            part = int(mp.get("part", 0) or 0)
        except (TypeError, ValueError):
            part = 0
        article_no = int(article.get("article", 0) or 0)
        ts = None
        try:
            dt = email.utils.parsedate_to_datetime(str(article.get("date") or ""))
            ts = dt.timestamp() if dt else None
        except Exception:
            ts = None
        duplicate_part = part > 0 and part in seen_parts
        article_gap = abs(previous_article - article_no) if previous_article and article_no else 0
        time_gap = abs((previous_ts or 0) - (ts or 0)) if previous_ts is not None and ts is not None else 0
        # A repeated part number means a new multipart stream.  Very large article/date
        # gaps are another conservative boundary for same-poster/same-total collisions.
        if current and (duplicate_part or article_gap > 5000 or time_gap > 6 * 60 * 60):
            flush()
        current.append(article)
        if part > 0:
            seen_parts.add(part)
        previous_article = article_no
        previous_ts = ts
    flush()
    return groups


def _opaque_filename_token(filename: str) -> bool:
    name = Path(str(filename or '').replace('\\', '/')).name.strip()
    if not name:
        return True
    stem = Path(name).stem
    compact = re.sub(r'[^A-Za-z0-9]', '', stem)
    if re.fullmatch(r'[A-Fa-f0-9]{14,}', compact or ''):
        return True
    if len(compact) >= 20 and not re.search(r'[._ -]', stem):
        digits = len(re.findall(r'\d', compact))
        vowels = len(re.findall(r'[AEIOUaeiou]', compact))
        if digits >= 4 and vowels / max(1, len(compact)) < 0.16:
            return True
    return False

def _anonymous_opaque_multipart_streams(articles: list[dict[str, Any]], *, exclude_articles: set[int] | None = None) -> list[list[dict[str, Any]]]:
    """Find heavily obfuscated yEnc streams even when the poster changes per segment.

    Some modern posters randomize not only the visible subject token but also the From
    identity for every segment.  In that case poster+total grouping cannot work.  We only
    enable this fallback when a same-total cluster is overwhelmingly opaque, has several
    distinct part numbers, similar segment sizes, and sits in one tight posting window.
    That keeps readable multipart traffic on the normal filename/poster path.
    """
    excluded = exclude_articles or set()
    by_total: dict[int, list[dict[str, Any]]] = {}
    for article in articles:
        article_no = int(article.get('article', 0) or 0)
        if article_no in excluded:
            continue
        mp = article.get('multipart') or {}
        try:
            part = int(mp.get('part', 0) or 0); total = int(mp.get('total', 0) or 0)
        except (TypeError, ValueError):
            continue
        subject = str(article.get('subject') or '')
        if total < 32 or part <= 0 or 'yenc' not in subject.casefold():
            continue
        by_total.setdefault(total, []).append(article)

    streams: list[list[dict[str, Any]]] = []
    for total, items in by_total.items():
        if len(items) < 6:
            continue
        opaque_count = 0
        sizes: list[int] = []
        times: list[float] = []
        parts: set[int] = set()
        for article in items:
            media = article.get('media') or {}
            filename = str(media.get('filename') or '')
            if not filename or _opaque_filename_token(filename):
                opaque_count += 1
            size = int(article.get('bytes', 0) or 0)
            if size > 0:
                sizes.append(size)
            try:
                dt = email.utils.parsedate_to_datetime(str(article.get('date') or ''))
                if dt:
                    times.append(dt.timestamp())
            except Exception:
                pass
            try:
                parts.add(int((article.get('multipart') or {}).get('part', 0) or 0))
            except (TypeError, ValueError):
                pass
        if len(parts) < 6 or opaque_count / max(1, len(items)) < 0.70:
            continue
        if times and max(times) - min(times) > 8 * 60 * 60:
            continue
        if len(sizes) >= 6:
            ordered = sorted(sizes)
            median = ordered[len(ordered)//2]
            near = sum(1 for n in sizes if median and 0.70 <= n / median <= 1.30)
            if near / len(sizes) < 0.75:
                continue
        # Reuse the conservative repeated-part/article-gap partitioner, but without
        # poster identity. Exact same-total collisions are split when part numbers
        # repeat or the posting sequence/time window jumps sharply.
        for stream in _partition_opaque_multipart(items):
            distinct = {int((x.get('multipart') or {}).get('part', 0) or 0) for x in stream}
            if len(stream) >= 6 and len(distinct) >= 6:
                streams.append(stream)
    return streams

def _grouped_article(items: list[dict[str, Any]], *, opaque: bool = False) -> dict[str, Any]:
    items = sorted(items, key=lambda a: int((a.get("multipart") or {}).get("part", 1) or 1))
    first = items[0]
    total = max(int((a.get("multipart") or {}).get("total", 1) or 1) for a in items)
    parts = sorted({int((a.get("multipart") or {}).get("part", 1) or 1) for a in items})
    resolved = next((a for a in items if a.get("media")), None)
    newest = max(items, key=lambda a: int(a.get("article", 0) or 0))
    base = dict(resolved or first)
    # Preserve the newest header identity as the browser anchor while using a resolved
    # member's media/name metadata when one segment has already been probed.
    base["article"] = int(newest.get("article", 0) or 0)
    base["message_id"] = str(newest.get("message_id") or base.get("message_id") or "")
    base["date"] = newest.get("date") or base.get("date") or ""
    base["from"] = newest.get("from") or base.get("from") or ""
    base["segments"] = [{
        "article": int(a.get("article", 0) or 0),
        "message_id": a.get("message_id", ""),
        "part": int((a.get("multipart") or {}).get("part", 1) or 1),
        "bytes": int(a.get("bytes", 0) or 0),
    } for a in items]
    base["segment_count"] = len(parts)
    base["segment_total"] = total
    base["complete"] = len(parts) == total and parts == list(range(1, total + 1))
    base["bytes"] = sum(int(a.get("bytes", 0) or 0) for a in items)
    if opaque:
        base["opaque_multipart"] = True
        base["opaque_grouping"] = "poster + yEnc part counter"
        if not base.get("media"):
            base["subject"] = f"Obfuscated multipart binary — {len(parts):,}/{total:,} segments"
    return base

def group_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    opaque_signatures = _opaque_multipart_signatures(articles)
    opaque_buckets: dict[tuple[str, int], list[dict[str, Any]]] = {}
    named_buckets: dict[str, list[dict[str, Any]]] = {}
    singles: list[dict[str, Any]] = []
    consumed: set[int] = set()

    for article in articles:
        mp = article.get("multipart")
        media = article.get("media")
        sig = _multipart_signature(article)
        if mp and sig in opaque_signatures:
            opaque_buckets.setdefault(sig, []).append(article)
        elif mp and media:
            named_buckets.setdefault(normalize_subject(article["subject"]), []).append(article)
        else:
            singles.append(article)

    output: list[dict[str, Any]] = []
    for items in named_buckets.values():
        output.append(_grouped_article(items, opaque=False))
        consumed.update(int(x.get("article", 0) or 0) for x in items)
    for items in opaque_buckets.values():
        for stream in _partition_opaque_multipart(items):
            grouped = _grouped_article(stream, opaque=True)
            output.append(grouped)
            consumed.update(int(x.get("article", 0) or 0) for x in stream)

    # Second opaque path: some uploaders randomize From on every yEnc segment.
    # Collapse those same-total posting streams before they can leak into the UI as
    # hundreds of misleading, individually-complete POST rows.
    anonymous_streams = _anonymous_opaque_multipart_streams(articles, exclude_articles=consumed)
    for stream in anonymous_streams:
        grouped = _grouped_article(stream, opaque=True)
        grouped["anonymous_opaque_multipart"] = True
        grouped["opaque_grouping"] = "yEnc counter + posting sequence"
        output.append(grouped)
        consumed.update(int(x.get("article", 0) or 0) for x in stream)

    for article in singles:
        article_no = int(article.get("article", 0) or 0)
        if article_no in consumed:
            continue
        # A lone multipart yEnc header is not a complete downloadable binary merely
        # because only one header was loaded. Preserve the true part/total state so
        # Packages view can hide it until reconstruction succeeds.
        mp = article.get("multipart") or {}
        try:
            mp_total = int(mp.get("total", 0) or 0)
            mp_part = int(mp.get("part", 0) or 0)
        except (TypeError, ValueError):
            mp_total = mp_part = 0
        is_fragment = mp_total > 1 and "yenc" in str(article.get("subject") or "").casefold()
        output.append({**article, "segments": [{
            "article": article["article"],
            "message_id": article.get("message_id", ""),
            "part": mp_part if is_fragment and mp_part > 0 else 1,
            "bytes": int(article.get("bytes", 0) or 0),
        }], "segment_count": 1, "segment_total": mp_total if is_fragment else 1, "complete": not is_fragment, "multipart_fragment": bool(is_fragment)})
    output.sort(key=lambda a: int(a.get("article", 0) or 0), reverse=True)
    return output

def _smart_binary_expansion_headers(raw_articles: list[dict[str, Any]], cap: int = 12000) -> int:
    """Estimate how many older headers are needed to finish an opaque yEnc stream.

    This is header-only work: no BODY data is downloaded.  It is intentionally used only
    by All Posts/Packages browsing so visual media browsing keeps its normal lightweight
    page fetch.
    """
    opaque = _opaque_multipart_signatures(raw_articles)
    buckets: list[tuple[int, list[dict[str, Any]]]] = []
    poster_consumed: set[int] = set()
    poster_buckets: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for article in raw_articles:
        sig = _multipart_signature(article)
        if sig in opaque:
            poster_buckets.setdefault(sig, []).append(article)
    for (_, total), items in poster_buckets.items():
        for stream in _partition_opaque_multipart(items):
            buckets.append((total, stream))
            poster_consumed.update(int(x.get("article", 0) or 0) for x in stream)
    for stream in _anonymous_opaque_multipart_streams(raw_articles, exclude_articles=poster_consumed):
        total = max(int((x.get("multipart") or {}).get("total", 0) or 0) for x in stream)
        buckets.append((total, stream))
    if not buckets:
        return 0
    need = 0
    for total, items in buckets:
        parts = sorted({int((a.get("multipart") or {}).get("part", 0) or 0) for a in items if int((a.get("multipart") or {}).get("part", 0) or 0) > 0})
        if len(parts) < 2:
            continue
        by_article = sorted(items, key=lambda a: int(a.get("article", 0) or 0))
        low_part = int((by_article[0].get("multipart") or {}).get("part", 0) or 0)
        high_part = int((by_article[-1].get("multipart") or {}).get("part", 0) or 0)
        ascending = high_part >= low_part
        missing_older = (parts[0] - 1) if ascending else (total - parts[-1])
        # When randomized From values make posting order noisy, the conservative
        # fallback is the larger missing side, bounded by the same 12k-header cap.
        if any(x.get("from") != items[0].get("from") for x in items[1:]):
            missing_older = max(parts[0] - 1, total - parts[-1])
        if missing_older > 0:
            estimate = int(missing_older * 1.25) + 64
            need = max(need, min(cap, estimate))
    return max(0, min(cap, need))

def _control_view(line: bytes) -> bytes:
    """Return a tolerant view for encoder control lines without altering payload data."""
    return line.lstrip(b" \t")

def parse_yenc(lines: list[bytes]) -> tuple[bytes, dict[str, Any]]:
    begin_index = None
    meta: dict[str, Any] = {"encoding": "yenc"}
    for i, line in enumerate(lines):
        control = _control_view(line)
        if control.lower().startswith(b"=ybegin"):
            begin_index = i
            text = control.decode("latin-1", errors="replace")
            name_match = re.search(r"\bname=(.*)$", text, flags=re.I)
            if name_match:
                meta["name"] = name_match.group(1).strip()
            for key in ("size", "part", "total", "line"):
                m = re.search(rf"\b{key}=(\d+)", text, flags=re.I)
                if m:
                    meta[key] = int(m.group(1))
            break
    if begin_index is None:
        raise NntpError("No yEnc payload")

    data_lines: list[bytes] = []
    saw_end = False
    for line in lines[begin_index + 1:]:
        control = _control_view(line)
        low = control.lower()
        if low.startswith(b"=ypart"):
            text = control.decode("latin-1", errors="replace")
            for key in ("begin", "end"):
                m = re.search(rf"\b{key}=(\d+)", text, flags=re.I)
                if m:
                    meta[key] = int(m.group(1))
            continue
        if low.startswith(b"=yend"):
            text = control.decode("latin-1", errors="replace")
            for key in ("size", "part"):
                m = re.search(rf"\b{key}=(\d+)", text, flags=re.I)
                if m:
                    meta["end_" + key] = int(m.group(1))
            for key in ("pcrc32", "crc32"):
                m = re.search(rf"\b{key}=([0-9a-fA-F]{{8}})", text, flags=re.I)
                if m:
                    meta[key] = m.group(1).lower()
            saw_end = True
            break
        data_lines.append(line)

    if not data_lines:
        raise NntpError("yEnc payload contained no data")

    decoded = bytearray()
    for line in data_lines:
        i = 0
        while i < len(line):
            b = line[i]
            if b == 61:
                i += 1
                if i >= len(line):
                    raise NntpError("Truncated yEnc escape sequence")
                b = (line[i] - 64) & 0xFF
            decoded.append((b - 42) & 0xFF)
            i += 1
    if not decoded:
        raise NntpError("yEnc payload decoded to zero bytes")
    meta["saw_end"] = saw_end
    return bytes(decoded), meta

def parse_uuencode(lines: list[bytes]) -> tuple[bytes, dict[str, Any]]:
    """Decode classic uuencode and begin-base64 Usenet attachments."""
    for i, line in enumerate(lines):
        control = _control_view(line)
        m = re.match(br"(?i)^begin(?:-base64)?\s+[0-7]{3,4}\s+(.+?)\s*$", control)
        if not m:
            continue
        name = m.group(1).decode("latin-1", errors="replace").strip()
        is_b64 = control.lower().startswith(b"begin-base64")
        if is_b64:
            encoded: list[bytes] = []
            for raw in lines[i + 1:]:
                c = _control_view(raw)
                if c == b"====" or c.lower() == b"end":
                    break
                if c:
                    encoded.append(c.strip())
            try:
                data = base64.b64decode(b"".join(encoded), validate=False)
            except Exception as exc:
                raise NntpError(f"Invalid uuencode base64 payload: {exc}")
        else:
            out = bytearray()
            for raw in lines[i + 1:]:
                c = _control_view(raw)
                if c.lower() == b"end":
                    break
                if not c or c in (b"`", b" "):
                    continue
                try:
                    out.extend(binascii.a2b_uu(c))
                except binascii.Error:
                    continue
            data = bytes(out)
        if data:
            return data, {"encoding": "uuencode", "name": name}
    raise NntpError("No uuencoded payload")

def parse_mime_base64(lines: list[bytes]) -> tuple[bytes, dict[str, Any]]:
    """Decode a MIME body part that uses Content-Transfer-Encoding: base64."""
    for i, line in enumerate(lines):
        low = _control_view(line).lower()
        if not low.startswith(b"content-transfer-encoding:") or b"base64" not in low:
            continue

        j = i + 1
        name = ""
        while j < len(lines) and lines[j].strip():
            text = lines[j].decode("latin-1", errors="replace")
            nm = re.search(r"(?i)(?:filename|name)\s*=\s*(?:\"([^\"]+)\"|([^;\s]+))", text)
            if nm:
                name = (nm.group(1) or nm.group(2) or "").strip()
            j += 1
        if j >= len(lines):
            continue
        j += 1
        encoded: list[bytes] = []
        while j < len(lines):
            raw = lines[j]
            stripped = raw.strip()
            if stripped.startswith(b"--"):
                break
            if stripped.lower().startswith(b"content-") and encoded:
                break
            if stripped:
                encoded.append(stripped)
            j += 1
        if not encoded:
            continue
        try:
            data = base64.b64decode(b"".join(encoded), validate=False)
        except Exception:
            continue
        if data:
            return data, {"encoding": "mime-base64", "name": name}
    raise NntpError("No MIME base64 payload")

def decode_binary_payload(lines: list[bytes]) -> tuple[bytes, dict[str, Any]]:
    errors: list[str] = []
    for decoder in (parse_yenc, parse_uuencode, parse_mime_base64):
        try:
            return decoder(lines)
        except NntpError as exc:
            errors.append(str(exc))
    raise NntpError("No supported binary attachment was found (tried yEnc, uuencode, and MIME/base64)")

def retrieve_segment_body(client: NntpClient, segment: dict[str, Any]) -> list[bytes]:
    """Retrieve by article number first, then Message-ID when available."""
    article = segment.get("article")
    first_error: Exception | None = None
    if article is not None and str(article).strip():
        try:
            return client.body(int(article))
        except Exception as exc:
            first_error = exc
    message_id = str(segment.get("message_id", "") or "").strip()
    if message_id:
        try:
            return client.body(message_id)
        except Exception as exc:
            if first_error:
                raise NntpError(f"Article body unavailable by number or Message-ID: {first_error}; {exc}")
            raise
    if first_error:
        raise first_error
    raise NntpError("Article segment has no retrievable article number or Message-ID")

def write_payload_chunk(f, chunk: bytes, meta: dict[str, Any]) -> int:
    """Write one decoded part, honoring yEnc =ypart byte offsets when supplied."""
    begin = int(meta.get("begin", 0) or 0)
    if begin > 0:
        f.seek(begin - 1)
    f.write(chunk)
    return len(chunk)

def retrieve_segment_body_iter(client: NntpClient, segment: dict[str, Any]):
    """Stream a segment by article number first, then Message-ID when the number is unavailable."""
    article = segment.get("article")
    message_id = str(segment.get("message_id", "") or "").strip()
    first_error: Exception | None = None
    if article is not None and str(article).strip():
        yielded = False
        try:
            for line in client.body_iter(int(article)):
                yielded = True
                yield line
            return
        except Exception as exc:
            if yielded:
                raise
            first_error = exc
    if message_id:
        try:
            yield from client.body_iter(message_id)
            return
        except Exception as exc:
            if first_error:
                raise NntpError(f"Article body unavailable by number or Message-ID: {first_error}; {exc}")
            raise
    if first_error:
        raise first_error
    raise NntpError("Article segment has no retrievable article number or Message-ID")

def _parse_yenc_begin(control: bytes, meta: dict[str, Any]) -> None:
    text = control.decode("latin-1", errors="replace")
    name_match = re.search(r"\bname=(.*)$", text, flags=re.I)
    if name_match:
        meta["name"] = name_match.group(1).strip()
    for key in ("size", "part", "total", "line"):
        m = re.search(rf"\b{key}=(\d+)", text, flags=re.I)
        if m:
            meta[key] = int(m.group(1))

def _parse_yenc_part(control: bytes, meta: dict[str, Any]) -> None:
    text = control.decode("latin-1", errors="replace")
    for key in ("begin", "end"):
        m = re.search(rf"\b{key}=(\d+)", text, flags=re.I)
        if m:
            meta[key] = int(m.group(1))

def _parse_yenc_end(control: bytes, meta: dict[str, Any]) -> None:
    text = control.decode("latin-1", errors="replace")
    for key in ("size", "part"):
        m = re.search(rf"\b{key}=(\d+)", text, flags=re.I)
        if m:
            meta["end_" + key] = int(m.group(1))
    for key in ("pcrc32", "crc32"):
        m = re.search(rf"\b{key}=([0-9a-fA-F]{{8}})", text, flags=re.I)
        if m:
            meta[key] = m.group(1).lower()

# --- Newsgroup name resolution -------------------------------------------------
# Obfuscated Usenet subjects frequently hide a perfectly useful filename inside
# the yEnc control header.  Keep name discovery separate from normal header
# loading so browsing remains instant, then persist successful discoveries and
# apply them on subsequent /api/articles calls before multipart grouping.
_NAME_RESOLUTION_CACHE_LOCK = threading.RLock()
_NAME_RESOLUTION_CACHE: dict[str, dict[str, Any]] | None = None
NAME_RESOLUTION_EXECUTOR = ThreadPoolExecutor(max_workers=NAME_RESOLUTION_WORKER_COUNT, thread_name_prefix="usenet-name")

def _resolution_filename_media(filename: str) -> dict[str, Any] | None:
    name = str(filename or "").replace("\\", "/").split("/")[-1].strip().strip('"\'')
    name = "".join(ch for ch in name if ord(ch) >= 32 and ch not in "\x7f")[:512]
    if not name or "." not in name:
        return None
    ext = Path(name).suffix.lower().lstrip(".")
    if not ext:
        return None
    if ext in {"jpg", "jpeg", "png", "gif", "webp", "bmp"}:
        kind = "image"
    elif ext in {"mp4", "m4v", "webm", "mov", "avi", "mkv"}:
        kind = "video"
    else:
        kind = "file"
    mime = mimetypes.guess_type(name)[0] or ("image/jpeg" if kind == "image" else "video/mp4" if kind == "video" else "application/octet-stream")
    return {"filename": name, "extension": ext, "kind": kind, "mime": mime}

def _name_resolution_cache_key(provider_id: str, group: str, article: dict[str, Any]) -> str:
    identity = str(article.get("message_id") or "").strip() or f"article:{int(article.get('article', 0) or 0)}"
    raw = f"{provider_id}\n{group}\n{identity}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()

def _load_name_resolution_cache() -> dict[str, dict[str, Any]]:
    global _NAME_RESOLUTION_CACHE
    with _NAME_RESOLUTION_CACHE_LOCK:
        if _NAME_RESOLUTION_CACHE is None:
            raw = json_read(NAME_RESOLUTION_CACHE_FILE, {"entries": {}})
            source = raw.get("entries") if isinstance(raw, dict) else {}
            _NAME_RESOLUTION_CACHE = {str(k): dict(v) for k, v in (source or {}).items() if isinstance(v, dict)}
        return _NAME_RESOLUTION_CACHE

def _save_name_resolution_cache_locked() -> None:
    cache = _load_name_resolution_cache()
    cutoff = time.time() - 180 * 24 * 60 * 60
    compact = [(k, v) for k, v in cache.items() if float(v.get("ts", 0) or 0) >= cutoff]
    compact.sort(key=lambda kv: float(kv[1].get("ts", 0) or 0), reverse=True)
    entries = dict(compact[:12000])
    cache.clear(); cache.update(entries)
    json_write(NAME_RESOLUTION_CACHE_FILE, {"version": 1, "entries": entries})

def _name_resolution_lookup(provider_id: str, group: str, article: dict[str, Any]) -> dict[str, Any] | None:
    cache = _load_name_resolution_cache()
    key = _name_resolution_cache_key(provider_id, group, article)
    with _NAME_RESOLUTION_CACHE_LOCK:
        entry = cache.get(key)
        if not entry:
            return None
        # Article-number fallback keys are less durable than Message-IDs.  Guard
        # them with the original subject so a retention-window rollover cannot
        # accidentally apply an old filename to a different article number.
        if not str(article.get("message_id") or "").strip():
            old_subject = str(entry.get("subject") or "")
            if old_subject and old_subject != str(article.get("subject") or ""):
                return None
        return dict(entry)

def _store_name_resolution_entries(entries: list[tuple[str, dict[str, Any]]]) -> None:
    if not entries:
        return
    cache = _load_name_resolution_cache()
    with _NAME_RESOLUTION_CACHE_LOCK:
        for key, entry in entries:
            cache[key] = dict(entry)
        _save_name_resolution_cache_locked()

def _apply_cached_name_resolutions(provider_id: str, group: str, articles: list[dict[str, Any]]) -> int:
    applied = 0
    for article in articles:
        entry = _name_resolution_lookup(provider_id, group, article)
        filename = str((entry or {}).get("filename") or "").strip()
        media = _resolution_filename_media(filename)
        if not media:
            continue
        original = str((article.get("media") or {}).get("filename") or "")
        article["media"] = media
        article["name_resolution"] = {
            "source": str(entry.get("source") or "yEnc header"),
            "confidence": str(entry.get("confidence") or "high"),
            "original_filename": original,
            "title_hint": str(entry.get("title_hint") or ""),
            "metadata_source": str(entry.get("metadata_source") or ""),
            "metadata_names": list(entry.get("metadata_names") or [])[:100],
            "archive_source": str(entry.get("archive_source") or ""),
            "archive_names": list(entry.get("archive_names") or [])[:100],
            "title_source": str(entry.get("title_source") or ""),
            "archive_checked": bool(float(entry.get("archive_checked_ts", 0) or 0) >= time.time() - 14 * 24 * 60 * 60 or not _archive_probe_candidate(filename)),
        }
        applied += 1
    return applied

def _parse_par2_filenames(data: bytes) -> list[str]:
    names: list[str] = []
    pos = 0
    magic = b"PAR2\x00PKT"
    while True:
        idx = data.find(magic, pos)
        if idx < 0 or idx + 64 > len(data):
            break
        try:
            packet_len = int(struct.unpack_from("<Q", data, idx + 8)[0])
        except (struct.error, ValueError):
            break
        if packet_len < 64 or packet_len > 64 * 1024 * 1024 or idx + packet_len > len(data):
            pos = idx + 8
            continue
        packet_type = data[idx + 48:idx + 64]
        if packet_type == b"PAR 2.0\x00FileDesc" and packet_len >= 120:
            raw_name = data[idx + 120:idx + packet_len].rstrip(b"\x00")
            for encoding in ("utf-8", "cp1252", "latin-1"):
                try:
                    name = raw_name.decode(encoding).strip().replace("\\", "/").split("/")[-1]
                    break
                except UnicodeDecodeError:
                    name = ""
            if name and name not in names:
                names.append(name[:512])
        pos = idx + packet_len
    return names[:250]

def _parse_sfv_filenames(data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="replace")
    names: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith((";", "#")):
            continue
        m = re.match(r"^(.*?)\s+[0-9A-Fa-f]{8}$", line)
        if not m:
            continue
        name = m.group(1).strip().strip('"').replace("\\", "/").split("/")[-1]
        if name and name not in names:
            names.append(name[:512])
    return names[:250]

def _decode_archive_name(raw: bytes) -> str:
    raw = bytes(raw or b"").split(b"\x00", 1)[0]
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding).strip()
            break
        except UnicodeDecodeError:
            text = ""
    text = text.replace("\\", "/").split("/")[-1]
    text = "".join(ch for ch in text if ord(ch) >= 32 and ch not in "\x7f")
    return text[:512]

def _read_rar_vint(data: bytes, pos: int, limit: int) -> tuple[int, int] | None:
    value = 0
    shift = 0
    for _ in range(10):
        if pos >= limit:
            return None
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return value, pos
        shift += 7
    return None

def _parse_rar4_prefix_filenames(data: bytes) -> list[str]:
    signature = b"Rar!\x1a\x07\x00"
    start = data.find(signature)
    if start < 0:
        return []
    pos = start + len(signature)
    names: list[str] = []
    while pos + 7 <= len(data) and len(names) < 24:
        try:
            head_type = data[pos + 2]
            flags = struct.unpack_from("<H", data, pos + 3)[0]
            head_size = struct.unpack_from("<H", data, pos + 5)[0]
        except struct.error:
            break
        if head_size < 7 or pos + head_size > len(data):
            break
        add_size = 0
        if flags & 0x8000 and pos + 11 <= len(data):
            try:
                add_size = int(struct.unpack_from("<I", data, pos + 7)[0])
            except struct.error:
                add_size = 0
        if head_type == 0x74 and pos + 32 <= len(data):
            try:
                name_size = int(struct.unpack_from("<H", data, pos + 26)[0])
            except struct.error:
                name_size = 0
            name_pos = pos + 32 + (8 if flags & 0x0100 else 0)
            name_end = min(pos + head_size, name_pos + max(0, name_size))
            if name_size and name_pos < name_end <= len(data):
                name = _decode_archive_name(data[name_pos:name_end])
                if name and name not in names:
                    names.append(name)
            # The first file header is enough to identify almost every release;
            # its payload usually starts immediately afterwards and is huge.
            if names:
                break
        step = head_size + max(0, add_size)
        if step <= 0:
            break
        pos += step
    return names

def _parse_rar5_prefix_filenames(data: bytes) -> list[str]:
    signature = b"Rar!\x1a\x07\x01\x00"
    start = data.find(signature)
    if start < 0:
        return []
    pos = start + len(signature)
    names: list[str] = []
    while pos + 6 <= len(data) and len(names) < 24:
        block_start = pos
        pos += 4  # header CRC32
        hv = _read_rar_vint(data, pos, len(data))
        if not hv:
            break
        header_size, pos = hv
        header_start = pos
        header_end = header_start + int(header_size)
        if header_size <= 0 or header_end > len(data):
            break
        tv = _read_rar_vint(data, pos, header_end)
        if not tv:
            break
        header_type, pos = tv
        fv = _read_rar_vint(data, pos, header_end)
        if not fv:
            break
        header_flags, pos = fv
        extra_size = 0
        data_size = 0
        if header_flags & 0x0001:
            ev = _read_rar_vint(data, pos, header_end)
            if not ev:
                break
            extra_size, pos = ev
        if header_flags & 0x0002:
            dv = _read_rar_vint(data, pos, header_end)
            if not dv:
                break
            data_size, pos = dv
        if header_type == 2:  # file header
            for _ in range(3):
                vv = _read_rar_vint(data, pos, header_end)
                if not vv:
                    return names
                value, pos = vv
                if _ == 0:
                    file_flags = value
            if file_flags & 0x0002:
                pos += 4
            if file_flags & 0x0004:
                pos += 4
            cv = _read_rar_vint(data, pos, header_end)
            if not cv:
                return names
            _, pos = cv
            ov = _read_rar_vint(data, pos, header_end)
            if not ov:
                return names
            _, pos = ov
            nv = _read_rar_vint(data, pos, header_end)
            if not nv:
                return names
            name_size, pos = nv
            if 0 < name_size <= 4096 and pos + name_size <= header_end:
                name = _decode_archive_name(data[pos:pos + name_size])
                if name and name not in names:
                    names.append(name)
            if names:
                break
        next_pos = header_end + max(0, int(data_size))
        if next_pos <= block_start or next_pos > len(data):
            break
        pos = next_pos
    return names

def _parse_zip_prefix_filenames(data: bytes) -> list[str]:
    names: list[str] = []
    pos = 0
    signature = b"PK\x03\x04"
    while len(names) < 24:
        idx = data.find(signature, pos)
        if idx < 0 or idx + 30 > len(data):
            break
        try:
            flags = int(struct.unpack_from("<H", data, idx + 6)[0])
            name_size = int(struct.unpack_from("<H", data, idx + 26)[0])
            extra_size = int(struct.unpack_from("<H", data, idx + 28)[0])
        except struct.error:
            break
        name_pos = idx + 30
        name_end = name_pos + name_size
        if name_size and name_end <= len(data):
            raw = data[name_pos:name_end]
            encoding = "utf-8" if flags & 0x0800 else "cp437"
            try:
                name = raw.decode(encoding, errors="replace").replace("\\", "/").split("/")[-1].strip()
            except Exception:
                name = _decode_archive_name(raw)
            if name and name not in names:
                names.append(name[:512])
        # Local data usually follows, so scanning for another signature is a
        # best-effort convenience rather than a requirement for title recovery.
        pos = max(name_end + extra_size, idx + 4)
    return names

def _parse_7z_prefix_filenames(data: bytes) -> list[str]:
    if b"7z\xbc\xaf'\x1c" not in data[:64]:
        return []
    # 7-Zip headers may be encoded/compressed.  When they are plain, filenames
    # often remain visible as UTF-16LE strings. Keep this heuristic deliberately
    # strict so random binary bytes are never presented as a recovered title.
    names: list[str] = []
    known = r"(?:mkv|mp4|avi|mov|m4v|mp3|flac|iso|exe|pdf|epub|nfo|sfv|rar|7z|zip)"
    pattern = re.compile(rb"((?:[ -~]\x00){4,180}\." + known.encode("ascii") + rb"\x00)", re.I)
    for match in pattern.finditer(data[:NAME_RESOLUTION_ARCHIVE_PROBE_BYTES]):
        try:
            name = match.group(1).decode("utf-16le", errors="ignore").replace("\\", "/").split("/")[-1].strip(" \x00")
        except Exception:
            continue
        if 4 <= len(name) <= 512 and name not in names:
            names.append(name)
        if len(names) >= 24:
            break
    return names

def _parse_archive_prefix_filenames(data: bytes) -> tuple[list[str], str]:
    if not data:
        return [], ""
    if b"Rar!\x1a\x07\x01\x00" in data[:64]:
        return _parse_rar5_prefix_filenames(data), "RAR5 header"
    if b"Rar!\x1a\x07\x00" in data[:64]:
        return _parse_rar4_prefix_filenames(data), "RAR header"
    if data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return _parse_zip_prefix_filenames(data), "ZIP header"
    if data.startswith(b"7z\xbc\xaf'\x1c"):
        return _parse_7z_prefix_filenames(data), "7-Zip header"
    return [], ""

def _filename_looks_obfuscated(filename: str) -> bool:
    name = str(filename or "").replace("\\", "/").split("/")[-1].strip()
    stem = Path(name).stem
    compact = re.sub(r"[^A-Za-z0-9]", "", stem)
    if not compact:
        return True
    if re.fullmatch(r"[a-fA-F0-9]{14,}", compact):
        return True
    if re.fullmatch(r"[a-fA-F0-9]{8}-[a-fA-F0-9-]{18,}", stem):
        return True
    separators = len(re.findall(r"[._ -]", stem))
    if separators == 0 and len(compact) >= 28 and len(re.findall(r"\d", compact)) >= 5:
        return True
    if len(compact) >= 20:
        digits = len(re.findall(r"\d", compact))
        vowels = len(re.findall(r"[aeiou]", compact, re.I))
        if separators <= 1 and digits >= 4 and vowels / max(1, len(compact)) < 0.16:
            return True
    return False

def _archive_probe_candidate(filename: str) -> bool:
    lower = str(filename or "").casefold()
    if not _filename_looks_obfuscated(filename):
        return False
    m = re.search(r"\.part0*(\d+)\.rar$", lower)
    if m:
        return int(m.group(1)) == 1
    m = re.search(r"\.r(\d{2,3})$", lower)
    if m:
        return False
    m = re.search(r"\.z(\d{2,3})$", lower)
    if m:
        return int(m.group(1)) == 1
    m = re.search(r"\.7z\.(\d{3,5})$", lower)
    if m:
        return int(m.group(1)) == 1
    m = re.search(r"\.(\d{3,5})$", lower)
    if m:
        return int(m.group(1)) == 1
    return lower.endswith((".rar", ".zip", ".7z"))

def _probe_archive_metadata(provider: dict[str, Any], group: str, target: int | str, filename: str) -> tuple[list[str], str]:
    if not _archive_probe_candidate(filename):
        return [], ""
    password = unprotect_secret(provider.get("password_protected", ""))
    client = NntpClient(
        provider["host"], provider["port"], bool(provider.get("ssl", True)),
        provider.get("username", ""), password, timeout=NAME_RESOLUTION_SOCKET_TIMEOUT, probe_capabilities=False,
    )
    try:
        client.connect(); client.group(group)
        prefix, _ = client.body_yenc_decoded_prefix(target)
        names, source = _parse_archive_prefix_filenames(prefix)
        return names[:100], source if names else ""
    except Exception:
        return [], ""
    finally:
        client.abort()
        try:
            client.close()
        except Exception:
            pass

def _metadata_title_hint(names: list[str]) -> str:
    candidates: list[str] = []
    for name in names:
        base = str(name or "").replace("\\", "/").split("/")[-1].strip()
        base = re.sub(r"(?i)\.vol\d+[+_]\d+\.par2$", "", base)
        base = re.sub(r"(?i)[._ -]part0*\d{1,5}\.rar$", "", base)
        base = re.sub(r"(?i)\.r\d{2,3}$", "", base)
        base = re.sub(r"(?i)\.(?:rar|par2|sfv|nfo|srr|7z|zip|mkv|mp4|m4v|avi|mov|webm|mp3|flac|wav|iso|img|exe|msi|pdf|epub)$", "", base)
        base = re.sub(r"(?i)\.7z\.\d{3,5}$", "", base)
        base = re.sub(r"\.\d{3,5}$", "", base)
        base = base.strip(" ._-[]()")
        if len(base) >= 4:
            candidates.append(base)
    if not candidates:
        return ""
    counts: dict[str, tuple[int, str]] = {}
    for candidate in candidates:
        norm = re.sub(r"[._ -]+", " ", candidate).casefold().strip()
        count, _ = counts.get(norm, (0, candidate))
        counts[norm] = (count + 1, candidate)
    return max(counts.values(), key=lambda item: (item[0], len(item[1])))[1][:512]

def _probe_yenc_name(provider: dict[str, Any], group: str, target: int | str) -> tuple[str, dict[str, Any]]:
    password = unprotect_secret(provider.get("password_protected", ""))
    client = NntpClient(
        provider["host"], provider["port"], bool(provider.get("ssl", True)),
        provider.get("username", ""), password, timeout=NAME_RESOLUTION_SOCKET_TIMEOUT, probe_capabilities=False,
    )
    try:
        client.connect(); client.group(group)
        lines = client.body_control_prefix(target)
        meta: dict[str, Any] = {"encoding": "yenc"}
        for line in lines:
            control = _control_view(line)
            if control.lower().startswith(b"=ybegin"):
                _parse_yenc_begin(control, meta)
                media = _resolution_filename_media(str(meta.get("name") or ""))
                return (str(media.get("filename")) if media else ""), meta
        return "", meta
    finally:
        # body_control_prefix intentionally leaves BODY unread; abort instead of
        # trying to reuse or gracefully QUIT an out-of-frame connection.
        client.abort()
        try:
            client.close()
        except Exception:
            pass

def _probe_small_metadata(provider: dict[str, Any], group: str, item: dict[str, Any], filename: str) -> tuple[list[str], str]:
    ext = Path(filename).suffix.casefold()
    lower = filename.casefold()
    if ext not in {".par2", ".sfv"} or re.search(r"(?i)\.vol\d+[+_]\d+\.par2$", lower):
        return [], ""
    segments = [dict(x) for x in (item.get("segments") or []) if isinstance(x, dict)]
    if not segments:
        article = item.get("article")
        message_id = str(item.get("message_id") or "").strip()
        if article is not None or message_id:
            segments = [{"article": article, "message_id": message_id, "part": 1, "bytes": int(item.get("bytes", 0) or 0)}]
    expected = sum(max(0, int(seg.get("bytes", 0) or 0)) for seg in segments)
    if not segments or len(segments) > 32 or expected <= 0 or expected > int(NAME_RESOLUTION_METADATA_MAX_BYTES * 1.45):
        return [], ""
    token = hashlib.sha256((str(provider.get("id") or provider.get("host")) + "|" + group + "|" + str(item.get("message_id") or item.get("article")) + "|metadata").encode("utf-8", errors="replace")).hexdigest()[:24]
    temp = CACHE_DIR / f".name-meta-{token}{ext}"
    temp.unlink(missing_ok=True)
    try:
        written, _ = _assemble_segments(provider, group, segments, temp, max_bytes=NAME_RESOLUTION_METADATA_MAX_BYTES + 1)
        if written <= 0 or written > NAME_RESOLUTION_METADATA_MAX_BYTES:
            return [], ""
        data = temp.read_bytes()
        if ext == ".par2":
            return _parse_par2_filenames(data), "PAR2 metadata"
        return _parse_sfv_filenames(data), "SFV metadata"
    except Exception:
        return [], ""
    finally:
        temp.unlink(missing_ok=True)

def _resolve_article_name_worker(provider: dict[str, Any], provider_id: str, group: str, item: dict[str, Any]) -> dict[str, Any]:
    client_key = str(item.get("client_key") or "")
    returned_fields = ("source", "confidence", "title_hint", "metadata_source", "metadata_names", "archive_source", "archive_names", "title_source", "archive_checked")
    segments = [x for x in (item.get("segments") or []) if isinstance(x, dict)]
    first = segments[0] if segments else item
    target: int | str | None = first.get("article")
    if target is None or not str(target).strip():
        target = str(first.get("message_id") or item.get("message_id") or "").strip() or None
    if target is None:
        return {"client_key": client_key, "resolved": False, "error": "No retrievable article reference"}
    target_value = int(target) if isinstance(target, (int, float)) or str(target).isdigit() else str(target)

    cached = _name_resolution_lookup(provider_id, group, item)
    if cached and str(cached.get("filename") or ""):
        filename = str(cached.get("filename"))
        media = _resolution_filename_media(filename)
        archive_recent = float(cached.get("archive_checked_ts", 0) or 0) >= time.time() - 14 * 24 * 60 * 60
        needs_archive_upgrade = bool(media and not str(cached.get("title_hint") or "") and _archive_probe_candidate(filename) and not archive_recent)
        if needs_archive_upgrade:
            archive_names, archive_source = _probe_archive_metadata(provider, group, target_value, filename)
            upgraded = dict(cached)
            upgraded["archive_checked_ts"] = time.time()
            upgraded["archive_names"] = archive_names
            upgraded["archive_source"] = archive_source
            archive_hint = _metadata_title_hint(archive_names)
            if archive_hint:
                upgraded["title_hint"] = archive_hint
                upgraded["title_source"] = archive_source
            upgraded["ts"] = time.time()
            key = _name_resolution_cache_key(provider_id, group, item)
            upgraded_result = {**{k: upgraded.get(k) for k in returned_fields}, "archive_checked": True}
            return {"client_key": client_key, "resolved": True, "cached": False, "filename": filename, "media": media, "_cache_key": key, "_cache_entry": upgraded, **upgraded_result}
        cached_result = {**{k: cached.get(k) for k in returned_fields}, "archive_checked": bool(archive_recent or not _archive_probe_candidate(filename))}
        return {"client_key": client_key, "resolved": True, "cached": True, "filename": filename, "media": media, **cached_result}

    try:
        filename, ymeta = _probe_yenc_name(provider, group, target_value)
    except Exception as exc:
        return {"client_key": client_key, "resolved": False, "error": classify_nntp_failure(exc).get("label") or str(exc)}
    media = _resolution_filename_media(filename)
    if not media:
        return {"client_key": client_key, "resolved": False, "error": "No filename was exposed by the yEnc header"}
    metadata_names, metadata_source = _probe_small_metadata(provider, group, item, filename)
    metadata_hint = _metadata_title_hint(metadata_names)
    title_hint = metadata_hint
    archive_names: list[str] = []
    archive_source = ""
    archive_checked_ts = 0.0
    if not title_hint and _archive_probe_candidate(filename):
        archive_names, archive_source = _probe_archive_metadata(provider, group, target_value, filename)
        archive_checked_ts = time.time()
        title_hint = _metadata_title_hint(archive_names)
    title_source = metadata_source if metadata_hint else archive_source if title_hint else "yEnc header"
    entry = {
        "filename": media["filename"], "source": "yEnc header", "confidence": "high",
        "subject": str(item.get("subject") or ""), "ts": time.time(),
        "title_hint": title_hint, "metadata_source": metadata_source, "metadata_names": metadata_names,
        "archive_source": archive_source, "archive_names": archive_names, "archive_checked_ts": archive_checked_ts,
        "title_source": title_source, "yenc_size": int(ymeta.get("size", 0) or 0),
    }
    key = _name_resolution_cache_key(provider_id, group, item)
    result_fields = {**{k: entry.get(k) for k in returned_fields}, "archive_checked": bool(archive_checked_ts or not _archive_probe_candidate(filename))}
    return {"client_key": client_key, "resolved": True, "cached": False, "filename": media["filename"], "media": media, "_cache_key": key, "_cache_entry": entry, **result_fields}

def resolve_article_names(provider_id: str, group: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    provider = provider_by_id(provider_id)
    limited = [dict(item) for item in items[:12] if isinstance(item, dict)]
    future_items = [(NAME_RESOLUTION_EXECUTOR.submit(_resolve_article_name_worker, provider, provider_id, group, item), item) for item in limited]
    futures = [future for future, _ in future_items]
    done, pending = wait(futures, timeout=40)
    results: list[dict[str, Any]] = []
    for future, item in future_items:
        if future not in done:
            future.cancel()
            results.append({"client_key": str(item.get("client_key") or ""), "resolved": False, "error": "Name probe timed out"})
            continue
        try:
            results.append(future.result())
        except Exception as exc:
            results.append({"client_key": str(item.get("client_key") or ""), "resolved": False, "error": str(exc)[:300]})
    pending_cache = [(str(result.pop("_cache_key")), dict(result.pop("_cache_entry"))) for result in results if result.get("_cache_key") and isinstance(result.get("_cache_entry"), dict)]
    _store_name_resolution_entries(pending_cache)
    resolved = sum(1 for result in results if result.get("resolved"))
    return {"results": results, "requested": len(limited), "resolved": resolved, "unresolved": len(limited) - resolved}

_YENC_DECODE_TABLE = bytes(((i - 42) & 0xFF) for i in range(256))

def _decode_yenc_data_line(line: bytes) -> bytes:
    """Decode one physical yEnc payload line with bulk translation.

    Ordinary bytes are translated in C via bytes.translate(); Python only loops
    over the comparatively rare '=' escape sequences. This is dramatically
    cheaper than walking every byte in Python when dozens of NNTP connections
    are decoding in parallel.
    """
    if b"=" not in line:
        return line.translate(_YENC_DECODE_TABLE)
    if line.endswith(b"="):
        raise NntpError("Truncated yEnc escape sequence")
    parts = line.split(b"=")
    out = bytearray(parts[0].translate(_YENC_DECODE_TABLE))
    for part in parts[1:]:
        if not part:
            raise NntpError("Truncated yEnc escape sequence")
        out.append((part[0] - 106) & 0xFF)
        if len(part) > 1:
            out.extend(part[1:].translate(_YENC_DECODE_TABLE))
    return bytes(out)

def _decode_yenc_blob_python(encoded: bytes) -> tuple[bytes, int]:
    """Bulk Python fallback for one yEnc data region.

    The normal queued-download path uses NewzDeckYenc.exe so the byte-heavy
    transform does not contend on Python's GIL. This fallback preserves full
    compatibility if the native helper is unavailable.
    """
    out = bytearray()
    for line in encoded.splitlines():
        if line:
            out.extend(_decode_yenc_data_line(line))
    data = bytes(out)
    return data, zlib.crc32(data) & 0xffffffff

class _NativeYencWorker:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.proc: subprocess.Popen | None = None

    def _start(self) -> subprocess.Popen:
        if self.proc is not None and self.proc.poll() is None:
            return self.proc
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
        self.proc = subprocess.Popen(
            [str(self.path)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            bufsize=0, creationflags=flags,
        )
        return self.proc

    @staticmethod
    def _read_exact(stream, count: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < count:
            chunk = stream.read(count - len(chunks))
            if not chunk:
                raise EOFError("Native yEnc decoder closed its output pipe")
            chunks.extend(chunk)
        return bytes(chunks)

    def decode(self, encoded: bytes) -> tuple[bytes, int]:
        with self.lock:
            try:
                proc = self._start()
                assert proc.stdin is not None and proc.stdout is not None
                proc.stdin.write(struct.pack("<Q", len(encoded)))
                proc.stdin.write(encoded)
                proc.stdin.flush()
                header = self._read_exact(proc.stdout, 16)
                decoded_len, crc, status = struct.unpack("<QII", header)
                if status != 0:
                    raise NntpError("Truncated yEnc escape sequence")
                if decoded_len > 128 * 1024 * 1024:
                    raise NntpError("Native yEnc decoder returned an invalid payload size")
                payload = self._read_exact(proc.stdout, int(decoded_len))
                return payload, int(crc)
            except Exception:
                try:
                    if self.proc is not None:
                        self.proc.kill()
                except Exception:
                    pass
                self.proc = None
                raise

    def close(self) -> None:
        with self.lock:
            proc, self.proc = self.proc, None
            if proc is not None:
                try:
                    proc.kill()
                except Exception:
                    pass

class NativeYencPool:
    """Persistent native yEnc workers used only by queued downloads.

    A small worker pool is enough because each process can decode much faster
    than one gigabit of Usenet traffic. Keeping the processes warm avoids a
    process-start penalty for each ~700 KB NZB article.
    """
    def __init__(self):
        candidate = APP_DIR / ("NewzDeckYenc.exe" if sys.platform == "win32" else "NewzDeckYenc")
        self.path = candidate
        self.lock = threading.Lock()
        self.next_worker = 0
        # External native decoders avoid the Python GIL. Four workers were enough
        # for ordinary broadband but could become the ceiling once 20-100 NNTP
        # connections were saturated. Scale to eight on modern CPUs.
        worker_count = max(4, min(12, int(os.cpu_count() or 4)))
        self.workers = [_NativeYencWorker(candidate) for _ in range(worker_count)] if candidate.exists() else []
        self.native_bytes = 0
        self.native_seconds = 0.0
        self.fallback_bytes = 0
        self.failures = 0

    def decode(self, encoded: bytes) -> tuple[bytes, int, bool, float]:
        started = time.perf_counter()
        if self.workers:
            with self.lock:
                worker = self.workers[self.next_worker % len(self.workers)]
                self.next_worker += 1
            try:
                data, crc = worker.decode(encoded)
                elapsed = time.perf_counter() - started
                with self.lock:
                    self.native_bytes += len(data)
                    self.native_seconds += elapsed
                return data, crc, True, elapsed
            except Exception:
                with self.lock:
                    self.failures += 1
        data, crc = _decode_yenc_blob_python(encoded)
        elapsed = time.perf_counter() - started
        with self.lock:
            self.fallback_bytes += len(data)
        return data, crc, False, elapsed

    def stats(self) -> dict[str, Any]:
        with self.lock:
            rate = int(self.native_bytes / self.native_seconds) if self.native_seconds > 0 else 0
            return {
                "available": bool(self.workers), "workers": len(self.workers),
                "native_bytes": self.native_bytes, "fallback_bytes": self.fallback_bytes,
                "native_rate_bps": rate, "failures": self.failures,
            }

NATIVE_YENC_POOL = NativeYencPool()
# Network reads and yEnc decode intentionally use different executors. A queued
# NNTP worker must be able to request the next article as soon as its socket is
# finished rather than sitting idle while a native decoder/pipe becomes free.
DOWNLOAD_DECODE_EXECUTOR = ThreadPoolExecutor(
    max_workers=max(8, min(32, int(os.cpu_count() or 4) * 2)),
    thread_name_prefix="usenet-decode",
)
# Disk commits must never block the queue coordinator that refills NNTP slots.
# Two workers are enough for NewzDeck's maximum two-volume rolling RAR window;
# each individual file still permits only one in-flight commit at a time.
DOWNLOAD_DISK_EXECUTOR = ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="usenet-disk",
)

def decode_raw_binary_article(raw: bytes) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    """Decode one raw NNTP BODY payload and return data plus decoder telemetry."""
    begin_pos = raw.find(b"=ybegin")
    if begin_pos >= 0 and (begin_pos == 0 or raw[begin_pos-1:begin_pos] == b"\n"):
        begin_eol = raw.find(b"\n", begin_pos)
        if begin_eol < 0:
            raise NntpError("Malformed yEnc =ybegin header")
        begin_line = raw[begin_pos:begin_eol].rstrip(b"\r")
        meta: dict[str, Any] = {"encoding": "yenc"}
        _parse_yenc_begin(begin_line, meta)
        pos = begin_eol + 1
        if raw.startswith(b"=ypart", pos):
            part_eol = raw.find(b"\n", pos)
            if part_eol < 0:
                raise NntpError("Malformed yEnc =ypart header")
            _parse_yenc_part(raw[pos:part_eol].rstrip(b"\r"), meta)
            pos = part_eol + 1
        marker = raw.rfind(b"\n=yend")
        if marker < pos:
            if raw.startswith(b"=yend", pos):
                marker = pos - 1
            else:
                raise NntpError("yEnc article is missing its =yend trailer")
        data_end = marker
        if data_end > pos and raw[data_end-1:data_end] == b"\r":
            data_end -= 1
        yend_start = marker + 1
        yend_eol = raw.find(b"\n", yend_start)
        if yend_eol < 0:
            yend_eol = len(raw)
        encoded = raw[pos:data_end]
        _parse_yenc_end(raw[yend_start:yend_eol].rstrip(b"\r"), meta)
        data, crc_value, native, decode_seconds = NATIVE_YENC_POOL.decode(encoded)
        if not data:
            raise NntpError("yEnc payload decoded to zero bytes")
        begin = int(meta.get("begin", 0) or 0)
        end = int(meta.get("end", 0) or 0)
        expected_part = (end - begin + 1) if begin > 0 and end >= begin else int(meta.get("end_size", 0) or 0)
        if expected_part and expected_part != len(data):
            raise NntpError(f"Decoded yEnc segment is truncated: expected {expected_part:,} bytes, received {len(data):,}")
        expected_crc = str(meta.get("pcrc32") or "").lower()
        if expected_crc:
            actual_crc = f"{crc_value & 0xffffffff:08x}"
            if actual_crc != expected_crc:
                raise NntpError(f"yEnc CRC mismatch: expected {expected_crc}, received {actual_crc}")
        return data, meta, {"decode_seconds": decode_seconds, "native_decode": native, "crc32": crc_value}

    lines = raw.splitlines()
    decode_started = time.perf_counter()
    data, meta = decode_binary_payload(lines)
    decode_seconds = time.perf_counter() - decode_started
    return data, meta, {"decode_seconds": decode_seconds, "native_decode": False, "crc32": zlib.crc32(data) & 0xffffffff}

def retrieve_segment_into_memory(client: NntpClient, segment: dict[str, Any], cancel_check=None, progress_callback=None) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    """High-throughput single-article path retained for retries/compatibility."""
    article = segment.get("article")
    message_id = str(segment.get("message_id", "") or "").strip()
    target: int | str
    if article is not None and str(article).strip():
        target = int(article)
    elif message_id:
        target = message_id
    else:
        raise NntpError("Article segment has no retrievable article number or Message-ID")
    network_started = time.perf_counter()
    raw = client.body_raw(target, cancel_check=cancel_check, progress_callback=progress_callback)
    network_seconds = time.perf_counter() - network_started
    if cancel_check is not None:
        cancel_check()
    data, meta, perf = decode_raw_binary_article(raw)
    perf["raw_body_bytes"] = len(raw)
    perf["network_seconds"] = network_seconds
    return data, meta, perf

def retrieve_segment_into_file(client: NntpClient, segment: dict[str, Any], f, cancel_check=None, progress_callback=None, apply_part_offset: bool = True) -> tuple[int, dict[str, Any]]:
    """Decode a segment directly into the destination file, streaming yEnc bodies.

    yEnc is overwhelmingly the common Usenet binary encoding. Streaming it avoids
    keeping the full encoded BODY plus a second full decoded copy in memory. Other
    encodings retain the existing buffered fallback for compatibility.
    """
    buffered: list[bytes] = []
    meta: dict[str, Any] = {"encoding": "yenc"}
    yenc = False
    saw_data = False
    saw_end = False
    written = 0

    last_progress = time.monotonic()
    for line in retrieve_segment_body_iter(client, segment):
        if cancel_check is not None:
            cancel_check()
        control = _control_view(line)
        low = control.lower()
        if not yenc:
            if low.startswith(b"=ybegin"):
                yenc = True
                _parse_yenc_begin(control, meta)
                continue
            buffered.append(line)
            continue

        if saw_end:
            continue
        if low.startswith(b"=ypart"):
            _parse_yenc_part(control, meta)
            begin = int(meta.get("begin", 0) or 0)
            if apply_part_offset and begin > 0:
                f.seek(begin - 1)
            continue
        if low.startswith(b"=yend"):
            _parse_yenc_end(control, meta)
            saw_end = True
            continue

        out = _decode_yenc_data_line(line)
        if out:
            f.write(out)
            written += len(out)
            saw_data = True
            now_progress = time.monotonic()
            if progress_callback is not None and (now_progress - last_progress >= 0.5 or len(out) >= 1024 * 1024):
                progress_callback(written)
                last_progress = now_progress

    if yenc:
        if progress_callback is not None and written:
            progress_callback(written)
        if cancel_check is not None:
            cancel_check()
        if not saw_data:
            raise NntpError("yEnc payload contained no data")
        meta["saw_end"] = saw_end
        return written, meta

    chunk, fallback_meta = decode_binary_payload(buffered)
    return write_payload_chunk(f, chunk, fallback_meta), fallback_meta

def sniff_mime(path: Path, fallback: str) -> str:
    try:
        with path.open("rb") as f:
            head = f.read(32)
    except OSError:
        return fallback
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if head.startswith(b"BM"):
        return "image/bmp"
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return fallback

_preview_lock = threading.Lock()
_preview_tokens: dict[str, dict[str, Any]] = {}
_preview_build_locks: dict[str, threading.Lock] = {}
_preview_worker_local = threading.local()
PREVIEW_EXECUTOR = ThreadPoolExecutor(max_workers=PREVIEW_WORKER_COUNT, thread_name_prefix="usenet-preview")
# v3.6.8: visible very-large multipart images may borrow a very small number
# of extra BODY lanes.  The global cap is deliberately lower than the normal
# browsing reserve so high-connection providers gain latency without multiplying
# every thumbnail request into an unbounded socket fan-out.
THUMB_EXTRA_LANE_SEMAPHORE = threading.BoundedSemaphore(4)
_THUMB_TRANSFER_STATS_LOCK = threading.Lock()
_THUMB_TRANSFER_RUNS = 0
_THUMB_TRANSFER_BYTES = 0
_THUMB_TRANSFER_MS = 0.0
_THUMB_TRANSFER_PARALLEL_RUNS = 0
_THUMB_TRANSFER_MAX_LANES = 1


def _provider_connection_key(provider: dict[str, Any]) -> tuple[Any, ...]:
    return (
        provider.get("id") or provider.get("host", ""), provider.get("host", ""),
        int(provider.get("port", 563)), bool(provider.get("ssl", True)), provider.get("username", ""),
    )

def _cancel_preview_idle_timer(holder: dict[str, Any] | None) -> None:
    if not holder:
        return
    timer = holder.pop("idle_timer", None)
    holder["idle_marker"] = None
    if timer is not None:
        try:
            timer.cancel()
        except Exception:
            pass

def _close_worker_client() -> None:
    holder = getattr(_preview_worker_local, "holder", None)
    _cancel_preview_idle_timer(holder)
    if holder and holder.get("client"):
        try:
            holder["client"].close()
        except Exception:
            pass
        holder["closed"] = True
    _preview_worker_local.holder = None

def _arm_preview_worker_idle_close() -> None:
    """Release an idle preview socket quickly after a browsing burst.

    High-concurrency gallery browsing may temporarily use most of a provider's
    configured connection budget. Keep sockets warm while work is flowing, but
    close each worker's NNTP session a few seconds after its last task so a real
    download can reclaim the provider connection budget promptly.
    """
    holder = getattr(_preview_worker_local, "holder", None)
    if not holder or not holder.get("client") or holder.get("closed"):
        return
    _cancel_preview_idle_timer(holder)
    marker = object()
    holder["idle_marker"] = marker
    client = holder["client"]
    def expire() -> None:
        if holder.get("idle_marker") is not marker:
            return
        if time.monotonic() - float(holder.get("last_used", 0.0)) < PREVIEW_CONNECTION_IDLE_CLOSE_SECONDS - 0.05:
            return
        try:
            client.close()
        except Exception:
            pass
        holder["closed"] = True
        holder["idle_timer"] = None
    timer = threading.Timer(PREVIEW_CONNECTION_IDLE_CLOSE_SECONDS, expire)
    timer.daemon = True
    holder["idle_timer"] = timer
    timer.start()

def _preview_worker_client(provider: dict[str, Any], group: str, force_reconnect: bool = False) -> NntpClient:
    """Return a warm NNTP connection owned exclusively by the current preview worker."""
    key = _provider_connection_key(provider)
    holder = getattr(_preview_worker_local, "holder", None)
    _cancel_preview_idle_timer(holder)
    now = time.monotonic()
    stale = bool(holder and (holder.get("closed") or now - float(holder.get("last_used", now)) > 90))
    if force_reconnect or stale or not holder or holder.get("key") != key:
        _close_worker_client()
        password = unprotect_secret(provider.get("password_protected", ""))
        client = NntpClient(
            provider["host"], provider["port"], bool(provider.get("ssl", True)),
            provider.get("username", ""), password, timeout=PREVIEW_SOCKET_TIMEOUT, probe_capabilities=False,
        )
        client.connect()
        holder = {"key": key, "client": client, "group": "", "last_used": now, "closed": False}
        _preview_worker_local.holder = holder
    client = holder["client"]
    if holder.get("group") != group:
        try:
            client.group(group)
        except Exception:
            if force_reconnect:
                raise
            return _preview_worker_client(provider, group, force_reconnect=True)
        holder["group"] = group
    holder["last_used"] = now
    return client

def _preview_build_lock(token: str) -> threading.Lock:
    with _preview_lock:
        lock = _preview_build_locks.get(token)
        if lock is None:
            lock = threading.Lock()
            _preview_build_locks[token] = lock
        return lock

def _segment_cache_refs(segments: list[dict[str, Any]]) -> list[tuple[str, str, int]]:
    """Stable segment identity for both browsed headers and NZB Message-ID-only entries."""
    refs: list[tuple[str, str, int]] = []
    for seg in segments:
        article = seg.get("article")
        refs.append((str(seg.get("message_id") or ""), str(article if article is not None else ""), int(seg.get("part", 1) or 1)))
    return refs

def preview_cache_token(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], media: dict[str, Any]) -> str:
    identity = {
        "provider": provider.get("id") or provider.get("host", ""),
        "group": group,
        "articles": _segment_cache_refs(segments),
        "filename": media.get("filename", ""),
        "preview_decoder": 2,
    }
    raw = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]

_THUMB_TOKEN_CACHE_LOCK = threading.Lock()
_THUMB_TOKEN_CACHE: OrderedDict[tuple[Any, ...], str] = OrderedDict()
_THUMB_TOKEN_CACHE_HITS = 0
_THUMB_TOKEN_CACHE_MISSES = 0
_THUMB_TOKEN_CACHE_LIMIT = 50_000

def _thumbnail_token_fast_key(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], media: dict[str, Any]) -> tuple[Any, ...]:
    first = segments[0] if segments else {}
    last = segments[-1] if segments else {}
    def ref(seg: dict[str, Any]) -> tuple[str, str, int]:
        article = seg.get("article") if isinstance(seg, dict) else None
        return (str(seg.get("message_id") or "") if isinstance(seg, dict) else "", str(article if article is not None else ""), int(seg.get("part", 1) or 1) if isinstance(seg, dict) else 1)
    return (
        str(provider.get("id") or provider.get("host", "")), str(group), str(media.get("filename", "")),
        len(segments), ref(first), ref(last), int(media.get("bytes", 0) or 0), str(media.get("kind", "")),
    )

def thumbnail_cache_token(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], media: dict[str, Any]) -> str:
    global _THUMB_TOKEN_CACHE_HITS, _THUMB_TOKEN_CACHE_MISSES
    fast_key = _thumbnail_token_fast_key(provider, group, segments, media)
    with _THUMB_TOKEN_CACHE_LOCK:
        cached = _THUMB_TOKEN_CACHE.get(fast_key)
        if cached is not None:
            _THUMB_TOKEN_CACHE.move_to_end(fast_key)
            _THUMB_TOKEN_CACHE_HITS += 1
            return cached
        _THUMB_TOKEN_CACHE_MISSES += 1
    identity = {
        "provider": provider.get("id") or provider.get("host", ""),
        "group": group,
        "articles": _segment_cache_refs(segments),
        "filename": media.get("filename", ""),
        "thumbnail_cache": 4,
    }
    raw = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    token = hashlib.sha256(raw).hexdigest()[:32]
    with _THUMB_TOKEN_CACHE_LOCK:
        _THUMB_TOKEN_CACHE[fast_key] = token
        _THUMB_TOKEN_CACHE.move_to_end(fast_key)
        while len(_THUMB_TOKEN_CACHE) > _THUMB_TOKEN_CACHE_LIMIT:
            _THUMB_TOKEN_CACHE.popitem(last=False)
    return token

def thumbnail_token_cache_stats() -> dict[str, Any]:
    with _THUMB_TOKEN_CACHE_LOCK:
        return {"entries":len(_THUMB_TOKEN_CACHE),"hits":_THUMB_TOKEN_CACHE_HITS,"misses":_THUMB_TOKEN_CACHE_MISSES,"limit":_THUMB_TOKEN_CACHE_LIMIT}

def thumbnail_cache_path(token: str) -> Path:
    return THUMB_CACHE_DIR / f"{token}.jpg"

def thumbnail_small_marker_path(token: str) -> Path:
    return THUMB_CACHE_DIR / f"{token}.small.json"

SMALL_IMAGE_MIN_LONG_EDGE = 320
SMALL_IMAGE_MIN_SHORT_EDGE = 160
SMALL_IMAGE_MIN_PIXELS = 100_000

def image_is_too_small_for_gallery(width: int, height: int) -> bool:
    width, height = int(width or 0), int(height or 0)
    if width <= 0 or height <= 0:
        return False
    long_edge, short_edge = max(width, height), min(width, height)
    return long_edge < SMALL_IMAGE_MIN_LONG_EDGE or short_edge < SMALL_IMAGE_MIN_SHORT_EDGE or (width * height) < SMALL_IMAGE_MIN_PIXELS

def cached_small_image_result(token: str) -> dict[str, Any] | None:
    global _THUMB_CATALOG_FS_FALLBACKS
    try:
        entry = _thumbnail_catalog_get(token)
        if entry and entry.get("small"):
            width, height = int(entry.get("source_width",0) or 0), int(entry.get("source_height",0) or 0)
            if width > 0 and height > 0:
                return {"suppressed_small":True,"width":width,"height":height,"method":"small-image-suppressed","cached":True,"thumbnail_token":token}
        with _THUMB_CATALOG_LOCK:
            if _THUMB_CATALOG_READY:
                return None
        _THUMB_CATALOG_FS_FALLBACKS += 1
    except NameError:
        pass
    path = thumbnail_small_marker_path(token)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        width, height = int(data.get("width", 0) or 0), int(data.get("height", 0) or 0)
        if width <= 0 or height <= 0:
            path.unlink(missing_ok=True)
            return None
        try:
            _thumbnail_catalog_register_small(token,width,height)
        except NameError:
            pass
        return {
            "suppressed_small": True, "width": width, "height": height,
            "method": "small-image-suppressed", "cached": True,
            "thumbnail_token": token,
        }
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None

def remember_small_image(token: str, width: int, height: int) -> dict[str, Any]:
    width, height = int(width), int(height)
    marker = thumbnail_small_marker_path(token)
    try:
        marker.write_text(json.dumps({"width": width, "height": height, "created": time.time()}, separators=(",", ":")), encoding="utf-8")
    except OSError:
        pass
    try:
        thumbnail_cache_path(token).unlink(missing_ok=True)
    except OSError:
        pass
    try:
        _thumbnail_catalog_register_small(token, width, height)
    except NameError:
        pass
    return {
        "suppressed_small": True, "width": width, "height": height,
        "method": "small-image-suppressed", "cached": True,
        "thumbnail_token": token,
    }

def thumbnail_full_fallback_path(token: str) -> Path:
    return THUMB_CACHE_DIR / f"{token}.full"

def remember_thumbnail_full_fallback(token: str) -> None:
    try:
        thumbnail_cache_path(token).unlink(missing_ok=True)
        thumbnail_full_fallback_path(token).write_text("full-preview\n", encoding="utf-8")
    except OSError:
        pass
    try:
        _thumbnail_catalog_remove(token)
        _thumbnail_catalog_register_full(token, True)
    except NameError:
        pass

def thumbnail_prefers_full_preview(token: str) -> bool:
    try:
        entry = _thumbnail_catalog_get(token)
        if entry is not None and "full" in entry:
            return bool(entry.get("full"))
    except NameError:
        entry = None
    try:
        exists = thumbnail_full_fallback_path(token).exists()
    except OSError:
        exists = False
    try:
        _thumbnail_catalog_register_full(token, exists)
    except NameError:
        pass
    return exists

def thumbnail_cache_url(token: str, path: Path | None = None) -> str:
    """Return a browser-cache-safe URL for the current bytes of a thumbnail.

    r5 keeps the stable fingerprint in the RAM thumbnail catalog so hot cached
    pages do not stat the same JPEG repeatedly. Filesystem fallback remains for
    startup while the catalog is being rebuilt.
    """
    path = path or thumbnail_cache_path(token)
    try:
        entry = _thumbnail_catalog_get(token)
    except NameError:
        entry = None
    if entry and entry.get("thumb") and entry.get("fingerprint"):
        return f"/thumb/{token}?v={entry['fingerprint']}"
    try:
        st = path.stat()
        fingerprint = f"{int(getattr(st, 'st_mtime_ns', int(st.st_mtime * 1_000_000_000))):x}-{int(st.st_size):x}"
        try:
            _thumbnail_catalog_register_thumb(token, path, size=int(st.st_size), mtime_ns=int(getattr(st, 'st_mtime_ns', int(st.st_mtime * 1_000_000_000))))
        except NameError:
            pass
    except OSError:
        fingerprint = str(time.time_ns())
    return f"/thumb/{token}?v={fingerprint}"

THUMB_HELPER_EXE = APP_DIR / "NewzDeckThumb.exe"

def _physical_memory_bytes() -> int:
    try:
        if sys.platform == "win32":
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.wintypes.DWORD), ("dwMemoryLoad", ctypes.wintypes.DWORD),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = MEMORYSTATUSEX(); st.dwLength = ctypes.sizeof(st)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return int(st.ullTotalPhys)
        pages = int(os.sysconf("SC_PHYS_PAGES")); page_size = int(os.sysconf("SC_PAGE_SIZE"))
        return max(0, pages * page_size)
    except Exception:
        return 0

def _thumbnail_decode_worker_count() -> int:
    ram = _physical_memory_bytes()
    gb = ram / (1024 ** 3) if ram else 8.0
    if gb <= 8: ram_cap = 2
    elif gb <= 16: ram_cap = 3
    elif gb <= 32: ram_cap = 4
    elif gb <= 64: ram_cap = 6
    else: ram_cap = 8
    cpu_cap = max(2, min(8, max(1, int(os.cpu_count() or 4)) // 2))
    return max(2, min(ram_cap, cpu_cap))

THUMB_DECODE_WORKER_COUNT = _thumbnail_decode_worker_count()
THUMB_DECODE_SEMAPHORE = threading.BoundedSemaphore(THUMB_DECODE_WORKER_COUNT)

# v3.6.8 persistent native thumbnail workers. The helper accepts newline-delimited
# JSON jobs in --worker mode so Windows process startup and executable/Defender setup
# are paid once per worker instead of once per gallery image.
class _ThumbnailHelperWorker:
    def __init__(self, index: int):
        self.index = index
        self.proc: subprocess.Popen | None = None
        self.jobs = 0

    def _stop(self) -> None:
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=0.5)
        except Exception:
            pass

    def _ensure(self) -> bool:
        if self.proc is not None and self.proc.poll() is None:
            return True
        self._stop()
        flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)
        try:
            self.proc = subprocess.Popen(
                [str(THUMB_HELPER_EXE), "--worker"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, encoding="utf-8", bufsize=1, creationflags=flags,
            )
            _thumbnail_helper_stat("process_starts", 1)
            return True
        except OSError:
            self.proc = None
            return False

    def run(self, source: Path, output: Path, max_dim: int, timeout: float) -> dict[str, Any] | None:
        if not self._ensure() or self.proc is None or self.proc.stdin is None or self.proc.stdout is None:
            return None
        req_id = uuid.uuid4().hex[:16]
        request = json.dumps({"id": req_id, "input": str(source), "output": str(output), "max_dim": int(max_dim)}, separators=(",", ":"))
        try:
            self.proc.stdin.write(request + "\n")
            self.proc.stdin.flush()
        except (OSError, BrokenPipeError):
            _thumbnail_helper_stat("worker_restarts", 1)
            self._stop()
            return None
        result: dict[str, Any] = {}
        done = threading.Event()
        def reader() -> None:
            nonlocal result
            try:
                line = self.proc.stdout.readline() if self.proc and self.proc.stdout else ""
                if line:
                    parsed = json.loads(line)
                    if isinstance(parsed, dict):
                        result = parsed
            except Exception:
                result = {}
            finally:
                done.set()
        threading.Thread(target=reader, name=f"thumb-helper-read-{self.index}", daemon=True).start()
        if not done.wait(max(1.0, float(timeout))):
            _thumbnail_helper_stat("timeouts", 1)
            self._stop()
            return None
        if result.get("id") != req_id or result.get("error"):
            _thumbnail_helper_stat("worker_failures", 1)
            if self.proc is None or self.proc.poll() is not None:
                self._stop()
            return None
        self.jobs += 1
        _thumbnail_helper_stat("jobs", 1)
        if self.jobs > 1:
            _thumbnail_helper_stat("reused_jobs", 1)
        return result

class _ThumbnailHelperPool:
    def __init__(self, count: int):
        self.workers = [_ThumbnailHelperWorker(i) for i in range(max(1, int(count)))]
        self.available: queue.Queue[_ThumbnailHelperWorker] = queue.Queue()
        for worker in self.workers:
            self.available.put(worker)

    def run(self, source: Path, output: Path, max_dim: int, timeout: float) -> dict[str, Any] | None:
        worker = self.available.get()
        try:
            return worker.run(source, output, max_dim, timeout)
        finally:
            self.available.put(worker)

_THUMB_HELPER_STATS_LOCK = threading.Lock()
_THUMB_HELPER_STATS = {"jobs":0,"reused_jobs":0,"process_starts":0,"worker_restarts":0,"worker_failures":0,"timeouts":0,"blank_rejections":0}
def _thumbnail_helper_stat(key: str, amount: int = 1) -> None:
    with _THUMB_HELPER_STATS_LOCK:
        _THUMB_HELPER_STATS[key] = int(_THUMB_HELPER_STATS.get(key, 0)) + int(amount)

def thumbnail_helper_stats() -> dict[str, Any]:
    with _THUMB_HELPER_STATS_LOCK:
        result = dict(_THUMB_HELPER_STATS)
    result["workers"] = THUMB_DECODE_WORKER_COUNT
    result["process_launches_avoided"] = max(0, int(result.get("jobs",0)) - int(result.get("process_starts",0)))
    result["reuse_rate_percent"] = round(100.0 * int(result.get("reused_jobs",0)) / max(1, int(result.get("jobs",0))), 1)
    return result

THUMB_HELPER_POOL = _ThumbnailHelperPool(THUMB_DECODE_WORKER_COUNT)

# RAM-resident thumbnail/suppression catalog. Existing persistent cache files are
# scanned once in the background, then article-page annotation is normally just a
# dictionary lookup rather than hundreds of NTFS stat/open calls.
_THUMB_CATALOG_LOCK = threading.RLock()
_THUMB_CATALOG: dict[str, dict[str, Any]] = {}
_THUMB_CATALOG_BUILDING = False
_THUMB_CATALOG_READY = False
_THUMB_CATALOG_HITS = 0
_THUMB_CATALOG_MISSES = 0
_THUMB_CATALOG_FS_FALLBACKS = 0
_THUMB_CATALOG_SCAN_FILES = 0

def _thumbnail_catalog_token_from_path(path: Path) -> str:
    name = path.name
    if name.endswith(".small.json"):
        return name[:-11]
    return path.stem

def _thumbnail_catalog_build() -> None:
    global _THUMB_CATALOG_READY, _THUMB_CATALOG_BUILDING, _THUMB_CATALOG_SCAN_FILES
    built: dict[str, dict[str, Any]] = {}
    scanned = 0
    try:
        paths = list(THUMB_CACHE_DIR.iterdir())
    except OSError:
        paths = []
    for path in paths:
        token = _thumbnail_catalog_token_from_path(path)
        if not re.fullmatch(r"[0-9a-f]{32}", token):
            continue
        entry = built.setdefault(token, {})
        try:
            if path.name.endswith(".small.json"):
                data = json.loads(path.read_text(encoding="utf-8"))
                w, h = int(data.get("width",0) or 0), int(data.get("height",0) or 0)
                if w > 0 and h > 0:
                    entry.update({"small":True,"source_width":w,"source_height":h})
                    scanned += 1
            elif path.suffix.casefold() == ".jpg":
                st = path.stat()
                if st.st_size <= 0:
                    continue
                with path.open("rb") as handle:
                    if handle.read(3) != b"\xff\xd8\xff":
                        continue
                dims = image_dimensions(path)
                mtime_ns = int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000)))
                entry.update({"thumb":True,"size":int(st.st_size),"mtime_ns":mtime_ns,"fingerprint":f"{mtime_ns:x}-{int(st.st_size):x}","thumb_width":int(dims[0]) if dims else 0,"thumb_height":int(dims[1]) if dims else 0})
                scanned += 1
            elif path.suffix.casefold() == ".full":
                entry["full"] = True
                scanned += 1
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    with _THUMB_CATALOG_LOCK:
        # Preserve entries learned while the background scan was running.
        for token, current in _THUMB_CATALOG.items():
            built.setdefault(token, {}).update(current)
        _THUMB_CATALOG.clear(); _THUMB_CATALOG.update(built)
        _THUMB_CATALOG_SCAN_FILES = scanned
        _THUMB_CATALOG_READY = True
        _THUMB_CATALOG_BUILDING = False

def _ensure_thumbnail_catalog_started() -> None:
    global _THUMB_CATALOG_BUILDING
    with _THUMB_CATALOG_LOCK:
        if _THUMB_CATALOG_READY or _THUMB_CATALOG_BUILDING:
            return
        _THUMB_CATALOG_BUILDING = True
    threading.Thread(target=_thumbnail_catalog_build, name="newzdeck-thumb-catalog", daemon=True).start()

def _thumbnail_catalog_get(token: str) -> dict[str, Any] | None:
    global _THUMB_CATALOG_HITS, _THUMB_CATALOG_MISSES
    _ensure_thumbnail_catalog_started()
    with _THUMB_CATALOG_LOCK:
        item = _THUMB_CATALOG.get(token)
        if item is not None:
            _THUMB_CATALOG_HITS += 1
            return dict(item)
        _THUMB_CATALOG_MISSES += 1
        return None

def _thumbnail_catalog_register_thumb(token: str, path: Path, *, size: int | None = None, mtime_ns: int | None = None, thumb_width: int = 0, thumb_height: int = 0, source_width: int = 0, source_height: int = 0) -> None:
    try:
        if size is None or mtime_ns is None:
            st = path.stat(); size = int(st.st_size); mtime_ns = int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000)))
    except OSError:
        return
    with _THUMB_CATALOG_LOCK:
        entry = _THUMB_CATALOG.setdefault(token,{})
        entry.update({"thumb":True,"size":int(size),"mtime_ns":int(mtime_ns),"fingerprint":f"{int(mtime_ns):x}-{int(size):x}"})
        if thumb_width and thumb_height: entry.update({"thumb_width":int(thumb_width),"thumb_height":int(thumb_height)})
        if source_width and source_height: entry.update({"source_width":int(source_width),"source_height":int(source_height)})
        entry.pop("small",None)

def _thumbnail_catalog_register_small(token: str, width: int, height: int) -> None:
    with _THUMB_CATALOG_LOCK:
        entry = _THUMB_CATALOG.setdefault(token,{})
        entry.clear(); entry.update({"small":True,"source_width":int(width),"source_height":int(height)})

def _thumbnail_catalog_register_full(token: str, value: bool = True) -> None:
    with _THUMB_CATALOG_LOCK:
        entry = _THUMB_CATALOG.setdefault(token,{})
        entry["full"] = bool(value)

def _thumbnail_catalog_remove(token: str) -> None:
    with _THUMB_CATALOG_LOCK:
        _THUMB_CATALOG.pop(token,None)

def _thumbnail_catalog_clear() -> None:
    global _THUMB_CATALOG_READY, _THUMB_CATALOG_BUILDING
    with _THUMB_CATALOG_LOCK:
        _THUMB_CATALOG.clear(); _THUMB_CATALOG_READY = True; _THUMB_CATALOG_BUILDING = False

def thumbnail_catalog_stats() -> dict[str, Any]:
    with _THUMB_CATALOG_LOCK:
        result = {"ready":_THUMB_CATALOG_READY,"building":_THUMB_CATALOG_BUILDING,"entries":len(_THUMB_CATALOG),"hits":_THUMB_CATALOG_HITS,"misses":_THUMB_CATALOG_MISSES,"filesystem_fallbacks":_THUMB_CATALOG_FS_FALLBACKS,"scanned_files":_THUMB_CATALOG_SCAN_FILES}
    result["token_cache"] = thumbnail_token_cache_stats()
    return result
_THUMB_DECODE_STATE_LOCK = threading.Lock()
_THUMB_DECODE_ACTIVE = 0
_THUMB_DECODE_PEAK = 0
_THUMB_DECODE_WAIT_MS = 0.0
_THUMB_DECODE_RUNS = 0
_THUMB_DECODE_MS = 0.0
_THUMB_DECODE_WIC_RUNS = 0
_THUMB_DECODE_FALLBACK_RUNS = 0

def thumbnail_decode_stats() -> dict[str, Any]:
    with _THUMB_DECODE_STATE_LOCK:
        avg_wait = _THUMB_DECODE_WAIT_MS / max(1, _THUMB_DECODE_RUNS)
        avg_decode = _THUMB_DECODE_MS / max(1, _THUMB_DECODE_RUNS)
        return {
            "workers": THUMB_DECODE_WORKER_COUNT, "active": _THUMB_DECODE_ACTIVE, "peak": _THUMB_DECODE_PEAK,
            "runs": _THUMB_DECODE_RUNS, "average_wait_ms": round(avg_wait, 1), "average_decode_ms": round(avg_decode, 1),
            "wic_runs": _THUMB_DECODE_WIC_RUNS, "fallback_runs": _THUMB_DECODE_FALLBACK_RUNS,
            "physical_memory_bytes": _physical_memory_bytes(), "helper": thumbnail_helper_stats(),
        }

def thumbnail_transfer_stats() -> dict[str, Any]:
    with _THUMB_TRANSFER_STATS_LOCK:
        avg_ms = _THUMB_TRANSFER_MS / max(1, _THUMB_TRANSFER_RUNS)
        avg_bytes = _THUMB_TRANSFER_BYTES / max(1, _THUMB_TRANSFER_RUNS)
        return {
            "runs": _THUMB_TRANSFER_RUNS, "parallel_runs": _THUMB_TRANSFER_PARALLEL_RUNS,
            "max_lanes": _THUMB_TRANSFER_MAX_LANES, "average_ms": round(avg_ms, 1),
            "average_bytes": int(avg_bytes), "total_bytes": int(_THUMB_TRANSFER_BYTES),
        }

def create_native_thumbnail(source: Path, token: str) -> dict[str, Any] | None:
    """Create a compact JPEG thumbnail outside the browser with a RAM-aware decode budget.

    NNTP reconstruction can remain highly parallel, but full-resolution image decode is
    intentionally bounded so a high-connection provider cannot launch dozens of giant
    decoders at once and force the machine into memory/CPU contention.
    """
    global _THUMB_DECODE_ACTIVE, _THUMB_DECODE_PEAK, _THUMB_DECODE_WAIT_MS, _THUMB_DECODE_RUNS, _THUMB_DECODE_MS, _THUMB_DECODE_WIC_RUNS, _THUMB_DECODE_FALLBACK_RUNS
    if not THUMB_HELPER_EXE.exists() or not source.exists():
        return None
    output = thumbnail_cache_path(token)
    temp = output.with_name(output.name + ".part")
    temp.unlink(missing_ok=True)
    flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)
    dims = image_dimensions(source)
    if dims and image_is_too_small_for_gallery(dims[0], dims[1]):
        temp.unlink(missing_ok=True)
        return remember_small_image(token, dims[0], dims[1])
    megapixels = ((dims[0] * dims[1]) / 1_000_000.0) if dims else 0.0
    timeout_seconds = 20 if megapixels <= 25 else (32 if megapixels <= 60 else 45)
    wait_started = time.monotonic()
    acquired = THUMB_DECODE_SEMAPHORE.acquire(timeout=30)
    if not acquired:
        return None
    waited_ms = (time.monotonic() - wait_started) * 1000.0
    with _THUMB_DECODE_STATE_LOCK:
        _THUMB_DECODE_ACTIVE += 1
        _THUMB_DECODE_PEAK = max(_THUMB_DECODE_PEAK, _THUMB_DECODE_ACTIVE)
        _THUMB_DECODE_WAIT_MS += waited_ms
        _THUMB_DECODE_RUNS += 1
    try:
        decode_started = time.monotonic()
        meta = THUMB_HELPER_POOL.run(source, temp, 480, timeout_seconds)
        # Keep a compatibility fallback for platforms/tests where persistent worker
        # mode cannot start, or if a worker is killed by security software.
        if meta is None:
            try:
                proc = subprocess.run(
                    [str(THUMB_HELPER_EXE), str(source), str(temp), "480"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_seconds, check=False,
                    creationflags=flags,
                )
                if proc.returncode == 0:
                    meta = json.loads(proc.stdout.decode("utf-8", errors="replace").strip() or "{}")
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError, UnicodeDecodeError):
                meta = None
        decode_ms = (time.monotonic() - decode_started) * 1000.0
        with _THUMB_DECODE_STATE_LOCK:
            _THUMB_DECODE_MS += decode_ms
        if not meta:
            temp.unlink(missing_ok=True)
            return None
        decode_method = str(meta.get("method") or "native").casefold()
        with _THUMB_DECODE_STATE_LOCK:
            if decode_method == "wic":
                _THUMB_DECODE_WIC_RUNS += 1
            else:
                _THUMB_DECODE_FALLBACK_RUNS += 1
        if bool(meta.get("visual_blank")):
            temp.unlink(missing_ok=True)
            source_width = int(meta.get("source_width",0) or (dims[0] if dims else 0))
            source_height = int(meta.get("source_height",0) or (dims[1] if dims else 0))
            remember_thumbnail_full_fallback(token)
            _thumbnail_helper_stat("blank_rejections", 1)
            return {
                "thumbnail_token": token, "thumbnail_url": "", "cached": False, "visual_blank": True,
                "width": source_width, "height": source_height, "method": "native-blank-fallback",
                "decode_method": str(meta.get("method") or "native"), "decode_ms": round(decode_ms, 1),
                "decode_wait_ms": round(waited_ms, 1), "decode_workers": THUMB_DECODE_WORKER_COUNT,
            }
        if not temp.exists() or temp.stat().st_size <= 0:
            temp.unlink(missing_ok=True)
            return None
        thumb_width = int(meta.get("width", 0) or 0)
        thumb_height = int(meta.get("height", 0) or 0)
        if thumb_width <= 0 or thumb_height <= 0:
            temp.unlink(missing_ok=True)
            return None
        temp.replace(output)
        _mark_thumbnail_stats_dirty()
        cleanup_thumbnail_cache()
        source_width = int(meta.get("source_width",0) or (dims[0] if dims else thumb_width))
        source_height = int(meta.get("source_height",0) or (dims[1] if dims else thumb_height))
        try:
            st = output.stat()
            _thumbnail_catalog_register_thumb(token, output, size=int(st.st_size), mtime_ns=int(getattr(st,"st_mtime_ns",int(st.st_mtime*1_000_000_000))), thumb_width=thumb_width, thumb_height=thumb_height, source_width=source_width, source_height=source_height)
        except OSError:
            pass
        return {
            "thumbnail_token": token, "thumbnail_url": thumbnail_cache_url(token, output), "cached": True,
            "size": output.stat().st_size, "width": int(source_width), "height": int(source_height),
            "thumbnail_width": thumb_width, "thumbnail_height": thumb_height,
            "method": "native-wic" if str(meta.get("method") or "").casefold() == "wic" else "native",
            "decode_method": str(meta.get("method") or "native"), "decode_ms": round(decode_ms, 1),
            "decode_wait_ms": round(waited_ms, 1), "decode_workers": THUMB_DECODE_WORKER_COUNT,
        }
    except (OSError, subprocess.SubprocessError, ValueError):
        temp.unlink(missing_ok=True)
        return None
    finally:
        with _THUMB_DECODE_STATE_LOCK:
            _THUMB_DECODE_ACTIVE = max(0, _THUMB_DECODE_ACTIVE - 1)
        THUMB_DECODE_SEMAPHORE.release()

def _mark_thumbnail_stats_dirty() -> None:
    global _THUMB_STATS_DIRTY
    with _THUMB_STATS_LOCK:
        _THUMB_STATS_DIRTY = True

def cached_thumbnail_result(token: str) -> dict[str, Any] | None:
    global _THUMB_CATALOG_FS_FALLBACKS
    entry = _thumbnail_catalog_get(token)
    if entry and entry.get("thumb") and int(entry.get("size",0) or 0) > 0:
        return {"thumbnail_token":token,"thumbnail_url":thumbnail_cache_url(token),"cached":True,"size":int(entry.get("size",0) or 0)}
    path = thumbnail_cache_path(token)
    with _THUMB_CATALOG_LOCK:
        ready = _THUMB_CATALOG_READY
    if ready:
        return None
    _THUMB_CATALOG_FS_FALLBACKS += 1
    try:
        st = path.stat()
        if st.st_size <= 0:
            return None
        with path.open("rb") as check:
            if check.read(3) != b"\xff\xd8\xff":
                path.unlink(missing_ok=True); _mark_thumbnail_stats_dirty(); return None
        dims = image_dimensions(path)
        _thumbnail_catalog_register_thumb(token,path,size=int(st.st_size),mtime_ns=int(getattr(st,"st_mtime_ns",int(st.st_mtime*1_000_000_000))),thumb_width=int(dims[0]) if dims else 0,thumb_height=int(dims[1]) if dims else 0)
        return {"thumbnail_token":token,"thumbnail_url":thumbnail_cache_url(token,path),"cached":True,"size":int(st.st_size)}
    except OSError:
        return None

def annotate_cached_thumbnail_urls(provider_id: str, group: str, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach direct local thumbnail URLs using the r5 RAM catalog hot path."""
    global _THUMB_CATALOG_FS_FALLBACKS
    if not articles:
        return articles
    _ensure_thumbnail_catalog_started()
    try:
        preview_provider = resolve_provider_for_purpose(provider_id, "previews")
    except Exception:
        preview_provider = provider_by_id(provider_id)
    cross_provider = str(preview_provider.get("id", "")) != str(provider_id)
    out: list[dict[str, Any]] = []
    for item in articles:
        media = item.get("media") if isinstance(item.get("media"), dict) else None
        segments = item.get("segments") if isinstance(item.get("segments"), list) else []
        if not media or media.get("kind") not in {"image", "video"} or not item.get("complete") or not segments:
            out.append(item); continue
        token_segments = [{**seg, "article": None} for seg in segments if isinstance(seg, dict)] if cross_provider else segments
        token = thumbnail_cache_token(preview_provider, group, token_segments, media)
        entry = _thumbnail_catalog_get(token)
        if entry and entry.get("small") and media.get("kind") == "image":
            enriched = dict(item); enriched["small_image_suppressed"] = True
            enriched["media_meta"] = {**(item.get("media_meta") or {}),"width":int(entry.get("source_width",0) or 0),"height":int(entry.get("source_height",0) or 0)}
            out.append(enriched); continue
        if entry and entry.get("thumb") and int(entry.get("size",0) or 0)>0:
            if media.get("kind") == "image":
                sw, sh = int(entry.get("source_width",0) or 0), int(entry.get("source_height",0) or 0)
                tw, th = int(entry.get("thumb_width",0) or 0), int(entry.get("thumb_height",0) or 0)
                # Existing pre-r4 cache entries may only know thumbnail dimensions.
                # A suspicious exactly-480 narrow thumb remains a one-time source recheck.
                if not sw or not sh:
                    if tw and th and image_is_too_small_for_gallery(tw,th):
                        if max(tw,th)<480:
                            small=remember_small_image(token,tw,th); enriched=dict(item); enriched["small_image_suppressed"]=True; enriched["media_meta"]={**(item.get("media_meta") or {}),"width":small["width"],"height":small["height"]}; out.append(enriched); continue
                        out.append(item); continue
                elif image_is_too_small_for_gallery(sw,sh):
                    small=remember_small_image(token,sw,sh); enriched=dict(item); enriched["small_image_suppressed"]=True; enriched["media_meta"]={**(item.get("media_meta") or {}),"width":small["width"],"height":small["height"]}; out.append(enriched); continue
                if entry.get("full"):
                    out.append(item); continue
            enriched=dict(item); enriched["cached_thumbnail_token"]=token; enriched["cached_thumbnail_url"]=thumbnail_cache_url(token); out.append(enriched); continue
        # While the one-time catalog scan is still running, retain r4-compatible
        # filesystem fallback so the first page never waits for indexing to finish.
        with _THUMB_CATALOG_LOCK:
            ready = _THUMB_CATALOG_READY
        if not ready:
            _THUMB_CATALOG_FS_FALLBACKS += 1
            small = cached_small_image_result(token) if media.get("kind") == "image" else None
            if small:
                _thumbnail_catalog_register_small(token,int(small["width"]),int(small["height"])); enriched=dict(item); enriched["small_image_suppressed"]=True; enriched["media_meta"]={**(item.get("media_meta") or {}),"width":int(small["width"]),"height":int(small["height"])}; out.append(enriched); continue
            cached = cached_thumbnail_result(token)
            if cached:
                entry = _thumbnail_catalog_get(token) or {}
                if not (media.get("kind")=="image" and entry.get("full")):
                    enriched=dict(item); enriched["cached_thumbnail_token"]=token; enriched["cached_thumbnail_url"]=cached["thumbnail_url"]; out.append(enriched); continue
        out.append(item)
    return out

def thumbnail_cache_stats(*, force: bool = False) -> dict[str, Any]:
    global _THUMB_STATS_CACHE, _THUMB_STATS_CACHE_TS, _THUMB_STATS_DIRTY
    now = time.monotonic()
    with _THUMB_STATS_LOCK:
        if not force and _THUMB_STATS_CACHE is not None and now - _THUMB_STATS_CACHE_TS < THUMB_STATS_TTL_SECONDS:
            return dict(_THUMB_STATS_CACHE)
    if not force and _THUMB_STATS_CACHE is None:
        saved = json_read(THUMB_STATS_FILE, None)
        if isinstance(saved, dict) and "bytes" in saved and "files" in saved:
            with _THUMB_STATS_LOCK:
                _THUMB_STATS_CACHE = dict(saved)
                _THUMB_STATS_CACHE_TS = now
            return dict(saved)
        settings = json_read(SETTINGS_FILE, {})
        limit_gb = max(0.25, min(20.0, float(settings.get("thumbnail_cache_gb", DEFAULT_THUMB_CACHE_GB) or DEFAULT_THUMB_CACHE_GB)))
        return {"files": 0, "bytes": 0, "limit_bytes": int(limit_gb * 1024**3), "limit_gb": limit_gb, "folder": str(THUMB_CACHE_DIR), "estimating": True}
    total = 0
    count = 0
    try:
        for path in THUMB_CACHE_DIR.glob("*.jpg"):
            try:
                st = path.stat()
                total += st.st_size
                count += 1
            except OSError:
                pass
    except OSError:
        pass
    settings = json_read(SETTINGS_FILE, {})
    limit_gb = max(0.25, min(20.0, float(settings.get("thumbnail_cache_gb", DEFAULT_THUMB_CACHE_GB) or DEFAULT_THUMB_CACHE_GB)))
    result = {"files": count, "bytes": total, "limit_bytes": int(limit_gb * 1024**3), "limit_gb": limit_gb, "folder": str(THUMB_CACHE_DIR)}
    with _THUMB_STATS_LOCK:
        _THUMB_STATS_CACHE = dict(result)
        _THUMB_STATS_CACHE_TS = time.monotonic()
        _THUMB_STATS_DIRTY = False
    try:
        json_write(THUMB_STATS_FILE, result)
    except OSError:
        pass
    return result

def cleanup_thumbnail_cache(max_age_days: int = 60, *, force: bool = False) -> None:
    """Schedule thumbnail cache pruning without blocking gallery requests."""
    global _THUMB_CLEANUP_LAST, _THUMB_CLEANUP_RUNNING
    now_mono = time.monotonic()
    with _THUMB_STATS_LOCK:
        if _THUMB_CLEANUP_RUNNING:
            return
        if not force and now_mono - _THUMB_CLEANUP_LAST < THUMB_CLEANUP_INTERVAL_SECONDS:
            return
        _THUMB_CLEANUP_LAST = now_mono
        _THUMB_CLEANUP_RUNNING = True

    def _run():
        global _THUMB_CLEANUP_RUNNING
        try:
            settings = json_read(SETTINGS_FILE, {})
            limit_gb = max(0.25, min(20.0, float(settings.get("thumbnail_cache_gb", DEFAULT_THUMB_CACHE_GB) or DEFAULT_THUMB_CACHE_GB)))
            max_bytes = int(limit_gb * 1024**3)
            cutoff = time.time() - max_age_days * 86400
            entries: list[tuple[float, int, Path]] = []
            total = 0
            changed = False
            try:
                paths = list(THUMB_CACHE_DIR.glob("*.jpg"))
            except OSError:
                paths = []
            for path in paths:
                try:
                    st = path.stat()
                    if st.st_mtime < cutoff:
                        path.unlink(missing_ok=True)
                        _thumbnail_catalog_remove(path.stem)
                        changed = True
                        continue
                    entries.append((st.st_mtime, st.st_size, path))
                    total += st.st_size
                except OSError:
                    pass
            if total > max_bytes:
                for _mtime, size, path in sorted(entries, key=lambda item: item[0]):
                    try:
                        path.unlink(missing_ok=True)
                        _thumbnail_catalog_remove(path.stem)
                        total -= size
                        changed = True
                    except OSError:
                        pass
                    if total <= max_bytes:
                        break
            if changed:
                _mark_thumbnail_stats_dirty()
        finally:
            with _THUMB_STATS_LOCK:
                _THUMB_CLEANUP_RUNNING = False

    if force:
        _run()
    else:
        threading.Thread(target=_run, name="newzdeck-thumbnail-cache-cleanup", daemon=True).start()

def store_thumbnail_data(token: str, data_url: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{32}", token or ""):
        raise ValueError("Invalid thumbnail token")
    match = re.fullmatch(r"data:image/(?:jpeg|jpg);base64,([A-Za-z0-9+/=\r\n]+)", str(data_url or ""), re.I)
    if not match:
        raise ValueError("Thumbnail must be a JPEG data URL")
    try:
        raw = base64.b64decode(match.group(1), validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Thumbnail data is invalid")
    if len(raw) < 64 or len(raw) > 1_500_000 or not raw.startswith(b"\xff\xd8\xff"):
        raise ValueError("Thumbnail data is invalid or too large")
    path = thumbnail_cache_path(token)
    temp = path.with_suffix(".jpg.part")
    temp.write_bytes(raw)
    temp.replace(path)
    dims = image_dimensions(path)
    _thumbnail_catalog_register_thumb(token,path,thumb_width=int(dims[0]) if dims else 0,thumb_height=int(dims[1]) if dims else 0)
    _mark_thumbnail_stats_dirty()
    cleanup_thumbnail_cache()
    return {"thumbnail_token": token, "thumbnail_url": thumbnail_cache_url(token, path), "cached": True, "size": len(raw)}

def cached_preview_result(token: str, filename: str, media: dict[str, Any]) -> dict[str, Any] | None:
    suffix = Path(filename).suffix or (".jpg" if media.get("kind") == "image" else ".mp4")
    output_path = CACHE_DIR / f"{token}{suffix}"
    if not output_path.exists() or output_path.stat().st_size <= 0:
        return None
    mime = sniff_mime(output_path, media.get("mime") or mimetypes.guess_type(filename)[0] or "application/octet-stream")
    with _preview_lock:
        _preview_tokens[token] = {"path": str(output_path), "mime": mime, "filename": filename, "created": time.time()}
    return {"token": token, "url": f"/media/{token}", "download_url": f"/download/{token}", "filename": filename, "mime": mime, "size": output_path.stat().st_size, "kind": media.get("kind"), "cached": True}

def _assemble_segments_sequential(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], output_path: Path, max_bytes: int | None = None, max_segments: int | None = None, cancel_check=None) -> tuple[int, int]:
    """Assemble preview segments without letting one bad part stall the gallery.

    Each segment is decoded into a small in-memory staging buffer and committed to
    the preview file only after that segment succeeds.  A transient connection
    failure therefore retries only the failed segment instead of downloading all
    earlier parts again.  Permanent missing/decode/auth failures fail fast and do
    not consume a second preview connection.
    """
    segments_sorted = sorted(segments, key=lambda seg: int(seg.get("part", 1)))
    temp_path = output_path.with_suffix(output_path.suffix + ".part")
    temp_path.unlink(missing_ok=True)
    written = 0
    fetched = 0
    try:
        with temp_path.open("w+b") as f:
            for seg in segments_sorted:
                if cancel_check is not None:
                    cancel_check()
                last_exc: Exception | None = None
                completed = False
                for attempt in range(2):
                    stage = io.BytesIO()
                    try:
                        client = _preview_worker_client(provider, group, force_reconnect=attempt > 0)
                        part_written, meta = retrieve_segment_into_file(
                            client, seg, stage, cancel_check=cancel_check, apply_part_offset=False,
                        )
                        payload = stage.getvalue()
                        begin = int(meta.get("begin", 0) or 0)
                        if begin > 0:
                            f.seek(begin - 1)
                        else:
                            f.seek(0, io.SEEK_END)
                        f.write(payload)
                        written += part_written
                        fetched += 1
                        completed = True
                        break
                    except (NntpError, socket.error, ssl.SSLError, OSError) as exc:
                        last_exc = exc
                        _close_worker_client()
                        failure = classify_nntp_failure(exc)
                        if attempt == 0 and bool(failure.get("retryable")) and failure.get("code") != "timeout":
                            continue
                        raise
                if not completed:
                    if last_exc:
                        raise last_exc
                    raise NntpError("Could not retrieve preview segment")
                if max_bytes is not None and written >= max_bytes:
                    break
                if max_segments is not None and fetched >= max_segments:
                    break
        temp_path.replace(output_path)
        return written, fetched
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

def _assemble_segments_parallel(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], output_path: Path, lanes: int, max_bytes: int | None = None, cancel_check=None) -> tuple[int, int]:
    """Retrieve one visible large multipart image with a few coordinated BODY lanes.

    Lane 0 keeps the preview worker's already-warm connection. Extra lanes use
    short-lived provider sessions and are globally capped, so this accelerates
    latency-sensitive large images without changing the normal gallery socket budget.
    """
    requested = max(1, min(3, int(lanes or 1)))
    acquired = 0
    for _ in range(requested - 1):
        if THUMB_EXTRA_LANE_SEMAPHORE.acquire(blocking=False):
            acquired += 1
        else:
            break
    actual = 1 + acquired
    if actual <= 1 or len(segments) < 4:
        for _ in range(acquired):
            THUMB_EXTRA_LANE_SEMAPHORE.release()
        return _assemble_segments_sequential(provider, group, segments, output_path, max_bytes=max_bytes, cancel_check=cancel_check)

    ordered = sorted(segments, key=lambda seg: int(seg.get("part", 1) or 1))
    buckets = [ordered[i::actual] for i in range(actual)]
    password = unprotect_secret(provider.get("password_protected", ""))

    def fetch_bucket(bucket: list[dict[str, Any]], warm: bool) -> list[tuple[int, bytes, dict[str, Any]]]:
        results: list[tuple[int, bytes, dict[str, Any]]] = []
        direct_client = None
        try:
            if not warm:
                direct_client = NntpClient(provider["host"], provider["port"], bool(provider.get("ssl", True)), provider.get("username", ""), password)
                direct_client.__enter__(); direct_client.group(group)
            for seg in bucket:
                if cancel_check is not None:
                    cancel_check()
                last_exc = None
                for attempt in range(2):
                    stage = io.BytesIO()
                    try:
                        if warm:
                            client = _preview_worker_client(provider, group, force_reconnect=attempt > 0)
                        else:
                            if attempt > 0:
                                try:
                                    direct_client.__exit__(None, None, None)
                                except Exception:
                                    pass
                                direct_client = NntpClient(provider["host"], provider["port"], bool(provider.get("ssl", True)), provider.get("username", ""), password)
                                direct_client.__enter__(); direct_client.group(group)
                            client = direct_client
                        part_written, meta = retrieve_segment_into_file(client, seg, stage, cancel_check=cancel_check, apply_part_offset=False)
                        results.append((int(seg.get("part", 1) or 1), stage.getvalue(), meta))
                        break
                    except (NntpError, socket.error, ssl.SSLError, OSError) as exc:
                        last_exc = exc
                        if warm:
                            _close_worker_client()
                        failure = classify_nntp_failure(exc)
                        if attempt == 0 and bool(failure.get("retryable")) and failure.get("code") != "timeout":
                            continue
                        raise
                else:
                    if last_exc:
                        raise last_exc
            return results
        finally:
            if direct_client is not None:
                try:
                    direct_client.__exit__(None, None, None)
                except Exception:
                    pass

    temp_path = output_path.with_suffix(output_path.suffix + ".part")
    temp_path.unlink(missing_ok=True)
    started = time.monotonic()
    try:
        with ThreadPoolExecutor(max_workers=max(1, actual - 1), thread_name_prefix="thumb-body-lane") as extras:
            futures = [extras.submit(fetch_bucket, buckets[i], False) for i in range(1, actual)]
            pieces = fetch_bucket(buckets[0], True)
            for fut in futures:
                pieces.extend(fut.result())
        pieces.sort(key=lambda item: item[0])
        written = 0
        with temp_path.open("w+b") as f:
            for _, payload, meta in pieces:
                begin = int(meta.get("begin", 0) or 0)
                if begin > 0:
                    f.seek(begin - 1)
                else:
                    f.seek(0, io.SEEK_END)
                f.write(payload); written += len(payload)
                if max_bytes is not None and written >= max_bytes:
                    break
        temp_path.replace(output_path)
        elapsed_ms = (time.monotonic() - started) * 1000.0
        global _THUMB_TRANSFER_RUNS, _THUMB_TRANSFER_BYTES, _THUMB_TRANSFER_MS, _THUMB_TRANSFER_PARALLEL_RUNS, _THUMB_TRANSFER_MAX_LANES
        with _THUMB_TRANSFER_STATS_LOCK:
            _THUMB_TRANSFER_RUNS += 1; _THUMB_TRANSFER_BYTES += written; _THUMB_TRANSFER_MS += elapsed_ms
            _THUMB_TRANSFER_PARALLEL_RUNS += 1; _THUMB_TRANSFER_MAX_LANES = max(_THUMB_TRANSFER_MAX_LANES, actual)
        return written, len(pieces)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        for _ in range(acquired):
            THUMB_EXTRA_LANE_SEMAPHORE.release()

def _assemble_segments(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], output_path: Path, max_bytes: int | None = None, max_segments: int | None = None, cancel_check=None, parallel_lanes: int = 1) -> tuple[int, int]:
    if parallel_lanes > 1 and max_segments is None and len(segments) >= 4:
        return _assemble_segments_parallel(provider, group, segments, output_path, parallel_lanes, max_bytes=max_bytes, cancel_check=cancel_check)
    started = time.monotonic()
    result = _assemble_segments_sequential(provider, group, segments, output_path, max_bytes=max_bytes, max_segments=max_segments, cancel_check=cancel_check)
    elapsed_ms = (time.monotonic() - started) * 1000.0
    global _THUMB_TRANSFER_RUNS, _THUMB_TRANSFER_BYTES, _THUMB_TRANSFER_MS
    # Only thumbnail callers consume these fields in Diagnostics; full-preview/video
    # assembly may also contribute, which intentionally reflects total BODY pressure.
    with _THUMB_TRANSFER_STATS_LOCK:
        _THUMB_TRANSFER_RUNS += 1; _THUMB_TRANSFER_BYTES += int(result[0]); _THUMB_TRANSFER_MS += elapsed_ms
    return result

def prepare_preview(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], media: dict[str, Any], max_mb: int, cancel_check=None) -> dict[str, Any]:
    if not media:
        raise ValueError("No previewable image or video was detected in this post")
    if not segments:
        raise ValueError("No article segments were supplied")
    if len(segments) > 10000:
        raise ValueError("Preview has too many segments")

    filename = media.get("filename") or f"preview.{media.get('extension', 'bin')}"
    filename = re.sub(r"[^A-Za-z0-9._ -]+", "_", filename).strip() or "preview.bin"
    expected_wire = sum(int(s.get("bytes", 0) or 0) for s in segments)
    if expected_wire > max_mb * 1024 * 1024 * 1.4:
        raise ValueError(f"Preview is larger than the {max_mb} MB preview safety limit")

    token = preview_cache_token(provider, group, segments, media)
    cached = cached_preview_result(token, filename, media)
    if cached:
        return cached
    lock = _preview_build_lock(token)
    with lock:
        cached = cached_preview_result(token, filename, media)
        if cached:
            return cached
        suffix = Path(filename).suffix or (".jpg" if media.get("kind") == "image" else ".mp4")
        output_path = CACHE_DIR / f"{token}{suffix}"
        written, _ = _assemble_segments(provider, group, segments, output_path, max_bytes=max_mb * 1024 * 1024 + 1, cancel_check=cancel_check)
        if written > max_mb * 1024 * 1024:
            output_path.unlink(missing_ok=True)
            raise ValueError(f"Preview exceeded the {max_mb} MB preview safety limit")
        mime = sniff_mime(output_path, media.get("mime") or mimetypes.guess_type(filename)[0] or "application/octet-stream")
        with _preview_lock:
            _preview_tokens[token] = {"path": str(output_path), "mime": mime, "filename": filename, "created": time.time()}
        cleanup_preview_cache()
        return {"token": token, "url": f"/media/{token}", "download_url": f"/download/{token}", "filename": filename, "mime": mime, "size": output_path.stat().st_size, "kind": media.get("kind"), "cached": False}

def _video_sample_token(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], media: dict[str, Any]) -> str:
    identity = {
        "provider": provider.get("id") or provider.get("host", ""), "group": group,
        "articles": _segment_cache_refs(segments),
        "filename": media.get("filename", ""), "video_thumb_sample": 2,
    }
    raw = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]

def _ffmpeg_path() -> str | None:
    candidates = [APP_DIR / "ffmpeg.exe", APP_DIR / "tools" / "ffmpeg.exe"]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return shutil.which("ffmpeg")

def _try_ffmpeg_frame(source: Path, thumb_token: str) -> str | None:
    cached = cached_thumbnail_result(thumb_token)
    if cached:
        return cached["thumbnail_url"]
    ffmpeg = _ffmpeg_path()
    if not ffmpeg:
        return None
    frame_path = thumbnail_cache_path(thumb_token)
    temp_path = frame_path.with_name(frame_path.stem + ".part.jpg")
    try:
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error", "-ss", "0.35", "-i", str(source),
            "-frames:v", "1", "-vf", "scale='min(480,iw)':-2", "-q:v", "4", str(temp_path),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=False)
    except Exception:
        temp_path.unlink(missing_ok=True)
        return None
    if not temp_path.exists() or temp_path.stat().st_size <= 0:
        temp_path.unlink(missing_ok=True)
        return None
    temp_path.replace(frame_path)
    _mark_thumbnail_stats_dirty()
    cleanup_thumbnail_cache()
    return thumbnail_cache_url(thumb_token, frame_path)

def prepare_image_thumbnail(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], media: dict[str, Any], max_mb: int, cancel_check=None, parallel_lanes: int = 1) -> dict[str, Any]:
    if media.get("kind") != "image":
        raise ValueError("Image thumbnail requested for a non-image post")
    if not segments:
        raise ValueError("No article segments were supplied")
    if len(segments) > 10000:
        raise ValueError("Preview has too many segments")

    thumb_token = thumbnail_cache_token(provider, group, segments, media)
    small = cached_small_image_result(thumb_token)
    if small:
        return {"kind": "image", "filename": media.get("filename") or "image", **small}
    cached = cached_thumbnail_result(thumb_token)
    if cached:
        # r3 and earlier do not retain source dimensions beside the JPEG. If the
        # generated thumbnail is below 480 px on its long edge, it was not scaled
        # down and its dimensions are safe to treat as the source dimensions. If
        # the long edge is exactly 480 and the shape looks tiny/suspicious, bypass
        # the old cache once and reconstruct the source so a narrow high-resolution
        # portrait/panorama is not falsely suppressed.
        cached_path = thumbnail_cache_path(thumb_token)
        dims = image_dimensions(cached_path)
        if dims and image_is_too_small_for_gallery(dims[0], dims[1]):
            if max(dims) < 480:
                return {"kind": "image", "filename": media.get("filename") or "image", **remember_small_image(thumb_token, dims[0], dims[1])}
            try:
                cached_path.unlink(missing_ok=True)
                _mark_thumbnail_stats_dirty()
            except OSError:
                pass
        else:
            return {"kind": "image", "filename": media.get("filename") or "image", **cached}

    filename = media.get("filename") or f"preview.{media.get('extension', 'jpg')}"
    filename = re.sub(r"[^A-Za-z0-9._ -]+", "_", filename).strip() or "preview.jpg"
    if thumbnail_prefers_full_preview(thumb_token):
        full = prepare_preview(provider, group, segments, media, max_mb, cancel_check=cancel_check)
        return {
            "kind": "image", "filename": filename, "thumbnail_token": thumb_token,
            "thumbnail_url": full.get("url", ""), "source_url": full.get("url", ""),
            "source_cached": bool(full.get("cached")), "cached": bool(full.get("cached")),
            "method": "full-preview-visual-fallback", "full_preview_fallback": True,
            "size": int(full.get("size", 0) or 0),
        }
    expected_wire = sum(int(seg.get("bytes", 0) or 0) for seg in segments)
    if expected_wire > max_mb * 1024 * 1024 * 1.4:
        raise ValueError(f"Preview is larger than the {max_mb} MB preview safety limit")

    lock = _preview_build_lock("thumb:" + thumb_token)
    with lock:
        small = cached_small_image_result(thumb_token)
        if small:
            return {"kind": "image", "filename": filename, **small}
        cached = cached_thumbnail_result(thumb_token)
        if cached:
            return {"kind": "image", "filename": filename, **cached}

        full_token = preview_cache_token(provider, group, segments, media)
        existing = cached_preview_result(full_token, filename, media)
        if existing:
            with _preview_lock:
                existing_item = _preview_tokens.get(full_token)
            if existing_item:
                native = create_native_thumbnail(Path(existing_item["path"]), thumb_token)
                if native:
                    if native.get("visual_blank"):
                        return {"kind":"image","filename":filename,"thumbnail_token":thumb_token,"thumbnail_url":existing.get("url",""),"source_url":existing.get("url",""),"source_cached":True,"cached":True,"method":"full-preview-native-blank","thumbnail_fallback":True,"width":native.get("width",0),"height":native.get("height",0)}
                    return {"kind": "image", "filename": filename, "source_cached": True, **native}

        suffix = Path(filename).suffix or ".jpg"
        source_path = CACHE_DIR / f".thumbsrc-{thumb_token}{suffix}"
        source_path.unlink(missing_ok=True)
        written = 0
        try:
            transfer_started = time.monotonic()
            written, _ = _assemble_segments(
                provider, group, segments, source_path,
                max_bytes=max_mb * 1024 * 1024 + 1, cancel_check=cancel_check, parallel_lanes=parallel_lanes,
            )
            transfer_ms = (time.monotonic() - transfer_started) * 1000.0
            if written > max_mb * 1024 * 1024:
                raise ValueError(f"Preview exceeded the {max_mb} MB preview safety limit")

            native = create_native_thumbnail(source_path, thumb_token)
            if native:
                if native.get("visual_blank"):
                    preview_path = CACHE_DIR / f"{full_token}{suffix}"
                    if preview_path.exists() and preview_path.stat().st_size > 0:
                        source_path.unlink(missing_ok=True)
                    else:
                        source_path.replace(preview_path)
                    mime = sniff_mime(preview_path, media.get("mime") or mimetypes.guess_type(filename)[0] or "application/octet-stream")
                    with _preview_lock:
                        _preview_tokens[full_token] = {"path": str(preview_path), "mime": mime, "filename": filename, "created": time.time()}
                    cleanup_preview_cache()
                    return {"kind":"image","filename":filename,"thumbnail_token":thumb_token,"thumbnail_url":f"/media/{full_token}","source_url":f"/media/{full_token}","source_cached":False,"cached":False,"method":"full-preview-native-blank","thumbnail_fallback":True,"width":native.get("width",0),"height":native.get("height",0),"transfer_ms":round(transfer_ms,1),"transfer_lanes":int(parallel_lanes or 1),"transfer_bytes":int(written)}
                return {"kind": "image", "filename": filename, "source_cached": False,
                        "transfer_ms": round(transfer_ms, 1), "transfer_lanes": int(parallel_lanes or 1),
                        "transfer_bytes": int(written), **native}

            preview_path = CACHE_DIR / f"{full_token}{suffix}"
            if preview_path.exists() and preview_path.stat().st_size > 0:
                source_path.unlink(missing_ok=True)
            else:
                source_path.replace(preview_path)
            mime = sniff_mime(preview_path, media.get("mime") or mimetypes.guess_type(filename)[0] or "application/octet-stream")
            with _preview_lock:
                _preview_tokens[full_token] = {"path": str(preview_path), "mime": mime, "filename": filename, "created": time.time()}
            cleanup_preview_cache()
            return {
                "kind": "image", "filename": filename, "thumbnail_token": thumb_token,
                "thumbnail_url": "", "source_url": f"/media/{full_token}",
                "source_cached": False, "cached": False, "method": "browser-fallback",
            }
        finally:
            source_path.unlink(missing_ok=True)

def prepare_video_thumbnail(provider: dict[str, Any], group: str, segments: list[dict[str, Any]], media: dict[str, Any], cancel_check=None) -> dict[str, Any]:
    if media.get("kind") != "video":
        raise ValueError("Video thumbnail requested for a non-video post")
    if not segments:
        raise ValueError("No article segments were supplied")
    filename = re.sub(r"[^A-Za-z0-9._ -]+", "_", str(media.get("filename") or "preview.mp4")).strip() or "preview.mp4"
    ext = (Path(filename).suffix.lower().lstrip(".") or str(media.get("extension") or "mp4").lower())
    thumb_token = thumbnail_cache_token(provider, group, segments, media)
    cached_thumb = cached_thumbnail_result(thumb_token)
    if cached_thumb:
        return {
            "kind": "video", "filename": filename, "sample_url": "", "thumbnail_url": cached_thumb["thumbnail_url"],
            "thumbnail_token": thumb_token, "browser_supported": ext in {"mp4", "m4v", "webm", "mov"},
            "partial": False, "cached": True, "method": "persistent-cache",
        }

    full_token = preview_cache_token(provider, group, segments, media)
    full = cached_preview_result(full_token, filename, media)
    if full:
        full_path = Path(_preview_tokens[full_token]["path"])
        frame_url = _try_ffmpeg_frame(full_path, thumb_token)
        return {
            "kind": "video", "filename": filename, "sample_url": full["url"], "thumbnail_url": frame_url,
            "thumbnail_token": thumb_token, "browser_supported": ext in {"mp4", "m4v", "webm", "mov"},
            "partial": False, "cached": bool(frame_url), "method": "ffmpeg" if frame_url else "browser",
        }

    token = _video_sample_token(provider, group, segments, media)
    suffix = Path(filename).suffix or ".mp4"
    sample_path = CACHE_DIR / f"{token}.sample{suffix}"
    lock = _preview_build_lock(token)
    with lock:
        if not sample_path.exists() or sample_path.stat().st_size <= 0:
            max_bytes = VIDEO_THUMB_SAMPLE_MB * 1024 * 1024
            written, fetched = _assemble_segments(provider, group, segments, sample_path, max_bytes=max_bytes, max_segments=12, cancel_check=cancel_check)
            if written <= 0:
                raise ValueError("Video sample contained no data")
        else:
            fetched = min(len(segments), 12)
        mime = media.get("mime") or mimetypes.guess_type(filename)[0] or "video/mp4"
        with _preview_lock:
            _preview_tokens[token] = {"path": str(sample_path), "mime": mime, "filename": filename, "created": time.time()}
        frame_url = _try_ffmpeg_frame(sample_path, thumb_token)
        cleanup_preview_cache()
        return {
            "kind": "video", "filename": filename, "sample_url": f"/media/{token}", "thumbnail_url": frame_url,
            "thumbnail_token": thumb_token, "browser_supported": ext in {"mp4", "m4v", "webm", "mov"},
            "partial": fetched < len(segments), "sample_size": sample_path.stat().st_size,
            "cached": bool(frame_url), "method": "ffmpeg" if frame_url else "browser",
        }

def run_preview_task(func, *args):
    def _run():
        try:
            return func(*args)
        finally:
            _arm_preview_worker_idle_close()
    return PREVIEW_EXECUTOR.submit(_run).result()

def cleanup_preview_cache(max_age_hours: int = 12, *, force: bool = False):
    """Rate-limit and background full-preview cache maintenance.

    Gallery browsing can prepare many images in a short burst. Cache expiry is
    housekeeping, not user-visible work, so it must not block those requests.
    """
    global _PREVIEW_CLEANUP_LAST, _PREVIEW_CLEANUP_RUNNING
    now_mono = time.monotonic()
    with _PREVIEW_CLEANUP_LOCK:
        if _PREVIEW_CLEANUP_RUNNING:
            return
        if not force and now_mono - _PREVIEW_CLEANUP_LAST < PREVIEW_CLEANUP_INTERVAL_SECONDS:
            return
        _PREVIEW_CLEANUP_LAST = now_mono
        _PREVIEW_CLEANUP_RUNNING = True

    def _run():
        global _PREVIEW_CLEANUP_RUNNING
        try:
            cutoff = time.time() - max_age_hours * 3600
            expired_paths: set[str] = set()
            with _preview_lock:
                expired = [k for k, v in _preview_tokens.items() if v.get("created", 0) < cutoff]
                for token in expired:
                    item = _preview_tokens.pop(token, None)
                    if item:
                        expired_paths.add(str(item.get("path", "")))
            for raw_path in expired_paths:
                if not raw_path:
                    continue
                try:
                    Path(raw_path).unlink(missing_ok=True)
                except OSError:
                    pass
            try:
                entries = list(os.scandir(CACHE_DIR))
            except OSError:
                entries = []
            for entry in entries:
                try:
                    if not entry.is_file():
                        continue
                    st = entry.stat()
                    if st.st_mtime < cutoff:
                        Path(entry.path).unlink(missing_ok=True)
                except OSError:
                    pass
        finally:
            with _PREVIEW_CLEANUP_LOCK:
                _PREVIEW_CLEANUP_RUNNING = False

    if force:
        _run()
    else:
        threading.Thread(target=_run, name="newzdeck-preview-cache-cleanup", daemon=True).start()

class DownloadCancelled(RuntimeError):
    pass

class PostProcessingCancelled(RuntimeError):
    pass

class GroupSearchManager:
    """Background full-newsgroup header scanner with cancellable, paged results."""

    CHUNK_SIZE = 5000
    MAX_JOBS = 8

    def __init__(self):
        self.lock = threading.RLock()
        self.jobs: dict[str, dict[str, Any]] = {}

    def _public(self, job: dict[str, Any]) -> dict[str, Any]:
        total = max(0, int(job.get("total_headers", 0) or 0))
        scanned = max(0, int(job.get("scanned_headers", 0) or 0))
        pct = 100.0 if total == 0 and job.get("status") == "completed" else (min(100.0, scanned * 100.0 / total) if total else 0.0)
        return {
            "id": job.get("id", ""),
            "provider_id": job.get("provider_id", ""),
            "group": job.get("group", ""),
            "query": job.get("query", ""),
            "filters": dict(job.get("filters") or {}),
            "status": job.get("status", "queued"),
            "low": int(job.get("low", 0) or 0),
            "high": int(job.get("high", 0) or 0),
            "total_headers": total,
            "scanned_headers": scanned,
            "match_headers": int(job.get("match_headers", 0) or 0),
            "match_posts": len(job.get("match_keys", set())),
            "percent": round(pct, 1),
            "started_at": job.get("started_at", 0),
            "completed_at": job.get("completed_at", 0),
            "elapsed_ms": int((time.time() - float(job.get("started_at", time.time()))) * 1000) if job.get("started_at") else 0,
            "error": job.get("error", ""),
        }

    @staticmethod
    def _article_timestamp(article: dict[str, Any]) -> float:
        raw = str(article.get("date") or "").strip()
        if not raw:
            return 0.0
        try:
            dt = email.utils.parsedate_to_datetime(raw)
            return dt.timestamp() if dt else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _match(article: dict[str, Any], query: str, filters: dict[str, Any] | None = None) -> bool:
        filters = filters or {}
        q = str(query or "").strip().casefold()
        media = article.get("media") or {}
        if q:
            haystack = "\n".join(str(v or "") for v in (article.get("subject"), article.get("from"), media.get("filename"), article.get("message_id"))).casefold()
            if q not in haystack:
                return False
        kind = str(filters.get("kind") or "all").lower()
        media_kind = str(media.get("kind") or "")
        if kind == "images" and media_kind != "image": return False
        if kind == "videos" and media_kind != "video": return False
        if kind == "media" and media_kind not in {"image", "video"}: return False
        poster = str(filters.get("poster") or "").strip().casefold()
        if poster and poster not in str(article.get("from") or "").casefold(): return False
        size = max(0, int(article.get("bytes", 0) or 0))
        min_bytes = max(0, int(filters.get("min_bytes", 0) or 0)); max_bytes = max(0, int(filters.get("max_bytes", 0) or 0))
        if min_bytes and size < min_bytes: return False
        if max_bytes and size > max_bytes: return False
        exts = filters.get("extensions") or []
        if isinstance(exts, str): exts = [x.strip().lower().lstrip(".") for x in re.split(r"[,\s]+", exts) if x.strip()]
        if exts and str(media.get("extension") or "").lower().lstrip(".") not in {str(x).lower().lstrip(".") for x in exts}: return False
        age_days = max(0, int(filters.get("age_days", 0) or 0))
        if age_days:
            ts = GroupSearchManager._article_timestamp(article)
            if ts and ts < time.time() - age_days * 86400: return False
        return True

    @staticmethod
    def _logical_key(article: dict[str, Any]) -> str:
        if article.get("multipart") and article.get("media"):
            return "mp|" + normalize_subject(str(article.get("subject", ""))) + "|" + str(article.get("from", "")).casefold()
        return "single|" + str(article.get("message_id") or article.get("article") or "")

    def _prune(self):
        if len(self.jobs) < self.MAX_JOBS:
            return
        candidates = sorted(
            (j for j in self.jobs.values() if j.get("status") in {"completed", "cancelled", "failed"}),
            key=lambda j: float(j.get("completed_at") or j.get("started_at") or 0),
        )
        while len(self.jobs) >= self.MAX_JOBS and candidates:
            old = candidates.pop(0)
            self.jobs.pop(str(old.get("id")), None)

    def start(self, provider_id: str, group: str, query: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        provider_by_id(provider_id)
        group = group.strip(); query = query.strip(); filters = normalize_search_filters(filters)
        if not group: raise ValueError("Newsgroup is required")
        has_filters = any(bool(filters.get(k)) and str(filters.get(k)).lower() not in {"all", "0", "false"} for k in ("kind", "poster", "min_bytes", "max_bytes", "age_days", "extensions"))
        if not query and not has_filters: raise ValueError("Enter search text or choose at least one filter")
        if len(query) > 300: raise ValueError("Search text is too long")
        with self.lock:
            self._prune()
            job_id = secrets.token_hex(10)
            job = {
                "id": job_id, "provider_id": provider_id, "group": group, "query": query, "filters": filters,
                "status": "queued", "low": 0, "high": 0, "total_headers": 0,
                "scanned_headers": 0, "match_headers": 0, "match_keys": set(),
                "matches": [], "grouped_cache": None, "started_at": time.time(), "completed_at": 0, "error": "",
                "cancel_event": threading.Event(),
            }
            self.jobs[job_id] = job
        threading.Thread(target=self._run, args=(job_id,), name=f"group-search-{job_id[:6]}", daemon=True).start()
        return self._public(job)

    def _run(self, job_id: str):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            job["status"] = "scanning"
            provider_id, group, query, filters = job["provider_id"], job["group"], job["query"], dict(job.get("filters") or {})
            cancel_event = job["cancel_event"]
        try:
            provider = provider_by_id(provider_id)
            password = unprotect_secret(provider.get("password_protected", ""))
            client: NntpClient | None = None

            def connect_client() -> NntpClient:
                started = time.perf_counter()
                try:
                    c = NntpClient(provider["host"], provider["port"], bool(provider.get("ssl", True)), provider.get("username", ""), password, timeout=30.0)
                    c.connect(); c.group(group)
                    DIAGNOSTICS.provider_result(provider.get('host',''), int(provider.get('port',563)), ok=True, latency_ms=(time.perf_counter()-started)*1000)
                    return c
                except Exception as exc:
                    DIAGNOSTICS.provider_result(provider.get('host',''), int(provider.get('port',563)), ok=False, error=str(exc))
                    raise

            try:
                client = connect_client()
                info = client.group(group)
                low, high = int(info["low"]), int(info["high"])
                total = max(0, high - low + 1) if int(info.get("count", 0) or 0) > 0 else 0
                with self.lock:
                    job = self.jobs.get(job_id)
                    if not job:
                        return
                    job.update({"low": low, "high": high, "total_headers": total})
                if total <= 0:
                    with self.lock:
                        job["status"] = "completed"
                        job["completed_at"] = time.time()
                    return

                cursor = high
                while cursor >= low:
                    if cancel_event.is_set():
                        with self.lock:
                            job["status"] = "cancelled"
                            job["completed_at"] = time.time()
                        return
                    start = max(low, cursor - self.CHUNK_SIZE + 1)
                    raw: list[dict[str, Any]] | None = None
                    last_error: Exception | None = None
                    for attempt in range(3):
                        try:
                            if client is None:
                                client = connect_client()
                            raw = client.overview(start, cursor)
                            break
                        except Exception as exc:
                            last_error = exc
                            try:
                                if client:
                                    client.close()
                            except Exception:
                                pass
                            client = None
                            if attempt < 2 and not cancel_event.is_set():
                                DIAGNOSTICS.provider_result(provider.get('host',''), int(provider.get('port',563)), ok=False, reconnect=True, error=str(exc))
                                time.sleep(0.3 * (2 ** attempt))
                    if raw is None:
                        raise NntpError(f"Search failed while scanning headers {start}-{cursor}: {last_error}")
                    found = [a for a in raw if self._match(a, query, filters)]
                    with self.lock:
                        job = self.jobs.get(job_id)
                        if not job:
                            return
                        job["matches"].extend(found)
                        job["grouped_cache"] = None
                        job["match_headers"] += len(found)
                        for article in found:
                            job["match_keys"].add(self._logical_key(article))
                        job["scanned_headers"] = min(total, int(job.get("scanned_headers", 0)) + (cursor - start + 1))
                    cursor = start - 1

                with self.lock:
                    job = self.jobs.get(job_id)
                    if job:
                        job["status"] = "completed"
                        job["scanned_headers"] = total
                        job["completed_at"] = time.time()
            finally:
                try:
                    if client:
                        client.close()
                except Exception:
                    pass
        except Exception as exc:
            DIAGNOSTICS.event("error", "search", str(exc), provider_id=provider_id if 'provider_id' in locals() else '', group=group if 'group' in locals() else '')
            with self.lock:
                job = self.jobs.get(job_id)
                if job:
                    if job.get("cancel_event") and job["cancel_event"].is_set():
                        job["status"] = "cancelled"
                    else:
                        job["status"] = "failed"
                        job["error"] = str(exc)
                    job["completed_at"] = time.time()

    def status(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                raise ValueError("Search job not found")
            return self._public(job)

    def cancel(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                raise ValueError("Search job not found")
            if job.get("status") in {"queued", "scanning"}:
                job["cancel_event"].set()
                job["status"] = "cancelling"
            return self._public(job)

    def results(self, job_id: str, page: int, page_size: int) -> dict[str, Any]:
        page = max(1, int(page or 1))
        page_size = max(25, min(2000, int(page_size or DEFAULT_ARTICLE_LIMIT)))
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                raise ValueError("Search job not found")
            public = self._public(job)
            terminal = job.get("status") in {"completed", "cancelled", "failed"}
            cached_grouped = job.get("grouped_cache") if terminal else None
            raw = [] if cached_grouped is not None else list(job.get("matches", []))
        grouped = list(cached_grouped) if cached_grouped is not None else group_articles(raw)
        if terminal and cached_grouped is None:
            with self.lock:
                current = self.jobs.get(job_id)
                if current is not None and current.get("status") in {"completed", "cancelled", "failed"}:
                    current["grouped_cache"] = list(grouped)
        total = len(grouped)
        page_count = max(1, (total + page_size - 1) // page_size) if total else 0
        if page_count:
            page = min(page, page_count)
            start_index = (page - 1) * page_size
            items = grouped[start_index:start_index + page_size]
        else:
            page = 1
            start_index = 0
            items = []
        paging = {
            "mode": "search", "page": page, "page_count": page_count, "page_size": page_size,
            "start": start_index + 1 if total else 0, "end": min(total, start_index + len(items)),
            "low": int(public.get("low", 0)), "high": int(public.get("high", 0)),
            "has_older": bool(page_count and page < page_count), "has_newer": bool(page_count and page > 1),
            "result_count": total,
        }
        return {"articles": items, "paging": paging, "search": public}

def normalize_search_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    f = dict(filters or {}); kind = str(f.get("kind") or "all").lower()
    if kind not in {"all", "images", "videos", "media"}: kind = "all"
    def n(name):
        try: return max(0, int(f.get(name, 0) or 0))
        except Exception: return 0
    exts = f.get("extensions") or []
    if isinstance(exts, str): exts = [x for x in re.split(r"[,\s]+", exts) if x]
    if not isinstance(exts, list): exts = []
    exts = list(dict.fromkeys(str(x).strip().lower().lstrip(".") for x in exts if str(x).strip()))[:30]
    return {"kind": kind, "poster": str(f.get("poster") or "").strip()[:300], "min_bytes": n("min_bytes"), "max_bytes": n("max_bytes"), "age_days": min(36500, n("age_days")), "extensions": exts}

def get_saved_searches() -> list[dict[str, Any]]:
    raw = json_read(SAVED_SEARCHES_FILE, {"items": []})
    return [dict(x) for x in raw.get("items", []) if isinstance(x, dict)] if isinstance(raw, dict) and isinstance(raw.get("items"), list) else []

def saved_search_save(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get("name") or "").strip()[:100]
    if not name: raise ValueError("Saved search name is required")
    items = get_saved_searches(); rid = str(data.get("id") or secrets.token_hex(8)); now = time.time(); old = next((x for x in items if str(x.get("id")) == rid), None)
    rec = {"id": rid, "name": name, "query": str(data.get("query") or "").strip()[:300], "filters": normalize_search_filters(data.get("filters") if isinstance(data.get("filters"), dict) else {}), "created_at": float(old.get("created_at", now)) if old else now, "updated_at": now}
    if old: items[items.index(old)] = rec
    else: items.append(rec)
    items.sort(key=lambda x: str(x.get("name") or "").casefold()); json_write(SAVED_SEARCHES_FILE, {"items": items}); return {"search": rec, "items": items}

def saved_search_delete(rid: str) -> list[dict[str, Any]]:
    items = get_saved_searches(); out = [x for x in items if str(x.get("id")) != str(rid)]
    if len(out) == len(items): raise ValueError("Saved search was not found")
    json_write(SAVED_SEARCHES_FILE, {"items": out}); return out

GROUP_SEARCH_MANAGER = GroupSearchManager()

def _provider_download_capacity(provider: dict[str, Any]) -> tuple[int, int, int]:
    """Return configured, interactive reserve, and download connection budget.

    The provider's Connections field is the overall ceiling. Downloads receive
    almost all of it while a small reserve remains for group browsing/previews.
    Providers dedicated to downloads can use their full configured allowance.
    """
    configured = max(1, min(100, int(provider.get("connections", 20) or 20)))
    interactive = bool(provider.get("use_browsing", True) or provider.get("use_previews", True))
    if not interactive or configured <= 2:
        reserve = 0
    else:
        reserve = max(1, min(4, int(math.ceil(configured * 0.04))))
        reserve = min(reserve, configured - 1)
    return configured, reserve, max(1, configured - reserve)

def _provider_pipeline_depth(provider: dict[str, Any]) -> int:
    """Adaptive articles-per-request target for NNTP pipelining.

    Keep roughly 80 articles in flight across the configured connections while
    avoiding giant per-connection bursts. This mirrors the practical sweet spot
    seen in modern SABnzbd high-speed testing: fewer connections can benefit from
    deeper pipelining, while large connection pools only need depth 2.
    """
    configured = max(1, min(100, int(provider.get("connections", 20) or 20)))
    explicit = int(provider.get("pipeline_depth", 0) or 0)
    if explicit > 0:
        return max(1, min(NNTP_PIPELINE_MAX_DEPTH, explicit))
    return max(2, min(NNTP_PIPELINE_MAX_DEPTH, int(math.ceil(NNTP_PIPELINE_TARGET_INFLIGHT / configured))))

class ProviderDownloadPool:
    """Reusable NNTP connections dedicated to queued downloads for one provider.

    Failures are classified at article-block granularity. Permanent NNTP answers
    such as 423/430 are not pointlessly retried on the same server, while network
    failures use bounded exponential retry. This keeps bad posts from pinning the
    whole queue for minutes at a time.
    """
    def __init__(self, provider: dict[str, Any]):
        self.provider = dict(provider)
        self.key = _provider_connection_key(provider) + (int(provider.get("connections", 20) or 20), int(provider.get("pipeline_depth", 0) or 0))
        configured, reserve, download_capacity = _provider_download_capacity(provider)
        self.configured_connections = configured
        self.interactive_reserve = reserve
        self.max_workers = download_capacity
        self.pipeline_depth = _provider_pipeline_depth(provider)
        self.pipeline_enabled = self.pipeline_depth > 1
        self.pipeline_fallbacks = 0
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix=f"usenet-dl-{provider.get('id','provider')}")
        self.request_slots = threading.BoundedSemaphore(self.max_workers)
        self.local = threading.local()
        self.lock = threading.RLock()
        self.clients: set[NntpClient] = set()
        self.owner_clients: dict[str, set[NntpClient]] = {}
        self.active_requests = 0
        self.closed = False
        self.successful_segments = 0
        self.failed_segments = 0
        self.retry_count = 0
        self.bytes_decoded = 0
        self.bytes_wire_received = 0
        self.last_error = ""
        self.last_error_ts = 0.0
        self.consecutive_failures = 0
        # Treat the configured connection count as the hard ceiling. Large pools
        # begin at a conservative high-throughput target and ramp only when live
        # measurements show a real gain. This prevents a 50-60 connection profile
        # from being slower than a 20-30 connection profile on the same provider.
        self.target_workers = min(self.max_workers, NNTP_AUTOTUNE_START_CONNECTIONS if self.max_workers >= 32 else self.max_workers)
        self.tune_lock = threading.RLock()
        self.tune_last_ts = 0.0
        self.tune_last_speed = 0
        self.tune_last_bytes = 0
        self.tune_last_target = self.target_workers
        self.tune_locked_target = 0
        self.tune_samples = 0

    def effective_capacity(self) -> int:
        with self.tune_lock:
            return max(1, min(self.max_workers, int(self.target_workers or self.max_workers)))

    def effective_pipeline_depth(self) -> int:
        """Keep roughly the target number of BODY commands in flight.

        When autotuning intentionally uses fewer sockets, a slightly deeper NNTP
        pipeline hides article-to-article RTT without recreating a huge thread pool.
        An explicit provider pipeline setting always wins.
        """
        if not self.pipeline_enabled:
            return 1
        explicit = max(0, int(self.provider.get("pipeline_depth", 0) or 0))
        if explicit > 0:
            return max(1, min(NNTP_PIPELINE_MAX_DEPTH, explicit))
        capacity = self.effective_capacity()
        return max(2, min(NNTP_PIPELINE_MAX_DEPTH, int(math.ceil(NNTP_PIPELINE_TARGET_INFLIGHT / max(1, capacity)))))

    def observe_speed(self, speed_bps: int = 0) -> int:
        """Adapt active socket count from measured NNTP wire throughput.

        The v3.4.15 queue separates BODY acquisition from yEnc decoding, so socket
        tuning must follow bytes received from the provider rather than decoder
        completion. This avoids mistaking decoder backlog for a slow provider.
        """
        now = time.monotonic()
        wire_now = max(0, int(self.bytes_wire_received or 0))
        with self.tune_lock:
            if self.max_workers < 32:
                return self.effective_capacity()
            if self.tune_last_ts > 0 and now - self.tune_last_ts >= NNTP_AUTOTUNE_RESET_SECONDS:
                # A later download gets a fresh measurement window instead of
                # inheriting a stale decision made under different network load.
                self.target_workers = min(self.max_workers, NNTP_AUTOTUNE_START_CONNECTIONS)
                self.tune_last_ts = 0.0
                self.tune_last_speed = 0
                self.tune_last_bytes = wire_now
                self.tune_last_target = self.target_workers
                self.tune_locked_target = 0
                self.tune_samples = 0
            if self.tune_locked_target:
                return self.effective_capacity()
            if self.tune_last_ts <= 0:
                self.tune_last_ts = now
                self.tune_last_bytes = wire_now
                return self.effective_capacity()
            interval = now - self.tune_last_ts
            if interval < NNTP_AUTOTUNE_SAMPLE_SECONDS:
                return self.effective_capacity()
            delta = max(0, wire_now - self.tune_last_bytes)
            speed = int(delta / max(0.001, interval)) if delta > 0 else max(0, int(speed_bps or 0))
            current = self.effective_capacity()
            self.tune_last_ts = now
            self.tune_last_bytes = wire_now
            if speed <= 0:
                return current
            self.tune_samples += 1
            if self.tune_last_speed <= 0:
                self.tune_last_speed = speed
                self.tune_last_target = current
                if current < self.max_workers:
                    self.target_workers = min(self.max_workers, current + NNTP_AUTOTUNE_STEP_CONNECTIONS)
                return self.effective_capacity()
            previous_speed = self.tune_last_speed
            previous_target = self.tune_last_target
            gain = (speed - previous_speed) / max(1, previous_speed)
            if speed < previous_speed * (1.0 - NNTP_AUTOTUNE_REGRESSION):
                self.target_workers = previous_target
                self.tune_locked_target = previous_target
            elif gain >= NNTP_AUTOTUNE_MIN_GAIN and current < self.max_workers:
                self.tune_last_speed = speed
                self.tune_last_target = current
                self.target_workers = min(self.max_workers, current + NNTP_AUTOTUNE_STEP_CONNECTIONS)
            else:
                if current > previous_target:
                    self.target_workers = previous_target
                    self.tune_locked_target = previous_target
                else:
                    self.tune_locked_target = current
            return self.effective_capacity()

    def _close_local(self) -> None:
        holder = getattr(self.local, "holder", None)
        if holder and holder.get("client"):
            client = holder["client"]
            try:
                client.close()
            except Exception:
                pass
            with self.lock:
                self.clients.discard(client)
        self.local.holder = None

    def _client(self, group: str, force_reconnect: bool = False) -> NntpClient:
        if self.closed:
            raise NntpError("Download connection pool is closed")
        holder = getattr(self.local, "holder", None)
        now = time.monotonic()
        stale = bool(holder and now - float(holder.get("last_used", now)) > 120)
        disconnected = bool(holder and not holder.get("client").is_connected())
        if force_reconnect or stale or disconnected or not holder:
            self._close_local()
            p = self.provider
            password = unprotect_secret(p.get("password_protected", ""))
            client = NntpClient(
                p["host"], p["port"], bool(p.get("ssl", True)), p.get("username", ""), password,
                timeout=25.0, probe_capabilities=False,
            )
            client.connect()
            holder = {"client": client, "group": "", "last_used": now}
            self.local.holder = holder
            with self.lock:
                self.clients.add(client)
        client = holder["client"]
        if group and holder.get("group") != group:
            try:
                client.group(group)
            except Exception:
                if force_reconnect:
                    raise
                return self._client(group, force_reconnect=True)
            holder["group"] = group
        holder["last_used"] = now
        return client

    def fetch_to_file(self, group: str, segment: dict[str, Any], output_path: Path,
                      cancel_event: threading.Event | None = None, owner_id: str = "",
                      progress_callback=None) -> dict[str, Any]:
        """Retrieve one segment with bounded retries and true cooperative cancellation.

        The old implementation buffered BODY into RAM and could remain stuck in a
        socket read after the queue item had been cancelled.  This version streams
        yEnc straight to scratch, tracks which live socket belongs to which job, and
        allows Cancel/Stop All to abort that socket immediately.
        """
        last_exc: Exception | None = None
        attempt_log: list[dict[str, Any]] = []
        max_attempts = 2
        provider_name = self.provider.get("name") or self.provider.get("host") or "Provider"

        def check_cancel():
            if cancel_event is not None and cancel_event.is_set():
                raise DownloadCancelled()
            if self.closed:
                raise DownloadCancelled()

        with self.request_slots:
            for attempt in range(max_attempts):
                check_cancel()
                with self.lock:
                    self.active_requests += 1
                    if attempt:
                        self.retry_count += 1
                started = time.perf_counter()
                client = None
                try:
                    direct_message_id = bool(segment.get("message_id")) and not (segment.get("article") is not None and str(segment.get("article")).strip())
                    client = self._client("" if direct_message_id else group, force_reconnect=attempt > 0)
                    if owner_id:
                        with self.lock:
                            self.owner_clients.setdefault(owner_id, set()).add(client)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.unlink(missing_ok=True)
                    with output_path.open("wb") as out:
                        written, meta = retrieve_segment_into_file(
                            client, segment, out, cancel_check=check_cancel,
                            progress_callback=progress_callback, apply_part_offset=False,
                        )
                    check_cancel()
                    if written <= 0:
                        raise NntpError("Decoded article block is empty")
                    if meta.get("encoding") == "yenc":
                        begin = int(meta.get("begin", 0) or 0)
                        end = int(meta.get("end", 0) or 0)
                        expected_part_size = (end - begin + 1) if begin > 0 and end >= begin else int(meta.get("end_size", 0) or 0)
                        if expected_part_size and expected_part_size != written:
                            raise NntpError(f"Decoded yEnc segment is truncated: expected {expected_part_size:,} bytes, received {written:,}")
                        expected_crc = str(meta.get("pcrc32") or "").lower()
                        if expected_crc:
                            crc = 0
                            with output_path.open("rb") as verify:
                                while True:
                                    check_cancel()
                                    chunk = verify.read(1024 * 1024)
                                    if not chunk:
                                        break
                                    crc = zlib.crc32(chunk, crc)
                            actual_crc = f"{crc & 0xffffffff:08x}"
                            if actual_crc != expected_crc:
                                raise NntpError(f"yEnc CRC mismatch: expected {expected_crc}, received {actual_crc}")
                    wire_bytes = max(0, int(segment.get("bytes", 0) or 0)) or written
                    latency = (time.perf_counter() - started) * 1000
                    with self.lock:
                        self.successful_segments += 1
                        self.bytes_decoded += written
                        self.last_error = ""
                        self.consecutive_failures = 0
                    DIAGNOSTICS.provider_result(self.provider.get('host',''), int(self.provider.get('port',563)), ok=True, latency_ms=latency, bytes_count=written, reconnect=attempt > 0)
                    return {"meta": meta, "wire_bytes": wire_bytes, "decoded_bytes": written, "path": str(output_path), "attempts": attempt + 1, "attempt_log": attempt_log}
                except DownloadCancelled:
                    output_path.unlink(missing_ok=True)
                    raise
                except (NntpError, socket.error, ssl.SSLError, OSError) as exc:
                    last_exc = exc
                    failure = classify_nntp_failure(exc)
                    elapsed_ms = int((time.perf_counter() - started) * 1000)
                    attempt_log.append({
                        "provider": provider_name,
                        "provider_id": str(self.provider.get("id", "")),
                        "attempt": attempt + 1,
                        "code": failure["code"],
                        "label": failure["label"],
                        "error": failure["raw"][:1000],
                        "retryable": bool(failure["retryable"]),
                        "status": int(failure.get("status", 0) or 0),
                        "elapsed_ms": elapsed_ms,
                        "ts": time.time(),
                    })
                    self._close_local()
                    output_path.unlink(missing_ok=True)
                    with self.lock:
                        self.last_error = str(exc)
                        self.last_error_ts = time.time()
                        self.consecutive_failures += 1
                    DIAGNOSTICS.provider_result(self.provider.get('host',''), int(self.provider.get('port',563)), ok=False, reconnect=attempt > 0, error=str(exc))
                    check_cancel()
                    nzb_missing_retry = (
                        failure.get("code") == "article_missing"
                        and str(segment.get("source") or "") == "nzb"
                        and bool(segment.get("message_id"))
                        and attempt + 1 < max_attempts
                    )
                    if not failure["retryable"] and not nzb_missing_retry:
                        break
                    if attempt + 1 < max_attempts:
                        if cancel_event is not None and cancel_event.wait(0.35 * (2 ** attempt)):
                            raise DownloadCancelled()
                        continue
                    break
                finally:
                    if client is not None and owner_id:
                        with self.lock:
                            owners = self.owner_clients.get(owner_id)
                            if owners is not None:
                                owners.discard(client)
                                if not owners:
                                    self.owner_clients.pop(owner_id, None)
                    with self.lock:
                        self.active_requests = max(0, self.active_requests - 1)

        with self.lock:
            self.failed_segments += 1
        final = classify_nntp_failure(last_exc or NntpError("Could not retrieve download segment"))
        DIAGNOSTICS.event('error', 'download', f"Segment failed: {final['label']}: {final['raw']}", provider=provider_name, group=group, article=segment.get('article'), message_id=segment.get('message_id'))
        raise SegmentFetchError(
            f"{final['label']}: {final['raw']}",
            code=final["code"], label=final["label"], retryable=bool(final["retryable"]),
            suggestion=final["suggestion"], attempts=attempt_log,
        ) from last_exc

    def fetch_batch_raw(self, group: str, segments: list[dict[str, Any]],
                        cancel_event: threading.Event | None = None, owner_id: str = "",
                        progress_callback=None) -> list[dict[str, Any]]:
        """Fetch article BODY payloads without decoding them on the NNTP worker.

        This is the queued-download fast path. Keeping raw network acquisition
        separate from yEnc decode means a warm NNTP worker can immediately pick up
        the next batch rather than idling its socket behind decoder/process-pipe
        work. Per-article status failures are returned for normal recovery logic.
        """
        if not segments:
            return []

        def check_cancel():
            if cancel_event is not None and cancel_event.is_set():
                raise DownloadCancelled()
            if self.closed:
                raise DownloadCancelled()

        with self.request_slots:
            check_cancel()
            with self.lock:
                self.active_requests += 1
            client = None
            started = time.perf_counter()
            pipelined = bool(self.pipeline_enabled and len(segments) > 1)
            try:
                direct_ids = all(
                    bool(seg.get("message_id"))
                    and not (seg.get("article") is not None and str(seg.get("article")).strip())
                    for seg in segments
                )
                client = self._client("" if direct_ids else group)
                if owner_id:
                    with self.lock:
                        self.owner_clients.setdefault(owner_id, set()).add(client)

                targets: list[int | str] = []
                for seg in segments:
                    article = seg.get("article")
                    mid = str(seg.get("message_id", "") or "").strip()
                    if article is not None and str(article).strip():
                        targets.append(int(article))
                    elif mid:
                        targets.append(mid)
                    else:
                        raise NntpError("Article segment has no retrievable article number or Message-ID")

                if pipelined:
                    raw_results = client.body_raw_pipelined(
                        targets, cancel_check=check_cancel, progress_callback=progress_callback
                    )
                else:
                    raw_results = []
                    for pos, target in enumerate(targets):
                        check_cancel()
                        cb = (
                            (lambda amount, p=pos: progress_callback(p, amount))
                            if progress_callback is not None else None
                        )
                        try:
                            raw = client.body_raw(target, cancel_check=check_cancel, progress_callback=cb)
                            raw_results.append({"ok": True, "article": target, "raw": raw})
                        except Exception as exc:
                            raw_results.append({"ok": False, "article": target, "error": exc})

                network_elapsed = max(0.0, time.perf_counter() - started)
                network_share = network_elapsed / max(1, len(segments))
                output: list[dict[str, Any]] = []
                for seg, raw_rec in zip(segments, raw_results):
                    if not raw_rec.get("ok"):
                        output.append({
                            "ok": False,
                            "error": raw_rec.get("error") or NntpError("Article BODY request failed"),
                        })
                        continue
                    raw = bytes(raw_rec.get("raw") or b"")
                    if not raw:
                        output.append({"ok": False, "error": NntpError("Article BODY response was empty")})
                        continue
                    wire_bytes = max(0, int(seg.get("bytes", 0) or 0)) or len(raw)
                    output.append({
                        "ok": True,
                        "result": {
                            "raw": raw,
                            "wire_bytes": wire_bytes,
                            "attempts": 1,
                            "attempt_log": [],
                            "pipelined": pipelined,
                            "network_seconds": network_share,
                        },
                    })
                wire_total = sum(
                    max(0, int((rec.get("result") or {}).get("wire_bytes", 0) or 0))
                    for rec in output if rec.get("ok")
                )
                if wire_total:
                    with self.lock:
                        self.bytes_wire_received += wire_total
                return output
            except DownloadCancelled:
                raise
            except Exception:
                self._close_local()
                if pipelined:
                    with self.lock:
                        self.pipeline_fallbacks += 1
                        # A provider/proxy that cannot safely pipeline should not
                        # keep paying the framing penalty for this pool session.
                        self.pipeline_enabled = False
                raise
            finally:
                if client is not None and owner_id:
                    with self.lock:
                        owners = self.owner_clients.get(owner_id)
                        if owners is not None:
                            owners.discard(client)
                            if not owners:
                                self.owner_clients.pop(owner_id, None)
                with self.lock:
                    self.active_requests = max(0, self.active_requests - 1)

    def decode_raw_result(self, segment: dict[str, Any], raw_result: dict[str, Any]) -> dict[str, Any]:
        """Decode one already-downloaded BODY outside the NNTP worker pool."""
        raw = bytes(raw_result.get("raw") or b"")
        if not raw:
            raise NntpError("Article BODY response was empty")
        data, meta, perf = decode_raw_binary_article(raw)
        perf["raw_body_bytes"] = len(raw)
        perf["network_seconds"] = float(raw_result.get("network_seconds", 0.0) or 0.0)
        wire_bytes = max(0, int(raw_result.get("wire_bytes", 0) or 0)) or len(raw) or len(data)
        result = {
            "data": data,
            "meta": meta,
            "wire_bytes": wire_bytes,
            "decoded_bytes": len(data),
            "attempts": max(1, int(raw_result.get("attempts", 1) or 1)),
            "attempt_log": list(raw_result.get("attempt_log") or []),
            "perf": perf,
            "pipelined": bool(raw_result.get("pipelined", False)),
        }
        with self.lock:
            self.successful_segments += 1
            self.bytes_decoded += len(data)
            self.last_error = ""
            self.consecutive_failures = 0
        return result

    def fetch_batch_to_memory(self, group: str, segments: list[dict[str, Any]],
                              cancel_event: threading.Event | None = None, owner_id: str = "",
                              progress_callback=None) -> list[dict[str, Any]]:
        """Compatibility wrapper that fetches raw BODY data and then decodes it.

        The main queue uses the decoupled network/decode pipeline below; this
        wrapper preserves the older API for tests/extensions and recovery paths.
        """
        raw_records = self.fetch_batch_raw(
            group, segments, cancel_event=cancel_event, owner_id=owner_id,
            progress_callback=progress_callback,
        )
        output: list[dict[str, Any]] = []
        for seg, rec in zip(segments, raw_records):
            if not rec.get("ok"):
                output.append({"ok": False, "error": rec.get("error") or NntpError("Article BODY request failed")})
                continue
            try:
                output.append({"ok": True, "result": self.decode_raw_result(seg, dict(rec.get("result") or {}))})
            except Exception as exc:
                output.append({"ok": False, "error": exc})
        return output

    def fetch_to_memory(self, group: str, segment: dict[str, Any],
                        cancel_event: threading.Event | None = None, owner_id: str = "",
                        progress_callback=None) -> dict[str, Any]:
        """High-throughput in-memory article fetch used by the v1.4 queue.

        Warm NNTP sockets are reused. NZB Message-ID misses get one additional
        clean-connection probe before recovery providers are tried. This preserves
        protection against uneven provider backends without multiplying a missing
        file into thousands of redundant requests.
        """
        last_exc: Exception | None = None
        attempt_log: list[dict[str, Any]] = []
        is_nzb_id = str(segment.get("source") or "") == "nzb" and bool(segment.get("message_id"))
        max_attempts = NZB_MISSING_PROVIDER_ATTEMPTS if is_nzb_id else 2
        provider_name = self.provider.get("name") or self.provider.get("host") or "Provider"

        def check_cancel():
            if cancel_event is not None and cancel_event.is_set():
                raise DownloadCancelled()
            if self.closed:
                raise DownloadCancelled()

        with self.request_slots:
            for attempt in range(max_attempts):
                check_cancel()
                with self.lock:
                    self.active_requests += 1
                    if attempt:
                        self.retry_count += 1
                started = time.perf_counter()
                client = None
                try:
                    direct_message_id = bool(segment.get("message_id")) and not (segment.get("article") is not None and str(segment.get("article")).strip())
                    client = self._client("" if direct_message_id else group, force_reconnect=attempt > 0)
                    if owner_id:
                        with self.lock:
                            self.owner_clients.setdefault(owner_id, set()).add(client)
                    data, meta, perf = retrieve_segment_into_memory(
                        client, segment, cancel_check=check_cancel, progress_callback=progress_callback,
                    )
                    check_cancel()
                    if not data:
                        raise NntpError("Decoded article block is empty")
                    wire_bytes = max(0, int(segment.get("bytes", 0) or 0)) or int(perf.get("raw_body_bytes", 0) or 0) or len(data)
                    latency = (time.perf_counter() - started) * 1000
                    with self.lock:
                        self.successful_segments += 1
                        self.bytes_decoded += len(data)
                        self.last_error = ""
                        self.consecutive_failures = 0
                    DIAGNOSTICS.provider_result(self.provider.get('host',''), int(self.provider.get('port',563)), ok=True, latency_ms=latency, bytes_count=len(data), reconnect=attempt > 0)
                    return {
                        "data": data, "meta": meta, "wire_bytes": wire_bytes, "decoded_bytes": len(data),
                        "attempts": attempt + 1, "attempt_log": attempt_log, "perf": perf,
                    }
                except DownloadCancelled:
                    raise
                except (NntpError, socket.error, ssl.SSLError, OSError) as exc:
                    last_exc = exc
                    failure = classify_nntp_failure(exc)
                    elapsed_ms = int((time.perf_counter() - started) * 1000)
                    attempt_log.append({
                        "provider": provider_name, "provider_id": str(self.provider.get("id", "")),
                        "attempt": attempt + 1, "code": failure["code"], "label": failure["label"],
                        "error": failure["raw"][:1000], "retryable": bool(failure["retryable"]),
                        "status": int(failure.get("status", 0) or 0), "elapsed_ms": elapsed_ms, "ts": time.time(),
                    })
                    self._close_local()
                    with self.lock:
                        self.last_error = str(exc)
                        self.last_error_ts = time.time()
                        self.consecutive_failures += 1
                    DIAGNOSTICS.provider_result(self.provider.get('host',''), int(self.provider.get('port',563)), ok=False, reconnect=attempt > 0, error=str(exc))
                    check_cancel()
                    missing_probe = failure.get("code") == "article_missing" and is_nzb_id and attempt + 1 < max_attempts
                    if not failure["retryable"] and not missing_probe:
                        break
                    if attempt + 1 < max_attempts:
                        delay = (0.08, 0.15, 0.25, 0.40)[min(attempt, 3)]
                        if cancel_event is not None and cancel_event.wait(delay):
                            raise DownloadCancelled()
                        continue
                    break
                finally:
                    if client is not None and owner_id:
                        with self.lock:
                            owners = self.owner_clients.get(owner_id)
                            if owners is not None:
                                owners.discard(client)
                                if not owners:
                                    self.owner_clients.pop(owner_id, None)
                    with self.lock:
                        self.active_requests = max(0, self.active_requests - 1)

        with self.lock:
            self.failed_segments += 1
        final = classify_nntp_failure(last_exc or NntpError("Could not retrieve download segment"))
        DIAGNOSTICS.event('error', 'download', f"Segment failed: {final['label']}: {final['raw']}", provider=provider_name, group=group, article=segment.get('article'), message_id=segment.get('message_id'))
        raise SegmentFetchError(
            f"{final['label']}: {final['raw']}", code=final["code"], label=final["label"],
            retryable=bool(final["retryable"]), suggestion=final["suggestion"], attempts=attempt_log,
        ) from last_exc

    def abort_owner(self, owner_id: str) -> int:
        """Break live socket reads belonging to one download without blocking."""
        with self.lock:
            clients = list(self.owner_clients.get(str(owner_id), set()))
        for client in clients:
            try:
                client.abort()
            except Exception:
                pass
        return len(clients)

    def abort_all(self) -> int:
        with self.lock:
            clients = list(self.clients)
        for client in clients:
            try:
                client.abort()
            except Exception:
                pass
        return len(clients)

    def stats(self) -> dict[str, Any]:
        with self.lock:
            return {"active": self.active_requests, "open": len(self.clients), "capacity": self.max_workers,
                    "effective_capacity": self.effective_capacity(), "autotune_locked": bool(self.tune_locked_target),
                    "configured": self.configured_connections, "interactive_reserve": self.interactive_reserve,
                    "pipeline_depth": self.effective_pipeline_depth(), "pipeline_enabled": self.pipeline_enabled, "pipeline_fallbacks": self.pipeline_fallbacks,
                    "successful_segments": self.successful_segments, "failed_segments": self.failed_segments,
                    "retries": self.retry_count, "bytes_decoded": self.bytes_decoded,
                    "bytes_wire_received": self.bytes_wire_received,
                    "last_error": self.last_error, "last_error_ts": self.last_error_ts,
                    "consecutive_failures": self.consecutive_failures}

    def shutdown(self) -> None:
        self.closed = True
        self.abort_all()
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            self.executor.shutdown(wait=False)
        with self.lock:
            self.clients.clear()
            self.owner_clients.clear()

_DOWNLOAD_POOLS_LOCK = threading.RLock()
_DOWNLOAD_POOLS: dict[str, ProviderDownloadPool] = {}

def get_download_pool(provider: dict[str, Any]) -> ProviderDownloadPool:
    provider_id = str(provider.get("id") or provider.get("host") or "provider")
    key = _provider_connection_key(provider) + (int(provider.get("connections", 20) or 20), int(provider.get("pipeline_depth", 0) or 0))
    with _DOWNLOAD_POOLS_LOCK:
        current = _DOWNLOAD_POOLS.get(provider_id)
        if current and current.key == key and not current.closed:
            return current
        if current:
            current.shutdown()
        current = ProviderDownloadPool(provider)
        _DOWNLOAD_POOLS[provider_id] = current
        return current

def download_pool_stats() -> dict[str, Any]:
    yenc = NATIVE_YENC_POOL.stats()
    result: dict[str, Any] = {
        "active": 0, "open": 0, "capacity": 0, "effective_capacity": 0, "configured": 0, "interactive_reserve": 0,
        "successful_segments": 0, "failed_segments": 0, "retries": 0, "bytes_decoded": 0, "bytes_wire_received": 0,
        "pipeline_depth": 1, "pipeline_fallbacks": 0, "pipeline_enabled": False,
        "pools": [], "yenc": yenc,
    }
    with _DOWNLOAD_POOLS_LOCK:
        pools = list(_DOWNLOAD_POOLS.values())
    for pool in pools:
        st = pool.stats()
        for key in ("active", "open", "capacity", "effective_capacity", "configured", "interactive_reserve", "successful_segments", "failed_segments", "retries", "bytes_decoded", "bytes_wire_received"):
            result[key] += int(st.get(key, 0) or 0)
        effective_depth = int(st.get("pipeline_depth", 1) or 1) if st.get("pipeline_enabled", False) else 1
        result["pipeline_depth"] = max(int(result["pipeline_depth"]), effective_depth)
        result["pipeline_fallbacks"] += int(st.get("pipeline_fallbacks", 0) or 0)
        result["pipeline_enabled"] = bool(result["pipeline_enabled"] or effective_depth > 1)
        result["pools"].append({"provider_id": pool.provider.get("id", ""), "provider_name": pool.provider.get("name") or pool.provider.get("host", "Provider"), **st})
    return result

def shutdown_download_pools() -> None:
    with _DOWNLOAD_POOLS_LOCK:
        pools = list(_DOWNLOAD_POOLS.values())
        _DOWNLOAD_POOLS.clear()
    for pool in pools:
        pool.shutdown()

def abort_download_jobs(job_ids: list[str] | set[str] | tuple[str, ...]) -> int:
    ids = {str(x) for x in job_ids if str(x)}
    if not ids:
        return 0
    with _DOWNLOAD_POOLS_LOCK:
        pools = list(_DOWNLOAD_POOLS.values())
    aborted = 0
    for pool in pools:
        for job_id in ids:
            aborted += pool.abort_owner(job_id)
    return aborted

def fetch_segment_with_recovery(primary_provider: dict[str, Any], group: str, segment: dict[str, Any], output_path: Path, cancel_event: threading.Event | None = None, owner_id: str = "", progress_callback=None) -> dict[str, Any]:
    """Fetch one block, then recover it by Message-ID from configured backups.

    Provider failures are retained so the UI can explain exactly what happened.
    Recovery is attempted immediately for permanent missing-article replies instead
    of repeating the same request against the same server.
    """
    provider_attempts: list[dict[str, Any]] = []
    primary_pool = get_download_pool(primary_provider)
    try:
        result = primary_pool.fetch_to_file(group, segment, output_path, cancel_event=cancel_event, owner_id=owner_id, progress_callback=progress_callback)
        result["provider_id"] = str(primary_provider.get("id", ""))
        result["provider_name"] = primary_provider.get("name") or primary_provider.get("host") or "Provider"
        result["recovered"] = False
        result["provider_attempts"] = list(result.get("attempt_log") or [])
        return result
    except DownloadCancelled:
        raise
    except SegmentFetchError as primary_exc:
        provider_attempts.extend(primary_exc.attempts)
        primary_failure = primary_exc
    except Exception as primary_exc_raw:
        info = classify_nntp_failure(primary_exc_raw)
        provider_attempts.append({"provider": primary_provider.get("name") or primary_provider.get("host") or "Provider", "provider_id": str(primary_provider.get("id", "")), "attempt": 1, "code": info["code"], "label": info["label"], "error": info["raw"], "retryable": info["retryable"], "status": info.get("status", 0), "ts": time.time()})
        primary_failure = SegmentFetchError(str(primary_exc_raw), code=info["code"], label=info["label"], retryable=info["retryable"], suggestion=info["suggestion"], attempts=provider_attempts)

    if cancel_event is not None and cancel_event.is_set():
        raise DownloadCancelled()
    message_id = str(segment.get("message_id", "") or "").strip()
    backups = providers_for_purpose("recovery", exclude_id=str(primary_provider.get("id", ""))) if message_id else []
    if message_id:
        for backup in backups:
            recovery_segment = dict(segment)
            recovery_segment["article"] = None
            try:
                backup_pool = get_download_pool(backup)
                if cancel_event is not None and cancel_event.is_set():
                    raise DownloadCancelled()
                result = backup_pool.fetch_to_file(group, recovery_segment, output_path, cancel_event=cancel_event, owner_id=owner_id, progress_callback=progress_callback)
                provider_attempts.extend(result.get("attempt_log") or [])
                result["provider_id"] = str(backup.get("id", ""))
                result["provider_name"] = backup.get("name") or backup.get("host") or "Recovery provider"
                result["recovered"] = True
                result["provider_attempts"] = provider_attempts
                DIAGNOSTICS.event("info", "recovery", f"Recovered missing segment from {result['provider_name']}", group=group, message_id=message_id)
                return result
            except DownloadCancelled:
                output_path.unlink(missing_ok=True)
                raise
            except SegmentFetchError as exc:
                output_path.unlink(missing_ok=True)
                provider_attempts.extend(exc.attempts)
                continue
            except Exception as exc:
                output_path.unlink(missing_ok=True)
                info = classify_nntp_failure(exc)
                provider_attempts.append({"provider": backup.get("name") or backup.get("host") or "Recovery provider", "provider_id": str(backup.get("id", "")), "attempt": 1, "code": info["code"], "label": info["label"], "error": info["raw"], "retryable": info["retryable"], "status": info.get("status", 0), "ts": time.time()})
                continue

    codes = [str(a.get("code") or "") for a in provider_attempts]
    retryable = bool(provider_attempts) and all(bool(a.get("retryable")) for a in provider_attempts)
    if "authentication" in codes:
        code, label, suggestion = "authentication", "Provider authentication failed", "Verify credentials for the provider reporting the authentication error."
        retryable = False
    elif "permission" in codes:
        code, label, suggestion = "permission", "Provider access denied", "The provider denied access to the article or group. Check account/server access."
        retryable = False
    elif "article_missing" in codes:
        posted_ts = max(0, int(segment.get("posted_ts", 0) or 0))
        age = max(0.0, time.time() - posted_ts) if posted_ts else 0.0
        recent_nzb = str(segment.get("source") or "") == "nzb" and posted_ts > 0 and age < 3 * 60 * 60
        if recent_nzb:
            code, label = "article_propagating", "Article block not propagated yet"
            suggestion = "This NZB is very recent. NewzDeck will retry only the unavailable blocks while preserving everything already downloaded."
            retryable = True
        else:
            code, label = "article_missing", "Article block missing on all providers tried"
            if not message_id:
                suggestion = "This item has no Message-ID, so NewzDeck cannot recover the missing block from another provider."
            elif not backups:
                suggestion = "Configure a secondary provider with Missing-segment recovery enabled, or retry later if the post is still propagating."
            else:
                suggestion = "The block was not available from the primary or configured recovery providers. It may be outside retention, removed, or not fully propagated."
            retryable = False
    elif "integrity" in codes:
        code, label, suggestion = "integrity", "Article block failed integrity checks", "The block was corrupt after retries. A different recovery provider may have a clean copy."
    else:
        code = primary_failure.code or "segment_failed"
        label = primary_failure.label or "Article block failed"
        suggestion = primary_failure.suggestion or "Retry is safe; completed blocks are preserved."

    tried = []
    for attempt in provider_attempts:
        name = str(attempt.get("provider") or "Provider")
        if name not in tried:
            tried.append(name)
    provider_text = ", ".join(tried) if tried else (primary_provider.get("name") or primary_provider.get("host") or "provider")
    raise SegmentFetchError(
        f"{label}. Providers tried: {provider_text}.",
        code=code, label=label, retryable=retryable, suggestion=suggestion, attempts=provider_attempts,
    ) from primary_failure

def fetch_segment_with_recovery_memory(primary_provider: dict[str, Any], group: str, segment: dict[str, Any], cancel_event: threading.Event | None = None, owner_id: str = "", progress_callback=None) -> dict[str, Any]:
    """High-throughput recovery path returning one decoded block in memory."""
    def pool_fetch(pool, provider_obj, target_segment):
        if hasattr(pool, "fetch_to_memory"):
            return pool.fetch_to_memory(group, target_segment, cancel_event=cancel_event, owner_id=owner_id, progress_callback=progress_callback)
        compat = DOWNLOAD_TEMP_DIR / f".v140-compat-{threading.get_ident()}-{secrets.token_hex(4)}.seg"
        compat.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = pool.fetch_to_file(group, target_segment, compat, cancel_event=cancel_event, owner_id=owner_id, progress_callback=progress_callback)
            data = compat.read_bytes()
            result = dict(result)
            result["data"] = data
            result["decoded_bytes"] = len(data)
            result.setdefault("perf", {"raw_body_bytes": int(result.get("wire_bytes", 0) or len(data)), "network_seconds": 0.0, "decode_seconds": 0.0, "native_decode": False})
            return result
        finally:
            compat.unlink(missing_ok=True)

    provider_attempts: list[dict[str, Any]] = []
    primary_pool = get_download_pool(primary_provider)
    try:
        result = pool_fetch(primary_pool, primary_provider, segment)
        result["provider_id"] = str(primary_provider.get("id", ""))
        result["provider_name"] = primary_provider.get("name") or primary_provider.get("host") or "Provider"
        result["recovered"] = False
        result["provider_attempts"] = list(result.get("attempt_log") or [])
        return result
    except DownloadCancelled:
        raise
    except SegmentFetchError as primary_exc:
        provider_attempts.extend(primary_exc.attempts)
        primary_failure = primary_exc
    except Exception as primary_exc_raw:
        info = classify_nntp_failure(primary_exc_raw)
        provider_attempts.append({"provider": primary_provider.get("name") or primary_provider.get("host") or "Provider", "provider_id": str(primary_provider.get("id", "")), "attempt": 1, "code": info["code"], "label": info["label"], "error": info["raw"], "retryable": info["retryable"], "status": info.get("status", 0), "ts": time.time()})
        primary_failure = SegmentFetchError(str(primary_exc_raw), code=info["code"], label=info["label"], retryable=info["retryable"], suggestion=info["suggestion"], attempts=provider_attempts)

    if cancel_event is not None and cancel_event.is_set():
        raise DownloadCancelled()
    message_id = str(segment.get("message_id", "") or "").strip()
    backups = providers_for_purpose("recovery", exclude_id=str(primary_provider.get("id", ""))) if message_id else []
    if message_id:
        for backup in backups:
            recovery_segment = dict(segment)
            recovery_segment["article"] = None
            try:
                backup_pool = get_download_pool(backup)
                if cancel_event is not None and cancel_event.is_set():
                    raise DownloadCancelled()
                result = pool_fetch(backup_pool, backup, recovery_segment)
                provider_attempts.extend(result.get("attempt_log") or [])
                result["provider_id"] = str(backup.get("id", ""))
                result["provider_name"] = backup.get("name") or backup.get("host") or "Recovery provider"
                result["recovered"] = True
                result["provider_attempts"] = provider_attempts
                DIAGNOSTICS.event("info", "recovery", f"Recovered missing segment from {result['provider_name']}", group=group, message_id=message_id)
                return result
            except DownloadCancelled:
                raise
            except SegmentFetchError as exc:
                provider_attempts.extend(exc.attempts)
                continue
            except Exception as exc:
                info = classify_nntp_failure(exc)
                provider_attempts.append({"provider": backup.get("name") or backup.get("host") or "Recovery provider", "provider_id": str(backup.get("id", "")), "attempt": 1, "code": info["code"], "label": info["label"], "error": info["raw"], "retryable": info["retryable"], "status": info.get("status", 0), "ts": time.time()})
                continue

    codes = [str(a.get("code") or "") for a in provider_attempts]
    retryable = bool(provider_attempts) and all(bool(a.get("retryable")) for a in provider_attempts)
    if "authentication" in codes:
        code, label, suggestion = "authentication", "Provider authentication failed", "Verify credentials for the provider reporting the authentication error."
        retryable = False
    elif "permission" in codes:
        code, label, suggestion = "permission", "Provider access denied", "The provider denied access to the article or group. Check account/server access."
        retryable = False
    elif "article_missing" in codes:
        posted_ts = max(0, int(segment.get("posted_ts", 0) or 0))
        age = max(0.0, time.time() - posted_ts) if posted_ts else 0.0
        recent_nzb = str(segment.get("source") or "") == "nzb" and posted_ts > 0 and age < 3 * 60 * 60
        if recent_nzb:
            code, label = "article_propagating", "Article block not propagated yet"
            suggestion = "This NZB is very recent. NewzDeck will retry only the unavailable blocks while preserving everything already downloaded."
            retryable = True
        elif str(segment.get("source") or "") == "nzb" and message_id:
            code, label = "article_soft_missing", "Article temporarily unavailable"
            suggestion = "The provider returned article-not-found on several fresh connections. NewzDeck will recheck this exact Message-ID before declaring it missing."
            retryable = True
        else:
            code, label = "article_missing", "Article block missing on all providers tried"
            suggestion = "The block was not available from configured providers. It may be outside retention or removed."
            retryable = False
    elif "integrity" in codes:
        code, label, suggestion = "integrity", "Article block failed integrity checks", "The block was corrupt after retries. A different recovery provider may have a clean copy."
    else:
        code = primary_failure.code or "segment_failed"
        label = primary_failure.label or "Article block failed"
        suggestion = primary_failure.suggestion or "Retry is safe; completed blocks are preserved."

    tried = []
    for attempt in provider_attempts:
        name = str(attempt.get("provider") or "Provider")
        if name not in tried:
            tried.append(name)
    provider_text = ", ".join(tried) if tried else (primary_provider.get("name") or primary_provider.get("host") or "provider")
    raise SegmentFetchError(
        f"{label}. Providers tried: {provider_text}.",
        code=code, label=label, retryable=retryable, suggestion=suggestion, attempts=provider_attempts,
    ) from primary_failure

_LEGACY_QUEUE_FETCH_ORIGINAL = fetch_segment_with_recovery

def fetch_queue_segment(primary_provider: dict[str, Any], group: str, segment: dict[str, Any], cancel_event: threading.Event | None = None, owner_id: str = "", progress_callback=None) -> dict[str, Any]:
    """Dispatch queued downloads to v1.4's memory pipeline.

    The legacy hook remains honored when tests/extensions monkeypatch the older
    file-based fetch function, which keeps the download manager API compatible.
    """
    if fetch_segment_with_recovery is _LEGACY_QUEUE_FETCH_ORIGINAL:
        return fetch_segment_with_recovery_memory(primary_provider, group, segment, cancel_event, owner_id, progress_callback)
    compat = DOWNLOAD_TEMP_DIR / f".v140-hook-{threading.get_ident()}-{secrets.token_hex(4)}.seg"
    compat.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = fetch_segment_with_recovery(primary_provider, group, segment, compat, cancel_event, owner_id, progress_callback)
        data = compat.read_bytes()
        result = dict(result)
        result["data"] = data
        result["decoded_bytes"] = len(data)
        result.setdefault("perf", {"raw_body_bytes": int(result.get("wire_bytes", 0) or len(data)), "network_seconds": 0.0, "decode_seconds": 0.0, "native_decode": False})
        return result
    finally:
        compat.unlink(missing_ok=True)

def fetch_queue_batch(primary_provider: dict[str, Any], group: str, indexed_segments: list[tuple[int, dict[str, Any]]], cancel_event: threading.Event | None = None, owner_id: str = "", progress_callback=None) -> list[tuple[int, dict[str, Any] | None, Exception | None]]:
    """Fetch one pipelined batch, falling back safely per failed block."""
    if not indexed_segments:
        return []
    # Preserve extension/test compatibility when the legacy fetch hook is replaced.
    if fetch_segment_with_recovery is not _LEGACY_QUEUE_FETCH_ORIGINAL or len(indexed_segments) == 1:
        out = []
        for idx, seg in indexed_segments:
            cb = (lambda amount, i=idx: progress_callback(i, amount)) if progress_callback is not None else None
            try:
                out.append((idx, fetch_queue_segment(primary_provider, group, seg, cancel_event, owner_id, cb), None))
            except Exception as exc:
                out.append((idx, None, exc))
        return out
    pool = get_download_pool(primary_provider)
    try:
        recs = pool.fetch_batch_to_memory(
            group, [seg for _, seg in indexed_segments], cancel_event=cancel_event, owner_id=owner_id,
            progress_callback=(lambda pos, amount: progress_callback(indexed_segments[pos][0], amount)) if progress_callback is not None else None,
        )
    except DownloadCancelled:
        raise
    except Exception:
        # Framing/transport fallback: retry through the mature single-block path.
        recs = [{"ok": False, "error": NntpError("Pipelining fallback")}] * len(indexed_segments)
    out: list[tuple[int, dict[str, Any] | None, Exception | None]] = []
    for (idx, seg), rec in zip(indexed_segments, recs):
        if rec.get("ok"):
            result = dict(rec.get("result") or {})
            result["provider_id"] = str(primary_provider.get("id", ""))
            result["provider_name"] = primary_provider.get("name") or primary_provider.get("host") or "Provider"
            result["recovered"] = False
            result["provider_attempts"] = list(result.get("attempt_log") or [])
            out.append((idx, result, None))
            continue
        cb = (lambda amount, i=idx: progress_callback(i, amount)) if progress_callback is not None else None
        try:
            out.append((idx, fetch_queue_segment(primary_provider, group, seg, cancel_event, owner_id, cb), None))
        except Exception as exc:
            out.append((idx, None, exc))
    return out

def fetch_queue_batch_network(primary_provider: dict[str, Any], group: str,
                              indexed_segments: list[tuple[int, dict[str, Any]]],
                              cancel_event: threading.Event | None = None, owner_id: str = "",
                              progress_callback=None) -> list[tuple[int, dict[str, Any] | None, Exception | None]]:
    """Network-only queue batch used by the v3.4.15 decoupled transfer path.

    Clean primary-provider blocks return raw BODY payloads for the dedicated
    decoder executor. Failed blocks still use the mature recovery path so error
    semantics, recovery providers and bounded retries remain unchanged.
    """
    if not indexed_segments:
        return []
    if fetch_segment_with_recovery is not _LEGACY_QUEUE_FETCH_ORIGINAL:
        return fetch_queue_batch(primary_provider, group, indexed_segments, cancel_event, owner_id, progress_callback)
    pool = get_download_pool(primary_provider)
    try:
        recs = pool.fetch_batch_raw(
            group, [seg for _, seg in indexed_segments], cancel_event=cancel_event, owner_id=owner_id,
            progress_callback=(lambda pos, amount: progress_callback(indexed_segments[pos][0], amount)) if progress_callback is not None else None,
        )
    except DownloadCancelled:
        raise
    except Exception:
        recs = [{"ok": False, "error": NntpError("NNTP batch transport fallback")}] * len(indexed_segments)
    out: list[tuple[int, dict[str, Any] | None, Exception | None]] = []
    for (idx, seg), rec in zip(indexed_segments, recs):
        if rec.get("ok"):
            result = dict(rec.get("result") or {})
            result["_raw_pending"] = True
            result["provider_id"] = str(primary_provider.get("id", ""))
            result["provider_name"] = primary_provider.get("name") or primary_provider.get("host") or "Provider"
            result["recovered"] = False
            result["provider_attempts"] = list(result.get("attempt_log") or [])
            out.append((idx, result, None))
            continue
        cb = (lambda amount, i=idx: progress_callback(i, amount)) if progress_callback is not None else None
        try:
            # Failures are uncommon on healthy posts. Handle them synchronously
            # here so the normal recovery-provider and retry policy stays exact.
            out.append((idx, fetch_queue_segment(primary_provider, group, seg, cancel_event, owner_id, cb), None))
        except Exception as exc:
            out.append((idx, None, exc))
    return out


def decode_queue_batch_results(primary_provider: dict[str, Any],
                               indexed_segments: list[tuple[int, dict[str, Any]]],
                               batch_results: list[tuple[int, dict[str, Any] | None, Exception | None]],
                               cancel_event: threading.Event | None = None) -> list[tuple[int, dict[str, Any] | None, Exception | None]]:
    """Decode raw queue results away from NNTP worker threads."""
    if cancel_event is not None and cancel_event.is_set():
        raise DownloadCancelled()
    segment_map = {idx: seg for idx, seg in indexed_segments}
    pool = get_download_pool(primary_provider)
    out: list[tuple[int, dict[str, Any] | None, Exception | None]] = []
    for idx, result, error in batch_results:
        if cancel_event is not None and cancel_event.is_set():
            raise DownloadCancelled()
        if error is not None or result is None or not result.get("_raw_pending"):
            out.append((idx, result, error))
            continue
        seg = segment_map.get(idx)
        if seg is None:
            out.append((idx, None, NntpError("Decoded batch lost its segment mapping")))
            continue
        try:
            decoded = pool.decode_raw_result(seg, result)
            decoded["provider_id"] = str(primary_provider.get("id", ""))
            decoded["provider_name"] = primary_provider.get("name") or primary_provider.get("host") or "Provider"
            decoded["recovered"] = False
            decoded["provider_attempts"] = list(decoded.get("attempt_log") or [])
            out.append((idx, decoded, None))
        except Exception as exc:
            out.append((idx, None, exc))
    return out


def _download_auto_retry_plan(job: dict[str, Any], error_code: str) -> dict[str, Any]:
    """Return a bounded automatic retry plan for one failed queue member.

    A small number of missing Message-IDs can merit delayed rechecks because a
    provider backend may be briefly inconsistent. When a substantial part of a
    file is missing, however, repeating every Message-ID is almost never useful:
    it creates thousands of NNTP requests and delays PAR2/terminal failure.
    Recent NZBs keep the longer propagation window because their articles may
    genuinely still be arriving.
    """
    code = str(error_code or "")
    failed = max(0, int(job.get("failed_parts", 0) or 0))
    total = max(0, int(job.get("total_parts", 0) or 0), len(job.get("segments") or []))
    missing_ratio = (failed / total) if total > 0 else 0.0
    propagation = code == "propagation"
    soft_missing = code == "soft_missing"
    bulk_missing = bool(
        soft_missing
        and failed >= NZB_BULK_MISSING_MIN_BLOCKS
        and missing_ratio >= NZB_BULK_MISSING_RATIO
    )
    if propagation:
        return {
            "max_auto": NZB_PROPAGATION_MAX_RECHECKS,
            "delays": NZB_PROPAGATION_RECHECK_DELAYS,
            "propagation": True, "soft_missing": False, "bulk_missing": False,
            "missing_ratio": missing_ratio,
        }
    if soft_missing:
        return {
            "max_auto": 0 if bulk_missing else NZB_SOFT_MISSING_MAX_RECHECKS,
            "delays": NZB_SOFT_MISSING_RECHECK_DELAYS,
            "propagation": False, "soft_missing": True, "bulk_missing": bulk_missing,
            "missing_ratio": missing_ratio,
        }
    return {
        "max_auto": 2, "delays": (8, 16),
        "propagation": False, "soft_missing": False, "bulk_missing": False,
        "missing_ratio": missing_ratio,
    }

def download_failure_info(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, DownloadIncompleteError):
        return {"error_code": exc.code, "error_label": exc.label, "retryable": exc.retryable, "suggestion": exc.suggestion}
    if isinstance(exc, SegmentFetchError):
        return {"error_code": exc.code, "error_label": exc.label, "retryable": exc.retryable, "suggestion": exc.suggestion}
    text = str(exc); low = text.lower()
    if 'insufficient disk space' in low:
        return {'error_code':'disk_space','error_label':'Disk space protection','retryable':False,'suggestion':'Free disk space or choose another Download Folder, then retry.'}
    if 'crc mismatch' in low or 'truncated' in low or 'size mismatch' in low or 'assembled file is empty' in low:
        return {'error_code':'integrity','error_label':'Integrity check failed','retryable':True,'suggestion':'Retry the failed blocks. Existing good blocks will be reused.'}
    info = classify_nntp_failure(exc)
    return {'error_code':info['code'],'error_label':info['label'],'retryable':bool(info['retryable']),'suggestion':info['suggestion']}

def _find_local_tool(names: Iterable[str]) -> str | None:
    """Find an optional post-processing executable without installing anything."""
    for name in names:
        local = APP_DIR / name
        if local.exists() and local.is_file():
            return str(local)
        found = shutil.which(name)
        if found:
            return found
    return None

def _windows_tool_candidates(relative_paths: Iterable[str]) -> Iterable[Path]:
    """Yield common per-user/system Windows install locations for optional tools.

    NewzDeck does not install or bundle third-party repair/unpack binaries here;
    this simply lets it reuse tools the user already has (including SABnzbd's
    bundled command-line helpers) without requiring PATH changes.
    """
    if os.name != "nt":
        return []
    roots: list[Path] = []
    for key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        value = os.environ.get(key)
        if value:
            root = Path(value)
            if root not in roots:
                roots.append(root)
    out: list[Path] = []
    for root in roots:
        for rel in relative_paths:
            candidate = root / Path(rel)
            if candidate not in out:
                out.append(candidate)
    return out

def _first_existing_tool(paths: Iterable[Path]) -> str | None:
    for path in paths:
        try:
            if path.exists() and path.is_file():
                return str(path)
        except OSError:
            continue
    return None

def _sevenzip_path() -> str | None:
    direct = _find_local_tool(("7z.exe", "7zz.exe", "7za.exe", "7z", "7zz", "7za"))
    if direct:
        return direct
    return _first_existing_tool(_windows_tool_candidates((
        r"7-Zip\7z.exe",
        r"SABnzbd\win\7zip\7z.exe",
        r"SABnzbd\win\7zip\7zz.exe",
        r"Programs\SABnzbd\win\7zip\7z.exe",
        r"Programs\SABnzbd\win\7zip\7zz.exe",
    )))

def _managed_unrar_path() -> str | None:
    try:
        if UNRAR_MANAGED_EXE.exists() and UNRAR_MANAGED_EXE.is_file():
            return str(UNRAR_MANAGED_EXE)
    except OSError:
        pass
    return None

def _unrar_path() -> str | None:
    """Find UnRAR for Direct Unpack, preferring NewzDeck's managed copy.

    Direct Unpack needs UnRAR's -vp (pause-before-next-volume) behavior. 7-Zip
    remains the normal post-processing extractor and is deliberately not used
    for progressive multi-volume extraction because it cannot wait safely for
    the next volume while that volume is still downloading.
    """
    managed = _managed_unrar_path()
    if managed:
        return managed
    direct = _find_local_tool(("UnRAR.exe", "unrar.exe", "unrar"))
    if direct:
        return direct
    return _first_existing_tool(_windows_tool_candidates((
        r"WinRAR\UnRAR.exe",
        r"SABnzbd\win\unrar\x64\UnRAR.exe",
        r"SABnzbd\win\unrar\UnRAR.exe",
        r"Programs\SABnzbd\win\unrar\x64\UnRAR.exe",
        r"Programs\SABnzbd\win\unrar\UnRAR.exe",
    )))

def _ensure_managed_unrar_tool(*, force: bool = False) -> str | None:
    """Provision RARLAB's official UnRAR x64 into NewzDeck's managed tools.

    The official RARLAB self-extracting UnRAR package is downloaded directly on
    the user's Windows machine, SHA-256 verified, and silently extracted into
    NewzDeck's version-independent data folder.  The user never needs to install
    WinRAR/UnRAR separately and the RARLAB license.txt is preserved alongside
    the executable.
    """
    global _unrar_install_attempt_ts, _unrar_install_error
    managed = _managed_unrar_path()
    if managed:
        return managed
    if sys.platform != "win32":
        return None
    now = time.time()
    if not force and _unrar_install_attempt_ts and now - _unrar_install_attempt_ts < 15 * 60:
        return None
    with _unrar_install_lock:
        managed = _managed_unrar_path()
        if managed:
            return managed
        now = time.time()
        if not force and _unrar_install_attempt_ts and now - _unrar_install_attempt_ts < 15 * 60:
            return None
        _unrar_install_attempt_ts = now
        temp_installer = UPDATE_DIR / f"unrarw64-{UNRAR_MANAGED_VERSION}.exe"
        temp_dir = UNRAR_MANAGED_DIR.with_name(UNRAR_MANAGED_DIR.name + ".installing")
        try:
            req = urllib.request.Request(
                UNRAR_MANAGED_URL,
                headers={"User-Agent": f"NewzDeck/{APP_VERSION} (+managed UnRAR installer)"},
            )
            h = hashlib.sha256()
            total = 0
            temp_installer.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(req, timeout=30) as response, temp_installer.open("wb") as out:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > 4 * 1024 * 1024:
                        raise ValueError("UnRAR download exceeded the expected size limit")
                    h.update(chunk)
                    out.write(chunk)
            digest = h.hexdigest().lower()
            if digest != UNRAR_MANAGED_SHA256.lower():
                raise ValueError(f"UnRAR checksum mismatch: expected {UNRAR_MANAGED_SHA256}, got {digest}")

            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)


            try:
                subprocess.run(
                    [str(temp_installer), "/s"],
                    cwd=str(temp_dir),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=20,
                    check=False,
                    creationflags=creationflags,
                )
            except subprocess.TimeoutExpired:

                pass

            extracted = temp_dir / "UnRAR.exe"
            deadline = time.monotonic() + 20.0
            last_size = -1
            stable_ticks = 0
            while time.monotonic() < deadline:
                try:
                    size = extracted.stat().st_size if extracted.is_file() else 0
                except OSError:
                    size = 0
                if size > 64 * 1024:
                    if size == last_size:
                        stable_ticks += 1
                        if stable_ticks >= 2:
                            break
                    else:
                        stable_ticks = 0
                        last_size = size
                time.sleep(0.25)
            if not extracted.is_file() or extracted.stat().st_size <= 64 * 1024:
                raise ValueError("The verified RARLAB package did not produce UnRAR.exe")


            try:
                probe = subprocess.run(
                    [str(extracted)], cwd=str(temp_dir),
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=5, check=False, creationflags=creationflags,
                )
                banner = probe.stdout.decode("utf-8", errors="replace")
            except Exception as exc:
                raise ValueError(f"Could not validate extracted UnRAR.exe: {exc}") from exc
            if f"UNRAR {UNRAR_MANAGED_VERSION}" not in banner.upper():
                raise ValueError("Extracted UnRAR.exe did not report the expected version")

            (temp_dir / "SOURCE.txt").write_text(
                f"RARLAB UnRAR {UNRAR_MANAGED_VERSION}\n{UNRAR_MANAGED_URL}\n"
                f"SHA-256 {UNRAR_MANAGED_SHA256}\n"
                "Downloaded and verified automatically by NewzDeck.\n",
                encoding="utf-8",
            )
            shutil.rmtree(UNRAR_MANAGED_DIR, ignore_errors=True)
            temp_dir.replace(UNRAR_MANAGED_DIR)
            _unrar_install_error = ""
            json_write(UNRAR_TOOL_STATUS_FILE, {
                "ok": True, "version": UNRAR_MANAGED_VERSION,
                "installed_ts": time.time(), "path": str(UNRAR_MANAGED_EXE),
                "source": UNRAR_MANAGED_URL, "sha256": UNRAR_MANAGED_SHA256,
            })
            DIAGNOSTICS.event("info", "direct-unpack", f"Installed verified managed UnRAR {UNRAR_MANAGED_VERSION}", path=str(UNRAR_MANAGED_EXE))
            return str(UNRAR_MANAGED_EXE)
        except Exception as exc:
            _unrar_install_error = str(exc)[:1000]
            try:
                json_write(UNRAR_TOOL_STATUS_FILE, {
                    "ok": False, "version": UNRAR_MANAGED_VERSION,
                    "attempted_ts": time.time(), "error": _unrar_install_error,
                })
            except Exception:
                pass
            DIAGNOSTICS.event("warning", "direct-unpack", f"Could not provision UnRAR automatically: {_unrar_install_error}")
            return None
        finally:
            temp_installer.unlink(missing_ok=True)
            shutil.rmtree(temp_dir, ignore_errors=True)

def _prewarm_unrar_tool() -> None:
    if sys.platform != "win32" or _managed_unrar_path():
        return
    try:
        raw = json_read(SETTINGS_FILE, {})
        if not isinstance(raw, dict):
            raw = {}
        mode = str(raw.get("direct_unpack_mode", DEFAULT_DIRECT_UNPACK_MODE) or DEFAULT_DIRECT_UNPACK_MODE).casefold()
        if bool(raw.get("post_processing", DEFAULT_POST_PROCESSING)) and bool(raw.get("auto_extract", DEFAULT_AUTO_EXTRACT)) and mode in {"auto", "on"}:
            _ensure_managed_unrar_tool()
    except Exception as exc:
        DIAGNOSTICS.event("warning", "direct-unpack", f"UnRAR prewarm failed: {exc}")

def _rar_volume_index(filename: str) -> int | None:
    """Return a 1-based RAR volume index for common modern and legacy names."""
    name = Path(str(filename or "")).name.casefold()
    match = re.search(r"\.part0*(\d+)\.rar$", name)
    if match:
        return max(1, int(match.group(1)))
    if name.endswith('.rar'):
        return 1
    match = re.search(r"\.r(\d{2,3})$", name)
    if match:
        return int(match.group(1)) + 2
    return None

def _is_rar_volume(filename: str) -> bool:
    return _rar_volume_index(filename) is not None

_unrar_install_lock = threading.Lock()
_unrar_install_attempt_ts = 0.0
_unrar_install_error = ""

_par2_install_lock = threading.Lock()
_par2_install_attempt_ts = 0.0
_par2_install_error = ""

def _managed_par2_path() -> str | None:
    try:
        if PAR2_MANAGED_EXE.exists() and PAR2_MANAGED_EXE.is_file():
            return str(PAR2_MANAGED_EXE)
    except OSError:
        pass
    return None

def _par2_path() -> str | None:
    managed = _managed_par2_path()
    if managed:
        return managed
    direct = _find_local_tool((
        "par2cmdline-turbo.exe", "par2.exe", "par2cmdline.exe",
        "par2cmdline-turbo", "par2", "par2cmdline",
    ))
    if direct:
        return direct
    return _first_existing_tool(_windows_tool_candidates((
        r"SABnzbd\win\par2\x64\par2.exe",
        r"SABnzbd\win\par2\par2.exe",
        r"SABnzbd\win\par2\par2cmdline-turbo.exe",
        r"Programs\SABnzbd\win\par2\x64\par2.exe",
        r"Programs\SABnzbd\win\par2\par2.exe",
        r"Programs\SABnzbd\win\par2\par2cmdline-turbo.exe",
    )))

def _ensure_managed_par2_tool(*, force: bool = False) -> str | None:
    """Install a verified PAR2 verifier/repair helper into NewzDeck's data folder.

    The helper is downloaded from the upstream par2cmdline-turbo GitHub release
    on the user's machine; NewzDeck does not redistribute the GPL binary inside
    its Setup EXE. The release archive is SHA-256 pinned before extraction.
    """
    global _par2_install_attempt_ts, _par2_install_error
    existing = _par2_path()
    if existing:
        return existing
    if sys.platform != "win32":
        return None
    now = time.time()
    if not force and _par2_install_attempt_ts and now - _par2_install_attempt_ts < 15 * 60:
        return None
    with _par2_install_lock:
        existing = _par2_path()
        if existing:
            return existing
        now = time.time()
        if not force and _par2_install_attempt_ts and now - _par2_install_attempt_ts < 15 * 60:
            return None
        _par2_install_attempt_ts = now
        temp_archive = UPDATE_DIR / f"par2cmdline-turbo-{PAR2_MANAGED_VERSION}-win-x64.zip.part"
        temp_dir = PAR2_MANAGED_DIR.with_name(PAR2_MANAGED_DIR.name + ".installing")
        try:
            req = urllib.request.Request(
                PAR2_MANAGED_URL,
                headers={"User-Agent": f"NewzDeck/{APP_VERSION} (+local post-processing tool installer)"},
            )
            h = hashlib.sha256()
            total = 0
            temp_archive.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(req, timeout=30) as response, temp_archive.open("wb") as out:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > 10 * 1024 * 1024:
                        raise ValueError("PAR2 helper download exceeded the expected size limit")
                    h.update(chunk)
                    out.write(chunk)
            digest = h.hexdigest().lower()
            if digest != PAR2_MANAGED_SHA256.lower():
                raise ValueError(f"PAR2 helper checksum mismatch: expected {PAR2_MANAGED_SHA256}, got {digest}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(temp_archive, "r") as zf:
                candidates = [i for i in zf.infolist() if not i.is_dir() and Path(i.filename).name.casefold() in {"par2.exe", "par2cmdline.exe", "par2cmdline-turbo.exe"}]
                if not candidates:
                    raise ValueError("The verified PAR2 archive did not contain a supported Windows executable")
                chosen = min(candidates, key=lambda i: (0 if Path(i.filename).name.casefold() == "par2.exe" else 1, len(i.filename)))
                with zf.open(chosen, "r") as src, (temp_dir / "par2.exe").open("wb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)

                for info in zf.infolist():
                    base = Path(info.filename).name.casefold()
                    if info.is_dir() or base not in {"copying", "copying.txt", "license", "license.txt", "readme", "readme.txt"}:
                        continue
                    try:
                        with zf.open(info, "r") as src, (temp_dir / Path(info.filename).name).open("wb") as dst:
                            shutil.copyfileobj(src, dst, length=256 * 1024)
                    except OSError:
                        pass
            (temp_dir / "SOURCE.txt").write_text(
                f"par2cmdline-turbo {PAR2_MANAGED_VERSION}\n{PAR2_MANAGED_URL}\nSHA-256 {PAR2_MANAGED_SHA256}\n",
                encoding="utf-8",
            )
            shutil.rmtree(PAR2_MANAGED_DIR, ignore_errors=True)
            temp_dir.replace(PAR2_MANAGED_DIR)
            _par2_install_error = ""
            json_write(PAR2_TOOL_STATUS_FILE, {"ok": True, "version": PAR2_MANAGED_VERSION, "installed_ts": time.time(), "path": str(PAR2_MANAGED_EXE)})
            DIAGNOSTICS.event("info", "post-processing", f"Installed verified PAR2 helper v{PAR2_MANAGED_VERSION}", path=str(PAR2_MANAGED_EXE))
            return str(PAR2_MANAGED_EXE)
        except Exception as exc:
            _par2_install_error = str(exc)[:1000]
            try:
                json_write(PAR2_TOOL_STATUS_FILE, {"ok": False, "version": PAR2_MANAGED_VERSION, "attempted_ts": time.time(), "error": _par2_install_error})
            except Exception:
                pass
            DIAGNOSTICS.event("warning", "post-processing", f"Could not install PAR2 helper automatically: {_par2_install_error}")
            return None
        finally:
            temp_archive.unlink(missing_ok=True)
            shutil.rmtree(temp_dir, ignore_errors=True)

def _prewarm_par2_tool() -> None:
    if sys.platform != "win32" or _par2_path():
        return
    try:
        raw = json_read(SETTINGS_FILE, {})
        if not isinstance(raw, dict):
            raw = {}
        if bool(raw.get("post_processing", DEFAULT_POST_PROCESSING)) and bool(raw.get("auto_repair", DEFAULT_AUTO_REPAIR)):
            _ensure_managed_par2_tool()
    except Exception as exc:
        DIAGNOSTICS.event("warning", "post-processing", f"PAR2 prewarm failed: {exc}")

def _archive_kind(path: Path) -> str:
    name = path.name.casefold()
    if name.endswith('.zip'):
        return 'zip'
    if name.endswith('.7z') or re.search(r'\.7z\.001$', name):
        return '7z'
    if name.endswith('.rar'):
        m = re.search(r'\.part0*(\d+)\.rar$', name)
        if m and int(m.group(1)) > 1:
            return ''
        return 'rar'
    return ''

def _safe_extract_zip(path: Path, output_dir: Path, password: str = "", cancel_event: threading.Event | None = None) -> list[str]:
    """Safely and cancellably extract a ZIP.

    zipfile.extractall()/testzip() are monolithic calls and were effectively
    uninterruptible.  Stream every member in chunks so Stop All/Cancel can break
    extraction promptly and so very large archives do not make the queue appear
    frozen.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    root = output_dir.resolve()
    extracted: list[str] = []
    pwd = password.encode("utf-8") if password else None

    def check_cancel():
        if cancel_event is not None and cancel_event.is_set():
            raise PostProcessingCancelled("Post-processing stopped by user")

    with zipfile.ZipFile(path, 'r') as zf:
        infos = zf.infolist()
        encrypted = any(bool(i.flag_bits & 0x1) for i in infos)
        if encrypted and not pwd:
            raise NntpError("ARCHIVE_PASSWORD_REQUIRED")
        for info in infos:
            check_cancel()
            target = (output_dir / info.filename).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise NntpError(f"Unsafe ZIP path: {info.filename}") from exc
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                continue
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with zf.open(info, 'r', pwd=pwd) as src, target.open('wb') as dst:
                    while True:
                        check_cancel()
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        dst.write(chunk)
            except RuntimeError as exc:
                target.unlink(missing_ok=True)
                if 'password' in str(exc).casefold() or 'encrypted' in str(exc).casefold():
                    raise NntpError("ARCHIVE_PASSWORD_REQUIRED") from exc
                raise
            except zipfile.BadZipFile as exc:
                target.unlink(missing_ok=True)
                raise NntpError(f"ZIP integrity check failed at {info.filename}") from exc
            extracted.append(info.filename)
    return extracted

def _run_post_tool(args: list[str], cwd: Path, timeout: int = 60 * 60, cancel_event: threading.Event | None = None) -> subprocess.CompletedProcess:
    """Run a repair/extraction tool without making queue cancellation wait on it.

    subprocess.run() previously made a PAR2/7-Zip invocation effectively
    uninterruptible for up to an hour.  Poll communicate() so Hard Stop / Remove
    can terminate the child immediately and release NewzDeck's post-processing
    worker.
    """
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if sys.platform == 'win32' else 0
    proc = subprocess.Popen(args, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, errors='replace', creationflags=flags)
    deadline = time.monotonic() + max(1, int(timeout))
    while True:
        if cancel_event is not None and cancel_event.is_set():
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.communicate(timeout=2)
            except Exception:
                pass
            raise PostProcessingCancelled('Post-processing stopped by user')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            try:
                proc.kill()
            except Exception:
                pass
            try:
                out, err = proc.communicate(timeout=2)
            except Exception:
                out, err = '', ''
            raise subprocess.TimeoutExpired(args, timeout, output=out, stderr=err)
        try:
            out, err = proc.communicate(timeout=min(0.25, remaining))
            return subprocess.CompletedProcess(args, proc.returncode, out, err)
        except subprocess.TimeoutExpired:
            continue

def _nzb_filename(subject: str, fallback: str) -> str:
    quoted = re.findall(r'["\']([^"\']+\.[A-Za-z0-9]{1,10})["\']', subject or '')
    if quoted:
        return safe_download_name(quoted[-1].replace('\\', '/').split('/')[-1])
    media = detect_media(subject)
    if media and media.get('filename'):
        return safe_download_name(str(media['filename']))
    clean = PART_PATTERN.sub('', subject or '')
    clean = re.sub(r'(?i)\byenc\b', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip(' -_[]()')
    return safe_download_name(clean[:180] or fallback)

AUXILIARY_NZB_EXTENSIONS = {"nfo", "sfv", "srr", "srs", "txt", "url", "md5", "sha1", "sha256", "sha512"}

def nzb_auxiliary_file(filename: str) -> bool:
    """Return True for optional NZB sidecars that never gate package completion.

    NewzDeck gives these files one normal download attempt when they are present.
    If an article is unavailable, the sidecar is skipped immediately rather than
    holding completed media in Retry/Waiting. Core media/archive files and PAR2
    data remain blocking/repairable payload.
    """
    name = str(filename or "").strip()
    ext = Path(name).suffix.casefold().lstrip(".")
    if ext in AUXILIARY_NZB_EXTENSIONS:
        return True
    return bool(re.search(r"(?i)(?:^|[._ -])(sample|proof|screenshot)(?:[._ -]|$)", Path(name).stem))

def nzb_job_blocks_collection(job: dict[str, Any]) -> bool:
    """Whether this queued NZB member must finish before post-processing starts."""
    return str(job.get("collection_role") or "payload") != "auxiliary" and not bool(job.get("is_auxiliary"))

def normalize_nzb_message_id(value: Any) -> str:
    """Return one canonical NNTP Message-ID wrapped in exactly one <...> pair.

    NZB 1.x stores segment Message-IDs without angle brackets, but real-world
    indexers sometimes include them (or XML-escaped equivalents).  Keep the ID
    byte-for-byte otherwise; only strip surrounding whitespace/brackets and
    reject embedded CR/LF so it is safe to place on an NNTP command line.
    """
    text = html.unescape(str(value or "")).strip()
    text = text.replace("\r", "").replace("\n", "")
    while len(text) >= 2 and text.startswith("<") and text.endswith(">"):
        text = text[1:-1].strip()
    if not text or any(ch.isspace() for ch in text):
        return ""
    return f"<{text}>"

def par2_volume_info(filename: str) -> tuple[int, int]:
    """Return (first recovery block, block count) from a PAR2 volume filename."""
    match = re.search(r'(?i)\.vol(\d+)[+_](\d+)\.par2$', str(filename or ''))
    if not match:
        return (0, 0)
    try:
        return (max(0, int(match.group(1))), max(0, int(match.group(2))))
    except (TypeError, ValueError):
        return (0, 0)

def _par2_slice_size(path: Path) -> int:
    """Read the PAR2 Main packet's slice size without loading the whole file.

    PAR2 packets start with a 64-byte header. The Main packet body begins with
    an unsigned little-endian 64-bit recovery slice size. Return 0 when the
    file is not a readable PAR2 index or the packet is not found.
    """
    try:
        with Path(path).open('rb') as src:
            scanned = 0
            while scanned < 32 * 1024 * 1024:
                header = src.read(64)
                if len(header) < 64:
                    return 0
                if header[:8] != b'PAR2\x00PKT':
                    rest = header[1:] + src.read(64 * 1024)
                    pos = rest.find(b'PAR2\x00PKT')
                    if pos < 0:
                        return 0
                    src.seek(-(len(rest) - pos), os.SEEK_CUR)
                    scanned += pos + 1
                    continue
                packet_len = struct.unpack('<Q', header[8:16])[0]
                if packet_len < 64 or packet_len > 512 * 1024 * 1024:
                    return 0
                packet_type = header[48:64]
                body_len = packet_len - 64
                if packet_type.startswith(b'PAR 2.0\x00Main'):
                    body = src.read(min(body_len, 16))
                    if len(body) >= 8:
                        return max(0, int(struct.unpack('<Q', body[:8])[0]))
                    return 0
                src.seek(body_len, os.SEEK_CUR)
                scanned += packet_len
    except (OSError, struct.error, ValueError):
        return 0
    return 0

def parse_nzb_bytes(raw: bytes, source_name: str = 'Imported NZB') -> dict[str, Any]:
    """Parse a standard NZB into DownloadManager-compatible logical files."""
    if not raw or len(raw) > 100 * 1024 * 1024:
        raise ValueError('NZB file is empty or too large')
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f'Invalid NZB XML: {exc}') from exc

    def local(tag: str) -> str:
        return tag.rsplit('}', 1)[-1].casefold()

    nzb_meta: dict[str, list[str]] = {}
    for node in root.iter():
        if local(node.tag) == "meta":
            key = str(node.attrib.get("type", "") or "").strip().casefold()
            value = (node.text or "").strip()
            if key and value:
                nzb_meta.setdefault(key, []).append(value)

    files: list[dict[str, Any]] = []
    for node in root.iter():
        if local(node.tag) != 'file':
            continue
        subject = str(node.attrib.get('subject', '') or '')
        poster = str(node.attrib.get('poster', '') or '')
        date_raw = str(node.attrib.get('date', '') or '')
        try:
            posted_ts = max(0, int(date_raw)) if date_raw else 0
            date_text = email.utils.formatdate(posted_ts, usegmt=True) if posted_ts else ''
        except (TypeError, ValueError, OverflowError):
            posted_ts = 0
            date_text = ''
        groups: list[str] = []
        segments: list[dict[str, Any]] = []
        for child in node.iter():
            lname = local(child.tag)
            if lname == 'group' and child.text and child.text.strip():
                groups.append(child.text.strip())
            elif lname == 'segment' and child.text and child.text.strip():
                msgid = normalize_nzb_message_id(child.text)
                if not msgid:
                    continue
                try:
                    number = max(1, int(child.attrib.get('number', len(segments) + 1)))
                except (TypeError, ValueError):
                    number = len(segments) + 1
                try:
                    byte_count = max(0, int(child.attrib.get('bytes', 0) or 0))
                except (TypeError, ValueError):
                    byte_count = 0
                segments.append({'article': None, 'message_id': msgid, 'part': number, 'bytes': byte_count, 'source': 'nzb', 'posted_ts': posted_ts})
        if not segments:
            continue
        segments.sort(key=lambda x: int(x.get('part', 1)))
        group = groups[0] if groups else ''
        filename = _nzb_filename(subject, f'nzb-file-{len(files)+1}.bin')
        ext = Path(filename).suffix.casefold().lstrip('.')
        if ext in {'jpg','jpeg','png','gif','webp','bmp'}:
            kind = 'image'
        elif ext in {'mp4','m4v','webm','mov','avi','mkv'}:
            kind = 'video'
        else:
            kind = 'file'
        media = {'filename': filename, 'extension': ext, 'kind': kind, 'mime': mimetypes.guess_type(filename)[0] or 'application/octet-stream'}
        is_par2 = ext == 'par2'
        recovery_start, recovery_blocks = par2_volume_info(filename) if is_par2 else (0, 0)
        is_par2_volume = bool(is_par2 and recovery_blocks > 0)
        files.append({
            'group': group, 'groups': groups, 'subject': subject, 'from': poster, 'date': date_text, 'posted_ts': posted_ts,
            'message_id': segments[0].get('message_id',''), 'segments': segments, 'media': media,
            'bytes': sum(int(x.get('bytes',0) or 0) for x in segments),
            'is_par2': is_par2, 'is_par2_volume': is_par2_volume,
            'is_auxiliary': bool(not is_par2 and nzb_auxiliary_file(filename)),
            'par2_recovery_start': recovery_start, 'par2_recovery_blocks': recovery_blocks,
        })
    if not files:
        raise ValueError('This NZB does not contain any downloadable file entries')
    collection_name = (nzb_meta.get('title') or [Path(source_name).stem or 'Imported NZB'])[0]
    return {'name': safe_folder_name(collection_name), 'files': files, 'meta': nzb_meta,
            'passwords': list(nzb_meta.get('password') or [])}

_nzb_inspect_lock = threading.Lock()
_nzb_inspect_tokens: dict[str, dict[str, Any]] = {}

def _nzb_inspect_store(parsed: dict[str, Any], source_name: str) -> str:
    token = secrets.token_hex(16)
    now = time.time()
    with _nzb_inspect_lock:
        for key, item in list(_nzb_inspect_tokens.items()):
            if now - float(item.get("ts", 0) or 0) > 30 * 60:
                _nzb_inspect_tokens.pop(key, None)
        _nzb_inspect_tokens[token] = {"ts": now, "parsed": parsed, "source_name": source_name}
    return token

def _nzb_inspect_get(token: str, consume: bool = False) -> dict[str, Any]:
    with _nzb_inspect_lock:
        item = _nzb_inspect_tokens.get(token)
        if not item or time.time() - float(item.get("ts", 0) or 0) > 30 * 60:
            _nzb_inspect_tokens.pop(token, None)
            raise ValueError("NZB preview expired. Choose the NZB again.")
        if consume:
            _nzb_inspect_tokens.pop(token, None)
        return item

class DownloadManager:
    """Persistent background queue with concurrent files and parallel NNTP segments."""
    def __init__(self):
        self.lock = threading.RLock()
        self.wake = threading.Event()
        self.shutdown_event = threading.Event()
        raw = json_read(DOWNLOADS_FILE, {"paused": False, "jobs": []})
        self.paused = bool(raw.get("paused", False)) if isinstance(raw, dict) else False
        self.jobs = raw.get("jobs", []) if isinstance(raw, dict) and isinstance(raw.get("jobs", []), list) else []
        raw_collections = raw.get("collections", {}) if isinstance(raw, dict) else {}
        self.collections: dict[str, dict[str, Any]] = raw_collections if isinstance(raw_collections, dict) else {}
        raw_statistics = raw.get("statistics", {}) if isinstance(raw, dict) else {}
        raw_statistics = raw_statistics if isinstance(raw_statistics, dict) else {}
        existing_times = [float(j.get("created_ts", 0) or 0) for j in self.jobs if float(j.get("created_ts", 0) or 0) > 0]
        tracking_since = float(raw_statistics.get("tracking_since_ts", 0) or 0) or (min(existing_times) if existing_times else time.time())
        self.statistics: dict[str, Any] = {
            "tracking_since_ts": tracking_since,
            "total_downloaded_bytes": max(0, int(raw_statistics.get("total_downloaded_bytes", 0) or 0)),
            "completed_files": max(0, int(raw_statistics.get("completed_files", 0) or 0)),
            "transfer_seconds": max(0.0, float(raw_statistics.get("transfer_seconds", 0) or 0)),
            "peak_speed_bps": max(0, int(raw_statistics.get("peak_speed_bps", 0) or 0)),
            "recovered_blocks": max(0, int(raw_statistics.get("recovered_blocks", 0) or 0)),
        }
        for index, job in enumerate(self.jobs):
            job.setdefault("priority", "normal")
            job.setdefault("paused", False)
            job.setdefault("queue_order", float(job.get("created_ts", index) or index))
            job.setdefault("destination_mode", "flat")
            job.setdefault("origin_provider_id", job.get("provider_id", ""))
            job.setdefault("origin_provider_name", job.get("provider_name", "Provider"))
            job.setdefault("recovered_parts", 0)
            job.setdefault("statistics_counted", False)
            job.setdefault("recovery_sources", {})
            job.setdefault("source", "browser")
            job.setdefault("collection_id", "")
            job.setdefault("collection_name", "")
            job.setdefault("collection_expected", 0)
            job.setdefault("destination_subdir", "")
            job.setdefault("post_status", "")
            job.setdefault("post_progress", 0)
            job.setdefault("post_message", "")
            job.setdefault("processed_parts", int(job.get("current_part", 0) or 0))
            job.setdefault("successful_parts", int(job.get("current_part", 0) or 0))
            job.setdefault("failed_parts", 0)
            job.setdefault("missing_bytes", 0)
            job.setdefault("retry_count", 0)
            job.setdefault("auto_retry_count", 0)
            job.setdefault("retry_at_ts", 0)
            job.setdefault("error_code", "")
            job.setdefault("error_label", "")
            job.setdefault("error_suggestion", "")
            job.setdefault("error_retryable", False)
            job.setdefault("segment_errors", [])
            job.setdefault("last_activity_ts", 0)
            job.setdefault("last_progress_ts", float(job.get("last_activity_ts", 0) or 0))
            job.setdefault("status_detail", "")
            job.setdefault("resumed_parts", 0)
            job.setdefault("transfer_phase", "")
            inferred_auxiliary = bool(str(job.get("source") or "") == "nzb" and nzb_auxiliary_file(str(job.get("filename") or "")))
            job.setdefault("is_auxiliary", inferred_auxiliary)
            role = "recovery_par2" if job.get("is_par2_volume") else "par2" if job.get("is_par2") else "auxiliary" if job.get("is_auxiliary") else "payload"
            job.setdefault("collection_role", role)
            if str(job.get("collection_role") or "") == "payload" and job.get("is_auxiliary"):
                job["collection_role"] = "auxiliary"
            job.setdefault("optional_missing", False)
            job.setdefault("collection_required_expected", 0)
            if (
                job.get("is_auxiliary")
                and job.get("status") in {"retry_wait", "failed"}
                and (str(job.get("error_code") or "") in {"soft_missing", "article_missing", "incomplete", "propagation"}
                     or "unavailable" in str(job.get("status_detail") or "").casefold()
                     or "propagat" in str(job.get("status_detail") or "").casefold())
            ):
                stale_partial = str(job.get("partial_path") or "")
                job["status"] = "completed"
                job["optional_missing"] = True
                job["path"] = ""
                job["partial_path"] = ""
                job["actual_size"] = 0
                job["downloaded_bytes"] = 0
                job["successful_parts"] = 0
                job["failed_parts"] = 0
                job["missing_bytes"] = 0
                job["segment_errors"] = []
                job["error"] = ""
                job["error_code"] = ""
                job["error_label"] = ""
                job["error_suggestion"] = ""
                job["error_retryable"] = False
                job["speed_bps"] = 0
                job["connections_used"] = 0
                job["completed_ts"] = time.time()
                job["status_detail"] = f"Optional {Path(str(job.get('filename') or '')).suffix or 'sidecar'} unavailable — skipped"
                job["transfer_phase"] = "optional_skipped"
                job["integrity_status"] = "optional_missing"
                if stale_partial:
                    try:
                        Path(stale_partial).unlink(missing_ok=True)
                    except OSError:
                        pass
                shutil.rmtree(DOWNLOAD_TEMP_DIR / str(job.get("id") or ""), ignore_errors=True)
            job.setdefault("par2_recovery_blocks", par2_volume_info(str(job.get("filename") or ""))[1])
            job.setdefault("integrity_status", "healthy" if job.get("status") == "completed" else "unknown")
            job.setdefault("repair_missing_bytes", 0)
            job.setdefault("repair_missing_blocks", 0)
            job.setdefault("average_speed_bps", 0)
            job.setdefault("duration_seconds", 0.0)
            job.setdefault("category", "")
            job.setdefault("category_folder", "")
            job.setdefault("automation_source", "")
            job.setdefault("automation_context", {})
        for job in self.jobs:
            cid = str(job.get("collection_id") or "")
            if not cid:
                continue
            rec = self.collections.setdefault(cid, {
                "id": cid, "name": str(job.get("collection_name") or "Imported NZB"),
                "provider_id": str(job.get("origin_provider_id") or job.get("provider_id") or ""),
                "created_ts": float(job.get("created_ts", time.time()) or time.time()),
                "recovery_catalog": [], "recovery_queued_names": [], "source_name": "",
            })
            rec.setdefault("recovery_catalog", [])
            rec.setdefault("recovery_queued_names", [])
            rec.setdefault("priority", str(job.get("priority") or "normal"))
            rec.setdefault("category", str(job.get("category") or ""))
            rec.setdefault("category_folder", str(job.get("category_folder") or ""))
            rec.setdefault("automation_source", str(job.get("automation_source") or ""))
            rec.setdefault("automation_context", job.get("automation_context") if isinstance(job.get("automation_context"), dict) else {})
        for cid, rec in self.collections.items():
            jobs = self._collection_jobs_locked(cid)
            required_expected = max(0, int(rec.get("required_expected", 0) or 0)) or sum(1 for j in jobs if nzb_job_blocks_collection(j))
            rec["required_expected"] = required_expected
            for target in jobs:
                if not int(target.get("collection_required_expected", 0) or 0):
                    target["collection_required_expected"] = required_expected
            direct = rec.get("direct_unpack") if isinstance(rec.get("direct_unpack"), dict) else {}
            if direct.get("status") == "active":


                direct = {**direct, "status": "fallback", "message": "Direct Unpack was interrupted by a restart; normal extraction will be used", "error": "interrupted"}
            rec["direct_unpack"] = direct
        self.concurrent_downloads = PACKAGE_QUEUE_CONCURRENCY
        self.active_jobs: dict[str, Any] = {}
        self.job_cancel_events: dict[str, threading.Event] = {}
        self.job_run_tokens: dict[str, str] = {}
        self.reserved_paths: set[str] = set()
        self.job_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS, thread_name_prefix="usenet-download-job")
        self.post_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="usenet-post-process")
        self.post_active: set[str] = set()
        self.post_futures: dict[str, Any] = {}
        self.post_cancel_events: dict[str, threading.Event] = {}
        self.post_passwords: dict[str, str] = {}
        self.direct_unpack_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="usenet-direct-unpack")
        self.direct_unpack_futures: dict[str, Any] = {}
        self.direct_unpack_cancel_events: dict[str, threading.Event] = {}
        self.direct_unpack_wake = threading.Event()
        self._last_hot_save_ts = 0.0
        # Wall-clock throughput sampler. Stage timers are useful for diagnostics
        # but summing elapsed time across 50 parallel workers dramatically
        # understates real throughput. These counters sample completed bytes over
        # elapsed wall time instead.
        self._rate_sample_lock = threading.Lock()
        self._rate_sample_ts = time.monotonic()
        self._rate_sample_network_bytes = 0
        self._rate_sample_decode_bytes = 0
        self._rate_sample_disk_bytes = 0
        self._rate_network_bps = 0.0
        self._rate_decode_bps = 0.0
        self._rate_disk_bps = 0.0
        self._disk_commit_bytes_total = 0

        live_ids = {str(job.get("id")) for job in self.jobs}
        for job in self.jobs:
            if job.get("status") in ("downloading", "cancelling"):
                job["status"] = "queued"
                job["connections_used"] = 0
                job["speed_bps"] = 0
                job["cancel_requested"] = False
                job["status_detail"] = "Resuming interrupted transfer"
            elif job.get("status") == "retry_wait":
                job["status_detail"] = job.get("status_detail") or "Waiting to retry provider connection"
        try:
            DOWNLOAD_TEMP_DIR.mkdir(parents=True, exist_ok=True)
            for child in DOWNLOAD_TEMP_DIR.iterdir():
                if child.name not in live_ids:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
        except OSError:
            pass
        self._save()
        self.scheduler = threading.Thread(target=self._scheduler_loop, name="usenet-download-scheduler", daemon=True)
        self.scheduler.start()
        threading.Thread(target=self._resume_post_processing, name="usenet-post-resume", daemon=True).start()

    def _reconcile_statistics_locked(self):
        stats = self.statistics
        for job in self.jobs:
            if bool(job.get("statistics_counted")) or str(job.get("status") or "") != "completed":
                continue

            if bool(job.get("optional_missing")) or str(job.get("transfer_phase") or "") == "optional_skipped":
                job["statistics_counted"] = True
                continue
            transferred = max(0, int(job.get("actual_size", 0) or job.get("downloaded_bytes", 0) or 0))
            stats["total_downloaded_bytes"] = max(0, int(stats.get("total_downloaded_bytes", 0) or 0)) + transferred
            stats["completed_files"] = max(0, int(stats.get("completed_files", 0) or 0)) + 1
            stats["transfer_seconds"] = max(0.0, float(stats.get("transfer_seconds", 0) or 0)) + max(0.0, float(job.get("duration_seconds", 0) or 0))
            stats["peak_speed_bps"] = max(max(0, int(stats.get("peak_speed_bps", 0) or 0)), max(0, int(job.get("peak_speed_bps", 0) or job.get("average_speed_bps", 0) or 0)))
            stats["recovered_blocks"] = max(0, int(stats.get("recovered_blocks", 0) or 0)) + max(0, int(job.get("recovered_parts", 0) or 0))
            job["statistics_counted"] = True

    def _save(self):
        with self.lock:
            self._reconcile_statistics_locked()
            json_write_compact(DOWNLOADS_FILE, {
                "paused": self.paused, "concurrent_downloads": self.concurrent_downloads,
                "jobs": self.jobs, "collections": self.collections, "statistics": self.statistics,
            })
            self._last_hot_save_ts = time.monotonic()

    def _save_hot(self, min_interval: float = DOWNLOAD_PROGRESS_PERSIST_INTERVAL) -> bool:
        """Persist transient transfer state without hammering the download disk.

        The live UI reads state from memory, while the resume journal protects
        completed article blocks. Rewriting downloads.json several times per
        second for every active RAR member creates avoidable metadata I/O and
        can become a real bottleneck on HDDs. Important state transitions still
        call _save() directly; progress/waiting updates use this coalesced path.
        """
        now = time.monotonic()
        with self.lock:
            if now - float(self._last_hot_save_ts or 0.0) < max(0.25, float(min_interval or 0.0)):
                return False
            self._save()
            return True

    @staticmethod
    def _is_rar_payload_job(job: dict[str, Any] | None) -> bool:
        if not isinstance(job, dict):
            return False
        return bool(
            str(job.get("source") or "") in {"nzb", "browser_set"}
            and str(job.get("collection_id") or "")
            and str(job.get("collection_role") or "payload") == "payload"
            and _is_rar_volume(str(job.get("filename") or ""))
        )

    @staticmethod
    def _queue_item_key(job: dict[str, Any] | None) -> str:
        """Return the top-level queue item that owns a transfer job.

        Every file in the same package/collection has one collection_id and therefore
        one queue-item key. A manually queued standalone file is its own queue
        item. This boundary is intentionally stricter than file concurrency: only
        one key may receive network bandwidth at a time.
        """
        if not isinstance(job, dict):
            return ""
        collection_id = str(job.get("collection_id") or "").strip()
        if collection_id:
            return f"collection:{collection_id}"
        job_id = str(job.get("id") or "").strip()
        return f"job:{job_id}" if job_id else ""

    @staticmethod
    def _queue_item_sort_key(jobs: list[dict[str, Any]]) -> tuple[int, float]:
        priority_rank = {"high": 0, "normal": 1, "low": 2}
        if not jobs:
            return (9, float("inf"))
        return (
            min(priority_rank.get(str(j.get("priority", "normal")), 1) for j in jobs),
            min(float(j.get("queue_order", j.get("created_ts", 0)) or 0) for j in jobs),
        )

    def _foreground_queue_item_locked(self) -> str:
        """Choose the one queue item allowed to use NNTP bandwidth.

        An already active item always keeps ownership. Otherwise the oldest/highest
        priority non-paused item in queued/retry-wait state owns the network. A
        retry-wait owner deliberately holds its place so NewzDeck never jumps ahead
        and starts another episode during a short provider backoff.
        """
        active: dict[str, list[dict[str, Any]]] = {}
        for job_id in self.active_jobs:
            job = self._find_job(job_id)
            key = self._queue_item_key(job)
            if job and key and job.get("status") in {"downloading", "cancelling"}:
                active.setdefault(key, []).append(job)
        if active:
            return min(active.items(), key=lambda kv: self._queue_item_sort_key(kv[1]))[0]

        pending: dict[str, list[dict[str, Any]]] = {}
        for job in self.jobs:
            if job.get("paused") or job.get("status") not in {"queued", "retry_wait"}:
                continue
            key = self._queue_item_key(job)
            if key:
                pending.setdefault(key, []).append(job)
        if not pending:
            return ""
        return min(pending.items(), key=lambda kv: self._queue_item_sort_key(kv[1]))[0]

    @staticmethod
    def _package_job_sort_key(job: dict[str, Any]) -> tuple[int, int, float]:
        """Favor real payload data inside an NZB before sidecars/repair metadata."""
        role = str(job.get("collection_role") or "payload")
        role_rank = {"payload": 0, "par2": 1, "recovery_par2": 2, "auxiliary": 3}.get(role, 2)
        rar_index = _rar_volume_index(str(job.get("filename") or ""))
        volume_rank = int(rar_index) if rar_index is not None else 1_000_000
        return (role_rank, volume_rank, float(job.get("queue_order", job.get("created_ts", 0)) or 0))

    def _rar_parallelism_target_locked(self, jobs: list[dict[str, Any]]) -> int:
        """Return the rolling-window width for a multipart RAR collection.

        A RAR volume normally contains hundreds of article blocks and can keep a
        full NNTP connection pool busy by itself. Starting five or six files at
        once therefore adds Python coordinator/cache/disk contention without adding
        useful network work. Keep one lead volume plus one bounded read-ahead
        volume; tiny providers stay single-file.
        """
        if not jobs:
            return 1
        try:
            provider = provider_by_id(str(jobs[0].get("provider_id") or ""))
            _configured, _reserve, capacity = _provider_download_capacity(provider)
        except Exception:
            capacity = 20
        if len(jobs) < 2 or capacity < RAR_COLLECTION_MIN_CONNECTIONS_FOR_READ_AHEAD:
            return 1
        return min(RAR_COLLECTION_FAST_LANE_MAX, len(jobs))

    def _rar_connection_target_locked(self, job: dict[str, Any], capacity: int) -> int:
        """Allocate provider sockets inside the two-volume RAR rolling window.

        The lead volume receives roughly 80% of the provider budget and the next
        volume receives a small read-ahead share. Budgets are computed from queue
        order, including the queued read-ahead member, so the first coordinator
        never races ahead and claims the whole pool before lane two starts. The two
        targets always add up to the provider's download capacity.
        """
        capacity = max(1, int(capacity or 1))
        owner_key = self._queue_item_key(job)
        if not owner_key or not self._is_rar_payload_job(job):
            return capacity
        candidates = [
            item for item in self.jobs
            if self._queue_item_key(item) == owner_key
            and self._is_rar_payload_job(item)
            and item.get("status") in {"queued", "downloading", "cancelling"}
            and not item.get("paused")
        ]
        candidates.sort(key=self._package_job_sort_key)
        if len(candidates) < 2 or capacity < RAR_COLLECTION_MIN_CONNECTIONS_FOR_READ_AHEAD:
            return capacity if candidates and str(candidates[0].get("id") or "") == str(job.get("id") or "") else 1
        window = candidates[:RAR_COLLECTION_FAST_LANE_MAX]
        try:
            lane = next(i for i, item in enumerate(window) if str(item.get("id") or "") == str(job.get("id") or ""))
        except StopIteration:
            return 1
        read_ahead = int(math.ceil(capacity * RAR_READ_AHEAD_SHARE))
        read_ahead = max(RAR_READ_AHEAD_MIN_CONNECTIONS, min(RAR_READ_AHEAD_MAX_CONNECTIONS, read_ahead))
        read_ahead = min(read_ahead, max(1, capacity - 1))
        lead = max(1, capacity - read_ahead)
        return lead if lane == 0 else read_ahead

    def _queue_item_launch_plan_locked(self, owner_key: str) -> tuple[list[dict[str, Any]], int]:
        """Return launchable jobs and coordinator limit for the active queue item.

        One top-level NZB owns NNTP bandwidth at a time. Within a multipart RAR
        package NewzDeck uses a small adaptive read-ahead window so high-capacity
        providers do not run out of ready article work at volume boundaries. The
        provider pool remains the hard socket ceiling and each active file receives
        only its share of those slots, so this cannot exceed the configured NNTP
        connection count.
        """
        if not owner_key:
            return ([], 0)
        active = []
        for job_id in self.active_jobs:
            job = self._find_job(job_id)
            if job and self._queue_item_key(job) == owner_key and job.get("status") in {"downloading", "cancelling"}:
                active.append(job)
        queued = [
            j for j in self.jobs
            if self._queue_item_key(j) == owner_key
            and j.get("status") == "queued"
            and not j.get("paused")
            and str(j.get("id") or "") not in self.active_jobs
        ]
        queued.sort(key=self._package_job_sort_key)
        if not queued:
            return ([], len(active))

        active_rar = [j for j in active if self._is_rar_payload_job(j)]
        active_non_rar = [j for j in active if not self._is_rar_payload_job(j)]
        queued_rar = [j for j in queued if self._is_rar_payload_job(j)]

        if active_non_rar:
            return ([], 1)
        if active_rar:
            rar_jobs = active_rar + queued_rar
            return (queued_rar, min(MAX_CONCURRENT_DOWNLOADS, self._rar_parallelism_target_locked(rar_jobs)))
        if len(queued_rar) >= 2:
            return (queued_rar, min(MAX_CONCURRENT_DOWNLOADS, self._rar_parallelism_target_locked(queued_rar)))


        return ([queued[0]], 1)

    def _find_job(self, job_id: str) -> dict[str, Any] | None:
        return next((j for j in self.jobs if j.get("id") == job_id), None)

    def _collection_jobs_locked(self, collection_id: str) -> list[dict[str, Any]]:
        cid = str(collection_id or "")
        return [j for j in self.jobs if str(j.get("collection_id") or "") == cid] if cid else []

    @staticmethod
    def _estimate_recovery_block_bytes(catalog: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> int:
        samples: list[int] = []
        for entry in list(catalog or []):
            blocks = max(0, int(entry.get("par2_recovery_blocks", 0) or 0))
            size = max(0, int(entry.get("bytes", 0) or 0))
            if blocks and size:
                samples.append(max(1, size // blocks))
        for job in jobs:
            blocks = max(0, int(job.get("par2_recovery_blocks", 0) or 0))
            size = max(0, int(job.get("expected_bytes", 0) or 0))
            if blocks and size:
                samples.append(max(1, size // blocks))
        if not samples:
            return 0
        samples.sort()
        return samples[len(samples) // 2]

    def _collection_health_locked(self, collection_id: str) -> dict[str, Any]:
        jobs = self._collection_jobs_locked(collection_id)
        rec = self.collections.get(str(collection_id or ""), {})
        catalog = list(rec.get("recovery_catalog") or []) if isinstance(rec, dict) else []
        missing_bytes = sum(max(0, int(j.get("repair_missing_bytes", j.get("missing_bytes", 0)) or 0))
                            for j in jobs if str(j.get("collection_role") or "payload") == "payload"
                            and (str(j.get("integrity_status") or "") == "repair_needed" or j.get("status") == "failed"))
        missing_articles = sum(max(0, int(j.get("repair_missing_blocks", j.get("failed_parts", 0)) or 0))
                              for j in jobs if str(j.get("collection_role") or "payload") == "payload"
                              and (str(j.get("integrity_status") or "") == "repair_needed" or j.get("status") == "failed"))
        block_bytes = self._estimate_recovery_block_bytes(catalog, jobs)
        estimated_needed = int(math.ceil(missing_bytes / block_bytes)) if missing_bytes and block_bytes else missing_articles
        if estimated_needed:
            estimated_needed += 2
        queued_recovery = sum(max(0, int(j.get("par2_recovery_blocks", 0) or 0)) for j in jobs if str(j.get("collection_role") or "") == "recovery_par2")
        deferred_recovery = sum(max(0, int(x.get("par2_recovery_blocks", 0) or 0)) for x in catalog)
        available_recovery = queued_recovery + deferred_recovery
        recovered_provider_blocks = sum(max(0, int(j.get("recovered_parts", 0) or 0)) for j in jobs)
        tool = bool(_par2_path())
        if missing_bytes <= 0 and not any(str(j.get("integrity_status") or "") == "repair_needed" for j in jobs):
            state = "healthy"
            label = "Healthy"
        elif not any(j.get("is_par2") for j in jobs) and not catalog:
            state = "incomplete"
            label = "Incomplete — no PAR2 recovery data"
        elif estimated_needed and available_recovery >= estimated_needed:
            state = "repairable" if tool else "repair_tool_needed"
            label = "Repairable" if tool else "Repair data available — PAR2 tool needed"
        elif available_recovery > 0:
            state = "recovery_limited"
            label = "Recovery data may be insufficient"
        else:
            state = "incomplete"
            label = "Incomplete"
        return {
            "state": state, "label": label, "missing_bytes": missing_bytes,
            "missing_articles": missing_articles, "estimated_blocks_needed": max(0, estimated_needed),
            "recovery_blocks_queued": queued_recovery, "recovery_blocks_deferred": deferred_recovery,
            "recovery_blocks_available": available_recovery, "recovered_provider_blocks": recovered_provider_blocks,
            "recovery_block_bytes_estimate": block_bytes, "par2_tool_available": tool,
        }

    def _collection_snapshots_locked(self) -> list[dict[str, Any]]:
        ids: list[str] = []
        seen: set[str] = set()
        for job in self.jobs:
            cid = str(job.get("collection_id") or "")
            if cid and cid not in seen:
                seen.add(cid); ids.append(cid)
        for cid in self.collections:
            if cid and cid not in seen:
                ids.append(cid); seen.add(cid)
        out: list[dict[str, Any]] = []
        priority_rank = {"high": 0, "normal": 1, "low": 2}
        for cid in ids:
            jobs = self._collection_jobs_locked(cid)
            if not jobs:
                continue
            rec = self.collections.get(cid, {})
            direct_state = rec.get("direct_unpack") if isinstance(rec, dict) and isinstance(rec.get("direct_unpack"), dict) else {}
            direct_active = str(direct_state.get("status") or "") == "active"
            blocking_jobs = [j for j in jobs if nzb_job_blocks_collection(j)]
            optional_jobs = [j for j in jobs if not nzb_job_blocks_collection(j)]
            status_jobs = blocking_jobs or jobs
            expected = sum(max(0, int(j.get("expected_bytes", 0) or 0)) for j in blocking_jobs)
            downloaded = sum(min(max(0, int(j.get("downloaded_bytes", 0) or 0)), max(0, int(j.get("expected_bytes", 0) or 0)) or max(0, int(j.get("downloaded_bytes", 0) or 0))) for j in blocking_jobs)
            speed = sum(max(0, int(j.get("speed_bps", 0) or 0)) for j in status_jobs if j.get("status") == "downloading")
            peak = max([max(0, int(j.get("peak_speed_bps", 0) or 0)) for j in status_jobs] + [0])
            connections = sum(max(0, int(j.get("connections_used", 0) or 0)) for j in status_jobs)
            statuses = [str(j.get("status") or "queued") for j in status_jobs]
            post_statuses = [str(j.get("post_status") or "") for j in jobs]
            health = self._collection_health_locked(cid)
            if direct_active and any(s in {"downloading", "queued", "retry_wait"} for s in statuses):
                status = "downloading"
            elif any(s in {"verifying", "repairing", "extracting", "importing", "queued"} for s in post_statuses if s):
                status = "post_processing"
            elif any(s == "downloading" for s in statuses):
                status = "downloading"
            elif any(s == "retry_wait" for s in statuses):
                status = "retry_wait"
            elif any(s == "queued" for s in statuses):
                status = "queued"
            elif any(str(j.get("integrity_status") or "") == "repair_needed" for j in jobs):
                status = "repair_needed"
            elif any(s == "failed" for s in statuses):
                status = "failed"
            elif all(s == "cancelled" for s in statuses):
                status = "cancelled"
            elif all(s in {"completed", "cancelled"} for s in statuses) and any(s == "completed" for s in statuses):
                status = "completed"
            else:
                status = statuses[0] if statuses else "queued"
            post_priority = ["failed", "needs_password", "needs_tool", "needs_attention", "blocked", "repairing", "extracting", "importing", "verifying", "waiting", "queued", "completed", "not_needed", "disabled", "cancelled", ""]
            post = next((p for p in post_priority if p and p in post_statuses), "")
            post_progress = max([max(0, min(100, int(j.get("post_progress", 0) or 0))) for j in jobs] + [0])
            post_message = next((str(j.get("post_message") or "") for j in jobs if j.get("post_message")), "")
            if direct_active:
                post_progress = max(post_progress, max(0, min(99, int(direct_state.get("progress", 0) or 0))))
                post_message = str(direct_state.get("message") or post_message or "Direct Unpacking while download continues")
            priority = min((str(j.get("priority") or "normal") for j in jobs), key=lambda x: priority_rank.get(x, 1), default="normal")
            created = min([float(j.get("created_ts", 0) or 0) for j in jobs] + [float(rec.get("created_ts", time.time()) or time.time())])
            completed_ts = max([float(j.get("completed_ts", 0) or 0) for j in jobs] + [0.0])
            started_ts_values = [float(j.get("started_ts", 0) or 0) for j in jobs if float(j.get("started_ts", 0) or 0) > 0]
            started_ts = min(started_ts_values) if started_ts_values else 0.0
            duration = max(0.0, (completed_ts or time.time()) - started_ts) if started_ts else 0.0
            avg_speed = int(downloaded / duration) if duration > 0 and downloaded > 0 else 0
            automation_context = dict(rec.get("automation_context") or next((j.get("automation_context") for j in jobs if isinstance(j.get("automation_context"),dict)), {}) or {})
            automation_import = dict(rec.get("automation_import") or {}) if isinstance(rec.get("automation_import"),dict) else {}
            auto_title=str(automation_context.get('title') or '')
            auto_kind=str(automation_context.get('kind') or '')
            auto_label=''
            if auto_title and auto_kind=='tv' and automation_context.get('season') is not None and automation_context.get('episode') is not None:
                auto_label=f"{auto_title} • S{int(automation_context.get('season') or 0):02d}E{int(automation_context.get('episode') or 0):02d}"
                if automation_context.get('episode_title'): auto_label += f" • {automation_context.get('episode_title')}"
            elif auto_title and auto_kind=='tv' and automation_context.get('season') is not None:
                auto_label=f"{auto_title} • Season {int(automation_context.get('season') or 0)}"
            elif auto_title:
                auto_label=auto_title
            auto_destination=str(automation_import.get('destination') or automation_context.get('planned_root_folder') or '')
            out.append({
                "id": cid, "name": str(rec.get("name") or jobs[0].get("collection_name") or "Imported NZB"),
                "source_name": str(rec.get("source_name") or ""), "status": status, "priority": priority,
                "category": str(rec.get("category") or jobs[0].get("category") or ""),
                "automation_source": str(rec.get("automation_source") or jobs[0].get("automation_source") or ""),
                "automation_context": automation_context,
                "automation_import": automation_import,
                "automation_label": auto_label, "automation_destination": auto_destination,
                "job_ids": [str(j.get("id")) for j in jobs], "files": len(blocking_jobs), "all_files": len(jobs),
                "optional_files": len(optional_jobs),
                "optional_skipped_files": sum(1 for j in optional_jobs if bool(j.get("optional_missing"))),
                "payload_files": sum(1 for j in blocking_jobs if str(j.get("collection_role") or "payload") == "payload"),
                "recovery_files": sum(1 for j in blocking_jobs if str(j.get("collection_role") or "") == "recovery_par2"),
                "completed_files": sum(1 for j in blocking_jobs if j.get("status") == "completed"),
                "failed_files": sum(1 for j in blocking_jobs if j.get("status") == "failed"),
                "queued_files": sum(1 for j in blocking_jobs if j.get("status") == "queued"),
                "active_files": sum(1 for j in blocking_jobs if j.get("status") in {"downloading", "cancelling"}),
                "expected_bytes": expected, "downloaded_bytes": downloaded, "speed_bps": speed,
                "peak_speed_bps": peak, "connections_used": connections,
                "retry_count": sum(max(0, int(j.get("retry_count", 0) or 0)) for j in jobs),
                "recovered_parts": sum(max(0, int(j.get("recovered_parts", 0) or 0)) for j in jobs),
                "failed_parts": sum(max(0, int(j.get("failed_parts", 0) or 0)) for j in jobs),
                "post_status": post, "post_progress": post_progress, "post_message": post_message,
                "direct_unpack_status": str(direct_state.get("status") or ""),
                "direct_unpack_progress": max(0, min(100, int(direct_state.get("progress", 0) or 0))),
                "direct_unpack_message": str(direct_state.get("message") or ""),
                "health": health, "created_ts": created, "started_ts": started_ts, "completed_ts": completed_ts,
                "average_speed_bps": avg_speed, "duration_seconds": round(duration, 3),
                "folder": str(DOWNLOAD_DIR / safe_folder_name(str(rec.get("category_folder") or jobs[0].get("category_folder") or "")) / safe_folder_name(str(rec.get("name") or jobs[0].get("collection_name") or "Imported NZB"))) if str(rec.get("category_folder") or jobs[0].get("category_folder") or "") else str(DOWNLOAD_DIR / safe_folder_name(str(rec.get("name") or jobs[0].get("collection_name") or "Imported NZB"))),
                "deferred_recovery_files": len(list(rec.get("recovery_catalog") or [])),
            })
        def collection_display_key(x: dict[str, Any]) -> tuple[Any, ...]:
            status = str(x.get("status") or "queued")
            created = float(x.get("created_ts", 0) or 0)
            if status in {"downloading", "queued", "retry_wait", "post_processing", "repair_needed"}:
                return (0, priority_rank.get(str(x.get("priority") or "normal"), 1), created)
            completed = float(x.get("completed_ts", 0) or 0)
            started = float(x.get("started_ts", 0) or 0)
            terminal_time = completed if completed > 0 else max(started, created)
            return (1, 0, -terminal_time, -created, str(x.get("id") or ""))
        out.sort(key=collection_display_key)
        return out

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            self._reconcile_statistics_locked()
            jobs = []
            priority_rank = {"high": 0, "normal": 1, "low": 2}
            def display_key(x):
                if x.get("status") in ("queued", "downloading", "retry_wait", "cancelling"):
                    return (0, priority_rank.get(str(x.get("priority", "normal")), 1), float(x.get("queue_order", x.get("created_ts", 0)) or 0))
                terminal_time = float(x.get("completed_ts") or x.get("started_ts") or x.get("created_ts") or 0)
                return (1, 0, -terminal_time)
            for job in sorted(self.jobs, key=display_key):
                copy = {k: v for k, v in job.items() if k not in ("segments", "media", "cancel_requested")}
                jobs.append(copy)
            counts = {k: 0 for k in ("queued", "downloading", "retry_wait", "completed", "failed", "cancelled", "cancelling")}
            for job in self.jobs:
                status = job.get("status", "queued")
                counts[status] = counts.get(status, 0) + 1
            active_transfer = [j for j in self.jobs if j.get("status") in ("downloading", "cancelling") and not j.get("paused")]
            total_speed = sum(max(0, int(j.get("speed_bps", 0) or 0)) for j in active_transfer)
            now = time.time()
            avg_parts = []
            for j in active_transfer:
                started = float(j.get("started_ts", 0) or 0)
                done = max(0, int(j.get("downloaded_bytes", 0) or 0))
                if started > 0 and now > started and done > 0:
                    avg_parts.append(done / max(1.0, now - started))
            average_speed = int(sum(avg_parts)) if avg_parts else 0
            remaining_bytes = 0
            for j in self.jobs:
                if j.get("status") not in {"queued", "downloading", "retry_wait", "cancelling"}:
                    continue
                expected = max(0, int(j.get("expected_bytes", 0) or 0))
                done = max(0, int(j.get("downloaded_bytes", 0) or 0)) if j.get("status") not in {"queued", "retry_wait"} else max(0, int(j.get("downloaded_bytes", 0) or 0))
                remaining_bytes += max(0, expected - done)
            post_active_count = sum(1 for j in self.jobs if str(j.get("post_status") or "") in {"queued","verifying","repairing","extracting","importing"})
            concurrency = PACKAGE_QUEUE_CONCURRENCY
            paused = self.paused
            collections = self._collection_snapshots_locked()
            statistics = dict(self.statistics)
            stats_seconds = max(0.0, float(statistics.get("transfer_seconds", 0) or 0))
            statistics["average_speed_bps"] = int(max(0, int(statistics.get("total_downloaded_bytes", 0) or 0)) / stats_seconds) if stats_seconds > 0 else 0
            soft_misses = sum(sum(1 for e in (j.get("segment_errors") or []) if str(e.get("code") or "") in {"article_soft_missing", "article_propagating"}) for j in self.jobs)
            native_parts = sum(max(0, int(j.get("native_parts", 0) or 0)) for j in self.jobs)
            disk_counter = int(self._disk_commit_bytes_total)
        pool = download_pool_stats()
        yenc_stats = pool.get("yenc") or {}
        network_counter = max(0, int(pool.get("bytes_wire_received", 0) or 0))
        if network_counter <= 0:
            network_counter = max(0, int(pool.get("bytes_decoded", 0) or 0))
        decode_counter = max(0, int(yenc_stats.get("native_bytes", 0) or 0)) + max(0, int(yenc_stats.get("fallback_bytes", 0) or 0))
        now_sample = time.monotonic()
        with self._rate_sample_lock:
            elapsed = max(0.001, now_sample - self._rate_sample_ts)
            if elapsed >= 0.20:
                def smooth(old: float, counter: int, previous: int) -> float:
                    raw = max(0.0, float(counter - previous) / elapsed) if counter >= previous else 0.0
                    return raw if old <= 0 else (old * 0.55 + raw * 0.45)
                self._rate_network_bps = smooth(self._rate_network_bps, network_counter, self._rate_sample_network_bytes)
                self._rate_decode_bps = smooth(self._rate_decode_bps, decode_counter, self._rate_sample_decode_bytes)
                self._rate_disk_bps = smooth(self._rate_disk_bps, disk_counter, self._rate_sample_disk_bytes)
                self._rate_sample_ts = now_sample
                self._rate_sample_network_bytes = network_counter
                self._rate_sample_decode_bytes = decode_counter
                self._rate_sample_disk_bytes = disk_counter
            wall_network_rate = int(self._rate_network_bps)
            wall_decode_rate = int(self._rate_decode_bps)
            wall_disk_rate = int(self._rate_disk_bps)
        capacity = max(0, int(pool.get("capacity", 0) or 0))
        effective_capacity = max(1, int(pool.get("effective_capacity", 0) or capacity or 1))
        active_requests = max(0, int(pool.get("active", 0) or 0))
        pipeline_depth = max(1, int(pool.get("pipeline_depth", 1) or 1))
        with self.lock:
            rar_lanes_active = sum(1 for jid, fut in self.active_jobs.items() if not fut.done() and self._is_rar_payload_job(self._find_job(jid)))
            rar_candidates = [j for j in self.jobs if self._is_rar_payload_job(j) and j.get("status") in {"queued", "downloading", "cancelling"}]
            rar_lanes_target = self._rar_parallelism_target_locked(rar_candidates) if len(rar_candidates) >= 2 else min(1, len(rar_candidates))
        telemetry = {
            "network_rate_bps": wall_network_rate or total_speed,
            "decode_rate_bps": wall_decode_rate,
            "disk_rate_bps": wall_disk_rate,
            "slot_utilization_pct": round((100.0 * active_requests / effective_capacity), 1) if effective_capacity else 0.0,
            "connection_target": effective_capacity,
            "connection_ceiling": capacity,
            "inflight_articles": active_requests * pipeline_depth,
            "rar_lanes_active": rar_lanes_active,
            "rar_lanes_target": rar_lanes_target,
            "soft_misses": soft_misses,
            "native_parts": native_parts,
            "bandwidth": DOWNLOAD_BANDWIDTH_LIMITER.current(),
        }
        return {
            "paused": paused, "jobs": jobs, "counts": counts, "folder": str(DOWNLOAD_DIR),
            "concurrent_downloads": concurrency, "max_concurrent_downloads": PACKAGE_QUEUE_CONCURRENCY,
            "queue_mode": "single_package", "rar_internal_parallelism": RAR_COLLECTION_FAST_LANE_MAX,
            "total_speed_bps": total_speed, "average_speed_bps": average_speed,
            "remaining_bytes": remaining_bytes,
            "queue_eta_seconds": int(remaining_bytes / total_speed) if total_speed > 0 else 0,
            "post_processing_active": post_active_count,
            "connections": pool, "thumbnail_cache": thumbnail_cache_stats(),
            "collections": collections, "telemetry": telemetry, "statistics": statistics,
        }

    @staticmethod
    def _job_identity(provider_id: str, group: str, media: dict[str, Any], segments: list[dict[str, Any]]) -> str:
        refs = []
        for seg in segments:
            article = seg.get("article")
            refs.append((str(seg.get("message_id") or ""), str(article if article is not None else ""), int(seg.get("part", 1) or 1)))
        raw = json.dumps({
            "provider": provider_id,
            "group": group,
            "filename": media.get("filename", ""),
            "articles": refs,
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def add(self, provider_id: str, group: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        if not group:
            raise ValueError("Newsgroup is required")
        if not items:
            raise ValueError("Select at least one media item")
        if len(items) > 500:
            raise ValueError("Add up to 500 files to the queue at a time")
        origin_provider = provider_by_id(provider_id)
        provider = resolve_provider_for_purpose(provider_id, "downloads")
        download_provider_id = str(provider.get("id", provider_id))
        now = time.time()
        added, duplicates = [], []
        settings = json_read(SETTINGS_FILE, {})
        destination_mode = str(settings.get("download_organization", DEFAULT_DOWNLOAD_ORGANIZATION)).lower()
        if destination_mode not in {"flat", "newsgroup", "kind", "newsgroup_kind"}:
            destination_mode = DEFAULT_DOWNLOAD_ORGANIZATION
        with self.lock:
            existing = {j.get("identity") for j in self.jobs if j.get("status") in ("queued", "downloading", "retry_wait", "cancelling")}
            queue_tail = max([float(j.get("queue_order", 0) or 0) for j in self.jobs] + [0.0])
            browser_collections: dict[str, dict[str, Any]] = {}
            for item in items:
                media = item.get("media") or {}
                segments = item.get("segments") or []
                if not isinstance(media, dict) or not isinstance(segments, list) or not segments:
                    continue
                filename = safe_download_name(media.get("filename") or "download.bin")
                identity = self._job_identity(provider_id, group, media, segments)
                if identity in existing:
                    duplicates.append(filename)
                    continue
                expected = sum(max(0, int(s.get("bytes", 0) or 0)) for s in segments)
                job_segments = [dict(seg) for seg in segments]
                if download_provider_id != provider_id:
                    for seg in job_segments:
                        seg["article"] = None
                job = {
                    "id": secrets.token_hex(8), "identity": identity,
                    "provider_id": download_provider_id, "provider_name": provider.get("name") or provider.get("host") or "Provider",
                    "origin_provider_id": provider_id, "origin_provider_name": origin_provider.get("name") or origin_provider.get("host") or "Provider",
                    "group": group, "filename": filename, "kind": media.get("kind", "file"),
                    "segments": job_segments, "media": media,
                    "status": "queued", "expected_bytes": expected, "downloaded_bytes": 0,
                    "current_part": 0, "total_parts": len(segments), "speed_bps": 0, "connections_used": 0,
                    "path": "", "error": "", "created_ts": now, "started_ts": 0,
                    "completed_ts": 0, "cancel_requested": False,
                    "recovered_parts": 0, "recovery_sources": {},
                    "priority": str(item.get("priority") or "normal") if str(item.get("priority") or "normal") in {"high","normal","low"} else "normal", "paused": False, "queue_order": queue_tail + len(added) + 1,
                    "destination_mode": destination_mode,
                    "destination_subdir": safe_folder_name(str(item.get("destination_subdir", "") or "")) if item.get("destination_subdir") else "",
                    "category": str(item.get("category") or "")[:80],
                    "category_folder": safe_folder_name(str(item.get("category_folder") or "")) if item.get("category_folder") else "",
                    "automation_source": str(item.get("automation_source") or "")[:40],
                    "source": str(item.get("source", "browser") or "browser"),
                    "collection_id": str(item.get("collection_id", "") or ""),
                    "collection_name": str(item.get("collection_name", "") or ""),
                    "collection_expected": max(0, int(item.get("collection_expected", 0) or 0)),
                    "collection_required_expected": max(0, int(item.get("collection_required_expected", 0) or 0)),
                    "post_status": "", "post_progress": 0, "post_message": "",
                    "processed_parts": 0, "successful_parts": 0, "failed_parts": 0, "missing_bytes": 0,
                    "retry_count": 0, "auto_retry_count": 0, "retry_at_ts": 0,
                    "error_code": "", "error_label": "", "error_suggestion": "", "error_retryable": False,
                    "segment_errors": [], "last_activity_ts": 0, "status_detail": "Waiting in queue", "resumed_parts": 0, "transfer_phase": "queued",
                    "subject": str(item.get("subject", "")), "poster": str(item.get("from", "")),
                    "message_id": str(item.get("message_id", "")),
                    "posted_ts": max(0, int(item.get("posted_ts", 0) or 0)),
                    "is_par2": bool(item.get("is_par2")), "is_par2_volume": bool(item.get("is_par2_volume")),
                    "is_auxiliary": bool(item.get("is_auxiliary") or (str(item.get("source") or "") == "nzb" and nzb_auxiliary_file(filename))),
                    "optional_missing": False,
                    "par2_recovery_blocks": max(0, int(item.get("par2_recovery_blocks", 0) or 0)),
                    "collection_role": str(item.get("collection_role") or ("recovery_par2" if item.get("is_par2_volume") else "par2" if item.get("is_par2") else "auxiliary" if (item.get("is_auxiliary") or (str(item.get("source") or "") == "nzb" and nzb_auxiliary_file(filename))) else "payload")),
                    "integrity_status": "unknown", "repair_missing_bytes": 0, "repair_missing_blocks": 0,
                    "average_speed_bps": 0, "duration_seconds": 0.0,
                }
                self.jobs.append(job)
                existing.add(identity)
                added.append({"id": job["id"], "filename": filename})
                cid = str(job.get("collection_id") or "")
                if cid and str(job.get("source") or "") == "browser_set":
                    browser_collections.setdefault(cid, {
                        "id": cid, "name": str(job.get("collection_name") or Path(filename).stem or "Newsgroup package"),
                        "source_name": "Newsgroup browser", "provider_id": provider_id,
                        "created_ts": now, "priority": str(job.get("priority") or "normal"),
                        "recovery_catalog": [], "recovery_queued_names": [],
                        "recovery_requested_blocks": 0, "recovery_queued_blocks": 0,
                        "category": str(job.get("category") or ""), "category_folder": str(job.get("category_folder") or ""),
                        "automation_source": "", "automation_context": {},
                        "required_expected": max(0, int(job.get("collection_required_expected", 0) or 0)),
                        "original_file_count": max(0, int(job.get("collection_expected", 0) or 0)),
                    })
            for cid, rec in browser_collections.items():
                if cid not in self.collections and self._collection_jobs_locked(cid):
                    self.collections[cid] = rec
            self._save()
        self.wake.set()
        disk_warning = ""
        try:
            free = shutil.disk_usage(DOWNLOAD_DIR).free
            queued_need = sum(max(0, int(j.get("expected_bytes",0) or 0)) for j in self.jobs if j.get("status") in {"queued","downloading","cancelling"})
            settings_now = json_read(SETTINGS_FILE, {})
            reserve = int(max(0.25, min(50.0, float(settings_now.get("disk_reserve_gb",1.0) or 1.0))) * 1024**3)
            if queued_need + reserve > free:
                disk_warning = f"Queued downloads total about {queued_need/1024**3:.1f} GB but only {free/1024**3:.1f} GB is free. Downloads will stop safely before the disk reserve is crossed."
                DIAGNOSTICS.event("warning", "storage", disk_warning)
        except OSError:
            pass
        return {"added": added, "duplicates": duplicates, "folder": str(DOWNLOAD_DIR), "disk_warning": disk_warning}

    def _register_nzb_collection(self, provider_id: str, collection_id: str, collection_name: str,
                                 parsed: dict[str, Any], selected_indices: list[int]) -> None:
        selected = set(int(i) for i in selected_indices)
        recovery_catalog: list[dict[str, Any]] = []
        for index, entry in enumerate(list(parsed.get("files") or [])):
            if index in selected or not bool(entry.get("is_par2")):
                continue
            copied = {**entry, "collection_role": ("recovery_par2" if entry.get("is_par2_volume") else "par2")}
            recovery_catalog.append(copied)
        recovery_catalog.sort(key=lambda x: (0 if not x.get("is_par2_volume") else 1,
                                             int(x.get("par2_recovery_start", 0) or 0),
                                             int(x.get("par2_recovery_blocks", 0) or 0)))
        with self.lock:
            self.collections[collection_id] = {
                "id": collection_id, "name": collection_name, "source_name": str(parsed.get("source_name") or ""),
                "provider_id": provider_id, "created_ts": time.time(), "priority": "normal",
                "recovery_catalog": recovery_catalog, "recovery_queued_names": [],
                "recovery_requested_blocks": 0, "recovery_queued_blocks": 0,
                "original_file_count": len(list(parsed.get("files") or [])),
                "selected_file_count": len(selected),
                "category": "", "category_folder": "", "automation_source": "", "automation_context": parsed.get("automation_context") if isinstance(parsed.get("automation_context"), dict) else {},
            }
            self._save()

    def _queue_recovery_for_collection(self, collection_id: str, *, missing_bytes: int = 0,
                                       minimum_blocks: int = 0, force_all: bool = False) -> dict[str, Any]:
        """Queue only the deferred PAR2 volumes needed for a repair attempt.

        Recovery volume names advertise their recovery-block count (volNNN+MM).
        When the PAR2 index has not yet been downloaded, estimate slice size from
        the NZB byte counts. This is intentionally conservative and adds two
        safety blocks. Additional volumes can be queued later if par2cmdline says
        more recovery is required.
        """
        cid = str(collection_id or "")
        with self.lock:
            rec = self.collections.get(cid)
            if not isinstance(rec, dict):
                return {"queued": [], "blocks": 0, "reason": "No deferred PAR2 recovery data is available for this NZB"}
            jobs = self._collection_jobs_locked(cid)
            catalog = list(rec.get("recovery_catalog") or [])
            if not catalog:
                return {"queued": [], "blocks": 0, "reason": "No deferred PAR2 recovery volumes remain"}
            existing_names = {str(j.get("filename") or "").casefold() for j in jobs}
            already_blocks = sum(max(0, int(j.get("par2_recovery_blocks", 0) or 0)) for j in jobs
                                 if str(j.get("collection_role") or "") == "recovery_par2")
            block_bytes = self._estimate_recovery_block_bytes(catalog, jobs)
            required = max(0, int(minimum_blocks or 0))
            if missing_bytes > 0 and block_bytes > 0:
                required = max(required, int(math.ceil(max(0, int(missing_bytes)) / block_bytes)) + 2)
            if required <= 0:
                required = 1
            need_more = max(0, required - already_blocks)
            to_queue: list[dict[str, Any]] = []
            queued_blocks = 0
            base = [x for x in catalog if bool(x.get("is_par2")) and not bool(x.get("is_par2_volume"))
                    and str((x.get("media") or {}).get("filename") or "").casefold() not in existing_names]
            if base:
                to_queue.append(base[0])
            for entry in catalog:
                if not bool(entry.get("is_par2_volume")):
                    continue
                name = str((entry.get("media") or {}).get("filename") or "")
                if not name or name.casefold() in existing_names:
                    continue
                blocks = max(0, int(entry.get("par2_recovery_blocks", 0) or 0))
                if force_all or queued_blocks < need_more:
                    to_queue.append(entry); queued_blocks += blocks
                if not force_all and queued_blocks >= need_more:
                    break
            provider_id = str(rec.get("provider_id") or (jobs[0].get("origin_provider_id") if jobs else "") or "")
            collection_name = str(rec.get("name") or (jobs[0].get("collection_name") if jobs else "Imported NZB"))
        if not to_queue or not provider_id:
            return {"queued": [], "blocks": 0, "required_blocks": required, "reason": "No additional recovery volume was required"}
        added: list[dict[str, Any]] = []
        queued_names: list[str] = []
        actual_blocks = 0
        for entry in to_queue:
            group = str(entry.get("group") or "").strip()
            if not group:
                continue
            role = "recovery_par2" if entry.get("is_par2_volume") else "par2"
            item = {**entry, "source": "nzb", "collection_id": cid, "collection_name": collection_name,
                    "destination_subdir": collection_name, "collection_role": role}
            try:
                result = self.add(provider_id, group, [item])
                newly = list(result.get("added") or [])
                if newly:
                    added.extend(newly)
                    name = str((entry.get("media") or {}).get("filename") or "")
                    queued_names.append(name)
                    actual_blocks += max(0, int(entry.get("par2_recovery_blocks", 0) or 0))
            except Exception as exc:
                DIAGNOSTICS.event("warning", "par2", f"Could not queue recovery volume: {exc}", collection=cid)
        if added:
            with self.lock:
                rec = self.collections.get(cid, {})
                queued_set = set(str(x).casefold() for x in queued_names)
                rec["recovery_catalog"] = [x for x in list(rec.get("recovery_catalog") or [])
                                           if str((x.get("media") or {}).get("filename") or "").casefold() not in queued_set]
                prior = list(rec.get("recovery_queued_names") or [])
                rec["recovery_queued_names"] = prior + [x for x in queued_names if x not in prior]
                rec["recovery_requested_blocks"] = max(int(rec.get("recovery_requested_blocks", 0) or 0), required)
                rec["recovery_queued_blocks"] = int(rec.get("recovery_queued_blocks", 0) or 0) + actual_blocks
                current_jobs = self._collection_jobs_locked(cid)
                expected_files = len(current_jobs)
                for target in current_jobs:
                    target["collection_expected"] = expected_files
                    if target.get("status") == "completed" and str(target.get("post_status") or "") in {"blocked", "cancelled", ""}:
                        target["post_status"] = "waiting"
                        target["post_progress"] = 0
                        target["post_message"] = "Waiting for PAR2 recovery volumes"
                self._save()
            self.wake.set()
            DIAGNOSTICS.event("info", "par2", f"Queued {len(added)} deferred PAR2 recovery file(s)", collection=cid, blocks=actual_blocks, required=required)
        return {"queued": added, "blocks": actual_blocks, "required_blocks": required, "names": queued_names}

    def add_nzb(self, provider_id: str, source_name: str, raw: bytes, automation_context: dict[str, Any] | None = None) -> dict[str, Any]:
        parsed = parse_nzb_bytes(raw, source_name)
        parsed["automation_context"] = dict(automation_context) if isinstance(automation_context, dict) else {}
        if parsed["automation_context"]:
            parsed["automation_source"] = str(parsed["automation_context"].get("source") or "automation_grab")
        collection_id = secrets.token_hex(8)
        collection_name = parsed["name"]
        parsed["source_name"] = source_name
        automation = automation_category_for(collection_name)
        automation_source = str(parsed.get("automation_source") or "")
        self._register_nzb_collection(provider_id, collection_id, collection_name, parsed, list(range(len(parsed.get("files") or []))))
        with self.lock:
            rec = self.collections.get(collection_id, {})
            rec["category"] = automation.get("name", ""); rec["category_folder"] = automation.get("folder", ""); rec["automation_source"] = automation_source
            rec["automation_context"] = parsed.get("automation_context") if isinstance(parsed.get("automation_context"), dict) else {}
            self._save()
        added: list[dict[str, Any]] = []
        duplicates: list[str] = []
        skipped: list[dict[str, str]] = []
        warnings: list[str] = []
        expected_collection_files = sum(1 for entry in parsed["files"] if str(entry.get("group") or "").strip())
        for entry in parsed["files"]:
            group = str(entry.get("group") or "").strip()
            if not group:
                skipped.append({"filename": entry["media"]["filename"], "reason": "NZB entry has no newsgroup"})
                continue
            item = {**entry, "source": "nzb", "collection_id": collection_id, "collection_name": collection_name, "collection_expected": expected_collection_files, "destination_subdir": collection_name,
                    "category": automation.get("name", ""), "category_folder": automation.get("folder", ""), "priority": automation.get("priority", "normal"), "automation_source": automation_source, "automation_context": parsed.get("automation_context") if isinstance(parsed.get("automation_context"), dict) else {},
                    "collection_role": ("recovery_par2" if entry.get("is_par2_volume") else "par2" if entry.get("is_par2") else "auxiliary" if entry.get("is_auxiliary") else "payload")}
            try:
                result = self.add(provider_id, group, [item])
                added.extend(result.get("added", []))
                duplicates.extend(result.get("duplicates", []))
                if result.get("disk_warning") and result["disk_warning"] not in warnings:
                    warnings.append(result["disk_warning"])
            except Exception as exc:
                skipped.append({"filename": entry["media"]["filename"], "reason": str(exc)})
        if not added and not duplicates:
            reason = skipped[0]["reason"] if skipped else "No NZB entries could be queued"
            raise ValueError(reason)
        with self.lock:
            jobs = self._collection_jobs_locked(collection_id)
            required_expected = sum(1 for j in jobs if nzb_job_blocks_collection(j))
            for target in jobs:
                target["collection_expected"] = len(jobs)
                target["collection_required_expected"] = required_expected
            rec = self.collections.get(collection_id)
            if isinstance(rec, dict):
                rec["required_expected"] = required_expected
            self._save()
        DIAGNOSTICS.event("info", "nzb", f"Imported NZB {source_name}", files=len(parsed["files"]), queued=len(added), skipped=len(skipped))
        return {
            "ok": True, "collection_id": collection_id, "collection_name": collection_name,
            "files": len(parsed["files"]), "added": added, "duplicates": duplicates,
            "skipped": skipped, "warnings": warnings, "folder": str(DOWNLOAD_DIR / collection_name),
        }

    def add_nzb_selection(self, provider_id: str, parsed: dict[str, Any], selected_indices: list[int] | None = None, collection_name: str = "") -> dict[str, Any]:
        files = list(parsed.get("files") or [])
        if selected_indices is None:
            selected = list(range(len(files)))
        else:
            selected = sorted({int(i) for i in selected_indices if isinstance(i, int) or str(i).isdigit()})
            selected = [i for i in selected if 0 <= i < len(files)]
        if not selected:
            raise ValueError("Select at least one NZB file")
        collection_id = secrets.token_hex(8)
        base_name = safe_folder_name(collection_name.strip() or str(parsed.get("name") or "Imported NZB"))
        selected_entries = [files[i] for i in selected]
        parsed["source_name"] = str(parsed.get("source_name") or "Imported NZB")
        automation = automation_category_for(base_name)
        automation_source = str(parsed.get("automation_source") or "")
        self._register_nzb_collection(provider_id, collection_id, base_name, parsed, selected)
        with self.lock:
            rec = self.collections.get(collection_id, {})
            rec["category"] = automation.get("name", ""); rec["category_folder"] = automation.get("folder", ""); rec["automation_source"] = automation_source
            self._save()
        expected_collection_files = sum(1 for entry in selected_entries if str(entry.get("group") or "").strip())
        added: list[dict[str, Any]] = []
        duplicates: list[str] = []
        skipped: list[dict[str, str]] = []
        warnings: list[str] = []
        for entry in selected_entries:
            group = str(entry.get("group") or "").strip()
            if not group:
                skipped.append({"filename": entry["media"]["filename"], "reason": "NZB entry has no newsgroup"})
                continue
            item = {**entry, "source": "nzb", "collection_id": collection_id, "collection_name": base_name,
                    "collection_expected": expected_collection_files, "destination_subdir": base_name,
                    "category": automation.get("name", ""), "category_folder": automation.get("folder", ""), "priority": automation.get("priority", "normal"), "automation_source": automation_source,
                    "collection_role": ("recovery_par2" if entry.get("is_par2_volume") else "par2" if entry.get("is_par2") else "auxiliary" if entry.get("is_auxiliary") else "payload")}
            try:
                result = self.add(provider_id, group, [item])
                added.extend(result.get("added", [])); duplicates.extend(result.get("duplicates", []))
                if result.get("disk_warning") and result["disk_warning"] not in warnings:
                    warnings.append(result["disk_warning"])
            except Exception as exc:
                skipped.append({"filename": entry["media"]["filename"], "reason": str(exc)})
        if not added and not duplicates:
            reason = skipped[0]["reason"] if skipped else "No NZB entries could be queued"
            raise ValueError(reason)
        with self.lock:
            jobs = self._collection_jobs_locked(collection_id)
            required_expected = sum(1 for j in jobs if nzb_job_blocks_collection(j))
            for target in jobs:
                target["collection_expected"] = len(jobs)
                target["collection_required_expected"] = required_expected
            rec = self.collections.get(collection_id)
            if isinstance(rec, dict):
                rec["required_expected"] = required_expected
            self._save()
        DIAGNOSTICS.event("info", "nzb", f"Imported NZB selection {base_name}", files=len(selected_entries), queued=len(added), skipped=len(skipped))
        return {"ok": True, "collection_id": collection_id, "collection_name": base_name,
                "files": len(selected_entries), "added": added, "duplicates": duplicates,
                "skipped": skipped, "warnings": warnings, "folder": str(DOWNLOAD_DIR / base_name)}

    def control(self, action: str, job_id: str = "", value: Any = None, job_ids: list[str] | None = None) -> dict[str, Any]:
        ids = [str(x) for x in (job_ids or []) if str(x)]
        if job_id and job_id not in ids:
            ids.append(job_id)
        abort_ids: set[str] = set()
        old_job_executor = None
        old_post_executor = None
        with self.lock:
            if action == "pause_all":
                self.paused = True
            elif action == "resume_all":
                self.paused = False
                self.wake.set()
            elif action == "hard_stop_all":
                self.paused = True
                now = time.time()
                for event in self.job_cancel_events.values():
                    event.set()
                abort_ids.update(self.active_jobs.keys())
                old_job_executor = self.job_executor
                self.job_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS, thread_name_prefix="usenet-download-job")
                self.active_jobs.clear()
                self.job_cancel_events = {}
                self.job_run_tokens = {}
                for job in self.jobs:
                    if job.get("status") in ("downloading", "cancelling"):
                        job["cancel_requested"] = True
                        job["status"] = "cancelled"
                        job["completed_ts"] = now
                        job["speed_bps"] = 0
                        job["connections_used"] = 0
                        job["paused"] = False
                        job["retry_at_ts"] = 0
                        job["status_detail"] = "Hard stopped; completed blocks preserved"
                        job["transfer_phase"] = "stopped"
                    elif job.get("status") in ("queued", "retry_wait"):
                        job["status"] = "cancelled"
                        job["completed_ts"] = now
                        job["paused"] = False
                        job["retry_at_ts"] = 0
                        job["status_detail"] = "Stopped; completed blocks preserved"
                        job["transfer_phase"] = "stopped"
                for event in self.post_cancel_events.values():
                    event.set()
                for event in self.direct_unpack_cancel_events.values():
                    event.set()
                self.direct_unpack_wake.set()
                old_post_executor = self.post_executor
                self.post_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="usenet-post-process")
                self.post_active.clear()
                self.post_futures.clear()
                self.post_cancel_events = {}
                for job in self.jobs:
                    if str(job.get("post_status") or "") in {"queued", "verifying", "repairing", "extracting", "importing", "waiting"}:
                        job["post_status"] = "cancelled"
                        job["post_progress"] = 0
                        job["post_message"] = "Post-processing stopped by user"
                self.wake.set()
            elif action == "fetch_recovery":
                collection_id = str(value or "").strip()
                if not collection_id:
                    raise ValueError("Choose an NZB package first")
                health = self._collection_health_locked(collection_id)
                result = self._queue_recovery_for_collection(
                    collection_id, missing_bytes=max(0, int(health.get("missing_bytes", 0) or 0)),
                    minimum_blocks=max(1, int(health.get("estimated_blocks_needed", 0) or 0)),
                )
                if not result.get("queued"):
                    raise ValueError(str(result.get("reason") or "No additional PAR2 recovery volumes are available"))
                self.wake.set()
            elif action == "set_concurrency":

                self.concurrent_downloads = PACKAGE_QUEUE_CONCURRENCY
                self.wake.set()
            elif action == "clear_completed":
                active_post = {"queued", "verifying", "repairing", "extracting", "importing"}
                self.jobs = [j for j in self.jobs if j.get("status") != "completed" or str(j.get("post_status") or "") in active_post]
                live_collections = {str(j.get("collection_id") or "") for j in self.jobs if j.get("collection_id")}
                self.collections = {cid: rec for cid, rec in self.collections.items() if cid in live_collections}
            elif action == "reorder":
                order = [str(x) for x in (value or []) if str(x)] if isinstance(value, list) else []
                if not order:
                    raise ValueError("Queue order is empty")
                pos = {download_id: i for i, download_id in enumerate(order)}
                ordered_jobs = [j for j in self.jobs if str(j.get("id")) in pos and j.get("status") == "queued"]
                ordered_jobs.sort(key=lambda j: pos[str(j.get("id"))])
                base = min([float(j.get("queue_order", 0) or 0) for j in self.jobs] + [0.0])
                for i, job in enumerate(ordered_jobs):
                    job["queue_order"] = base + i
                self.wake.set()
            elif action == "post_password":
                targets = [j for j in self.jobs if str(j.get("id")) in ids]
                if not targets:
                    raise ValueError("Choose a download that is waiting for an archive password")
                password = str(value or "")
                if not password:
                    raise ValueError("Archive password cannot be blank")
                key, collection_targets = self._post_targets(targets[0])
                self.post_passwords[key] = password
                for target in collection_targets:
                    target["post_status"] = ""
                    target["post_progress"] = 0
                    target["post_message"] = "Retrying with supplied password"
                self._save()
                threading.Thread(target=self._after_download_completed, args=(targets[0],), daemon=True).start()
            elif action in {"pause", "resume", "retry", "cancel", "remove", "priority", "move_top", "move_bottom"}:
                targets = [j for j in self.jobs if str(j.get("id")) in ids]
                if not targets:
                    raise ValueError("No downloads were selected")
                if action == "pause":
                    for job in targets:
                        if job.get("status") in ("queued", "downloading"):
                            job["paused"] = True
                elif action == "resume":
                    for job in targets:
                        job["paused"] = False
                    self.wake.set()
                elif action == "retry":
                    for job in targets:
                        if job.get("status") not in ("failed", "cancelled", "retry_wait"):
                            continue
                        job.update(status="queued", speed_bps=0, connections_used=0,
                                   path="", error="", error_code="", error_label="", error_suggestion="", error_retryable=False,
                                   started_ts=0, completed_ts=0, cancel_requested=False, paused=False,
                                   failed_parts=0, missing_bytes=0, segment_errors=[], retry_at_ts=0, auto_retry_count=0,
                                   post_status="", post_progress=0, post_message="", status_detail="Retrying missing blocks; completed blocks preserved", transfer_phase="queued")
                        self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                    self.wake.set()
                elif action == "cancel":
                    for job in targets:
                        collection_id = str(job.get("collection_id") or "")
                        direct_event = self.direct_unpack_cancel_events.get(collection_id) if collection_id else None
                        if direct_event:
                            direct_event.set()
                            self.direct_unpack_wake.set()
                        if job.get("status") in ("downloading", "cancelling"):
                            jid = str(job.get("id") or "")
                            job["cancel_requested"] = True
                            event = self.job_cancel_events.get(jid)
                            if event:
                                event.set()
                            abort_ids.add(jid)
                            future = self.active_jobs.pop(jid, None)
                            if future is not None:
                                try:
                                    future.cancel()
                                except Exception:
                                    pass
                            self.job_cancel_events.pop(jid, None)
                            self.job_run_tokens.pop(jid, None)
                            job["status"] = "cancelled"
                            job["completed_ts"] = time.time()
                            job["paused"] = False
                            job["retry_at_ts"] = 0
                            job["speed_bps"] = 0
                            job["connections_used"] = 0
                            job["status_detail"] = "Cancelled immediately; verified blocks preserved"
                            job["transfer_phase"] = "stopped"
                            self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                        elif job.get("status") in ("queued", "retry_wait"):
                            job["status"] = "cancelled"
                            job["completed_ts"] = time.time()
                            job["paused"] = False
                            job["retry_at_ts"] = 0
                            job["status_detail"] = "Cancelled; partial blocks are retained until removed"
                            job["transfer_phase"] = "stopped"
                            self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                        key, _post_targets = self._post_targets(job)
                        post_event = self.post_cancel_events.get(key)
                        if post_event and str(job.get("post_status") or "") in {"queued", "verifying", "repairing", "extracting", "importing"}:
                            post_event.set()
                            job["post_status"] = "cancelling"
                            job["post_message"] = "Stopping post-processing"
                elif action == "remove":
                    target_ids = {str(j.get("id")) for j in targets}
                    cleanup_targets = [(str(j.get("id")), str(j.get("partial_path") or "")) for j in targets]
                    affected_collections = {str(j.get("collection_id") or "") for j in targets if j.get("collection_id")}
                    for job in targets:
                        job["cancel_requested"] = True
                        collection_id = str(job.get("collection_id") or "")
                        direct_event = self.direct_unpack_cancel_events.get(collection_id) if collection_id else None
                        if direct_event:
                            direct_event.set()
                            self.direct_unpack_wake.set()
                        event = self.job_cancel_events.get(str(job.get("id") or ""))
                        if event:
                            event.set()
                        jid = str(job.get("id") or "")
                        abort_ids.add(jid)
                        future = self.active_jobs.pop(jid, None)
                        if future is not None:
                            try:
                                future.cancel()
                            except Exception:
                                pass
                        self.job_cancel_events.pop(jid, None)
                        self.job_run_tokens.pop(jid, None)
                        key, _ = self._post_targets(job)
                        event = self.post_cancel_events.get(key)
                        if event:
                            event.set()
                    self.jobs = [j for j in self.jobs if str(j.get("id")) not in target_ids]
                    live_collections = {str(j.get("collection_id") or "") for j in self.jobs if j.get("collection_id")}
                    for collection_id in affected_collections:
                        if collection_id not in live_collections:
                            self.collections.pop(collection_id, None)
                        else:
                            self._refresh_collection_post_state_locked(collection_id)
                    for target_id, partial_path in cleanup_targets:
                        threading.Thread(target=self._cleanup_removed_scratch, args=(target_id, partial_path),
                                         name=f"newzdeck-clean-{target_id[:6]}", daemon=True).start()
                elif action == "priority":
                    priority = str(value or "normal").lower()
                    if priority not in {"high", "normal", "low"}:
                        raise ValueError("Priority must be High, Normal, or Low")
                    for job in targets:
                        job["priority"] = priority
                    self.wake.set()
                elif action in {"move_top", "move_bottom"}:
                    orders = [float(j.get("queue_order", 0) or 0) for j in self.jobs]
                    edge = (min(orders) if orders else 0) - 1 if action == "move_top" else (max(orders) if orders else 0) + 1
                    for offset, job in enumerate(targets):
                        job["queue_order"] = edge + (offset * (1 if action == "move_bottom" else -1))
                    self.wake.set()
            else:
                raise ValueError("Unknown download action")
            self._save()
        if abort_ids:
            abort_download_jobs(abort_ids)
        if action == "hard_stop_all":
            shutdown_download_pools()
            if old_job_executor is not None:
                try:
                    old_job_executor.shutdown(wait=False, cancel_futures=True)
                except TypeError:
                    old_job_executor.shutdown(wait=False)
            if old_post_executor is not None:
                try:
                    old_post_executor.shutdown(wait=False, cancel_futures=True)
                except TypeError:
                    old_post_executor.shutdown(wait=False)
        return self.snapshot()

    def _scheduler_loop(self):
        while not self.shutdown_event.is_set():
            stale_abort: list[str] = []
            with self.lock:
                for job_id, future in list(self.active_jobs.items()):
                    if future.done():
                        self.active_jobs.pop(job_id, None)
                        self.job_cancel_events.pop(job_id, None)
                        self.job_run_tokens.pop(job_id, None)
                        try:
                            future.result()
                        except Exception as exc:
                            safe_print("Download coordinator error:", repr(exc))

                now = time.time()
                for stale_id, future in list(self.active_jobs.items()):
                    job = self._find_job(stale_id)
                    if not job or job.get("status") not in {"downloading", "cancelling"}:
                        continue
                    phase = str(job.get("transfer_phase") or "")
                    last_progress = float(job.get("last_progress_ts", job.get("started_ts", now)) or now)
                    if phase == "fetching" and not job.get("paused") and not self.paused and now - last_progress >= 60:
                        event = self.job_cancel_events.get(stale_id)
                        if event:
                            event.set()
                        job["cancel_requested"] = True
                        job["watchdog_retry"] = True
                        job["status"] = "retry_wait"
                        job["retry_at_ts"] = now + 10
                        job["speed_bps"] = 0
                        job["connections_used"] = 0
                        job["status_detail"] = "Transfer stalled — resetting connection and retrying from preserved blocks"
                        job["transfer_phase"] = "retry_wait"
                        job["error_code"] = "stalled"
                        job["error_label"] = "Transfer stalled"
                        job["error_suggestion"] = "NewzDeck detected no real network progress and automatically reset this download."
                        self.active_jobs.pop(stale_id, None)
                        self.job_cancel_events.pop(stale_id, None)
                        self.job_run_tokens.pop(stale_id, None)
                        stale_abort.append(stale_id)
                        try:
                            future.cancel()
                        except Exception:
                            pass
                        DIAGNOSTICS.event("warning", "download", "Watchdog reset stalled transfer", job_id=stale_id, filename=job.get("filename", ""))

                retry_ready = False
                for job in self.jobs:
                    if job.get("status") == "retry_wait" and float(job.get("retry_at_ts", 0) or 0) <= now:
                        job["status"] = "queued"
                        job["retry_at_ts"] = 0
                        job["status_detail"] = "Automatic retry starting; completed blocks preserved"
                        retry_ready = True

                owner_key = "" if self.paused else self._foreground_queue_item_locked()
                candidates, effective_limit = self._queue_item_launch_plan_locked(owner_key) if owner_key else ([], 0)
                owner_active = sum(1 for jid in self.active_jobs if self._queue_item_key(self._find_job(jid)) == owner_key) if owner_key else 0
                slots = max(0, effective_limit - owner_active)
                for job in candidates[:slots]:
                    job["status"] = "downloading"
                    job["started_ts"] = time.time()
                    job["speed_bps"] = 0
                    job["connections_used"] = 0
                    job["error"] = ""
                    job["error_code"] = ""
                    job["error_label"] = ""
                    job["error_suggestion"] = ""
                    job["error_retryable"] = False
                    job["failed_parts"] = 0
                    job["missing_bytes"] = 0
                    job["segment_errors"] = []
                    job["cancel_requested"] = False
                    job["last_activity_ts"] = time.time()
                    job["last_progress_ts"] = time.time()
                    job["status_detail"] = "Preparing article blocks"
                    job["transfer_phase"] = "preparing"
                    job_id = str(job["id"])
                    cancel_event = threading.Event()
                    run_token = secrets.token_hex(8)
                    self.job_cancel_events[job_id] = cancel_event
                    self.job_run_tokens[job_id] = run_token
                    future = self.job_executor.submit(self._run_job, job_id, cancel_event, run_token)
                    self.active_jobs[job_id] = future
                if candidates[:slots] or retry_ready or stale_abort:
                    self._save()
            if stale_abort:
                abort_download_jobs(stale_abort)
            self.wake.wait(0.25)
            self.wake.clear()

    def _auto_prepare_par2_repair(self, job: dict[str, Any]) -> bool:
        """Promote a sparse v1.4 partial file into the NZB folder for PAR2 repair.

        This is only used after NewzDeck has exhausted Message-ID rechecks and
        only when a PAR2 command-line tool is actually available plus the NZB
        contains enough advertised recovery blocks for a reasonable repair
        attempt. It turns an otherwise failed payload into a controlled
        repair-needed state and queues only the deferred recovery volumes needed.
        """
        if str(job.get("source") or "") not in {"nzb", "browser_set"} or bool(job.get("is_par2")):
            return False
        post_settings = self._post_settings()
        if not post_settings.get("enabled") or not post_settings.get("repair") or not post_settings.get("fetch_par2"):
            return False
        cid = str(job.get("collection_id") or "")
        partial_text = str(job.get("partial_path") or "")
        if not cid or not partial_text or not _par2_path():
            return False
        partial = Path(partial_text)
        if not partial.exists() or not partial.is_file():
            return False
        with self.lock:
            rec = self.collections.get(cid)
            if not isinstance(rec, dict):
                return False
            jobs = self._collection_jobs_locked(cid)
            catalog = list(rec.get("recovery_catalog") or [])
            has_par2 = any(bool(j.get("is_par2")) for j in jobs) or any(bool(x.get("is_par2")) for x in catalog)
            if not has_par2:
                return False
            block_bytes = self._estimate_recovery_block_bytes(catalog, jobs)
            missing_bytes = max(0, int(job.get("missing_bytes", 0) or 0))
            missing_articles = max(0, int(job.get("failed_parts", 0) or 0))
            needed = int(math.ceil(missing_bytes / block_bytes)) + 2 if missing_bytes and block_bytes else max(1, missing_articles)
            available = (
                sum(max(0, int(x.get("par2_recovery_blocks", 0) or 0)) for x in catalog) +
                sum(max(0, int(j.get("par2_recovery_blocks", 0) or 0)) for j in jobs if str(j.get("collection_role") or "") == "recovery_par2")
            )
            if available < needed:
                return False
        try:
            dest = self._reserve_download_path(str(job.get("filename") or "download.bin"), job)
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.replace(dest)
        except OSError as exc:
            try:
                self._release_download_path(dest)
            except Exception:
                pass
            DIAGNOSTICS.event("warning", "par2", f"Could not prepare damaged file for PAR2 repair: {exc}", collection=cid)
            return False
        with self.lock:
            job["path"] = str(dest)
            job["partial_path"] = ""
            try:
                job["actual_size"] = dest.stat().st_size
            except OSError:
                job["actual_size"] = max(0, int(job.get("expected_bytes", 0) or 0))
            job["status"] = "completed"
            job["integrity_status"] = "repair_needed"
            job["repair_missing_bytes"] = max(0, int(job.get("missing_bytes", 0) or 0))
            job["repair_missing_blocks"] = max(0, int(job.get("failed_parts", 0) or 0))
            job["completed_ts"] = time.time()
            job["speed_bps"] = 0
            job["connections_used"] = 0
            job["error_code"] = "repair_needed"
            job["error_label"] = "Transfer incomplete — PAR2 repair queued"
            job["error_suggestion"] = "NewzDeck preserved the incomplete file and is fetching only the PAR2 recovery data needed for repair."
            job["error_retryable"] = False
            job["status_detail"] = f"PAR2 repair needed • about {needed} recovery block{'s' if needed != 1 else ''}"
            job["transfer_phase"] = "repair_wait"
            self._save()
        plan = self._queue_recovery_for_collection(cid, missing_bytes=missing_bytes, minimum_blocks=needed)
        if not plan.get("queued") and not any(str(j.get("collection_role") or "") == "recovery_par2" for j in self._collection_jobs_locked(cid)):
            DIAGNOSTICS.event("warning", "par2", "PAR2 repair candidate prepared but no recovery volume could be queued", collection=cid)
        try:
            shutil.rmtree(DOWNLOAD_TEMP_DIR / str(job.get("id") or ""), ignore_errors=True)
        except OSError:
            pass
        self._release_download_path(dest)
        DIAGNOSTICS.event("info", "par2", "Prepared incomplete payload for PAR2 repair", collection=cid, missing_bytes=missing_bytes, needed_blocks=needed)
        threading.Thread(target=self._after_download_completed, args=(job,), name=f"newzdeck-par2-wait-{str(job.get('id'))[:6]}", daemon=True).start()
        return True

    def _run_job(self, job_id: str, cancel_event: threading.Event, run_token: str) -> None:
        with self.lock:
            job = self._find_job(job_id)
            current = self.job_run_tokens.get(job_id) == run_token
        if not job or not current:
            return
        try:
            self._process(job, cancel_event, run_token)
        except DownloadCancelled:
            with self.lock:
                if self.job_run_tokens.get(job_id) != run_token:
                    return
                if job.pop("watchdog_retry", False) and job.get("status") == "retry_wait":
                    job["cancel_requested"] = False
                    job["speed_bps"] = 0
                    job["connections_used"] = 0
                    job["transfer_phase"] = "retry_wait"
                else:
                    job["status"] = "cancelled"
                    job["speed_bps"] = 0
                    job["connections_used"] = 0
                    job["completed_ts"] = time.time()
                    job["cancel_requested"] = False
                    job["status_detail"] = "Cancelled; partial blocks are retained until removed"
                    job["transfer_phase"] = "stopped"
                    self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                self._save()
        except Exception as exc:
            if cancel_event.is_set() or job.get("cancel_requested"):
                with self.lock:
                    if self.job_run_tokens.get(job_id) != run_token:
                        return
                    if job.pop("watchdog_retry", False) and job.get("status") == "retry_wait":
                        job["cancel_requested"] = False
                        job["speed_bps"] = 0
                        job["connections_used"] = 0
                        job["transfer_phase"] = "retry_wait"
                    elif job.get("status") != "completed":
                        job["status"] = "cancelled"
                        job["speed_bps"] = 0
                        job["connections_used"] = 0
                        job["completed_ts"] = time.time()
                        job["cancel_requested"] = False
                        job["status_detail"] = job.get("status_detail") or "Cancelled; partial blocks are retained until removed"
                        job["transfer_phase"] = "stopped"
                        self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                    self._save()
                return
            with self.lock:
                if self.job_run_tokens.get(job_id) != run_token:
                    return
            DIAGNOSTICS.event("error", "download", str(exc), job_id=job_id, filename=job.get("filename", ""), provider=job.get("provider_name", ""), group=job.get("group", ""))
            failure = download_failure_info(exc)
            with self.lock:
                if self.job_run_tokens.get(job_id) != run_token:
                    return
                retryable = bool(failure.get("retryable"))
                auto_count = int(job.get("auto_retry_count", 0) or 0)
                error_code = str(failure.get("error_code") or "")
                retry_plan = _download_auto_retry_plan(job, error_code)
                propagation = bool(retry_plan["propagation"])
                soft_missing = bool(retry_plan["soft_missing"])
                bulk_missing = bool(retry_plan["bulk_missing"])
                optional_aux_failure = bool(
                    str(job.get("source") or "") in {"nzb", "browser_set"}
                    and bool(job.get("is_auxiliary") or str(job.get("collection_role") or "") == "auxiliary")
                    and error_code in {"soft_missing", "article_missing", "incomplete", "propagation"}
                )
                if optional_aux_failure:
                    partial_path = str(job.get("partial_path") or "")
                    job["status"] = "completed"
                    job["optional_missing"] = True
                    job["path"] = ""
                    job["partial_path"] = ""
                    job["actual_size"] = 0
                    job["downloaded_bytes"] = 0
                    job["current_part"] = len(job.get("segments") or [])
                    job["processed_parts"] = len(job.get("segments") or [])
                    job["successful_parts"] = 0
                    job["failed_parts"] = 0
                    job["missing_bytes"] = 0
                    job["segment_errors"] = []
                    job["error"] = ""
                    job["error_code"] = ""
                    job["error_label"] = ""
                    job["error_suggestion"] = ""
                    job["error_retryable"] = False
                    job["speed_bps"] = 0
                    job["connections_used"] = 0
                    job["retry_at_ts"] = 0
                    job["completed_ts"] = time.time()
                    job["last_activity_ts"] = time.time()
                    job["status_detail"] = f"Optional {Path(str(job.get('filename') or '')).suffix or 'sidecar'} unavailable — skipped"
                    job["transfer_phase"] = "optional_skipped"
                    job["integrity_status"] = "optional_missing"
                    self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                    self._save()
                    if partial_path:
                        try:
                            Path(partial_path).unlink(missing_ok=True)
                        except OSError:
                            pass
                    shutil.rmtree(DOWNLOAD_TEMP_DIR / str(job.get("id") or ""), ignore_errors=True)
                    DIAGNOSTICS.event("warning", "download", "Optional NZB sidecar was unavailable and was skipped immediately", job_id=job_id, filename=job.get("filename", ""))
                    threading.Thread(target=self._after_download_completed, args=(job,), name=f"newzdeck-optional-{job_id[:6]}", daemon=True).start()
                    return
                max_auto = int(retry_plan["max_auto"])
                delays = tuple(int(x) for x in retry_plan.get("delays", (8, 16)))
                # If a large share of an established NZB file is absent after the
                # primary and recovery providers have already been checked, skip
                # delayed Message-ID loops. PAR2 gets the first opportunity to
                # recover it; otherwise the file becomes a normal terminal failure.
                if bulk_missing and self._auto_prepare_par2_repair(job):
                    self._save()
                    return
                if retryable and auto_count < max_auto and not job.get("cancel_requested"):
                    auto_count += 1
                    delay = delays[min(auto_count - 1, len(delays) - 1)] if delays else 8
                    job["status"] = "retry_wait"
                    job["auto_retry_count"] = auto_count
                    job["retry_at_ts"] = time.time() + delay
                    job["error"] = str(exc)
                    job["error_code"] = failure["error_code"]
                    job["error_label"] = failure["error_label"]
                    job["error_suggestion"] = failure.get("suggestion", "")
                    job["error_retryable"] = True
                    job["speed_bps"] = 0
                    job["connections_used"] = 0
                    job["status_detail"] = (f"Waiting for Usenet propagation — retrying missing blocks in {delay}s" if propagation else
                                            f"Rechecking provider backends — retrying unavailable Message-IDs in {delay}s" if soft_missing else
                                            f"Provider problem — retrying automatically in {delay}s")
                    job["transfer_phase"] = "retry_wait"
                else:
                    optional_missing = bool(
                        str(job.get("source") or "") in {"nzb", "browser_set"}
                        and bool(job.get("is_auxiliary") or str(job.get("collection_role") or "") == "auxiliary")
                        and error_code in {"soft_missing", "article_missing", "incomplete", "propagation"}
                    )
                    if optional_missing:
                        partial_path = str(job.get("partial_path") or "")
                        job["status"] = "completed"
                        job["optional_missing"] = True
                        job["path"] = ""
                        job["partial_path"] = ""
                        job["actual_size"] = 0
                        job["downloaded_bytes"] = 0
                        job["current_part"] = len(job.get("segments") or [])
                        job["processed_parts"] = len(job.get("segments") or [])
                        job["successful_parts"] = 0
                        job["failed_parts"] = 0
                        job["missing_bytes"] = 0
                        job["segment_errors"] = []
                        job["error"] = ""
                        job["error_code"] = ""
                        job["error_label"] = ""
                        job["error_suggestion"] = ""
                        job["error_retryable"] = False
                        job["speed_bps"] = 0
                        job["connections_used"] = 0
                        job["completed_ts"] = time.time()
                        job["last_activity_ts"] = time.time()
                        job["status_detail"] = f"Optional {Path(str(job.get('filename') or '')).suffix or 'sidecar'} unavailable — skipped"
                        job["transfer_phase"] = "optional_skipped"
                        job["integrity_status"] = "optional_missing"
                        self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                        self._save()
                        if partial_path:
                            try:
                                Path(partial_path).unlink(missing_ok=True)
                            except OSError:
                                pass
                        shutil.rmtree(DOWNLOAD_TEMP_DIR / str(job.get("id") or ""), ignore_errors=True)
                        DIAGNOSTICS.event("warning", "download", "Optional NZB sidecar was unavailable and was skipped", job_id=job_id, filename=job.get("filename", ""), collection=job.get("collection_name", ""))
                        threading.Thread(target=self._after_download_completed, args=(job,), name=f"newzdeck-optional-{job_id[:6]}", daemon=True).start()
                        return
                    if (soft_missing or error_code in {"incomplete", "integrity"}) and self._auto_prepare_par2_repair(job):
                        self._save()
                        return
                    job["status"] = "failed"
                    job["error"] = str(exc)
                    final_label = failure["error_label"]
                    final_suggestion = failure.get("suggestion", "")
                    if soft_missing:
                        if bulk_missing:
                            final_label = "Download incomplete — widespread article blocks unavailable"
                            final_suggestion = "A large share of this file was missing across the configured providers, so NewzDeck stopped redundant delayed rechecks. Try another recovery provider, use PAR2 recovery if available, or choose another release."
                        else:
                            final_label = "Download incomplete — blocks unavailable after bounded rechecks"
                            final_suggestion = "NewzDeck exhausted the bounded Message-ID recheck budget while preserving every good block. Try another recovery provider or retry later."
                    job["error_code"] = failure["error_code"]
                    job["error_label"] = final_label
                    job["error_suggestion"] = final_suggestion
                    job["error_retryable"] = retryable
                    job["speed_bps"] = 0
                    job["connections_used"] = 0
                    job["completed_ts"] = time.time()
                    job["status_detail"] = final_label
                    job["transfer_phase"] = "failed"
                    self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                self._save()
        finally:
            self.wake.set()
            self.direct_unpack_wake.set()

    def _wait_if_paused(self, job: dict[str, Any], cancel_event: threading.Event | None = None, run_token: str = ""):
        job_id = str(job.get("id") or "")
        def invalid_run() -> bool:
            return bool(run_token and self.job_run_tokens.get(job_id) != run_token)
        while (self.paused or job.get("paused")) and not self.shutdown_event.is_set():
            if invalid_run() or job.get("cancel_requested") or (cancel_event is not None and cancel_event.is_set()):
                raise DownloadCancelled()
            if cancel_event is not None:
                cancel_event.wait(0.15)
            else:
                time.sleep(0.15)
        if invalid_run() or self.shutdown_event.is_set() or job.get("cancel_requested") or (cancel_event is not None and cancel_event.is_set()):
            raise DownloadCancelled()

    def _reserve_download_path(self, filename: str, job: dict[str, Any]) -> Path:
        mode = str(job.get("destination_mode", "flat"))
        folder = DOWNLOAD_DIR
        category_folder = safe_folder_name(str(job.get("category_folder") or "")) if job.get("category_folder") else ""
        if category_folder:
            folder = folder / category_folder
        subdir = safe_folder_name(str(job.get("destination_subdir") or "")) if job.get("destination_subdir") else ""
        if subdir:
            folder = folder / subdir
        if mode == "newsgroup":
            folder = folder / safe_folder_name(job.get("group") or "Newsgroup")
        elif mode == "kind":
            folder = folder / ("Images" if job.get("kind") == "image" else "Videos" if job.get("kind") == "video" else "Other")
        elif mode == "newsgroup_kind":
            folder = folder / safe_folder_name(job.get("group") or "Newsgroup") / ("Images" if job.get("kind") == "image" else "Videos" if job.get("kind") == "video" else "Other")
        folder.mkdir(parents=True, exist_ok=True)
        base = folder / safe_download_name(filename)
        stem, suffix = base.stem, base.suffix
        n = 1
        while True:
            candidate = base if n == 1 else folder / f"{stem} ({n}){suffix}"
            key = str(candidate).lower()
            if not candidate.exists() and key not in self.reserved_paths:
                self.reserved_paths.add(key)
                return candidate
            n += 1

    def _release_download_path(self, path: Path) -> None:
        with self.lock:
            self.reserved_paths.discard(str(path).lower())

    def _active_provider_jobs(self, provider_id: str) -> int:
        """Count only live coordinator futures when dividing provider slots.

        A stale persisted/status-only `downloading` row must never cut the active
        file's connection budget in half. This was especially visible as 26 active
        requests on a 52-slot provider even though only one real coordinator was
        doing work.
        """
        with self.lock:
            count = 0
            for job_id, future in self.active_jobs.items():
                if future.done():
                    continue
                job = self._find_job(job_id)
                if job and str(job.get("provider_id") or "") == str(provider_id) and job.get("status") in ("downloading", "cancelling"):
                    count += 1
            return max(1, count)

    def _process(self, job: dict[str, Any], cancel_event: threading.Event, run_token: str):
        provider = provider_by_id(job["provider_id"])
        group = job["group"]
        segments = sorted(job.get("segments") or [], key=lambda s: int(s.get("part", 1)))
        media = job.get("media") or {}
        if not segments:
            raise ValueError("This queued item has no article segments")
        filename = safe_download_name(job.get("filename") or media.get("filename") or "download.bin")
        with self.lock:
            dest = self._reserve_download_path(filename, job)
        expected = max(0, int(job.get("expected_bytes", 0) or 0))
        try:
            usage = shutil.disk_usage(dest.parent)
            settings = json_read(SETTINGS_FILE, {})
            reserve_gb = max(0.25, min(50.0, float(settings.get("disk_reserve_gb", 1.0) or 1.0)))
            reserve = int(reserve_gb * 1024**3)
            needed = max(expected, 64 * 1024 * 1024) + reserve
            if usage.free < needed:
                raise OSError(f"Insufficient disk space: {usage.free / 1024**3:.1f} GB free; this job needs about {max(expected,0) / 1024**3:.1f} GB plus a {reserve_gb:.1f} GB safety reserve")
        except FileNotFoundError:
            pass

        temp = dest.with_suffix(dest.suffix + f".{job['id']}.part")
        scratch = DOWNLOAD_TEMP_DIR / str(job["id"])
        scratch.mkdir(parents=True, exist_ok=True)
        journal_path = scratch / "resume-v4.jsonl"
        fallback_dir = scratch / "fallback"
        pending: dict[Any, list[int]] = {}
        decode_pending: dict[Any, list[int]] = {}
        completed_ok = False
        io_lock = threading.RLock()
        progress_lock = threading.RLock()
        inflight_progress: dict[int, int] = {}
        journal_last_flush = [time.monotonic()]
        partial_fp = None
        journal_fp = None

        with self.lock:
            job["partial_path"] = str(temp)

        def segment_key(index: int, seg: dict[str, Any]) -> str:
            raw = json.dumps({
                "cache_format": 4,
                "index": index,
                "part": int(seg.get("part", index + 1) or index + 1),
                "message_id": str(seg.get("message_id") or ""),
                "article": str(seg.get("article") if seg.get("article") is not None else ""),
                "bytes": int(seg.get("bytes", 0) or 0),
            }, sort_keys=True, separators=(",", ":")).encode("utf-8")
            return hashlib.sha1(raw).hexdigest()

        def load_resume_journal() -> dict[int, dict[str, Any]]:
            if not journal_path.exists() or not temp.exists():
                return {}
            latest: dict[int, dict[str, Any]] = {}
            try:
                with journal_path.open("r", encoding="utf-8", errors="replace") as src:
                    for line in src:
                        try:
                            rec = json.loads(line)
                            index = int(rec.get("index", -1))
                            if 0 <= index < len(segments):
                                latest[index] = rec
                        except Exception:
                            continue
            except OSError:
                return {}
            temp_size = temp.stat().st_size
            loaded: dict[int, dict[str, Any]] = {}
            for index, rec in latest.items():
                if rec.get("segment_key") != segment_key(index, segments[index]):
                    continue
                result = dict(rec.get("result") or {})
                decoded = max(0, int(result.get("decoded_bytes", 0) or 0))
                if decoded <= 0:
                    continue
                if bool(result.get("direct", False)):
                    offset = max(0, int(result.get("direct_offset", 0) or 0))
                    if offset + decoded > temp_size:
                        continue
                else:
                    fallback_path = Path(str(result.get("fallback_path") or ""))
                    if not fallback_path.exists() or fallback_path.stat().st_size != decoded:
                        continue
                result["cached_segment"] = True
                loaded[index] = result
            return loaded

        try:
            token = preview_cache_token(provider, group, segments, media)
            cached = cached_preview_result(token, filename, media)
            if cached:
                self._wait_if_paused(job, cancel_event, run_token)
                source = Path(_preview_tokens[token]["path"])
                shutil.copy2(source, temp)
                self._wait_if_paused(job, cancel_event, run_token)
                temp.replace(dest)
                with self.lock:
                    job["downloaded_bytes"] = int(job.get("expected_bytes") or source.stat().st_size)
                    job["current_part"] = len(segments)
                    job["processed_parts"] = len(segments)
                    job["successful_parts"] = len(segments)
                    job["failed_parts"] = 0
                    job["total_parts"] = len(segments)
                    job["path"] = str(dest)
                    job["actual_size"] = dest.stat().st_size
                    job["status"] = "completed"
                    job["speed_bps"] = 0
                    job["connections_used"] = 0
                    job["completed_ts"] = time.time()
                    job["last_activity_ts"] = time.time()
                    job["status_detail"] = "Completed from local preview cache"
                    job["transfer_phase"] = "complete"
                    job["pipeline"] = "preview-cache"
                    job["integrity_status"] = "healthy"
                    job["repair_missing_bytes"] = 0
                    job["repair_missing_blocks"] = 0
                    duration = max(0.0, time.time() - float(job.get("started_ts", time.time()) or time.time()))
                    job["duration_seconds"] = round(duration, 3)
                    job["average_speed_bps"] = int(job["downloaded_bytes"] / duration) if duration > 0 else 0
                    job["partial_path"] = ""
                    self._save()
                completed_ok = True
                self._wait_if_paused(job, cancel_event, run_token)
                self._maybe_start_direct_unpack(job)
                self._after_download_completed(job)
                return

            pool = get_download_pool(provider)

            def desired_parallelism() -> int:
                capacity = pool.effective_capacity()
                with self.lock:
                    if self._is_rar_payload_job(job):
                        return self._rar_connection_target_locked(job, capacity)
                active_provider_jobs = self._active_provider_jobs(str(job["provider_id"]))
                return max(1, int(math.ceil(capacity / max(1, active_provider_jobs))))

            temp.parent.mkdir(parents=True, exist_ok=True)
            partial_fp = temp.open("r+b" if temp.exists() else "w+b", buffering=0)
            journal_fp = journal_path.open("a", encoding="utf-8", buffering=64 * 1024)

            results: dict[int, dict[str, Any]] = load_resume_journal()
            completed_wire = sum(max(0, int(r.get("wire_bytes", 0) or 0)) for r in results.values())
            resumed_parts = len(results)
            recovered_parts = sum(1 for r in results.values() if r.get("recovered"))
            recovery_sources: dict[str, int] = {}
            for r in results.values():
                if r.get("recovered"):
                    name = str(r.get("provider_name") or "Recovery provider")
                    recovery_sources[name] = recovery_sources.get(name, 0) + 1

            missing_indices = [i for i in range(len(segments)) if i not in results]
            parallelism = min(desired_parallelism(), len(missing_indices)) if missing_indices else 0
            retry_base = int(job.get("retry_count", 0) or 0)
            new_retry_count = 0
            failures: dict[int, dict[str, Any]] = {}
            transient_fail_streak = 0
            provider_outage = False
            started = time.perf_counter()
            last_persist = started
            base_wire = completed_wire
            stage_network_seconds = 0.0
            stage_decode_seconds = 0.0
            stage_disk_seconds = 0.0
            native_parts = 0

            with self.lock:
                job["connections_used"] = parallelism
                job["downloaded_bytes"] = completed_wire
                job["current_part"] = len(results)
                job["processed_parts"] = len(results)
                job["successful_parts"] = len(results)
                job["failed_parts"] = 0
                job["total_parts"] = len(segments)
                job["resumed_parts"] = resumed_parts
                job["recovered_parts"] = recovered_parts
                job["recovery_sources"] = recovery_sources
                job["transfer_phase"] = "fetching"
                job["pipeline"] = "native-yenc" if NATIVE_YENC_POOL.stats().get("available") else "bulk-python-yenc"
                job["peak_speed_bps"] = max(0, int(job.get("peak_speed_bps", 0) or 0))
                job["status_detail"] = (f"Resumed {resumed_parts} verified block{'s' if resumed_parts != 1 else ''}; fetching {len(missing_indices)} remaining" if resumed_parts else f"Fetching {len(missing_indices)} article blocks")
                job["last_activity_ts"] = time.time()
                self._save()

            active_for_cache = max(1, self._active_provider_jobs(str(job["provider_id"])))
            cache_total_mb, cache_job_mb = _download_article_cache_budget_mb(active_for_cache)
            article_cache_limit = int(cache_job_mb * 1024 * 1024)
            write_cache: dict[int, dict[str, Any]] = {}
            write_cache_bytes = 0
            write_cache_last_flush = time.monotonic()
            # Windows must explicitly mark the partial file sparse before reserving
            # the yEnc-advertised final size. Without this, Python/CRT truncate()
            # extends the file with NUL bytes and can write many gigabytes before
            # the first real article block reaches disk.
            sparse_direct_write = _enable_sparse_partial_file(partial_fp)
            disk_future = None
            disk_inflight_bytes = 0
            disk_inflight_count = 0

            with self.lock:
                job["article_cache_limit_bytes"] = article_cache_limit
                job["article_cache_total_budget_bytes"] = int(cache_total_mb * 1024 * 1024)
                job["article_cache_bytes"] = 0
                job["direct_write_mode"] = "sparse-async" if sparse_direct_write else "sequential-fallback"
                job["pipeline"] = (("native-yenc" if NATIVE_YENC_POOL.stats().get("available") else "bulk-python-yenc") + "+article-cache+async-disk+" + ("sparse-write" if sparse_direct_write else "sequential-fallback"))

            def cache_result(index: int, seg: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
                """Validate a decoded article and retain it in RAM for batched writes."""
                nonlocal write_cache_bytes, native_parts
                data = result.get("data")
                if not isinstance(data, (bytes, bytearray)) or not data:
                    raise NntpError("Decoded article block is empty")
                meta = dict(result.get("meta") or {})
                decoded = len(data)
                begin = int(meta.get("begin", 0) or 0)
                end = int(meta.get("end", 0) or 0)
                expected_part = (end - begin + 1) if begin > 0 and end >= begin else int(meta.get("end_size", 0) or 0)
                if expected_part and expected_part != decoded:
                    raise NntpError(f"Decoded yEnc segment is truncated: expected {expected_part:,} bytes, received {decoded:,}")
                direct = bool(begin > 0 or len(segments) == 1)
                result["decoded_bytes"] = decoded
                result["direct"] = direct
                result["_cache_offset"] = (begin - 1 if begin > 0 else 0) if direct else -1
                result["_cache_advertised_size"] = max(0, int(meta.get("size", 0) or 0))
                write_cache[index] = result
                write_cache_bytes += decoded
                if bool((result.get("perf") or {}).get("native_decode")):
                    native_parts += 1
                with self.lock:
                    job["article_cache_bytes"] = write_cache_bytes + disk_inflight_bytes
                return result

            def _write_cache_batch(batch: dict[int, dict[str, Any]], force_journal: bool = False):
                """Commit one detached cache batch on a disk worker thread.

                The queue coordinator never waits here during normal transfer, so
                an HDD/USB/filesystem stall cannot drain all warm NNTP sockets.
                Sparse Direct Write is used where supported; otherwise only writes
                that do not create a hole are committed directly and later blocks
                spill to sidecars for compatibility assembly.
                """
                disk_started = time.perf_counter()
                flushed: dict[int, dict[str, Any]] = {}
                journal_lines: list[str] = []
                with io_lock:
                    if cancel_event.is_set() or self.job_run_tokens.get(str(job["id"])) != run_token:
                        raise DownloadCancelled()
                    direct_entries = []
                    fallback_entries = []
                    advertised_size = 0
                    for idx, cached_result in batch.items():
                        if cached_result.get("direct"):
                            offset = max(0, int(cached_result.get("_cache_offset", 0) or 0))
                            direct_entries.append((offset, idx, cached_result))
                            advertised_size = max(advertised_size, int(cached_result.get("_cache_advertised_size", 0) or 0))
                        else:
                            fallback_entries.append((idx, cached_result))

                    current_size = os.fstat(partial_fp.fileno()).st_size
                    if advertised_size and sparse_direct_write and current_size < advertised_size:
                        # Safe only after FSCTL_SET_SPARSE on Windows. POSIX
                        # truncate() naturally creates a hole on normal filesystems.
                        partial_fp.truncate(advertised_size)
                        current_size = advertised_size

                    direct_entries.sort(key=lambda item: (item[0], item[1]))
                    last_end: int | None = None
                    logical_end = current_size
                    for offset, idx, cached_result in direct_entries:
                        data = cached_result.get("data")
                        if not isinstance(data, (bytes, bytearray)):
                            raise NntpError("Article cache lost decoded data before disk flush")
                        # On a filesystem where sparse mode could not be enabled,
                        # never seek past EOF: Windows would zero-fill the gap and
                        # recreate the multi-gigabyte preallocation bottleneck.
                        if not sparse_direct_write and offset > logical_end:
                            fallback_entries.append((idx, cached_result))
                            continue
                        if last_end != offset:
                            partial_fp.seek(offset)
                        partial_fp.write(data)
                        last_end = offset + len(data)
                        logical_end = max(logical_end, last_end)
                        cached_result["direct_offset"] = offset
                        flushed[idx] = cached_result

                    if fallback_entries:
                        fallback_dir.mkdir(parents=True, exist_ok=True)
                        for idx, cached_result in sorted(fallback_entries, key=lambda item: item[0]):
                            data = cached_result.get("data")
                            if not isinstance(data, (bytes, bytearray)):
                                raise NntpError("Article cache lost fallback data before disk flush")
                            fallback_path = fallback_dir / f"{idx:06d}.bin"
                            with fallback_path.open("wb", buffering=1024 * 1024) as out:
                                out.write(data)
                            cached_result["fallback_path"] = str(fallback_path)
                            # A sidecar block is intentionally not direct so final
                            # compatibility assembly reads it sequentially.
                            cached_result["direct"] = False
                            flushed[idx] = cached_result

                    for idx in sorted(flushed):
                        cached_result = flushed[idx]
                        compact = {
                            k: v for k, v in cached_result.items()
                            if k != "data" and not str(k).startswith("_cache_")
                        }
                        journal_lines.append(json.dumps({
                            "format": 5, "index": idx, "segment_key": segment_key(idx, segments[idx]), "result": compact,
                        }, separators=(",", ":")) + "\n")
                        flushed[idx] = compact
                    if journal_lines:
                        journal_fp.write("".join(journal_lines))
                    now2 = time.monotonic()
                    if force_journal or now2 - journal_last_flush[0] >= DOWNLOAD_JOURNAL_FLUSH_INTERVAL:
                        journal_fp.flush()
                        journal_last_flush[0] = now2

                flushed_bytes = sum(max(0, int(compact.get("decoded_bytes", 0) or 0)) for compact in flushed.values())
                return flushed, flushed_bytes, max(0.0, time.perf_counter() - disk_started)

            def reap_disk_flush(wait_for_completion: bool = False) -> int:
                nonlocal disk_future, disk_inflight_bytes, disk_inflight_count
                nonlocal stage_disk_seconds, write_cache_last_flush
                if disk_future is None:
                    return 0
                if not wait_for_completion and not disk_future.done():
                    return 0
                flushed, flushed_bytes, disk_elapsed = disk_future.result()
                for idx, compact in flushed.items():
                    results[idx] = compact
                stage_disk_seconds += disk_elapsed
                disk_future = None
                disk_inflight_bytes = 0
                disk_inflight_count = 0
                write_cache_last_flush = time.monotonic()
                with self.lock:
                    self._disk_commit_bytes_total += flushed_bytes
                    job["article_cache_bytes"] = write_cache_bytes
                    job["stage_disk_seconds"] = round(stage_disk_seconds, 3)
                return len(flushed)

            def start_disk_flush(force: bool = False) -> bool:
                nonlocal write_cache, write_cache_bytes, disk_future
                nonlocal disk_inflight_bytes, disk_inflight_count
                reap_disk_flush(False)
                if disk_future is not None or not write_cache:
                    return False
                now = time.monotonic()
                # Prefer large, contiguous batches. This mirrors the purpose of a
                # SAB-style article cache and avoids one-second random-write waves.
                pressure_target = min(article_cache_limit, 256 * 1024 * 1024)
                if not force:
                    age = now - write_cache_last_flush
                    if write_cache_bytes < pressure_target and (age < 2.0 or write_cache_bytes < 32 * 1024 * 1024):
                        return False
                batch = write_cache
                batch_bytes = write_cache_bytes
                write_cache = {}
                write_cache_bytes = 0
                disk_inflight_bytes = batch_bytes
                disk_inflight_count = len(batch)
                disk_future = DOWNLOAD_DISK_EXECUTOR.submit(_write_cache_batch, batch, force)
                with self.lock:
                    job["article_cache_bytes"] = disk_inflight_bytes
                return True

            def flush_write_cache(force: bool = False) -> int:
                """Schedule or finalize an asynchronous Direct Write cache flush."""
                flushed_count = reap_disk_flush(False)
                if force:
                    if disk_future is not None:
                        flushed_count += reap_disk_flush(True)
                    if write_cache:
                        start_disk_flush(True)
                    if disk_future is not None:
                        flushed_count += reap_disk_flush(True)
                    return flushed_count
                start_disk_flush(False)
                return flushed_count

            def current_pipeline_depth() -> int:
                return max(1, int(pool.effective_pipeline_depth()))

            pipeline_depth = current_pipeline_depth()
            with self.lock:
                job["pipeline_depth"] = pipeline_depth
                job["pipeline"] = (("native-yenc" if NATIVE_YENC_POOL.stats().get("available") else "bulk-python-yenc") + f"+nntp-pipeline-{pipeline_depth}+split-decode+article-cache")

            def segment_progress(index: int, written: int) -> None:
                now_ts = time.time()
                with progress_lock:
                    inflight_progress[index] = max(0, int(written or 0))
                    live_wire = completed_wire + sum(inflight_progress.values())
                elapsed = max(0.001, time.perf_counter() - started)
                live_speed = int(max(0, live_wire - base_wire) / elapsed)
                with self.lock:
                    if self.job_run_tokens.get(str(job["id"])) != run_token:
                        return
                    job["last_activity_ts"] = now_ts
                    job["last_progress_ts"] = now_ts
                    job["downloaded_bytes"] = min(expected, live_wire) if expected else live_wire
                    job["speed_bps"] = live_speed
                    job["peak_speed_bps"] = max(int(job.get("peak_speed_bps", 0) or 0), live_speed)

            max_decode_backlog = max(16, min(128, pool.max_workers * DOWNLOAD_DECODE_BACKLOG_WAVES))

            def submit_batch(indices: list[int]) -> None:
                indexed = [(index, segments[index]) for index in indices]

                def fetch_only():
                    result = fetch_queue_batch_network(
                        provider, group, indexed, cancel_event, str(job["id"]), segment_progress
                    )
                    if cancel_event.is_set() or self.job_run_tokens.get(str(job["id"])) != run_token:
                        raise DownloadCancelled()
                    return result

                fut = pool.executor.submit(fetch_only)
                pending[fut] = list(indices)

            def submit_decode(batch_indices: list[int], batch_results) -> None:
                indexed = [(index, segments[index]) for index in batch_indices]

                def decode_only():
                    result = decode_queue_batch_results(
                        provider, indexed, batch_results, cancel_event
                    )
                    if cancel_event.is_set() or self.job_run_tokens.get(str(job["id"])) != run_token:
                        raise DownloadCancelled()
                    return result

                fut = DOWNLOAD_DECODE_EXECUTOR.submit(decode_only)
                decode_pending[fut] = list(batch_indices)

            def fill_pending(target_parallelism: int) -> None:
                nonlocal next_pos
                # Network work is intentionally allowed to stay ahead of decode by
                # a bounded amount. This keeps TLS/NNTP sockets continuously busy
                # without letting raw BODY data consume unbounded memory.
                while (
                    next_pos < len(missing_indices)
                    and len(pending) < target_parallelism
                    and len(decode_pending) < max_decode_backlog
                    and (write_cache_bytes + disk_inflight_bytes) < article_cache_limit * 2
                    and not provider_outage
                ):
                    self._wait_if_paused(job, cancel_event, run_token)
                    batch_depth = current_pipeline_depth()
                    batch_indices = missing_indices[next_pos:next_pos + batch_depth]
                    submit_batch(batch_indices)
                    next_pos += len(batch_indices)

            def update_live_status() -> int:
                nonlocal parallelism
                elapsed = max(0.001, time.perf_counter() - started)
                current_speed = int(max(0, completed_wire - base_wire) / elapsed)
                pool.observe_speed(current_speed)
                current_target = min(desired_parallelism(), len(missing_indices))
                parallelism = current_target
                with self.lock:
                    job["speed_bps"] = current_speed
                    job["peak_speed_bps"] = max(int(job.get("peak_speed_bps", 0) or 0), current_speed)
                    job["connections_used"] = min(current_target, len(pending))
                    job["connection_target"] = current_target
                    job["decode_backlog"] = len(decode_pending)
                    job["pipeline_depth"] = current_pipeline_depth()
                    job["pipeline"] = (("native-yenc" if NATIVE_YENC_POOL.stats().get("available") else "bulk-python-yenc") + f"+nntp-pipeline-{current_pipeline_depth()}+split-decode+article-cache+async-disk+" + ("sparse-write" if sparse_direct_write else "sequential-fallback"))
                return current_target

            def process_decoded_batch(batch_results) -> None:
                nonlocal new_retry_count, transient_fail_streak, provider_outage
                nonlocal recovered_parts, stage_network_seconds, stage_decode_seconds
                nonlocal last_persist, parallelism

                for index, result, batch_error in batch_results:
                    seg = segments[index]
                    try:
                        if batch_error is not None:
                            raise batch_error
                        if result is None:
                            raise NntpError("Article batch returned no result")
                        result = cache_result(index, seg, result)
                        perf = dict(result.get("perf") or {})
                        stage_network_seconds += float(perf.get("network_seconds", 0) or 0)
                        stage_decode_seconds += float(perf.get("decode_seconds", 0) or 0)
                        provider_attempts = list(result.get("provider_attempts") or [])
                        attempts_total = max(int(result.get("attempts", 1) or 1), len(provider_attempts) + 1)
                        new_retry_count += max(0, attempts_total - 1)
                        transient_fail_streak = 0
                        failures.pop(index, None)
                        if result.get("recovered"):
                            source_name = str(result.get("provider_name") or "Recovery provider")
                            recovered_parts += 1
                            recovery_sources[source_name] = recovery_sources.get(source_name, 0) + 1
                    except SegmentFetchError as exc:
                        attempts = list(exc.attempts or [])
                        new_retry_count += max(0, len(attempts) - 1)
                        failure = {
                            "index": index, "part": int(seg.get("part", index + 1) or index + 1),
                            "article": seg.get("article"), "message_id": str(seg.get("message_id") or ""),
                            "bytes": max(0, int(seg.get("bytes", 0) or 0)), "code": exc.code,
                            "label": exc.label, "error": str(exc)[:1600], "retryable": bool(exc.retryable),
                            "suggestion": exc.suggestion, "attempts": attempts[-16:],
                        }
                        failures[index] = failure
                        if failure["retryable"] and failure["code"] in {"connection", "connection_refused", "connection_limit", "timeout", "dns", "tls", "io", "segment_failed"}:
                            transient_fail_streak += 1
                        else:
                            transient_fail_streak = 0
                    except Exception as exc:
                        info = classify_nntp_failure(exc)
                        failure = {
                            "index": index, "part": int(seg.get("part", index + 1) or index + 1),
                            "article": seg.get("article"), "message_id": str(seg.get("message_id") or ""),
                            "bytes": max(0, int(seg.get("bytes", 0) or 0)), "code": info["code"],
                            "label": info["label"], "error": info["raw"][:1600], "retryable": bool(info["retryable"]),
                            "suggestion": info["suggestion"], "attempts": [],
                        }
                        failures[index] = failure
                        if failure["retryable"] and failure["code"] in {"connection", "connection_refused", "connection_limit", "timeout", "dns", "tls", "io", "segment_failed"}:
                            transient_fail_streak += 1
                        else:
                            transient_fail_streak = 0

                current_target = min(desired_parallelism(), len(missing_indices))
                parallelism = current_target
                outage_threshold = 1 if current_target <= 1 else max(2, min(4, current_target))
                if transient_fail_streak >= outage_threshold:
                    provider_outage = True

                cached_successes = len(results) + len(write_cache) + disk_inflight_count
                processed = cached_successes + len(failures)
                elapsed = max(0.001, time.perf_counter() - started)
                current_speed = int(max(0, completed_wire - base_wire) / elapsed)
                pool.observe_speed(current_speed)
                missing_bytes = sum(int(x.get("bytes", 0) or 0) for x in failures.values())
                with self.lock:
                    job["downloaded_bytes"] = min(expected, completed_wire) if expected else completed_wire
                    job["current_part"] = processed
                    job["processed_parts"] = processed
                    job["successful_parts"] = cached_successes
                    job["failed_parts"] = len(failures)
                    job["missing_bytes"] = missing_bytes
                    job["retry_count"] = retry_base + new_retry_count
                    job["recovered_parts"] = recovered_parts
                    job["recovery_sources"] = dict(recovery_sources)
                    job["speed_bps"] = current_speed
                    job["peak_speed_bps"] = max(int(job.get("peak_speed_bps", 0) or 0), current_speed)
                    job["segment_errors"] = list(failures.values())[-40:]
                    job["last_activity_ts"] = time.time()
                    job["last_progress_ts"] = time.time()
                    job["native_parts"] = native_parts
                    job["stage_network_seconds"] = round(stage_network_seconds, 3)
                    job["stage_decode_seconds"] = round(stage_decode_seconds, 3)
                    job["stage_disk_seconds"] = round(stage_disk_seconds, 3)
                    job["connections_used"] = min(current_target, len(pending))
                    job["connection_target"] = current_target
                    job["decode_backlog"] = len(decode_pending)
                    if failures:
                        soft = sum(1 for x in failures.values() if x.get("code") in {"article_soft_missing", "article_propagating"})
                        job["status_detail"] = (f"Fetching remaining blocks • {soft} awaiting recheck" if soft == len(failures) else f"Fetching remaining blocks • {len(failures)} unavailable so far")
                    else:
                        cache_mb = (write_cache_bytes + disk_inflight_bytes) / (1024 * 1024)
                        job["status_detail"] = f"Retrieved {processed} of {len(segments)} blocks" + (f" • {cache_mb:.0f} MB write cache" if cache_mb >= 1 else "")
                    now_perf = time.perf_counter()
                    if now_perf - last_persist >= DOWNLOAD_PROGRESS_PERSIST_INTERVAL or processed == len(segments):
                        self._save_hot(DOWNLOAD_PROGRESS_PERSIST_INTERVAL)
                        last_persist = now_perf

            next_pos = 0
            fill_pending(parallelism)

            while pending or decode_pending:
                self._wait_if_paused(job, cancel_event, run_token)
                all_futures = list(pending.keys()) + list(decode_pending.keys())
                done, _ = wait(all_futures, timeout=0.20, return_when=FIRST_COMPLETED)
                if not done:
                    target_parallelism = update_live_status()
                    fill_pending(target_parallelism)
                    flush_write_cache(False)
                    continue

                # Network completions are intentionally handled first. Their raw
                # BODY payloads are handed to the decoder executor and vacated NNTP
                # slots are refilled before decoded blocks are validated/written.
                # This is the critical v3.4.15 change: a socket no longer sits idle
                # while the same worker waits for yEnc/process-pipe/cache work.
                network_done = [fut for fut in done if fut in pending]
                decode_done = [fut for fut in done if fut in decode_pending]

                for fut in network_done:
                    batch_indices = pending.pop(fut)
                    try:
                        batch_results = fut.result()
                    except DownloadCancelled:
                        raise
                    except Exception as batch_exc:
                        batch_results = [(index, None, batch_exc) for index in batch_indices]

                    # The network-stage progress counter is finalized here, before
                    # decoding. This makes the speed meter reflect NNTP acquisition
                    # rather than downstream CPU/process latency.
                    for index, result, batch_error in batch_results:
                        with progress_lock:
                            inflight_progress.pop(index, None)
                        if batch_error is None and result is not None:
                            completed_wire += max(0, int(result.get("wire_bytes", 0) or 0))
                    submit_decode(batch_indices, batch_results)

                target_parallelism = update_live_status()
                fill_pending(target_parallelism)

                # Pick up decoder futures that may have completed while the network
                # wave was being refilled, not only those returned by the first wait.
                ready_decode = set(decode_done)
                ready_decode.update(fut for fut in list(decode_pending.keys()) if fut.done())
                for fut in list(ready_decode):
                    batch_indices = decode_pending.pop(fut, None)
                    if batch_indices is None:
                        continue
                    try:
                        decoded_results = fut.result()
                    except DownloadCancelled:
                        raise
                    except Exception as batch_exc:
                        decoded_results = [(index, None, batch_exc) for index in batch_indices]
                    process_decoded_batch(decoded_results)

                if provider_outage:
                    flush_write_cache(True)
                    cancel_event.set()
                    for other in list(pending.keys()):
                        other.cancel()
                    for other in list(decode_pending.keys()):
                        other.cancel()
                    pending.clear()
                    decode_pending.clear()
                    abort_download_jobs([str(job["id"])])
                    with self.lock:
                        job["watchdog_retry"] = True
                        job["status"] = "retry_wait"
                        job["retry_at_ts"] = time.time() + 8
                        job["status_detail"] = "Provider appears offline — connection pool reset; retrying from preserved blocks"
                        job["transfer_phase"] = "retry_wait"
                        self._save()
                    raise DownloadCancelled()

                # Disk commits stay off the network refill path. If decode begins
                # to lag, the bounded raw backlog naturally back-pressures new BODY
                # submissions without parking already-warm NNTP workers on decoding.
                flush_write_cache(False)
                target_parallelism = update_live_status()
                fill_pending(target_parallelism)

            flush_write_cache(True)
            if journal_fp is not None:
                journal_fp.flush()

            if failures:
                failure_list = [failures[i] for i in sorted(failures)]
                codes = [str(f.get("code") or "") for f in failure_list]
                retryable = all(bool(f.get("retryable")) for f in failure_list)
                missing_count = len(failure_list)
                missing_bytes = sum(int(f.get("bytes", 0) or 0) for f in failure_list)
                if "authentication" in codes:
                    code, label = "authentication", "Provider authentication failed"
                    suggestion = next((f.get("suggestion") for f in failure_list if f.get("code") == "authentication"), "Verify provider credentials.")
                    retryable = False
                elif "permission" in codes:
                    code, label = "permission", "Provider access denied"
                    suggestion = next((f.get("suggestion") for f in failure_list if f.get("code") == "permission"), "Check provider access settings.")
                    retryable = False
                elif all(c == "article_propagating" for c in codes):
                    code, label = "propagation", "Waiting for recent NZB articles to propagate"
                    suggestion = f"{missing_count} recent block{'s are' if missing_count != 1 else ' is'} not available yet. NewzDeck will retry only those blocks; {len(results)} good blocks are preserved."
                    retryable = True
                elif all(c in {"article_soft_missing", "article_propagating"} for c in codes):
                    code, label = "soft_missing", "Rechecking temporarily unavailable article blocks"
                    suggestion = f"{missing_count} Message-ID block{'s are' if missing_count != 1 else ' is'} being rechecked across fresh provider connections. {len(results)} verified blocks are preserved."
                    retryable = True
                elif "article_missing" in codes:
                    code, label = "incomplete", "Download incomplete — confirmed missing article blocks"
                    suggestion = f"{missing_count} block{'s are' if missing_count != 1 else ' is'} unavailable after repeated provider/recovery checks. Retry later or add another recovery provider; {len(results)} good blocks are preserved."
                    retryable = False
                elif "integrity" in codes or "decode" in codes:
                    code, label = "incomplete", "Download incomplete — damaged article blocks"
                    suggestion = f"{missing_count} block{'s failed' if missing_count != 1 else ' failed'} integrity/decoding. Good blocks are preserved; a recovery provider may have clean copies."
                    retryable = False
                elif retryable:
                    code, label = "provider_temporary", "Provider temporarily unavailable"
                    suggestion = f"NewzDeck will retry automatically. {len(results)} completed blocks are preserved, so they will not be downloaded again."
                    retryable = True
                else:
                    first_permanent = next((f for f in failure_list if not f.get("retryable")), failure_list[0])
                    code = str(first_permanent.get("code") or "incomplete")
                    label = str(first_permanent.get("label") or "Download could not continue")
                    suggestion = str(first_permanent.get("suggestion") or f"{len(results)} good blocks are preserved. Resolve the reported provider/post problem, then retry.")
                    retryable = False

                message = f"{missing_count} of {len(segments)} article blocks could not be retrieved"
                if missing_bytes:
                    message += f" ({missing_bytes / 1024**2:.1f} MB unavailable)"
                message += "."
                with self.lock:
                    job["failed_parts"] = missing_count
                    job["missing_bytes"] = missing_bytes
                    job["segment_errors"] = failure_list[-40:]
                    job["error_code"] = code
                    job["error_label"] = label
                    job["error_suggestion"] = suggestion
                    job["error_retryable"] = retryable
                    job["status_detail"] = label
                    job["speed_bps"] = 0
                    job["connections_used"] = 0
                    job["last_activity_ts"] = time.time()
                    self._save()
                raise DownloadIncompleteError(message, failures=failure_list, retryable=retryable, code=code, label=label, suggestion=suggestion)

            self._wait_if_paused(job, cancel_event, run_token)
            if partial_fp is not None:
                partial_fp.flush()
                partial_fp.close()
                partial_fp = None
            if journal_fp is not None:
                journal_fp.flush()
                journal_fp.close()
                journal_fp = None

            direct_all = all(bool(results[i].get("direct", False)) for i in range(len(segments)))
            if not direct_all:
                with self.lock:
                    job["transfer_phase"] = "assembling"
                    job["status_detail"] = f"Assembling {len(segments)} verified blocks"
                    job["speed_bps"] = 0
                    job["connections_used"] = 0
                    self._save()
                assembled = temp.with_suffix(temp.suffix + ".assemble")
                assembled.unlink(missing_ok=True)
                with assembled.open("wb") as out, temp.open("rb") as direct_src:
                    for index in range(len(segments)):
                        self._wait_if_paused(job, cancel_event, run_token)
                        result = results[index]
                        meta = result.get("meta") or {}
                        begin = int(meta.get("begin", 0) or 0)
                        if begin > 0:
                            out.seek(begin - 1)
                        decoded = int(result.get("decoded_bytes", 0) or 0)
                        if result.get("direct"):
                            direct_src.seek(int(result.get("direct_offset", 0) or 0))
                            remaining = decoded
                            while remaining > 0:
                                chunk = direct_src.read(min(1024 * 1024, remaining))
                                if not chunk:
                                    raise NntpError("Partial-file block could not be reread during compatibility assembly")
                                out.write(chunk)
                                remaining -= len(chunk)
                        else:
                            with Path(result["fallback_path"]).open("rb") as src:
                                shutil.copyfileobj(src, out, length=1024 * 1024)
                assembled.replace(temp)

            self._wait_if_paused(job, cancel_event, run_token)
            with self.lock:
                job["transfer_phase"] = "finalizing"
                job["status_detail"] = "Finalizing downloaded file"
                job["speed_bps"] = 0
                job["connections_used"] = 0
                self._save()
            actual_size = temp.stat().st_size
            if actual_size <= 0:
                raise NntpError("Assembled file is empty")
            advertised_sizes = [int((results[i].get("meta") or {}).get("size", 0) or 0) for i in results]
            full_sizes = [x for x in advertised_sizes if x > 0]
            if full_sizes and len(segments) > 1:
                expected_full = max(full_sizes)
                if expected_full and actual_size != expected_full:
                    raise NntpError(f"Multipart assembly size mismatch: expected {expected_full:,} bytes, assembled {actual_size:,}")
            temp.replace(dest)
            with self.lock:
                job["path"] = str(dest)
                job["partial_path"] = ""
                job["actual_size"] = dest.stat().st_size
                job["status"] = "completed"
                job["downloaded_bytes"] = max(completed_wire, expected)
                job["current_part"] = len(segments)
                job["processed_parts"] = len(segments)
                job["successful_parts"] = len(segments)
                job["failed_parts"] = 0
                job["missing_bytes"] = 0
                job["segment_errors"] = []
                job["error"] = ""
                job["error_code"] = ""
                job["error_label"] = ""
                job["error_suggestion"] = ""
                job["error_retryable"] = False
                job["status_detail"] = "Download completed"
                job["transfer_phase"] = "complete"
                job["integrity_status"] = "healthy"
                job["repair_missing_bytes"] = 0
                job["repair_missing_blocks"] = 0
                duration = max(0.0, time.time() - float(job.get("started_ts", time.time()) or time.time()))
                job["duration_seconds"] = round(duration, 3)
                job["average_speed_bps"] = int(max(completed_wire, expected) / duration) if duration > 0 else 0
                job["speed_bps"] = 0
                job["connections_used"] = 0
                job["completed_ts"] = time.time()
                job["last_activity_ts"] = time.time()
                self._save()
            completed_ok = True
            DIAGNOSTICS.event("info", "download", f"Completed {filename}", bytes=dest.stat().st_size, provider=job.get("provider_name",""), group=group)
            self.direct_unpack_wake.set()
            self._wait_if_paused(job, cancel_event, run_token)
            self._maybe_start_direct_unpack(job)
            self._after_download_completed(job)
        except Exception:
            for future in list(pending.keys()):
                future.cancel()
            raise
        finally:
            try:
                if journal_fp is not None:
                    journal_fp.flush()
                    journal_fp.close()
            except Exception:
                pass
            try:
                if partial_fp is not None:
                    partial_fp.close()
            except Exception:
                pass
            if completed_ok:
                shutil.rmtree(scratch, ignore_errors=True)
            self._release_download_path(dest)

    def _cleanup_removed_scratch(self, job_id: str, partial_path: str = "") -> None:
        path = DOWNLOAD_TEMP_DIR / str(job_id)
        for delay in (0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0):
            if delay:
                time.sleep(delay)
            try:
                shutil.rmtree(path)
            except FileNotFoundError:
                return
            except OSError:
                continue
            if not path.exists():
                break
        if partial_path:
            try:
                partial = Path(partial_path)
                if str(job_id) in partial.name and partial.name.endswith(".part"):
                    partial.unlink(missing_ok=True)
            except OSError:
                pass

    def _refresh_collection_post_state_locked(self, collection_id: str) -> None:
        collection_id = str(collection_id or "")
        if not collection_id:
            return
        targets = [j for j in self.jobs if str(j.get("collection_id") or "") == collection_id]
        if not targets:
            return
        completed = [j for j in targets if j.get("status") == "completed"]
        if not completed:
            return
        blocking = [j for j in targets if nzb_job_blocks_collection(j)]
        completed_blocking = [j for j in blocking if j.get("status") == "completed"]
        if not completed_blocking:
            return
        expected = max([int(j.get("collection_required_expected", 0) or 0) for j in targets] + [0]) or len(blocking)
        terminal_bad = [j for j in blocking if j.get("status") in {"failed", "cancelled"}]
        pending = [j for j in blocking if j.get("status") in {"queued", "downloading", "retry_wait", "cancelling"}]
        if expected and len(blocking) < expected:
            missing = expected - len(blocking)
            for target in completed:
                if str(target.get("post_status") or "") not in {"completed", "not_needed", "needs_tool", "disabled"}:
                    target["post_status"] = "blocked"
                    target["post_progress"] = 100
                    target["post_message"] = f"Post-processing blocked: {missing} package file{'s were' if missing != 1 else ' was'} removed"
        elif terminal_bad:
            for target in completed:
                if str(target.get("post_status") or "") not in {"completed", "not_needed", "needs_tool", "disabled"}:
                    target["post_status"] = "blocked"
                    target["post_progress"] = 100
                    target["post_message"] = f"Post-processing blocked: {len(terminal_bad)} file{'s' if len(terminal_bad) != 1 else ''} failed or were cancelled. Retry those files or process this package manually."
        elif pending:
            for target in completed:
                if str(target.get("post_status") or "") in {"", "waiting", "blocked", "cancelled"}:
                    target["post_status"] = "waiting"
                    target["post_progress"] = 0
                    target["post_message"] = "Waiting for the rest of this package"

    def _post_settings(self) -> dict[str, Any]:
        raw = json_read(SETTINGS_FILE, {})
        if not isinstance(raw, dict):
            raw = {}
        return {
            "enabled": bool(raw.get("post_processing", DEFAULT_POST_PROCESSING)),
            "repair": bool(raw.get("auto_repair", DEFAULT_AUTO_REPAIR)),
            "fetch_par2": bool(raw.get("auto_fetch_par2", DEFAULT_AUTO_FETCH_PAR2)),
            "extract": bool(raw.get("auto_extract", DEFAULT_AUTO_EXTRACT)),
            "cleanup": bool(raw.get("cleanup_archives", DEFAULT_CLEANUP_ARCHIVES)),
            "subfolder": bool(raw.get("extract_subfolder", DEFAULT_EXTRACT_SUBFOLDER)),
            "direct_unpack": str(raw.get("direct_unpack_mode", DEFAULT_DIRECT_UNPACK_MODE) or DEFAULT_DIRECT_UNPACK_MODE).casefold() if str(raw.get("direct_unpack_mode", DEFAULT_DIRECT_UNPACK_MODE) or DEFAULT_DIRECT_UNPACK_MODE).casefold() in {"off","auto","on"} else DEFAULT_DIRECT_UNPACK_MODE,
            "automation_cleanup": bool(raw.get("automation_media_cleanup", DEFAULT_AUTOMATION_MEDIA_CLEANUP)),
        }

    def _direct_unpack_state_locked(self, collection_id: str) -> dict[str, Any]:
        rec = self.collections.get(str(collection_id or ""))
        if not isinstance(rec, dict):
            return {}
        state = rec.get("direct_unpack")
        return state if isinstance(state, dict) else {}

    def _set_direct_unpack_state(self, collection_id: str, *, persist: bool = True, **updates: Any) -> dict[str, Any]:
        cid = str(collection_id or "")
        with self.lock:
            rec = self.collections.get(cid)
            if not isinstance(rec, dict):
                return {}
            state = dict(rec.get("direct_unpack") or {}) if isinstance(rec.get("direct_unpack"), dict) else {}
            state.update(updates)
            state["updated_ts"] = time.time()
            rec["direct_unpack"] = state
            if persist:
                self._save()
            else:
                self._save_hot(5.0)
        self.direct_unpack_wake.set()
        return state

    def _automation_context_locked(self, collection_id: str, targets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        cid = str(collection_id or "")
        rec = self.collections.get(cid) if cid else None
        context = rec.get("automation_context") if isinstance(rec, dict) else None
        if isinstance(context, dict) and context:
            return context
        for job in targets or []:
            candidate = job.get("automation_context")
            if isinstance(candidate, dict) and candidate:
                return candidate
        return {}

    def _is_automation_grab_locked(self, collection_id: str, targets: list[dict[str, Any]] | None = None) -> bool:
        context = self._automation_context_locked(collection_id, targets)
        return str(context.get("source") or "") in {"automation_grab", "manual_media_grab"}

    def _cleanup_automation_staging(self, collection_id: str, targets: list[dict[str, Any]], parent: Path, destination: str = "") -> bool:
        """Remove a completed Automation NZB staging folder only after verified import.

        The safety checks deliberately require the staging directory to be a child of
        NewzDeck's configured Download Folder. This prevents a malformed queue record
        from ever turning post-processing cleanup into an arbitrary recursive delete.
        """
        settings = self._post_settings()
        if not settings.get("automation_cleanup", DEFAULT_AUTOMATION_MEDIA_CLEANUP):
            return False
        with self.lock:
            if not self._is_automation_grab_locked(collection_id, targets):
                return False
        try:
            root = DOWNLOAD_DIR.resolve()
            staging = parent.resolve()
            if staging == root or not staging.is_relative_to(root):
                DIAGNOSTICS.event("warning", "automation-cleanup", "Refused to remove staging folder outside the configured Download Folder", collection=collection_id, path=str(staging))
                return False
            if destination:
                try:
                    dest = Path(destination).resolve()
                    if dest == staging or dest.is_relative_to(staging):
                        DIAGNOSTICS.event("warning", "automation-cleanup", "Refused staging cleanup because imported media is still inside the staging folder", collection=collection_id, path=str(staging), destination=str(dest))
                        return False
                except OSError:
                    pass
            shutil.rmtree(staging)
        except FileNotFoundError:
            pass
        except OSError as exc:
            DIAGNOSTICS.event("warning", "automation-cleanup", f"Could not completely remove Automation staging folder: {exc}", collection=collection_id, path=str(parent))
            return False
        with self.lock:
            rec = self.collections.get(str(collection_id or ""))
            if isinstance(rec, dict):
                rec["staging_cleaned"] = True
                rec["staging_cleaned_ts"] = time.time()
                if destination:
                    rec["automation_destination"] = str(destination)
            for target in targets:
                target["source_cleaned"] = True
                target["path"] = ""
                target["partial_path"] = ""
            self._save()
        DIAGNOSTICS.event("info", "automation-cleanup", "Removed downloaded archives and staging files after successful media import", collection=collection_id, destination=str(destination or ""))
        return True

    def _direct_unpack_volume_jobs_locked(self, collection_id: str) -> list[dict[str, Any]]:
        jobs = []
        for job in self._collection_jobs_locked(collection_id):
            if str(job.get("collection_role") or "payload") != "payload":
                continue
            index = _rar_volume_index(str(job.get("filename") or ""))
            if index is None:
                continue
            jobs.append((index, float(job.get("created_ts", 0) or 0), job))
        jobs.sort(key=lambda item: (item[0], item[1]))

        seen: set[int] = set()
        ordered: list[dict[str, Any]] = []
        for index, _created, job in jobs:
            if index in seen:
                return []
            seen.add(index)
            ordered.append(job)
        return ordered

    def _maybe_start_direct_unpack(self, job: dict[str, Any]) -> None:
        settings = self._post_settings()
        mode = str(settings.get("direct_unpack") or DEFAULT_DIRECT_UNPACK_MODE).casefold()
        if mode not in {"auto", "on"} or not settings.get("enabled") or not settings.get("extract"):
            return
        if str(job.get("source") or "") not in {"nzb", "browser_set"}:
            return
        if mode == "auto":
            pool_state = download_pool_stats()
            active = int(pool_state.get("active", 0) or 0)
            capacity = int(pool_state.get("capacity", 0) or 0)
            # In Auto mode, network throughput wins. Direct Unpack can start near
            # the tail when sockets are no longer heavily occupied. Users can
            # still choose On to force concurrent unpacking.
            if capacity > 0 and active >= max(2, int(math.ceil(capacity * 0.20))):
                return
        cid = str(job.get("collection_id") or "")
        if not cid or _rar_volume_index(str(job.get("filename") or "")) is None:
            return
        unrar = _unrar_path()
        if not unrar:


            if sys.platform == "win32" and not _unrar_install_lock.locked():
                threading.Thread(target=_ensure_managed_unrar_tool, name="newzdeck-unrar-on-demand", daemon=True).start()
            if mode == "on":
                self._set_direct_unpack_state(cid, status="preparing", message=f"Preparing managed UnRAR {UNRAR_MANAGED_VERSION}; download continues normally", error="")
            return
        with self.lock:
            rec = self.collections.get(cid)
            if not isinstance(rec, dict):
                return
            current = rec.get("direct_unpack") if isinstance(rec.get("direct_unpack"), dict) else {}
            if str(current.get("status") or "") in {"active", "completed", "fallback", "failed", "cancelled"}:
                return
            volumes = self._direct_unpack_volume_jobs_locked(cid)
            if len(volumes) < 2:
                return
            if _rar_volume_index(str(volumes[0].get("filename") or "")) != 1:
                return
            if mode == "auto":
                # Never let a transient lull start UnRAR in the middle of a fast
                # transfer. Automatic Direct Unpack is a tail optimization only;
                # explicit On still honors the user's request for full overlap.
                remaining = sum(1 for v in volumes if v.get("status") != "completed")
                if remaining > max(2, DIRECT_UNPACK_AUTO_READ_AHEAD_VOLUMES):
                    return

            if all(v.get("status") == "completed" for v in volumes):
                return
            if any(v.get("status") in {"failed", "cancelled", "retry_wait"} or str(v.get("integrity_status") or "") == "repair_needed" for v in volumes):
                return
            first_path = Path(str(volumes[0].get("path") or ""))
            if not first_path.is_file():
                return
            output_dir = first_path.parent / f"_NEWZDECK_DIRECT_UNPACK_{cid[:8]}"
            rec["direct_unpack"] = {
                "status": "active", "mode": mode, "message": "Direct Unpack starting while remaining RAR volumes download",
                "progress": 0, "first_archive": str(first_path), "output_dir": str(output_dir),
                "started_ts": time.time(), "updated_ts": time.time(), "tool": Path(unrar).name,
            }
            self._save()
            cancel = threading.Event()
            self.direct_unpack_cancel_events[cid] = cancel
            future = self.direct_unpack_executor.submit(self._run_direct_unpack, cid, unrar, cancel)
            self.direct_unpack_futures[cid] = future
        DIAGNOSTICS.event("info", "direct-unpack", "Started Direct Unpack", collection=cid, archive=str(first_path), tool=str(unrar))

    def _direct_unpack_should_abort_locked(self, collection_id: str) -> str:
        jobs = self._collection_jobs_locked(collection_id)
        if not jobs:
            return "NZB package was removed"
        for job in jobs:
            if not nzb_job_blocks_collection(job):
                continue
            if job.get("status") in {"failed", "cancelled"}:
                return "A required NZB file failed or was cancelled"
            if str(job.get("integrity_status") or "") == "repair_needed":
                return "PAR2 repair is required"
            if job.get("status") == "retry_wait":
                return "A required RAR volume needs a provider retry"
        return ""

    def _run_direct_unpack(self, collection_id: str, unrar: str, cancel_event: threading.Event) -> None:
        cid = str(collection_id or "")
        process: subprocess.Popen | None = None
        reader: threading.Thread | None = None
        output_queue: queue.Queue[str | None] = queue.Queue()
        try:
            with self.lock:
                state = dict(self._direct_unpack_state_locked(cid))
                volumes = self._direct_unpack_volume_jobs_locked(cid)
            first = Path(str(state.get("first_archive") or ""))
            output_dir = Path(str(state.get("output_dir") or ""))
            direct_mode = str(state.get("mode") or DEFAULT_DIRECT_UNPACK_MODE).casefold()
            if not first.is_file() or len(volumes) < 2:
                raise RuntimeError("Direct Unpack prerequisites disappeared")
            shutil.rmtree(output_dir, ignore_errors=True)
            output_dir.mkdir(parents=True, exist_ok=True)

            cmd = [unrar, "x", "-vp", "-idp", "-o+", "-ai", "-p-", str(first), str(output_dir) + os.sep]
            creationflags = (getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)) if os.name == "nt" else 0
            process = subprocess.Popen(
                cmd, cwd=str(first.parent), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=0, creationflags=creationflags,
            )

            def read_output() -> None:
                assert process is not None and process.stdout is not None
                try:
                    while True:
                        chunk = process.stdout.read(1)
                        if not chunk:
                            break
                        output_queue.put(chunk)
                finally:
                    output_queue.put(None)

            reader = threading.Thread(target=read_output, name=f"newzdeck-direct-unpack-reader-{cid[:6]}", daemon=True)
            reader.start()
            buffer = ""
            prompt_number = 0
            last_activity = time.monotonic()
            last_state_update = 0.0
            reader_done = False
            while True:
                if cancel_event.is_set() or self.shutdown_event.is_set():
                    raise PostProcessingCancelled()
                with self.lock:
                    abort_reason = self._direct_unpack_should_abort_locked(cid)
                    volumes = self._direct_unpack_volume_jobs_locked(cid)
                    completed_volume_bytes = sum(max(0, int(v.get("actual_size", 0) or v.get("expected_bytes", 0) or 0)) for v in volumes if v.get("status") == "completed")
                    total_volume_bytes = sum(max(0, int(v.get("expected_bytes", 0) or 0)) for v in volumes)
                if abort_reason:
                    raise RuntimeError(abort_reason)
                try:
                    item = output_queue.get(timeout=0.25)
                    if item is None:
                        reader_done = True
                    else:
                        buffer = (buffer + item)[-8192:]
                        last_activity = time.monotonic()
                except queue.Empty:
                    pass



                folded = buffer.casefold()
                marker = folded.rfind("insert disk with ")
                continue_marker = folded.rfind("[c]ontinue")
                if marker >= 0 and continue_marker > marker:
                    prompt_number += 1
                    next_index = prompt_number + 1
                    with self.lock:
                        volumes = self._direct_unpack_volume_jobs_locked(cid)
                    if next_index > len(volumes):
                        raise RuntimeError("Direct Unpack requested a RAR volume that is not present in this NZB")
                    next_job = volumes[next_index - 1]
                    next_name = str(next_job.get("filename") or f"volume {next_index}")
                    self._set_direct_unpack_state(cid, persist=False, status="active", message=f"Direct Unpack waiting for {next_name}", progress=max(1, min(99, int(100 * completed_volume_bytes / total_volume_bytes))) if total_volume_bytes else 0)
                    yield_announced = False
                    while True:
                        if cancel_event.is_set() or self.shutdown_event.is_set():
                            raise PostProcessingCancelled()
                        with self.lock:
                            live = self._find_job(str(next_job.get("id") or ""))
                            abort_reason = self._direct_unpack_should_abort_locked(cid)
                            ready_path = Path(str(live.get("path") or "")) if live else Path()
                            ready = bool(live and live.get("status") == "completed" and ready_path.is_file())
                            if ready and direct_mode == "auto":



                                lookahead_end = min(len(volumes), next_index + DIRECT_UNPACK_AUTO_READ_AHEAD_VOLUMES)
                                ahead = volumes[next_index:lookahead_end]
                                if ahead and any(v.get("status") in {"queued", "downloading", "cancelling"} for v in ahead):
                                    ready = False
                        if abort_reason:
                            raise RuntimeError(abort_reason)
                        if ready:
                            break
                        if direct_mode == "auto" and not yield_announced:
                            self._set_direct_unpack_state(cid, persist=False, status="active", message="Direct Unpack yielding to downloader • buffering RAR read-ahead")
                            self.direct_unpack_wake.clear()
                            yield_announced = True
                        self.direct_unpack_wake.wait(0.25)
                        self.direct_unpack_wake.clear()
                    if process.stdin is None:
                        raise RuntimeError("Direct Unpack lost the UnRAR control pipe")
                    process.stdin.write("C\n")
                    process.stdin.flush()
                    self._set_direct_unpack_state(cid, persist=False, status="active", message=f"Direct Unpacking through {next_name}")
                    buffer = ""
                    last_activity = time.monotonic()

                now = time.monotonic()
                if now - last_state_update >= 2.0:
                    progress = max(1, min(99, int(100 * completed_volume_bytes / total_volume_bytes))) if total_volume_bytes else 0
                    self._set_direct_unpack_state(cid, persist=False, status="active", progress=progress)
                    last_state_update = now
                if process.poll() is not None and reader_done:
                    break
                if now - last_activity > 15 * 60:
                    raise RuntimeError("Direct Unpack stopped making progress; normal extraction will be used")

            returncode = process.wait(timeout=5)
            if returncode != 0:
                raise RuntimeError(f"UnRAR Direct Unpack exited with code {returncode}")
            extracted_files = []
            try:
                extracted_files = [p for p in output_dir.rglob('*') if p.is_file()]
            except OSError:
                pass
            if not extracted_files:
                raise RuntimeError("Direct Unpack finished but did not produce any files")
            self._set_direct_unpack_state(cid, status="completed", progress=100, message="Direct Unpack completed during download", completed_ts=time.time(), error="")
            DIAGNOSTICS.event("info", "direct-unpack", "Direct Unpack completed", collection=cid, output=str(output_dir))
        except PostProcessingCancelled:
            self._set_direct_unpack_state(cid, status="cancelled", message="Direct Unpack stopped", error="cancelled")
        except Exception as exc:
            self._set_direct_unpack_state(cid, status="fallback", message=f"Direct Unpack fallback: {exc}", error=str(exc)[:1000])
            DIAGNOSTICS.event("warning", "direct-unpack", f"Direct Unpack fell back to normal extraction: {exc}", collection=cid)
        finally:
            if process is not None and process.poll() is None:
                try:
                    if process.stdin is not None:
                        process.stdin.write("Q\n")
                        process.stdin.flush()
                except Exception:
                    pass
                try:
                    process.terminate()
                    process.wait(timeout=3)
                except Exception:
                    try: process.kill()
                    except Exception: pass
            with self.lock:
                self.direct_unpack_cancel_events.pop(cid, None)
                self.direct_unpack_futures.pop(cid, None)
            self.direct_unpack_wake.set()

            with self.lock:
                candidate = next((j for j in self._collection_jobs_locked(cid) if j.get("status") == "completed"), None)
            if candidate is not None:
                threading.Thread(target=self._after_download_completed, args=(candidate,), name=f"newzdeck-direct-finalize-{cid[:6]}", daemon=True).start()

    def _wait_for_direct_unpack(self, collection_id: str, targets: list[dict[str, Any]], cancel_event: threading.Event | None = None) -> dict[str, Any]:
        cid = str(collection_id or "")
        if not cid:
            return {}
        started = time.monotonic()
        last_ui_state: tuple[int, str] | None = None
        last_ui_update = 0.0
        all_rars_complete_since: float | None = None
        while True:
            with self.lock:
                state = dict(self._direct_unpack_state_locked(cid))
            if str(state.get("status") or "") != "active":
                return state
            if cancel_event is not None and cancel_event.is_set():
                event = self.direct_unpack_cancel_events.get(cid)
                if event: event.set()
                raise PostProcessingCancelled()
            now_mono = time.monotonic()
            if now_mono - started > 20 * 60:
                event = self.direct_unpack_cancel_events.get(cid)
                if event: event.set()
                self._set_direct_unpack_state(cid, status="fallback", message="Direct Unpack finalization timed out; normal extraction will be used", error="timeout")
                return dict(self._direct_unpack_state_locked(cid))
            with self.lock:
                rar_jobs = self._direct_unpack_volume_jobs_locked(cid)
                all_rars_complete = bool(rar_jobs) and all(str(v.get("status") or "") == "completed" for v in rar_jobs)
            if all_rars_complete:
                if all_rars_complete_since is None:
                    all_rars_complete_since = now_mono
                elif now_mono - all_rars_complete_since > DIRECT_UNPACK_ALL_COMPLETE_GRACE_SECONDS:
                    event = self.direct_unpack_cancel_events.get(cid)
                    if event: event.set()
                    self._set_direct_unpack_state(cid, status="fallback", message="Direct Unpack did not finish after all RAR volumes completed; retrying with normal extraction", error="finalize_stalled")
                    return dict(self._direct_unpack_state_locked(cid))
            else:
                all_rars_complete_since = None
            progress = max(0, min(99, int(state.get("progress", 0) or 0)))
            message = str(state.get("message") or "Direct Unpack is finishing")
            ui_state = (progress, message)
            now = time.monotonic()
            if ui_state != last_ui_state or now - last_ui_update >= 2.0:
                self._set_post_state(targets, "extracting", max(45, progress), message)
                last_ui_state = ui_state
                last_ui_update = now
            self.direct_unpack_wake.wait(0.25)
            self.direct_unpack_wake.clear()

    def _discard_direct_unpack_output(self, collection_id: str) -> None:
        with self.lock:
            state = dict(self._direct_unpack_state_locked(collection_id))
        raw = str(state.get("output_dir") or "")
        if raw:
            try:
                shutil.rmtree(Path(raw), ignore_errors=True)
            except OSError:
                pass

    def _set_post_state(self, targets: list[dict[str, Any]], status: str, progress: int, message: str = "") -> None:
        with self.lock:
            for target in targets:
                target["post_status"] = status
                target["post_progress"] = max(0, min(100, int(progress)))
                target["post_message"] = str(message)[:1000]
            self._save()

    def _post_targets(self, job: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        collection_id = str(job.get("collection_id") or "")
        if collection_id:
            targets = [j for j in self.jobs if str(j.get("collection_id") or "") == collection_id]
            return "collection:" + collection_id, targets
        return "job:" + str(job.get("id") or ""), [job]

    def _automation_import(self, targets: list[dict[str,Any]], candidates: list[Path], staging_dir: Path | None = None) -> dict[str,Any] | None:
        if not targets:
            return None
        cid=str(targets[0].get('collection_id') or '')
        with self.lock:
            rec=self.collections.get(cid,{}) if cid else {}
            context=rec.get('automation_context') if isinstance(rec,dict) else {}
            if not isinstance(context,dict) or not context:
                context=next((j.get('automation_context') for j in targets if isinstance(j.get('automation_context'),dict) and j.get('automation_context')), {})
        if not isinstance(context,dict) or str(context.get('source') or '') not in {'automation_grab','manual_media_grab'}:
            return None
        last_progress_emit = [0.0, -1]
        def import_progress(percent: float, message: str = "") -> None:
            now = time.monotonic()
            value = max(0, min(100, int(percent or 0)))
            # Smart Import occupies the final 10% of the post-processing pipeline.
            post_value = max(90, min(99, 90 + int(round(value * 0.09))))
            if value >= 100:
                post_value = 99
            if value == last_progress_emit[1] and now - last_progress_emit[0] < 1.0:
                return
            last_progress_emit[:] = [now, value]
            self._set_post_state(targets, "importing", post_value, str(message or "Smart Import • organizing media"))
        result=None
        settle_attempts=0
        try:
            current_candidates=list(candidates or [])
            # SAB can mark a package complete a moment before the final media file is
            # observable by the service (especially after extraction/AV scanning).
            # Keep the package in Post-processing and rescan the owned staging folder
            # instead of turning a harmless settle window into NEEDS ATTENTION.
            for attempt in range(7):
                result=MEDIA_AUTOMATION.import_completed_download(context,[str(x) for x in current_candidates],staging_dir=str(staging_dir) if staging_dir else None,progress_callback=import_progress)
                if not (isinstance(result,dict) and result.get('retryable')):
                    break
                settle_attempts=attempt+1
                if attempt>=6:
                    break
                self._set_post_state(targets,'waiting',89,f"Smart Import • waiting for completed media to settle ({attempt+1}/6)")
                time.sleep(2.0)
                refreshed=[]
                if staging_dir:
                    try:
                        stage=Path(staging_dir)
                        refreshed=[x for x in stage.rglob('*') if x.is_file() and x.suffix.casefold() in {'.mkv','.mp4','.m4v','.avi','.mov','.wmv','.ts','.m2ts','.webm','.mpg','.mpeg'}]
                    except OSError:
                        refreshed=[]
                if refreshed:
                    current_candidates=refreshed
        except Exception as exc:
            DIAGNOSTICS.event('error','automation-import',str(exc),collection=cid)
            return {'ok':False,'reason':str(exc)}
        if isinstance(result,dict):
            if settle_attempts:
                result=dict(result); result['settle_attempts']=settle_attempts
            with self.lock:
                rec=self.collections.get(cid)
                if isinstance(rec,dict):
                    rec['automation_import']=dict(result)
                    rec['automation_import_ts']=time.time()
                    self._save()
            if result.get('ok'):
                DIAGNOSTICS.event('info','automation-import','Imported completed media into library',collection=cid,destination=str(result.get('destination') or ''))
        return result if isinstance(result,dict) else None

    def _after_download_completed(self, job: dict[str, Any]) -> None:
        settings = self._post_settings()
        with self.lock:
            live = self._find_job(str(job.get("id") or ""))
            if live is not job or job.get("cancel_requested"):
                return
        key, targets = self._post_targets(job)
        if not settings["enabled"]:
            self._set_post_state(targets if len(targets) == 1 else [job], "disabled", 100, "Post-processing disabled")
            return
        with self.lock:
            blocking_targets = [j for j in targets if nzb_job_blocks_collection(j)]
            expected_collection = max([int(j.get("collection_required_expected", 0) or 0) for j in targets] + [0]) or len(blocking_targets)
            terminal_bad = [j for j in blocking_targets if j.get("status") in {"failed", "cancelled"}]
            pending = [j for j in blocking_targets if j.get("status") in {"queued", "downloading", "retry_wait", "cancelling"}]
            if expected_collection and len(blocking_targets) < expected_collection:
                self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                self._save()
                return
            if terminal_bad:
                self._refresh_collection_post_state_locked(str(job.get("collection_id") or ""))
                self._save()
                return
            if pending or (len(blocking_targets) > 1 and any(j.get("status") != "completed" for j in blocking_targets)):
                direct_state = self._direct_unpack_state_locked(str(job.get("collection_id") or ""))
                direct_active = str(direct_state.get("status") or "") == "active"
                for target in targets:
                    if target.get("status") == "completed" and str(target.get("post_status") or "") not in {"completed", "not_needed", "needs_tool", "disabled"}:
                        if direct_active:
                            target["post_status"] = "extracting"
                            target["post_progress"] = max(1, min(99, int(direct_state.get("progress", 0) or 0)))
                            target["post_message"] = str(direct_state.get("message") or "Direct Unpacking while download continues")
                        else:
                            target["post_status"] = "waiting"
                            target["post_progress"] = 0
                            target["post_message"] = "Waiting for the rest of this package"
                self._save_hot(3.0)
                return
            if key in self.post_active:
                return
            if targets and all(str(j.get("post_status") or "") in {"completed", "not_needed", "needs_tool", "disabled"} for j in targets):
                return
            self.post_active.add(key)
            cancel_event = threading.Event()
            self.post_cancel_events[key] = cancel_event
            for target in targets:
                target["post_status"] = "queued"
                target["post_progress"] = 0
                target["post_message"] = "Queued for verification"
            self._save()
        future = self.post_executor.submit(self._run_post_processing, key, [str(j.get("id")) for j in targets], cancel_event)
        with self.lock:
            self.post_futures[key] = future
        def finished(_future):
            with self.lock:
                if self.post_futures.get(key) is _future:
                    self.post_active.discard(key)
                    self.post_futures.pop(key, None)
                    self.post_cancel_events.pop(key, None)
        future.add_done_callback(finished)

    def _run_post_processing(self, key: str, job_ids: list[str], cancel_event: threading.Event | None = None) -> None:
        with self.lock:
            targets = [j for j in self.jobs if str(j.get("id")) in job_ids]
        if not targets:
            return
        def set_state(status: str, progress: int, message: str = ""):
            with self.lock:
                if cancel_event is not None and self.post_cancel_events.get(key) is not cancel_event:
                    return
            self._set_post_state(targets, status, progress, message)
        def check_cancel():
            if self.shutdown_event.is_set() or (cancel_event is not None and cancel_event.is_set()):
                raise PostProcessingCancelled("Post-processing stopped by user")
        try:
            check_cancel()
            password = self.post_passwords.get(key, "")
            paths = [Path(str(j.get("path") or "")) for j in targets]
            paths = [p for p in paths if p.exists() and p.is_file()]
            if not paths:
                set_state("failed", 0, "Downloaded files are no longer available for post-processing")
                return
            settings = self._post_settings()
            collection_id = str(targets[0].get("collection_id") or "")
            direct_state = self._wait_for_direct_unpack(collection_id, targets, cancel_event) if collection_id else {}

            paths = [Path(str(j.get("path") or "")) for j in targets]
            paths = [p for p in paths if p.exists() and p.is_file()]
            if not paths:
                set_state("failed", 0, "Downloaded files are no longer available for post-processing")
                return
            archives = [p for p in paths if _archive_kind(p)]
            par2_files = sorted([p for p in paths if p.name.casefold().endswith('.par2')], key=lambda p: ('.vol' in p.name.casefold(), len(p.name)))
            parent = Path(os.path.commonpath([str(p.parent) for p in paths]))
            if not archives and not par2_files:
                imported=self._automation_import(targets,paths,parent)
                if imported and imported.get("ok"):
                    destination=str(imported.get('destination') or '')
                    self._cleanup_automation_staging(collection_id, targets, parent, destination)

                    if imported.get('season_pack'):
                        count=int(imported.get('imported_count') or 0); kept=int(imported.get('kept_existing') or 0)
                        message=f"Smart Import complete • {count} episode{'s' if count!=1 else ''} imported" + (f" • {kept} existing kept" if kept else '')
                        set_state("completed",100,message)
                    else:
                        set_state("completed", 100, f"Smart Import complete • {destination}")
                elif imported and (imported.get("needs_root") or imported.get("needs_attention") or (imported.get("reason") and not imported.get("skipped"))):
                    set_state("needs_attention", 100, f"Download preserved • Import needs attention: {imported.get('reason')}")
                else:
                    set_state("not_needed", 100, "No repair or extraction required")
                return

            set_state("verifying", 15, "Verifying downloaded files")
            check_cancel()

            for archive in archives:
                check_cancel()
                if _archive_kind(archive) == 'zip':
                    try:
                        with zipfile.ZipFile(archive, 'r') as zf:
                            infos = zf.infolist()
                            encrypted = any(bool(i.flag_bits & 0x1) for i in infos)
                            if encrypted and not password:
                                raise NntpError("ARCHIVE_PASSWORD_REQUIRED")
                            pwd = password.encode("utf-8") if password else None
                            for info in infos:
                                check_cancel()
                                if info.is_dir():
                                    continue
                                try:
                                    with zf.open(info, 'r', pwd=pwd) as src:
                                        while True:
                                            check_cancel()
                                            chunk = src.read(1024 * 1024)
                                            if not chunk:
                                                break
                                except zipfile.BadZipFile as exc:
                                    raise NntpError(f"ZIP integrity check failed at {info.filename}") from exc
                    except RuntimeError as exc:
                        if 'password' in str(exc).casefold() or 'encrypted' in str(exc).casefold():
                            raise NntpError("ARCHIVE_PASSWORD_REQUIRED") from exc
                        raise
                    except zipfile.BadZipFile as exc:
                        raise NntpError(f"ZIP integrity check failed: {archive.name}") from exc

            repair_note = ""
            optional_missing_targets = [j for j in targets if not nzb_job_blocks_collection(j) and bool(j.get("optional_missing"))]
            required_repair_targets = [j for j in targets if nzb_job_blocks_collection(j) and str(j.get("integrity_status") or "") == "repair_needed"]
            if par2_files and optional_missing_targets and not required_repair_targets:



                repair_note = f"Payload complete • {len(optional_missing_targets)} optional sidecar{'s' if len(optional_missing_targets) != 1 else ''} skipped • PAR2 repair not needed"
                DIAGNOSTICS.event("info", "par2", "Skipped PAR2 repair for optional-only missing sidecar", target=key, optional=len(optional_missing_targets))
            elif par2_files:
                par2 = _par2_path() or _ensure_managed_par2_tool()
                base = next((p for p in par2_files if '.vol' not in p.name.casefold()), par2_files[0])
                if par2:
                    verify = _run_post_tool([par2, 'v', str(base)], parent, cancel_event=cancel_event)
                    if verify.returncode != 0:
                        if settings["repair"]:
                            set_state("repairing", 35, f"Repairing with {Path(par2).name}")
                            repair = _run_post_tool([par2, 'r', str(base)], parent, cancel_event=cancel_event)
                            if repair.returncode != 0:
                                detail = (repair.stderr or repair.stdout or '').strip()[-1200:]
                                collection_id = str(targets[0].get("collection_id") or "")
                                extra_match = re.search(r'(?i)(?:need|needs|require|requires|missing)[^0-9]{0,30}(\d+)\s+(?:more\s+)?(?:recovery\s+)?blocks?', detail)
                                extra_blocks = max(1, int(extra_match.group(1))) if extra_match else 1
                                if collection_id:
                                    plan = self._queue_recovery_for_collection(collection_id, minimum_blocks=extra_blocks)
                                    if plan.get("queued"):
                                        set_state("waiting", 35, f"PAR2 needs more recovery data • queued {len(plan['queued'])} additional volume{'s' if len(plan['queued']) != 1 else ''}")
                                        DIAGNOSTICS.event("info", "par2", "Queued additional recovery data after repair check", collection=collection_id, blocks=plan.get("blocks", 0))
                                        return
                                raise NntpError(f"PAR2 repair failed{': ' + detail if detail else ''}")
                            repair_note = "PAR2 repair completed"
                            if str(direct_state.get("status") or "") == "completed":
                                self._discard_direct_unpack_output(collection_id)
                                direct_state = self._set_direct_unpack_state(collection_id, status="fallback", message="PAR2 repaired the archive; using a fresh normal extraction", error="repaired_after_direct_unpack")
                            with self.lock:
                                for target in targets:
                                    if str(target.get("integrity_status") or "") == "repair_needed":
                                        target["integrity_status"] = "healthy"
                                        target["repair_missing_bytes"] = 0
                                        target["repair_missing_blocks"] = 0
                                        target["failed_parts"] = 0
                                        target["missing_bytes"] = 0
                                        target["segment_errors"] = []
                                        target["error"] = ""
                                        target["error_code"] = ""
                                        target["error_label"] = ""
                                        target["error_suggestion"] = ""
                                self._save()
                        else:
                            raise NntpError("PAR2 verification found damage and automatic repair is disabled")
                    else:
                        repair_note = "PAR2 verification passed"
                        with self.lock:
                            for target in targets:
                                if str(target.get("integrity_status") or "") == "repair_needed":
                                    target["integrity_status"] = "healthy"
                                    target["repair_missing_bytes"] = 0
                                    target["repair_missing_blocks"] = 0
                                    target["failed_parts"] = 0
                                    target["missing_bytes"] = 0
                                    target["segment_errors"] = []
                                    target["error"] = ""
                                    target["error_code"] = ""
                                    target["error_label"] = ""
                                    target["error_suggestion"] = ""
                            self._save()
                else:
                    repair_note = "PAR2 files present; install par2cmdline beside NewzDeck.exe to enable verification/repair"

            if not settings["extract"] or not archives:
                message = repair_note or ("Archive verification passed" if archives else "Verification complete")
                imported=self._automation_import(targets,paths,parent) if not archives else None
                if imported and imported.get("ok"):
                    destination=str(imported.get('destination') or '')
                    message=(message+" • " if message else "")+f"Plex-ready import → {destination}"
                    cleaned=self._cleanup_automation_staging(collection_id, targets, parent, destination)
                    if not cleaned and settings.get("cleanup"):
                        for p in paths:
                            if p.exists() and (p.suffix.casefold()=='.par2' or nzb_auxiliary_file(p.name)):
                                try: p.unlink(missing_ok=True)
                                except OSError: pass
                elif imported and (imported.get("needs_root") or imported.get("needs_attention") or (imported.get("reason") and not imported.get("skipped"))):
                    set_state("needs_attention",100,f"Download preserved • Import needs attention: {imported.get('reason')}")
                    return
                set_state("completed", 100, message)
                self.post_passwords.pop(key, None)
                return

            raw_collection_name = str(targets[0].get("collection_name") or "").strip()
            collection_name = safe_folder_name(raw_collection_name) if raw_collection_name else ""
            if settings["subfolder"]:
                if collection_name:
                    output_dir = parent / "Extracted"
                elif len(archives) == 1:
                    output_dir = parent / safe_folder_name(archives[0].stem)
                else:
                    output_dir = parent / "Extracted"
            else:
                output_dir = parent
            sevenzip = _sevenzip_path()
            unrar = _unrar_path()
            extracted_any = False
            direct_used = False
            if str(direct_state.get("status") or "") == "completed":
                direct_dir = Path(str(direct_state.get("output_dir") or ""))
                if direct_dir.is_dir():
                    set_state("extracting", 90, "Finalizing Direct Unpack output")
                    if settings["subfolder"]:
                        if output_dir.exists() and output_dir != direct_dir:
                            shutil.rmtree(output_dir, ignore_errors=True)
                        if output_dir != direct_dir:
                            direct_dir.replace(output_dir)
                    else:
                        output_dir = parent
                        for child in list(direct_dir.iterdir()):
                            check_cancel()
                            target = parent / child.name
                            if target.exists():
                                if target.is_dir(): shutil.rmtree(target, ignore_errors=True)
                                else: target.unlink(missing_ok=True)
                            child.replace(target)
                        direct_dir.rmdir()
                    extracted_any = True
                    direct_used = True
                    set_state("importing", 90, "Direct Unpack complete • preparing Smart Import")
                else:
                    direct_state = self._set_direct_unpack_state(collection_id, status="fallback", message="Direct Unpack output was unavailable; using normal extraction", error="output_missing")
            if not direct_used:
                self._discard_direct_unpack_output(collection_id)
                output_dir.mkdir(parents=True, exist_ok=True)
                total_archives = max(1, len(archives))
                for index, archive in enumerate(archives, start=1):
                    check_cancel()
                    kind = _archive_kind(archive)
                    progress = 45 + int(45 * ((index - 1) / total_archives))
                    set_state("extracting", progress, f"Extracting {archive.name}")
                    if kind == 'zip':
                        _safe_extract_zip(archive, output_dir, password, cancel_event=cancel_event)
                        extracted_any = True
                    elif kind == 'rar':
                        rar_tool = unrar or _ensure_managed_unrar_tool() or _unrar_path()
                        if rar_tool:
                            args = [rar_tool, 'x', '-idp', '-o+', '-ai', f'-p{password}' if password else '-p-', str(archive), str(output_dir) + os.sep]
                        elif sevenzip:
                            args = [sevenzip, 'x', '-y', f'-o{output_dir}', f'-p{password}' if password else '-p', str(archive)]
                        else:
                            set_state("needs_tool", 100, f"{archive.name} needs UnRAR or 7-Zip. NewzDeck will retry managed UnRAR automatically.")
                            return
                        proc = _run_post_tool(args, parent, cancel_event=cancel_event)
                        if proc.returncode != 0:
                            detail = (proc.stderr or proc.stdout or '').strip()[-1200:]
                            folded = detail.casefold()
                            if any(x in folded for x in ('wrong password', 'enter password', 'password is incorrect', 'encrypted file')):
                                raise NntpError("ARCHIVE_PASSWORD_REQUIRED")
                            raise NntpError(f"Archive extraction failed for {archive.name}{': ' + detail if detail else ''}")
                        extracted_any = True
                    elif kind == '7z':
                        if not sevenzip:
                            set_state("needs_tool", 100, f"{archive.name} needs 7-Zip. Put 7z.exe beside NewzDeck.exe or install 7-Zip.")
                            return
                        args = [sevenzip, 'x', '-y', f'-o{output_dir}', f'-p{password}' if password else '-p', str(archive)]
                        proc = _run_post_tool(args, parent, cancel_event=cancel_event)
                        if proc.returncode != 0:
                            detail = (proc.stderr or proc.stdout or '').strip()[-1200:]
                            folded = detail.casefold()
                            if any(x in folded for x in ('wrong password', 'enter password', 'password is incorrect', 'encrypted file')):
                                raise NntpError("ARCHIVE_PASSWORD_REQUIRED")
                            raise NntpError(f"Archive extraction failed for {archive.name}{': ' + detail if detail else ''}")
                        extracted_any = True

            check_cancel()
            imported=None
            if extracted_any:
                try:
                    import_candidates=[x for x in output_dir.rglob('*') if x.is_file() and x.suffix.casefold() in {'.mkv','.mp4','.m4v','.avi','.mov','.wmv','.ts','.m2ts','.webm','.mpg','.mpeg'}]
                except OSError:
                    import_candidates=[]
                imported=self._automation_import(targets,import_candidates,output_dir)
            automation_cleaned = False
            if imported and imported.get("ok"):
                automation_cleaned = self._cleanup_automation_staging(collection_id, targets, parent, str(imported.get('destination') or ''))
            elif imported and (imported.get("needs_root") or imported.get("needs_attention") or (imported.get("reason") and not imported.get("skipped"))):
                set_state("needs_attention",100,f"Download and extraction preserved • Import needs attention: {imported.get('reason')}")
                DIAGNOSTICS.event("warning","automation-import","Import needs attention; source package preserved",collection=collection_id,reason=str(imported.get('reason') or ''))
                return
            if settings["cleanup"] and extracted_any and not automation_cleaned:
                for path in paths:
                    check_cancel()
                    name = path.name.casefold()
                    is_volume = bool(_archive_kind(path) or re.search(r'\.r\d{2,3}$', name) or re.search(r'\.7z\.\d{3}$', name) or name.endswith('.par2'))
                    if is_volume:
                        try:
                            path.unlink(missing_ok=True)
                        except OSError:
                            pass
            msg = f"Extracted to {output_dir}"
            if direct_used:
                msg = f"Direct Unpack complete → {output_dir}"
            if imported and imported.get("ok"):
                if imported.get('season_pack'):
                    count=int(imported.get('imported_count') or 0)
                    kept=int(imported.get('kept_existing') or 0)
                    msg=f"Season-pack import complete → {count} episode{'s' if count!=1 else ''} imported" + (f" • {kept} existing kept" if kept else '')
                    if automation_cleaned: msg += " • source archives cleaned"
                else:
                    msg = f"Smart Import → {imported.get('destination')} • source archives cleaned" if automation_cleaned else f"Smart Import → {imported.get('destination')}"
            elif imported and imported.get("reason") and not imported.get("skipped"):
                msg += f" • Smart Import: {imported.get('reason')}"
            if repair_note:
                msg = repair_note + " • " + msg
            set_state("completed", 100, msg)
            self.post_passwords.pop(key, None)
            DIAGNOSTICS.event("info", "postprocess", "Post-processing completed", target=key, output=str(output_dir))
        except PostProcessingCancelled:
            set_state("cancelled", 0, "Post-processing stopped by user")
            return
        except Exception as exc:
            if str(exc) == "ARCHIVE_PASSWORD_REQUIRED":
                set_state("needs_password", 100, "Archive password required. Choose Enter password to continue extraction.")
                DIAGNOSTICS.event("warning", "postprocess", "Archive password required", target=key)
            else:
                set_state("failed", 100, str(exc))
                DIAGNOSTICS.event("error", "postprocess", str(exc), target=key)

    def retry_automation_import(self, collection_id:str) -> dict[str,Any]:
        """Retry processing/import for an already-downloaded Automation package.

        This never re-downloads the NZB. Source archives/extracted files are kept when
        an import enters NEEDS ATTENTION so the user can correct a Root Folder or disk
        condition and resume safely.
        """
        cid=str(collection_id or '').strip()
        if not cid: raise ValueError('A download package is required')
        with self.lock:
            targets=[j for j in self.jobs if str(j.get('collection_id') or '')==cid]
            if not targets: raise ValueError('Download package was not found')
            context=next((j.get('automation_context') for j in targets if isinstance(j.get('automation_context'),dict) and j.get('automation_context')),None)
            if not isinstance(context,dict) or str(context.get('source') or '') not in {'automation_grab','manual_media_grab'}: raise ValueError('This package is not a Smart Import media download')
            if any(str(j.get('status') or '')!='completed' for j in targets if nzb_job_blocks_collection(j)):
                raise ValueError('The package download is not complete yet')
            for target in targets:
                target['post_status']=''; target['post_progress']=0; target['post_message']='Retrying preserved Smart Import'
            rec=self.collections.get(cid)
            if isinstance(rec,dict):
                rec['automation_import_retry_ts']=time.time(); rec.pop('automation_import',None)
            self._save()
        self._after_download_completed(targets[0])
        return {'ok':True,'started':True,'collection_id':cid,'message':'Retrying Smart Import from the preserved files'}

    def _resume_post_processing(self) -> None:
        seen: set[str] = set()
        with self.lock:
            candidates = [j for j in self.jobs if j.get("status") == "completed" and str(j.get("post_status") or "") not in {"completed", "not_needed", "needs_tool", "needs_attention", "disabled", "blocked", "cancelled"}]
        for job in candidates:
            key = str(job.get("collection_id") or job.get("id") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            self._after_download_completed(job)

    def stop(self):
        self.shutdown_event.set()
        self.wake.set()
        with self.lock:
            for event in self.post_cancel_events.values():
                event.set()
            for event in self.direct_unpack_cancel_events.values():
                event.set()
        self.direct_unpack_wake.set()
        try:
            self.job_executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            self.job_executor.shutdown(wait=False)
        try:
            self.post_executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            self.post_executor.shutdown(wait=False)
        try:
            self.direct_unpack_executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            self.direct_unpack_executor.shutdown(wait=False)
        shutdown_download_pools()

def preview_error_info(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, BrowseSessionCancelled):
        return {'error': str(exc), 'error_code': 'browse_cancelled', 'error_label': 'Browsing request cancelled', 'retryable': False}
    text = str(exc)
    low = text.lower()
    if 'unavailable' in low or '430' in low or '423' in low or 'no such article' in low:
        return {'error': text, 'error_code': 'article_missing', 'error_label': 'Article missing', 'retryable': False}
    if 'incomplete' in low or 'parts' in low and 'missing' in low:
        return {'error': text, 'error_code': 'multipart_incomplete', 'error_label': 'Multipart post incomplete', 'retryable': False}
    if 'timed out' in low or 'timeout' in low or 'connection' in low or 'ssl' in low:
        return {'error': text, 'error_code': 'provider_temporary', 'error_label': 'Provider connection issue', 'retryable': True}
    if 'supported binary' in low or 'decode' in low or 'encoding' in low:
        return {'error': text, 'error_code': 'decode_failed', 'error_label': 'Unsupported or corrupt encoding', 'retryable': False}
    return {'error': text, 'error_code': 'preview_failed', 'error_label': 'Preview unavailable', 'retryable': True}

def safe_download_name(filename: str) -> str:
    name = re.sub(r'[\x00-\x1f<>:"/\\|?*]+', '_', str(filename)).strip(' .')
    if not name:
        return 'download.bin'
    stem = name.split('.', 1)[0].casefold()
    if stem in {'con','prn','aux','nul'} or re.fullmatch(r'(?:com|lpt)[1-9]', stem):
        name = '_' + name
    return name[:220].rstrip(' .') or 'download.bin'

def safe_folder_name(value: str) -> str:
    name = re.sub(r'[^A-Za-z0-9._ ()\[\]-]+', '_', str(value)).strip(' .')
    return name[:120] or 'Usenet'

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while True:
            chunk = f.read(4 * 1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open('rb') as f:
            head = f.read(32)
            if head.startswith(b'\x89PNG\r\n\x1a\n') and len(head) >= 24:
                return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')
            if head.startswith((b'GIF87a', b'GIF89a')) and len(head) >= 10:
                return int.from_bytes(head[6:8], 'little'), int.from_bytes(head[8:10], 'little')
            if head[:2] == b'BM' and len(head) >= 26:
                return abs(int.from_bytes(head[18:22], 'little', signed=True)), abs(int.from_bytes(head[22:26], 'little', signed=True))
            if head[:2] == b'\xff\xd8':
                f.seek(2)
                while True:
                    b = f.read(1)
                    if not b:
                        break
                    if b != b'\xff':
                        continue
                    marker_byte = f.read(1)
                    while marker_byte == b'\xff':
                        marker_byte = f.read(1)
                    if not marker_byte or marker_byte in {b'\xd8', b'\xd9'}:
                        continue
                    raw_len = f.read(2)
                    if len(raw_len) != 2:
                        break
                    seg_len = int.from_bytes(raw_len, 'big')
                    if marker_byte[0] in {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}:
                        data = f.read(5)
                        if len(data) >= 5:
                            return int.from_bytes(data[3:5], 'big'), int.from_bytes(data[1:3], 'big')
                        break
                    f.seek(max(0, seg_len - 2), 1)
    except OSError:
        return None
    return None

def video_metadata(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        ffmpeg = _ffmpeg_path()
        if ffmpeg:
            candidate = Path(ffmpeg).with_name("ffprobe.exe" if sys.platform == "win32" else "ffprobe")
            if candidate.exists():
                ffprobe = str(candidate)
    if not ffprobe:
        return {}
    try:
        proc = subprocess.run([
            ffprobe, "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name,avg_frame_rate:format=duration",
            "-of", "json", str(path)
        ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=12, check=False)
        data = json.loads(proc.stdout or "{}")
        stream = (data.get("streams") or [{}])[0]
        fmt = data.get("format") or {}
        fps = 0.0
        rate = str(stream.get("avg_frame_rate") or "")
        if "/" in rate:
            a,b = rate.split("/",1)
            try:
                fps = float(a) / float(b) if float(b) else 0.0
            except (ValueError, ZeroDivisionError):
                fps = 0.0
        return {
            "width": int(stream.get("width") or 0), "height": int(stream.get("height") or 0),
            "codec": str(stream.get("codec_name") or ""), "duration": float(fmt.get("duration") or 0),
            "frame_rate": round(fps, 3) if fps else 0,
        }
    except Exception:
        return {}

def unique_download_path(filename: str) -> Path:
    base = DOWNLOAD_DIR / safe_download_name(filename)
    if not base.exists():
        return base
    stem, suffix = base.stem, base.suffix
    n = 2
    while True:
        candidate = DOWNLOAD_DIR / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1

class AutomationManager:
    def __init__(self):
        self.lock = threading.RLock(); self.stop = threading.Event(); self.file_state: dict[str, tuple[int,float,int]] = {}; self.completed_seen: set[str] = set()
        self.watch_imported = 0; self.watch_failed = 0; self.last_watch_message = ''; self.last_watch_ts = 0.0; self.last_media_auto_check = 0.0
        self.watch_scan_cursor = 0
        self.last_media_notification_ts = time.time()
        self.thread = threading.Thread(target=self._loop, name='newzdeck-automation', daemon=True)
        self._started = False
    def start(self):
        if self._started:
            return
        self._started = True
        try:
            self.completed_seen = {str(x.get('id') or '') for x in DOWNLOAD_MANAGER.snapshot().get('collections', []) if x.get('status') == 'completed' and x.get('id')}
        except Exception:
            self.completed_seen = set()
        self.thread.start()
    def snapshot(self) -> dict[str, Any]:
        settings = json_read(SETTINGS_FILE, {}); settings = settings if isinstance(settings, dict) else {}; bw = DOWNLOAD_BANDWIDTH_LIMITER.current()
        with self.lock:
            return {'watch_enabled':bool(settings.get('watch_folder_enabled',False)), 'watch_folder':str(settings.get('watch_folder') or DEFAULT_WATCH_FOLDER), 'watch_imported':self.watch_imported, 'watch_failed':self.watch_failed, 'last_watch_message':self.last_watch_message, 'last_watch_ts':self.last_watch_ts, 'bandwidth':bw}
    def _provider_id(self, settings: dict[str, Any]) -> str:
        wanted = str(settings.get('watch_provider_id') or '')
        if wanted:
            try:
                p=provider_by_id(wanted)
                if provider_enabled_for(p,'downloads'): return wanted
            except Exception: pass
        candidates = providers_for_purpose('downloads')
        return str(candidates[0].get('id') or '') if candidates else ''
    def _watch_once(self):
        settings = json_read(SETTINGS_FILE, {}); settings = settings if isinstance(settings, dict) else {}
        if not bool(settings.get('watch_folder_enabled',False)): return
        folder = Path(str(settings.get('watch_folder') or DEFAULT_WATCH_FOLDER)).expanduser(); folder.mkdir(parents=True, exist_ok=True)
        provider_id = self._provider_id(settings)
        if not provider_id: return
        all_paths = sorted(folder.glob('*.nzb'))
        entries = [(path, str(path.resolve()).casefold()) for path in all_paths]
        live = {key for _, key in entries}
        if entries:
            start = self.watch_scan_cursor % len(entries)
            scan = (entries[start:] + entries[:start])[:100]
            self.watch_scan_cursor = (start + len(scan)) % len(entries)
        else:
            scan = []
            self.watch_scan_cursor = 0
        for path, key in scan:
            try: st=path.stat()
            except OSError: continue
            prior=self.file_state.get(key); stable=(prior is not None and prior[0]==st.st_size and abs(prior[1]-st.st_mtime)<0.001)
            self.file_state[key]=(st.st_size,st.st_mtime,(prior[2]+1 if stable else 0) if prior else 0)
            if not stable or self.file_state[key][2] < 1: continue
            try:
                raw=path.read_bytes()
                if not raw or len(raw)>100*1024*1024: raise ValueError('NZB must be between 1 byte and 100 MB')
                parsed=parse_nzb_bytes(raw,path.name); parsed['source_name']=path.name; parsed['automation_source']='watch_folder'
                selected=recommended_nzb_indices(parsed)
                if not selected: raise ValueError('No recommended payload files were found in the NZB')
                result=DOWNLOAD_MANAGER.add_nzb_selection(provider_id,parsed,selected,str(parsed.get('name') or path.stem))
                processed=folder/'Processed'; processed.mkdir(exist_ok=True)
                target=processed/path.name; n=2
                while target.exists(): target=processed/f'{path.stem} ({n}){path.suffix}'; n+=1
                if bool(settings.get('watch_archive_processed',DEFAULT_WATCH_ARCHIVE_PROCESSED)): shutil.move(str(path),str(target))
                else: path.unlink(missing_ok=True)
                with self.lock: self.watch_imported+=1; self.last_watch_message=f"Imported {path.name} ({len(result.get('added') or [])} files)"; self.last_watch_ts=time.time()
                DIAGNOSTICS.event('info','watch-folder',self.last_watch_message,source=str(path)); self.file_state.pop(key,None)
            except (PermissionError, OSError) as exc:
                with self.lock: self.last_watch_message=f"Waiting for {path.name}: {exc}"; self.last_watch_ts=time.time()
                continue
            except Exception as exc:
                failed=folder/'Failed'; failed.mkdir(exist_ok=True)
                try:
                    target=failed/path.name
                    if target.exists(): target=failed/f'{path.stem}-{int(time.time())}{path.suffix}'
                    shutil.move(str(path),str(target)); target.with_suffix(target.suffix+'.error.txt').write_text(str(exc),encoding='utf-8')
                except Exception: pass
                with self.lock: self.watch_failed+=1; self.last_watch_message=f"Failed to import {path.name}: {exc}"; self.last_watch_ts=time.time()
                DIAGNOSTICS.event('error','watch-folder',self.last_watch_message); self.file_state.pop(key,None)
        for key in list(self.file_state):
            if key not in live: self.file_state.pop(key,None)
    def _notify_completion(self, name: str, folder: str, settings: dict[str, Any]):
        if sys.platform != 'win32':
            return
        text = str(name or 'NZB package completed')[:180]
        if bool(settings.get('completion_notification', False)):
            if SERVICE_MODE:
                try: tray_helper_request('notify', title='NewzDeck', text=text, timeout=3)
                except Exception: pass
            else:
                safe_text = text.replace("'", "''")
                ps=f"Add-Type -AssemblyName System.Windows.Forms;Add-Type -AssemblyName System.Drawing;$n=New-Object System.Windows.Forms.NotifyIcon;$n.Icon=[System.Drawing.SystemIcons]::Information;$n.BalloonTipTitle='NewzDeck';$n.BalloonTipText='{safe_text}';$n.Visible=$true;$n.ShowBalloonTip(5000);Start-Sleep -Seconds 5;$n.Dispose()"
                try: subprocess.Popen(['powershell.exe','-NoProfile','-STA','-ExecutionPolicy','Bypass','-Command',ps],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                except Exception: pass
        if bool(settings.get('completion_open_folder', False)) and folder:
            if SERVICE_MODE:
                try: tray_helper_request('open_path', path=str(folder), timeout=3)
                except Exception: pass
            else:
                try: os.startfile(str(folder))
                except Exception: pass
    def _automation_notify_balloon(self, title: str, text: str) -> None:
        if sys.platform != 'win32': return
        title=str(title or 'NewzDeck Automation')[:80]; text=str(text or 'Automation event')[:220]
        if SERVICE_MODE:
            try: tray_helper_request('notify', title=title, text=text, timeout=3)
            except Exception: pass
            return
        safe_title=title.replace("'", "''"); safe_text=text.replace("'", "''")
        ps=f"Add-Type -AssemblyName System.Windows.Forms;Add-Type -AssemblyName System.Drawing;$n=New-Object System.Windows.Forms.NotifyIcon;$n.Icon=[System.Drawing.SystemIcons]::Information;$n.BalloonTipTitle='{safe_title}';$n.BalloonTipText='{safe_text}';$n.Visible=$true;$n.ShowBalloonTip(5000);Start-Sleep -Seconds 5;$n.Dispose()"
        try: subprocess.Popen(['powershell.exe','-NoProfile','-STA','-ExecutionPolicy','Bypass','-Command',ps],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except Exception: pass

    def _media_notifications_once(self):
        try: cfg=MEDIA_AUTOMATION.public_config()
        except Exception: return
        if not bool(cfg.get('automatic_notifications_enabled',False)):
            self.last_media_notification_ts=time.time(); return
        try: rows=MEDIA_AUTOMATION.history(limit=80)
        except Exception: return
        fresh=[r for r in rows if isinstance(r,dict) and float(r.get('ts') or 0)>self.last_media_notification_ts]
        if not fresh: return
        max_ts=self.last_media_notification_ts; sent=0
        labels={'auto-grab':'Release grabbed','import':'Media imported','upgrade-import':'Quality upgrade imported','release-blacklisted':'Release failed','auto-error':'Automation needs attention','import-inspection':'Import needs attention'}
        for rec in reversed(fresh):
            ts=float(rec.get('ts') or 0); max_ts=max(max_ts,ts); kind=str(rec.get('kind') or '')
            if kind not in labels: continue
            details=rec.get('details') if isinstance(rec.get('details'),dict) else {}
            if kind=='import-inspection' and not int(details.get('needs_attention') or 0): continue
            self._automation_notify_balloon('NewzDeck Automation • '+labels[kind],str(rec.get('message') or labels[kind]))
            sent+=1
            if sent>=4: break
        self.last_media_notification_ts=max_ts

    def _completion_once(self):
        settings=json_read(SETTINGS_FILE, {}); settings=settings if isinstance(settings,dict) else {}
        if not (settings.get('completion_notification') or settings.get('completion_open_folder')): return
        snap=DOWNLOAD_MANAGER.snapshot()
        for pkg in snap.get('collections') or []:
            cid=str(pkg.get('id') or '')
            if pkg.get('status')=='completed' and cid and cid not in self.completed_seen:
                self.completed_seen.add(cid); self._notify_completion(str(pkg.get('name') or 'NZB package'),str(pkg.get('folder') or ''),settings)
        live={str(x.get('id') or '') for x in snap.get('collections') or []}; self.completed_seen.intersection_update(live)
    def _loop(self):
        while not self.stop.wait(2.0):
            try: self._watch_once()
            except Exception as exc: DIAGNOSTICS.event('warning','automation',f'Watch-folder check failed: {exc}')
            try: self._completion_once()
            except Exception as exc: DIAGNOSTICS.event('warning','automation',f'Completion action failed: {exc}')
            try: self._media_notifications_once()
            except Exception as exc: DIAGNOSTICS.event('warning','media-automation',f'Automation notification check failed: {exc}')
            if time.time()-self.last_media_auto_check >= 5.0:
                self.last_media_auto_check=time.time()
                try: MEDIA_AUTOMATION.maybe_reconcile_library()
                except Exception as exc: DIAGNOSTICS.event('warning','media-automation',f'Library reconciliation failed to start: {exc}')
                try: MEDIA_AUTOMATION.maybe_run_automatic()
                except Exception as exc: DIAGNOSTICS.event('warning','media-automation',f'Automatic media check failed to start: {exc}')

# Download Engine v2. SABnzbd owns NNTP/yEnc/PAR2/unpack; NewzDeck keeps the
# visible queue, provider settings, Automation context and final library import.
# The legacy engine remains in this source tree only as an explicit diagnostic fallback.
def _download_settings_snapshot() -> dict[str, Any]:
    value = json_read(SETTINGS_FILE, {})
    return value if isinstance(value, dict) else {}

def _download_dir_snapshot() -> Path:
    return DOWNLOAD_DIR

if str(os.environ.get("NEWZDECK_DOWNLOAD_ENGINE", "sab") or "sab").strip().casefold() == "legacy":
    DOWNLOAD_MANAGER = DownloadManager()
else:
    def _launch_private_sab_in_user_session(exe: Path, args: list[str], cwd: Path, log_path: Path) -> dict[str, Any]:
        """Launch private SAB through the signed-in tray when the backend is a Windows service.

        SABnzbd's frozen Windows executable treats every Session-0 process as a
        Windows service and calls StartServiceCtrlDispatcher().  NewzDeck's own
        background service therefore must not spawn SAB directly from Session 0.
        The tray helper is already a single-instance signed-in-user companion, so
        it is the correct broker for this narrowly restricted process launch.
        """
        return tray_helper_request(
            'launch_private_sab',
            path=str(exe),
            args=[str(x) for x in args],
            working_dir=str(cwd),
            log_path=str(log_path),
            timeout=8.0,
        )

    # CPython's Windows embeddable runtime uses python312._pth/isolated mode.
    # In that mode the directory containing server.py is not guaranteed to be on
    # sys.path, so a normal sibling import can fail before /api/health starts.
    # Load the adapter explicitly from APP_DIR so installed and portable launches
    # behave identically regardless of Python path isolation.
    _sab_module_path = APP_DIR / "sab_engine.py"
    try:
        _sab_module = _load_app_source_module("newzdeck_sab_engine", _sab_module_path)
    except Exception as exc:
        raise RuntimeError(f"Unable to load built-in download engine adapter from current source: {_sab_module_path}: {exc}") from exc
    SabDownloadManager = _sab_module.SabDownloadManager
    DOWNLOAD_MANAGER = SabDownloadManager(
        user_root=USER_ROOT, app_dir=APP_DIR, download_dir_getter=_download_dir_snapshot,
        settings_getter=_download_settings_snapshot, providers_getter=get_providers,
        secret_unprotect=unprotect_secret, parse_nzb=parse_nzb_bytes, diagnostics=DIAGNOSTICS,
        legacy_statistics_file=DOWNLOADS_FILE,
        keep_engine_running=lambda: bool(SERVICE_MODE or service_status_snapshot().get("service_ready")),
        process_launcher=_launch_private_sab_in_user_session,
        start_threads=False,
    )

# Legacy post-processing tools are prewarmed only when the diagnostic legacy
# downloader is explicitly selected. Download Engine v2 delegates repair/unpack
# to SABnzbd and therefore avoids these extra startup downloads.
if isinstance(DOWNLOAD_MANAGER, DownloadManager):
    threading.Thread(target=_prewarm_par2_tool, name="newzdeck-par2-prewarm", daemon=True).start()
    threading.Thread(target=_prewarm_unrar_tool, name="newzdeck-unrar-prewarm", daemon=True).start()

class _LazyMediaAutomation:
    """Lazy media automation; never block core backend startup."""
    def __init__(self):
        self._lock = threading.RLock()
        self._engine = None
        self._last_error = ''
        self._last_attempt = 0.0

    def _write_failure(self, exc: Exception) -> None:
        self._last_error = f"{type(exc).__name__}: {exc}"
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with (DATA_DIR / 'automation-startup.log').open('a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat(timespec='seconds')} {self._last_error}\n")
                f.write(traceback.format_exc() + '\n')
        except Exception:
            pass
        try:
            DIAGNOSTICS.event('error', 'media-automation', 'Automation engine initialization failed', error=self._last_error)
        except Exception:
            pass

    def _get(self):
        if self._engine is not None:
            return self._engine
        with self._lock:
            if self._engine is not None:
                return self._engine
            now = time.monotonic()
            if self._last_error and now - self._last_attempt < 2.0:
                raise RuntimeError('Media Automation is still initializing. ' + self._last_error)
            self._last_attempt = now
            try:
                module_path = APP_DIR / 'automation_engine.py'
                if not module_path.is_file():
                    raise FileNotFoundError(f'Automation engine module is missing: {module_path}')
                module = _load_app_source_module('newzdeck_automation_engine', module_path)
                MediaAutomationEngine = module.MediaAutomationEngine
                self._engine = MediaAutomationEngine(
                    DATA_DIR, protect_secret, unprotect_secret, DOWNLOAD_MANAGER, get_providers, APP_VERSION
                )
                self._last_error = ''
                return self._engine
            except Exception as exc:
                self._write_failure(exc)
                raise RuntimeError('Media Automation could not initialize: ' + self._last_error) from exc

    def __getattr__(self, name):
        return getattr(self._get(), name)

MEDIA_AUTOMATION = _LazyMediaAutomation()
try:
    DOWNLOAD_MANAGER.set_media_automation(MEDIA_AUTOMATION)
except Exception:
    pass
AUTOMATION_MANAGER = AutomationManager()
# v3.5.33: background managers start only after the HTTP listener has been created.

def _process_memory_bytes() -> int:
    try:
        if sys.platform == "win32":
            class PMC(ctypes.Structure):
                _fields_ = [("cb", ctypes.wintypes.DWORD), ("PageFaultCount", ctypes.wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            pmc = PMC(); pmc.cb = ctypes.sizeof(PMC)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb): return int(pmc.WorkingSetSize)
        else:
            import resource
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return int(rss * (1 if sys.platform == 'darwin' else 1024))
    except Exception:
        pass
    return 0

def _dir_size(path: Path, pattern: str = '*') -> int:
    total = 0
    try:
        for item in path.glob(pattern):
            try:
                if item.is_file(): total += item.stat().st_size
            except OSError: pass
    except OSError: pass
    return total

def diagnostics_snapshot() -> dict[str, Any]:
    base = DIAGNOSTICS.snapshot(); metrics = base.get('providers', {})
    providers = []
    pool_stats = download_pool_stats()
    pool_by_id = {str(x.get('provider_id')): x for x in pool_stats.get('pools', [])}
    for p in get_providers():
        key = DIAGNOSTICS.provider_key(p.get('host',''), int(p.get('port',563)))
        m = metrics.get(key, {})
        successes, failures = int(m.get('successes',0)), int(m.get('failures',0)); total = successes + failures
        avg = (float(m.get('latency_sum',0)) / max(1,int(m.get('latency_samples',0)))) if m.get('latency_samples') else 0
        pool = pool_by_id.get(str(p.get('id')), {})
        providers.append({
            'id': p.get('id',''), 'name': p.get('name') or p.get('host','Provider'), 'host': p.get('host',''), 'port': p.get('port',563), 'ssl': bool(p.get('ssl',True)), 'role': _provider_role(p), 'priority': max(1,int(p.get('priority',10) or 10)),
            'configured_connections': int(p.get('connections',20) or 20), 'status': 'connected' if pool.get('open') else ('error' if failures and float(m.get('last_error_ts',0)) > float(m.get('last_ok',0)) else 'standby'),
            'last_latency_ms': m.get('last_latency_ms',0), 'average_latency_ms': round(avg,1), 'success_rate': round(successes*100/total,1) if total else None,
            'successes': successes, 'failures': failures, 'reconnects': int(m.get('reconnects',0)), 'bytes': int(m.get('bytes',0)), 'last_error': m.get('last_error',''), 'last_error_ts': m.get('last_error_ts',0),
            'pool': pool,
        })
    try:
        disk = shutil.disk_usage(DOWNLOAD_DIR)
        disk_info = {'total': disk.total, 'used': disk.used, 'free': disk.free, 'path': str(DOWNLOAD_DIR)}
    except OSError:
        disk_info = {'total':0,'used':0,'free':0,'path':str(DOWNLOAD_DIR)}
    with GROUP_SEARCH_MANAGER.lock:
        searches = [GROUP_SEARCH_MANAGER._public(j) for j in GROUP_SEARCH_MANAGER.jobs.values() if j.get('status') in {'queued','scanning','cancelling'}]
    snap = DOWNLOAD_MANAGER.snapshot()
    if str((snap.get('engine') or {}).get('name') or '').casefold() == 'sabnzbd':
        pool_stats = snap.get('connections') or pool_stats
    return {
        'version': APP_VERSION, 'uptime_seconds': int(time.time()-base.get('started',time.time())), 'memory_bytes': _process_memory_bytes(),
        'providers': providers, 'connections': pool_stats, 'downloads': {'counts': snap.get('counts',{}), 'speed_bps': snap.get('total_speed_bps',0), 'concurrent_downloads': snap.get('concurrent_downloads',0), 'telemetry': snap.get('telemetry',{}), 'collections': snap.get('collections',[]), 'engine': snap.get('engine',{})},
        'storage': {'disk': disk_info, 'thumbnail_cache': thumbnail_cache_stats(), 'preview_cache_bytes': _dir_size(CACHE_DIR), 'download_temp_bytes': _dir_size(DOWNLOAD_TEMP_DIR), 'data_bytes': _dir_size(DATA_DIR)},
        'thumbnail_decode': thumbnail_decode_stats(),
        'thumbnail_transfer': thumbnail_transfer_stats(),
        'thumbnail_catalog': thumbnail_catalog_stats(),
        'searches': searches, 'events': base.get('events',[])[:80], 'desktop_mode': DESKTOP_MODE, 'ffmpeg': bool(_ffmpeg_path()),
        'automation': AUTOMATION_MANAGER.snapshot() if 'AUTOMATION_MANAGER' in globals() else {'watch_enabled':False,'watch_imported':0,'watch_failed':0},
        'metadata_cloud': MEDIA_AUTOMATION.metadata_service_status_snapshot() if 'MEDIA_AUTOMATION' in globals() else {'status':'unknown','url':'https://api.newzdeck.com','authenticated':False,'compatible':True},
    }

def diagnostics_report() -> str:
    d = diagnostics_snapshot(); lines = [f"NewzDeck Diagnostics v{APP_VERSION}", f"Generated: {datetime.now().isoformat(timespec='seconds')}", f"Uptime: {d['uptime_seconds']}s", f"Memory: {d['memory_bytes']} bytes"]
    disk=d['storage']['disk']; lines.append(f"Download disk free: {disk.get('free',0)} / {disk.get('total',0)} bytes")
    td=d.get('thumbnail_decode') or {}; th=td.get('helper') or {}; tc=d.get('thumbnail_catalog') or {}; lines.append(f"Thumbnail decode: workers={td.get('workers',0)} active={td.get('active',0)} peak={td.get('peak',0)} runs={td.get('runs',0)} average_wait_ms={td.get('average_wait_ms',0)} physical_memory={td.get('physical_memory_bytes',0)} helper_jobs={th.get('jobs',0)} helper_starts={th.get('process_starts',0)} starts_avoided={th.get('process_launches_avoided',0)} catalog_entries={tc.get('entries',0)} catalog_hits={tc.get('hits',0)} catalog_fs_fallbacks={tc.get('filesystem_fallbacks',0)}")
    conn=d['connections']; engine=(d.get('downloads') or {}).get('engine') or {}
    if str(engine.get('name') or '').casefold() == 'sabnzbd':
        lines.append(f"Download engine: SABnzbd {engine.get('version','')} built-in; ready={engine.get('ready',False)}; live_connections={conn.get('active',0)}; allocated_connections={conn.get('capacity',0)}; provider_workers={conn.get('runtime_servers',0)}/{conn.get('expected_servers',0)} runtime, {conn.get('configured_servers',0)}/{conn.get('expected_servers',0)} configured; provider_summary={conn.get('provider_summary','')}; localhost_only={engine.get('localhost_only',True)}; last_error={engine.get('last_error','')}")
        tel=(d.get('downloads') or {}).get('telemetry') or {}
        lines.append(f"Active-card continuity: bridges={int(tel.get('active_card_continuity_bridges',0) or 0)}; last_bridge_ts={float(tel.get('active_card_continuity_last_ts',0) or 0):.3f}")
        probe=conn.get('provider_test') or {}
        if probe.get('tested'):
            lines.append(f"Provider connection test: ok={probe.get('ok',False)}; message={probe.get('summary','')}")
    else:
        lines.append(f"NNTP connections: {conn.get('active',0)} active, {conn.get('open',0)} warm, {conn.get('effective_capacity',conn.get('capacity',0))} target / {conn.get('capacity',0)} ceiling; pipeline={conn.get('pipeline_depth',1)} fallback={conn.get('pipeline_fallbacks',0)}; retries={conn.get('retries',0)} failed_segments={conn.get('failed_segments',0)}; yenc_workers={(conn.get('yenc') or {}).get('workers',0)}")
    cloud=d.get('metadata_cloud') or {}; lines.append(f"Metadata cloud: {cloud.get('status','unknown')} url={cloud.get('url','')} server={cloud.get('server_version','')} tmdb={cloud.get('tmdb_status','unknown')} authenticated={cloud.get('authenticated',False)} compatible={cloud.get('compatible',True)} circuit_open={cloud.get('circuit_open',False)} retry_seconds={cloud.get('circuit_retry_seconds',0)} cached_fallbacks={cloud.get('cached_fallbacks',0)} last_error={cloud.get('last_error','') or cloud.get('tmdb_last_error','')}")
    lines.append('Providers:')
    for p in d['providers']:
        lines.append(f"- {p['name']} ({p['host']}:{p['port']}): {p['status']}, latency={p.get('last_latency_ms',0)}ms, success={p.get('success_rate')}%, reconnects={p.get('reconnects',0)}, last_error={p.get('last_error','')}")
    lines.append('Recent events:')
    for e in d['events'][:20]: lines.append(f"- {datetime.fromtimestamp(e.get('ts',0)).isoformat(timespec='seconds')} [{e.get('level')}] {e.get('area')}: {e.get('message')}")
    return '\n'.join(lines)

def _user_safe_error_message(exc: Exception, *, operation: str = "request") -> str:
    """Translate transport/OS exceptions into stable user-facing messages."""
    text = str(exc or "").strip()
    low = text.casefold()
    reset = any(x in low for x in (
        "winerror 10054", "errno 10054", "forcibly closed", "connection reset",
        "connection aborted", "broken pipe", "remote end closed connection",
    )) or isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError))
    unavailable = any(x in low for x in (
        "winerror 10061", "errno 10061", "connection refused", "timed out", "timeout",
        "no connection could be made because the target machine actively refused it",
    )) or isinstance(exc, TimeoutError)
    if reset:
        if operation == "grab":
            return ("The built-in download engine briefly reset its local connection while "
                    "queueing this release. Check Downloads; if the release is not listed, "
                    "try Grab again in a moment.")
        return "NewzDeck briefly lost a local connection. The operation can be retried."
    if unavailable:
        if operation == "grab":
            return ("The built-in download engine was temporarily unavailable while queueing "
                    "this release. Check Downloads; if it is not listed, try Grab again in a moment.")
        return "A required local service was temporarily unavailable. Try again in a moment."
    return text or "The operation could not be completed."


def _probe_local_newzdeck_backend(port: int, timeout: float = 0.35) -> dict[str, Any] | None:
    """Probe another localhost NewzDeck backend without trusting the shared port file."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{int(port)}/api/health?startup=1", headers={"Connection": "close"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if int(getattr(resp, "status", 0) or 0) != 200:
                return None
            data = json.loads(resp.read().decode("utf-8-sig"))
        if not isinstance(data, dict) or not bool(data.get("ok")):
            return None
        return data
    except Exception:
        return None


def _authoritative_runtime_snapshot(current_port: int) -> dict[str, Any]:
    """Prefer the installed background-service backend over a stray desktop peer.

    v3.6.2 recovery proved that a service backend could have the real provider state
    while a same-version desktop backend still owned the Chromium window. Version-only
    handoff cannot detect that split. Scan NewzDeck's bounded localhost port range and
    make a healthy same-version service runtime authoritative.
    """
    current_port = int(current_port or 0)
    current_url = f"http://127.0.0.1:{current_port}" if current_port > 0 else ""
    if SERVICE_MODE:
        return {
            "ok": True, "authoritative": True, "current_port": current_port,
            "current_service_mode": True, "url": current_url, "reason": "current runtime is the background service",
        }

    ports = list(range(DEFAULT_PORT, DEFAULT_PORT + 25))
    candidates: list[tuple[int, dict[str, Any]]] = []
    # Probe concurrently so a stale/non-NewzDeck listener cannot add seconds to UI startup.
    with ThreadPoolExecutor(max_workers=8, thread_name_prefix="runtime-authority") as pool:
        future_map = {pool.submit(_probe_local_newzdeck_backend, port): port for port in ports if port != current_port}
        for fut, port in [(f, future_map[f]) for f in future_map]:
            try:
                data = fut.result(timeout=0.7)
            except Exception:
                data = None
            if not data:
                continue
            if str(data.get("version") or "").strip() != APP_VERSION:
                continue
            if bool(data.get("service_mode")):
                candidates.append((port, data))
    if candidates:
        # Lowest port is deterministic when more than one stale service listener exists.
        port, data = sorted(candidates, key=lambda item: item[0])[0]
        return {
            "ok": True, "authoritative": False, "current_port": current_port,
            "current_service_mode": False, "url": f"http://127.0.0.1:{port}",
            "service_port": port, "reason": "healthy same-version background service is authoritative",
        }
    return {
        "ok": True, "authoritative": True, "current_port": current_port,
        "current_service_mode": False, "url": current_url, "reason": "no healthy same-version service peer found",
    }


def _finish_progressive_smart_page(provider_id: str, provider: dict[str, Any], group: str, cache_key, info: dict[str, Any], low: int, high: int, page: int, page_count: int, limit: int, start_num: int, end_num: int, fetch_start: int, fetch_end: int) -> None:
    """Finish deep multipart reconstruction after the first usable page is visible."""
    try:
        started = time.perf_counter()
        with BROWSE_HEADER_POOL.lease(provider, group) as client:
            client.group(group)
            raw_articles = client.overview(fetch_start, fetch_end)
        _apply_cached_name_resolutions(provider_id, group, raw_articles)
        grouped_all = group_articles(raw_articles); articles = []
        for item in grouped_all:
            nums = [int(seg.get("article", 0) or 0) for seg in (item.get("segments") or [])]
            anchor_num = max(nums) if nums else int(item.get("article", 0) or 0)
            if start_num <= anchor_num <= end_num:
                articles.append(item)
        scanned_page_end = min(page_count, max(page, ((high - max(low, fetch_start)) // limit) + 1)) if page_count else page
        next_older_page = scanned_page_end + 1 if page_count and scanned_page_end < page_count else 0
        paging = {
            "page": page, "page_count": page_count, "page_size": limit, "start": start_num, "end": end_num,
            "low": low, "high": high, "has_older": bool(next_older_page), "has_newer": bool(page_count and page > 1),
            "scanned_page_end": scanned_page_end, "next_older_page": next_older_page, "smart_binary_scan": True,
        }
        payload = {"group": info, "articles": articles, "paging": paging, "elapsed_ms": round((time.perf_counter() - started) * 1000), "cache_source": "background reconstruction", "cache_age_seconds": 0, "smart_binary_headers": max(0, fetch_end - fetch_start + 1), "smart_binary_pending": False}
        with ARTICLE_PAGE_CACHE_LOCK:
            current = ARTICLE_PAGE_CACHE.get(cache_key)
            # Do not overwrite a newer explicit refresh of this page.
            if current and bool((current.get("payload") or {}).get("smart_binary_pending")):
                ARTICLE_PAGE_CACHE[cache_key] = {"cached_at": time.time(), "payload": payload}
    except Exception as exc:
        DIAGNOSTICS.event("warning", "browse", f"Progressive binary reconstruction failed: {exc}", provider_id=provider_id, group=group, page=page)
        with ARTICLE_PAGE_CACHE_LOCK:
            current = ARTICLE_PAGE_CACHE.get(cache_key)
            if current and bool((current.get("payload") or {}).get("smart_binary_pending")):
                failed = dict(current.get("payload") or {}); failed["smart_binary_pending"] = False; failed["smart_binary_background_error"] = str(exc)[:300]
                ARTICLE_PAGE_CACHE[cache_key] = {"cached_at": time.time(), "payload": failed}

class AppHandler(SimpleHTTPRequestHandler):
    server_version = f"NewzDeck/{APP_VERSION}"
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        # v3.5.18: the desktop shell is a Chromium app-mode window. Earlier
        # builds allowed Chromium's normal HTTP cache to retain index.html/app.js
        # across portable upgrades, which could connect an old UI (for example
        # v3.5.14) to a newer backend. Never cache executable UI assets. Media
        # thumbnails/previews keep their dedicated cache headers below.
        try:
            ui_path = urllib.parse.urlparse(str(getattr(self, "path", "") or "")).path.lower()
        except Exception:
            ui_path = ""
        if ui_path in {"/", "/index.html", "/app.js", "/styles.css"} or ui_path.endswith((".html", ".js", ".css")):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("X-NewzDeck-UI-Version", APP_VERSION)
        # Localhost applications still need browser-origin boundaries.  These
        # headers prevent another site from embedding or casually consuming the
        # NewzDeck UI/API as a cross-origin resource.
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
        super().end_headers()

    def log_message(self, format, *args):
        if DESKTOP_MODE:
            path = str(getattr(self, "path", "")).split("?", 1)[0]
            if path.startswith(("/thumb/", "/media/", "/api/thumbnail/")) or path in {"/api/downloads", "/api/app/heartbeat"}:
                return
        safe_print("[%s] %s" % (self.log_date_time_string(), format % args))

    def _mutation_origin_allowed(self) -> bool:
        """Reject browser cross-site POSTs while allowing native/local helpers.

        Native helpers and command-line clients generally omit Origin and
        Sec-Fetch-Site, so absence of those browser headers remains allowed.  A
        browser request that supplies them must be same-origin with this exact
        localhost listener.
        """
        fetch_site = str(self.headers.get("Sec-Fetch-Site", "") or "").strip().casefold()
        if fetch_site == "cross-site":
            return False
        origin = str(self.headers.get("Origin", "") or "").strip()
        if not origin:
            return True
        try:
            parsed = urllib.parse.urlparse(origin)
            hostname = str(parsed.hostname or "").casefold()
            request_host = str(self.headers.get("Host", "") or "").strip().casefold()
            return (
                parsed.scheme.casefold() in {"http", "https"}
                and hostname in {"127.0.0.1", "localhost"}
                and bool(request_host)
                and parsed.netloc.casefold() == request_host
            )
        except Exception:
            return False

    def _json(self, status: int, payload: Any):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # v3.5.18 cache recovery: v3.5.17 changed the backend's default port
        # without rebuilding the native desktop bootstrapper, which broke
        # readiness detection. We keep the long-established 8765 launcher
        # contract and instead ask Chromium to discard any pre-3.5.17 cached
        # UI when it performs its startup health check. The launcher itself may
        # make the first health request, so advertise the reset for the first
        # two minutes rather than only once. Clear-Site-Data is ignored by the
        # native launcher but honored by Chromium on the local trusted origin.
        try:
            request_path = urllib.parse.urlparse(str(getattr(self, "path", "") or "")).path
        except Exception:
            request_path = ""
        if request_path == "/api/health" and (time.monotonic() - BACKEND_PROCESS_STARTED_AT) < 120.0:
            self.send_header("Clear-Site-Data", '"cache"')
            self.send_header("X-NewzDeck-Cache-Recovery", APP_VERSION)
        self.end_headers()
        self.wfile.write(body)

    def _body_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > 2_000_000:
            raise ValueError("Request is too large")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/app-icon.ico":
            icon_path = APP_DIR / "NewzDeck.ico"
            if not icon_path.exists():
                self.send_error(404); return
            body = icon_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/x-icon")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers(); self.wfile.write(body); return
        if parsed.path == "/api/health":
            heartbeat_last, heartbeat_seen = desktop_heartbeat_state()
            heartbeat_age = max(0.0, time.monotonic() - heartbeat_last) if heartbeat_seen else None
            base_health = {
                "ok": True, "version": APP_VERSION, "platform": sys.platform,
                "desktop_mode": DESKTOP_MODE, "service_mode": SERVICE_MODE,
                "desktop_heartbeat_seen": bool(heartbeat_seen),
                "desktop_heartbeat_age_seconds": round(heartbeat_age, 3) if heartbeat_age is not None else None,
            }
            # v3.5.33 startup probes intentionally avoid download-engine pings,
            # PATH/tool scans and other diagnostics. The launcher needs only the
            # identity/mode/heartbeat tuple; all normal UI health calls retain the
            # full response below. This keeps /api/health?startup=1 on the cold
            # launch critical path effectively constant-time.
            health_query = urllib.parse.parse_qs(parsed.query or "")
            if str((health_query.get("startup") or [""])[0]).lower() in {"1", "true", "yes"}:
                return self._json(200, base_health)
            base_health.update({
                "data_dir": str(DATA_DIR), "user_root": str(USER_ROOT), "download_dir": str(DOWNLOAD_DIR),
                "backend_pid": os.getpid(), "provider_count": len(get_providers()),
                "background_capable": sys.platform == "win32" and TRAY_HELPER_EXE.exists(),
                "ffmpeg": bool(_ffmpeg_path()), "sevenzip": bool(_sevenzip_path()),
                "unrar": bool(_unrar_path()), "unrar_managed": bool(_managed_unrar_path()),
                "unrar_managed_version": UNRAR_MANAGED_VERSION, "unrar_auto_install": sys.platform == "win32",
                "unrar_install_error": _unrar_install_error, "par2": bool(_par2_path()),
                "par2_managed": bool(_managed_par2_path()), "par2_auto_install": sys.platform == "win32",
                "par2_install_error": _par2_install_error,
                "private_runtime": (APP_DIR / "runtime" / "python.exe").exists(),
                "installed": (APP_DIR / "Uninstall.exe").exists(),
                "download_engine": DOWNLOAD_MANAGER.engine_status() if hasattr(DOWNLOAD_MANAGER, "engine_status") else {"name":"NewzDeck Legacy","ready":True},
            })
            return self._json(200, base_health)
        if parsed.path == "/api/service/status":
            return self._json(200, service_status_snapshot())
        if parsed.path == "/api/diagnostics":
            return self._json(200, diagnostics_snapshot())
        if parsed.path == "/api/diagnostics/report":
            return self._json(200, {"report": diagnostics_report()})
        if parsed.path == "/api/update/status":
            query = urllib.parse.parse_qs(parsed.query or "")
            check_online = str((query.get("online") or [""])[0]).lower() in {"1","true","yes"}
            force = str((query.get("force") or [""])[0]).lower() in {"1","true","yes"}
            online = online_update_status(force=force) if check_online else {"online_feed": True}
            return self._json(200, {
                "version": APP_VERSION,
                "installed": (APP_DIR / "Uninstall.exe").exists(),
                "private_runtime": (APP_DIR / "runtime" / "python.exe").exists(),
                "app_dir": str(APP_DIR),
                "data_dir": str(USER_ROOT),
                "launcher_pid": int(os.environ.get("NEWZDECK_LAUNCHER_PID", os.environ.get("USENET_BROWSER_LAUNCHER_PID", "0")) or 0),
                "service_mode": SERVICE_MODE,
                **online,
            })
        if parsed.path == "/api/runtime/authoritative":
            return self._json(200, _authoritative_runtime_snapshot(int(getattr(self.server, "server_port", 0) or 0)))
        if parsed.path == "/api/providers":
            return self._json(200, {"providers": [public_provider(p) for p in get_providers()]})
        if parsed.path == "/api/downloads":
            return self._json(200, DOWNLOAD_MANAGER.snapshot())
        if parsed.path == "/api/automation/sidebar-counts":
            try:
                counts = dict(MEDIA_AUTOMATION.sidebar_counts() or {})
                counts["source"] = "automation"
                return self._json(200, counts)
            except Exception as exc:
                try:
                    DIAGNOSTICS.event("warning", "media-automation", "Automation sidebar counts failed", error=str(exc))
                except Exception:
                    pass
                return self._json(503, {"error": "Automation sidebar counts are not ready", "detail": _user_safe_error_message(exc), "version": APP_VERSION})
        if parsed.path == "/api/automation/summary":
            try:
                return self._json(200, MEDIA_AUTOMATION.summary())
            except Exception as exc:

                try:
                    DIAGNOSTICS.event("error", "media-automation", "Automation summary failed", error=str(exc), trace=traceback.format_exc(limit=6))
                except Exception:
                    pass
                return self._json(503, {"error": "Automation could not be initialized", "detail": _user_safe_error_message(exc), "version": APP_VERSION})
        if parsed.path == "/api/saved-searches":
            return self._json(200, {"items": get_saved_searches()})
        if parsed.path == "/api/cache/stats":
            return self._json(200, thumbnail_cache_stats())
        if parsed.path == "/api/config/backup":
            return self.config_backup_api()
        if parsed.path == "/api/settings":
            defaults = {
                "article_limit": DEFAULT_ARTICLE_LIMIT,
                "preview_limit_mb": DEFAULT_PREVIEW_LIMIT_MB,
                "thumbnail_cache_gb": DEFAULT_THUMB_CACHE_GB,
                "concurrent_downloads": PACKAGE_QUEUE_CONCURRENCY,
                "thumbnail_size": DEFAULT_THUMBNAIL_SIZE,
                "continuous_browse": DEFAULT_CONTINUOUS_BROWSE,
                "view_mode": DEFAULT_VIEW_MODE,
                "content_filter": DEFAULT_CONTENT_FILTER,
                "download_organization": DEFAULT_DOWNLOAD_ORGANIZATION,
                "download_folder": str(DOWNLOAD_DIR),
                "group_related_media": DEFAULT_GROUP_RELATED_MEDIA,
                "group_binary_sets": DEFAULT_GROUP_BINARY_SETS,
                "binary_min_size_value": 0.0,
                "binary_min_size_unit": "MB",
                "favorites": [],
                "bookmark_folders": [],
                "recent_groups": [],
                "group_states": {},
                "blocked_posters": [],
                "group_seen_high": {},
                "group_read_states": {},
                "browser_tabs": [],
                "active_browser_tab": "",
                "disk_reserve_gb": 1.0,
                "post_processing": DEFAULT_POST_PROCESSING,
                "auto_repair": DEFAULT_AUTO_REPAIR,
                "auto_fetch_par2": DEFAULT_AUTO_FETCH_PAR2,
                "auto_extract": DEFAULT_AUTO_EXTRACT,
                "cleanup_archives": DEFAULT_CLEANUP_ARCHIVES,
                "extract_subfolder": DEFAULT_EXTRACT_SUBFOLDER,
                "direct_unpack_mode": DEFAULT_DIRECT_UNPACK_MODE,
                "automation_media_cleanup": DEFAULT_AUTOMATION_MEDIA_CLEANUP,
                "watch_folder_enabled": DEFAULT_WATCH_FOLDER_ENABLED,
                "watch_folder": DEFAULT_WATCH_FOLDER,
                "watch_provider_id": "",
                "watch_archive_processed": DEFAULT_WATCH_ARCHIVE_PROCESSED,
                "smart_categories_enabled": DEFAULT_SMART_CATEGORIES,
                "category_movies_keywords": "2160p, 1080p, bluray, remux, bdrip",
                "category_movies_folder": "Movies",
                "category_tv_keywords": "season, episode, complete series",
                "category_tv_folder": "TV",
                "category_images_keywords": ".jpg, .jpeg, .png, .gif, image, photo",
                "category_images_folder": "Images",
                "category_other_folder": "Other",
                "bandwidth_schedule_enabled": DEFAULT_BANDWIDTH_SCHEDULE_ENABLED,
                "bandwidth_schedule_start": DEFAULT_BANDWIDTH_SCHEDULE_START,
                "bandwidth_schedule_end": DEFAULT_BANDWIDTH_SCHEDULE_END,
                "bandwidth_schedule_limit_mb_s": DEFAULT_BANDWIDTH_SCHEDULE_LIMIT_MB_S,
                "completion_notification": DEFAULT_COMPLETION_NOTIFICATION,
                "completion_open_folder": DEFAULT_COMPLETION_OPEN_FOLDER,
            }
            settings = json_read(SETTINGS_FILE, defaults)
            if not isinstance(settings, dict):
                settings = {}
            return self._json(200, {**defaults, **settings})
        if parsed.path.startswith("/media/"):
            token = parsed.path.split("/", 2)[2]
            return self.serve_media(token)
        if parsed.path.startswith("/thumb/"):
            token = parsed.path.split("/", 2)[2]
            return self.serve_thumbnail(token)
        if parsed.path.startswith("/download/"):
            token = parsed.path.split("/", 2)[2]
            return self.serve_media(token, attachment=True)
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            if not self._mutation_origin_allowed():
                try:
                    DIAGNOSTICS.event("warning", "http-security", "Rejected cross-origin localhost POST", path=parsed.path)
                except Exception:
                    pass
                return self._json(403, {"error": "Cross-origin requests are not allowed."})
            if parsed.path == "/api/update/online-install":
                return self.online_update_install_api()
            if parsed.path == "/api/update/install":
                return self.update_install_api()
            if parsed.path == "/api/nzb/import":
                return self.nzb_import_upload_api()
            if parsed.path == "/api/nzb/inspect":
                return self.nzb_inspect_upload_api()
            data = self._body_json()
            if parsed.path == "/api/nzb/import-selection":
                return self.nzb_import_selection_api(data)
            if parsed.path == "/api/app/heartbeat":
                desktop_heartbeat()
                return self._json(200, {"ok": True})
            if parsed.path == "/api/app/taskbar-identify":
                return self._json(200, {"ok": True, "launched": _launch_taskbar_identity()})
            if parsed.path == "/api/service/install":
                return self.service_install_api(data)
            if parsed.path == "/api/service/control":
                return self.service_control_api(data)
            if parsed.path == "/api/service/shutdown":
                if not SERVICE_MODE:
                    raise ValueError("Shutdown is only available to the background service")
                self._json(200, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if parsed.path == "/api/diagnostics/probe":
                return self.diagnostics_probe_api(data)
            if parsed.path == "/api/diagnostics/clear":
                with DIAGNOSTICS.lock: DIAGNOSTICS.events.clear()
                try: DIAGNOSTICS_LOG_FILE.unlink(missing_ok=True)
                except OSError: pass
                return self._json(200, {"ok": True})
            if parsed.path == "/api/providers/save":
                return self.save_provider_api(data)
            if parsed.path == "/api/providers/delete":
                return self.delete_provider_api(data)
            if parsed.path == "/api/providers/test":
                return self.test_provider_api(data)
            if parsed.path == "/api/groups":
                return self.groups_api(data)
            if parsed.path == "/api/groups/status":
                return self.groups_status_api(data)
            if parsed.path == "/api/browse/session":
                return self._json(200, register_browse_session(str(data.get("provider_id", "")), str(data.get("group", "")), str(data.get("browse_session", ""))))
            if parsed.path == "/api/articles":
                return self.articles_api(data)
            if parsed.path == "/api/articles/resolve-names":
                return self.article_name_resolution_api(data)
            if parsed.path == "/api/group-search/start":
                return self.group_search_start_api(data)
            if parsed.path == "/api/group-search/status":
                return self.group_search_status_api(data)
            if parsed.path == "/api/group-search/results":
                return self.group_search_results_api(data)
            if parsed.path == "/api/group-search/cancel":
                return self.group_search_cancel_api(data)
            if parsed.path == "/api/saved-searches/save":
                return self._json(200, saved_search_save(data))
            if parsed.path == "/api/saved-searches/delete":
                return self._json(200, {"items": saved_search_delete(str(data.get("id", "")))})
            if parsed.path == "/api/preview/prepare":
                return self.preview_api(data)
            if parsed.path == "/api/thumbnail/image":
                return self.image_thumbnail_api(data)
            if parsed.path == "/api/thumbnail/video":
                return self.video_thumbnail_api(data)
            if parsed.path == "/api/thumbnail/store":
                return self.thumbnail_store_api(data)
            if parsed.path == "/api/thumbnail/invalidate":
                return self.thumbnail_invalidate_api(data)
            if parsed.path == "/api/cache/clear":
                return self.cache_clear_api(data)
            if parsed.path == "/api/cache/preview/clear":
                return self.preview_cache_clear_api(data)
            if parsed.path == "/api/downloads/add":
                return self.downloads_add_api(data)
            if parsed.path == "/api/downloads/control":
                return self.downloads_control_api(data)
            if parsed.path == "/api/downloads/open-folder":
                return self.downloads_open_folder_api(data)
            if parsed.path == "/api/settings/choose-download-folder":
                return self.choose_download_folder_api(data)
            if parsed.path == "/api/settings/choose-watch-folder":
                return self.choose_watch_folder_api(data)
            if parsed.path == "/api/config/restore":
                return self.config_restore_api(data)
            if parsed.path == "/api/app/open-data":
                return self.app_open_data_api(data)
            if parsed.path == "/api/download/items":
                return self.download_items_api(data)
            if parsed.path == "/api/discover/home":
                mode=str(data.get('mode') or 'home').strip().lower()
                return self._json(200, MEDIA_AUTOMATION.discover_home(personalized=(mode=='for_you')))
            if parsed.path == "/api/discover/new":
                return self._json(200, MEDIA_AUTOMATION.discover_new())
            if parsed.path == "/api/discover/genres":
                return self._json(200, MEDIA_AUTOMATION.discover_genres(str(data.get("kind") or "movie")))
            if parsed.path == "/api/discover/person":
                return self._json(200, MEDIA_AUTOMATION.discover_person(data))
            if parsed.path == "/api/discover/browse":
                return self._json(200, MEDIA_AUTOMATION.discover_browse(data))
            if parsed.path == "/api/discover/detail":
                return self._json(200, MEDIA_AUTOMATION.discover_detail(data))
            if parsed.path == "/api/discover/preference":
                return self._json(200, MEDIA_AUTOMATION.discover_preference(data))
            if parsed.path == "/api/discover/releases/search":
                return self._json(200, MEDIA_AUTOMATION.discover_search_releases(data))
            if parsed.path == "/api/automation/config/save":
                return self._json(200, MEDIA_AUTOMATION.save_config(data))
            if parsed.path == "/api/automation/metadata/search":
                return self._json(200, {"results": MEDIA_AUTOMATION.metadata_search(str(data.get("kind") or "tv"), str(data.get("query") or ""))})
            if parsed.path == "/api/automation/media/add":
                return self._json(200, {"item": MEDIA_AUTOMATION.add_media(data)})
            if parsed.path == "/api/automation/media/update":
                return self._json(200, {"item": MEDIA_AUTOMATION.update_media(data)})
            if parsed.path == "/api/automation/media/delete":
                return self._json(200, MEDIA_AUTOMATION.delete_media(str(data.get("id") or "")))
            if parsed.path == "/api/automation/media/refresh":
                return self._json(200, MEDIA_AUTOMATION.refresh_media_metadata(str(data.get("id") or "")))
            if parsed.path == "/api/automation/media/open-folder":
                location=MEDIA_AUTOMATION.media_location(str(data.get("id") or ""))
                if SERVICE_MODE:
                    tray_helper_request('open_path',path=location,timeout=4)
                elif sys.platform=='win32':
                    os.startfile(location)
                return self._json(200, {'ok':True,'path':location})
            if parsed.path == "/api/automation/import/retry":
                return self._json(200, DOWNLOAD_MANAGER.retry_automation_import(str(data.get("collection_id") or "")))
            if parsed.path == "/api/automation/library/scan":
                return self._json(200, MEDIA_AUTOMATION.scan_library(str(data.get("id") or "")))
            if parsed.path == "/api/automation/run-now":
                return self._json(200, MEDIA_AUTOMATION.run_automatic_now())
            if parsed.path == "/api/automation/metadata/service-test":
                return self._json(200, MEDIA_AUTOMATION.test_metadata_service())
            if parsed.path == "/api/automation/metadata/refresh":
                return self._json(200, MEDIA_AUTOMATION.refresh_monitored_metadata(force=True))
            if parsed.path == "/api/automation/profile/save":
                return self._json(200, {"profile": MEDIA_AUTOMATION.save_profile(data)})
            if parsed.path == "/api/automation/profile/delete":
                return self._json(200, MEDIA_AUTOMATION.delete_profile(str(data.get("id") or "")))
            if parsed.path == "/api/automation/indexer/save":
                return self._json(200, {"indexer": MEDIA_AUTOMATION.save_indexer(data)})
            if parsed.path == "/api/automation/indexer/delete":
                return self._json(200, MEDIA_AUTOMATION.delete_indexer(str(data.get("id") or "")))
            if parsed.path == "/api/automation/indexer/test":
                return self._json(200, MEDIA_AUTOMATION.test_indexer(str(data.get("id") or "")))
            if parsed.path == "/api/automation/releases/search":
                return self._json(200, MEDIA_AUTOMATION.search_releases(str(data.get("item_id") or ""), data.get("season"), data.get("episode")))
            if parsed.path == "/api/automation/releases/grab":
                try:
                    return self._json(200, MEDIA_AUTOMATION.grab_release(data))
                except Exception as exc:
                    try:
                        DIAGNOSTICS.event("warning", "automation-grab", "Grab request failed",
                                          error=str(exc), safe_error=_user_safe_error_message(exc, operation="grab"),
                                          release=str(data.get("title") or ""), indexer=str(data.get("indexer") or ""))
                    except Exception:
                        pass
                    return self._json(400, {
                        "error": _user_safe_error_message(exc, operation="grab"),
                        "code": "grab_failed",
                    })
            if parsed.path == "/api/automation/blacklist/add":
                return self._json(200, MEDIA_AUTOMATION.blacklist_release(data))
            if parsed.path == "/api/automation/blacklist/clear":
                return self._json(200, MEDIA_AUTOMATION.clear_release_blacklist(str(data.get("target_key") or ""), str(data.get("guid") or "")))
            if parsed.path == "/api/automation/root/add":
                return self.automation_add_root_api(data)
            if parsed.path == "/api/automation/choose-folder":
                return self.automation_choose_folder_api(data)
            if parsed.path == "/api/settings/save":
                return self.settings_api(data)
            return self._json(404, {"error": "Not found"})
        except (ValueError, NntpError, socket.error, ssl.SSLError, OSError) as exc:
            try:
                DIAGNOSTICS.event("warning", "http", "Request failed", path=parsed.path, error=str(exc))
            except Exception:
                pass
            return self._json(400, {"error": _user_safe_error_message(exc)})
        except Exception as exc:
            safe_print("Unexpected error:", repr(exc))
            DIAGNOSTICS.event("error", "http", str(exc), path=parsed.path, trace=traceback.format_exc(limit=4))
            return self._json(500, {"error": "Unexpected application error. See Diagnostics for details."})

    def diagnostics_probe_api(self, data: dict[str, Any]):
        requested = str(data.get("provider_id", "") or "")
        targets = [provider_by_id(requested)] if requested else get_providers()
        results = []
        for p in targets:
            started = time.perf_counter()
            try:
                password = unprotect_secret(p.get("password_protected", ""))
                with NntpClient(p["host"], p["port"], bool(p.get("ssl", True)), p.get("username", ""), password, timeout=12.0) as client:
                    latency = round((time.perf_counter() - started) * 1000, 1)
                    DIAGNOSTICS.provider_result(p.get('host',''), int(p.get('port',563)), ok=True, latency_ms=latency)
                    results.append({"id": p.get("id"), "ok": True, "latency_ms": latency, "capabilities": client.capabilities[:8]})
            except Exception as exc:
                latency = round((time.perf_counter() - started) * 1000, 1)
                DIAGNOSTICS.provider_result(p.get('host',''), int(p.get('port',563)), ok=False, latency_ms=latency, error=str(exc))
                DIAGNOSTICS.event('warning','provider',f"Provider health probe failed: {exc}", provider=p.get('name') or p.get('host'))
                results.append({"id": p.get("id"), "ok": False, "latency_ms": latency, "error": str(exc)})
        return self._json(200, {"results": results, "diagnostics": diagnostics_snapshot()})

    def save_provider_api(self, data: dict[str, Any]):
        host = str(data.get("host", "")).strip()
        name = str(data.get("name", "")).strip() or host
        username = str(data.get("username", "")).strip()
        if not host:
            raise ValueError("Server hostname is required")
        try:
            port = int(data.get("port", 563))
        except ValueError:
            raise ValueError("Port must be a number")
        if not (1 <= port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        provider_id = str(data.get("id") or secrets.token_hex(8))
        providers = get_providers()
        existing = next((p for p in providers if p.get("id") == provider_id), None)
        password = data.get("password")
        password_protected = existing.get("password_protected", "") if existing else ""
        if password is not None and str(password) != "":
            password_protected = protect_secret(str(password))
        record = {
            "id": provider_id,
            "name": name,
            "host": host,
            "port": port,
            "ssl": bool(data.get("ssl", True)),
            "username": username,
            "password_protected": password_protected,
            "connections": max(1, min(100, int(data.get("connections", 20) or 20))),
            "pipeline_depth": max(0, min(NNTP_PIPELINE_MAX_DEPTH, int(data.get("pipeline_depth", existing.get("pipeline_depth", 0) if existing else 0) or 0))),
            "enabled": bool(data.get("enabled", True)),
            "role": str(data.get("role", existing.get("role", "primary") if existing else "primary") or "primary").lower() if str(data.get("role", existing.get("role", "primary") if existing else "primary") or "primary").lower() in PROVIDER_ROLE_ORDER else "primary",
            "priority": max(1, min(999, int(data.get("priority", existing.get("priority", 10) if existing else 10) or 10))),
            "use_browsing": bool(data.get("use_browsing", existing.get("use_browsing", True) if existing else True)),
            "use_previews": bool(data.get("use_previews", existing.get("use_previews", True) if existing else True)),
            "use_downloads": bool(data.get("use_downloads", existing.get("use_downloads", True) if existing else True)),
            "use_recovery": bool(data.get("use_recovery", existing.get("use_recovery", True) if existing else True)),
        }
        connection_changed = not existing or _provider_group_cache_signature(existing) != _provider_group_cache_signature(record)
        if existing:
            providers[providers.index(existing)] = record
        else:
            providers.append(record)
        save_providers(providers)
        try:
            DOWNLOAD_MANAGER.request_sync()
        except Exception:
            pass
        if connection_changed:
            with GROUP_CACHE_LOCK:
                GROUP_CACHE.pop(provider_id, None)
            _drop_persistent_group_cache(provider_id)
        return self._json(200, {"provider": public_provider(record)})

    def delete_provider_api(self, data: dict[str, Any]):
        provider_id = str(data.get("id", ""))
        providers = [p for p in get_providers() if p.get("id") != provider_id]
        save_providers(providers)
        try:
            DOWNLOAD_MANAGER.request_sync()
        except Exception:
            pass
        with GROUP_CACHE_LOCK:
            GROUP_CACHE.pop(provider_id, None)
        _drop_persistent_group_cache(provider_id)
        return self._json(200, {"ok": True})

    def _provider_from_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        if data.get("provider_id"):
            return provider_by_id(str(data["provider_id"]))
        host = str(data.get("host", "")).strip()
        if not host:
            raise ValueError("Server hostname is required")
        return {
            "host": host,
            "port": int(data.get("port", 563)),
            "ssl": bool(data.get("ssl", True)),
            "username": str(data.get("username", "")),
            "password_protected": protect_secret(str(data.get("password", ""))),
        }

    def test_provider_api(self, data: dict[str, Any]):
        provider = self._provider_from_payload(data)
        password = str(data.get("password", "")) if data.get("password") else unprotect_secret(provider.get("password_protected", ""))
        started = time.perf_counter()
        with NntpClient(provider["host"], provider["port"], bool(provider.get("ssl", True)), provider.get("username", ""), password) as client:
            latency = round((time.perf_counter() - started) * 1000)
            caps = client.capabilities[:30]
        return self._json(200, {"ok": True, "latency_ms": latency, "capabilities": caps})

    def groups_api(self, data: dict[str, Any]):
        provider_id = str(data.get("provider_id", ""))
        provider = provider_by_id(provider_id)
        password = unprotect_secret(provider.get("password_protected", ""))
        query = str(data.get("query", "")).strip().lower()
        refresh = bool(data.get("refresh", False))
        offset = max(0, int(data.get("offset", 0)))
        page_size = max(100, min(MAX_GROUP_PAGE_SIZE, int(data.get("page_size", DEFAULT_GROUP_PAGE_SIZE))))
        sort = str(data.get("sort", "articles_desc"))

        started = time.perf_counter()
        with GROUP_CACHE_LOCK:
            cached = GROUP_CACHE.get(provider_id)

        cache_source = "memory" if cached else ""
        if not cached and not refresh:
            cached = _load_persistent_group_cache(provider_id, provider)
            if cached:
                cache_source = "disk"
                with GROUP_CACHE_LOCK:
                    GROUP_CACHE[provider_id] = cached

        cache_hit = bool(cached) and not refresh
        if not cache_hit:
            with NntpClient(provider["host"], provider["port"], bool(provider.get("ssl", True)), provider.get("username", ""), password) as client:
                groups = client.list_active(None)
            cached = {"groups": groups, "loaded_at": time.time(), "source": "network"}
            cache_source = "network"
            with GROUP_CACHE_LOCK:
                GROUP_CACHE[provider_id] = cached
            _save_persistent_group_cache(provider_id, provider, cached)
        groups = _sorted_group_view(cached, sort)

        if query:
            if "*" in query or "?" in query:
                groups = [g for g in groups if fnmatch.fnmatchcase(g["name"].lower(), query)]
            else:
                groups = [g for g in groups if query in g["name"].lower()]

        total = len(groups)
        page = groups[offset:offset + page_size]
        elapsed = round((time.perf_counter() - started) * 1000)
        return self._json(200, {
            "groups": page,
            "total": total,
            "offset": offset,
            "page_size": page_size,
            "has_more": offset + len(page) < total,
            "elapsed_ms": elapsed,
            "cache_hit": cache_hit,
            "cache_source": cache_source or ("memory" if cache_hit else "network"),
            "cache_age_seconds": max(0, int(time.time() - float(cached.get("loaded_at", time.time()) or time.time()))),
        })

    def groups_status_api(self, data: dict[str, Any]):
        provider_id = str(data.get("provider_id", ""))
        provider = provider_by_id(provider_id)
        raw_names = data.get("groups") if isinstance(data.get("groups"), list) else []
        names = []
        seen = set()
        for value in raw_names:
            name = str(value or "").strip()[:300]
            if name and name not in seen:
                seen.add(name); names.append(name)
            if len(names) >= 50:
                break
        if not names:
            return self._json(200, {"groups": [], "elapsed_ms": 0})
        password = unprotect_secret(provider.get("password_protected", ""))
        started = time.perf_counter(); groups = []
        with NntpClient(provider["host"], provider["port"], bool(provider.get("ssl", True)), provider.get("username", ""), password) as client:
            for name in names:
                try:
                    info = client.group(name)
                    groups.append({"name": name, "articles": int(info.get("count", 0) or 0), "low": int(info.get("low", 0) or 0), "high": int(info.get("high", 0) or 0)})
                except Exception as exc:
                    DIAGNOSTICS.event("warning", "browse", f"Background group status failed: {exc}", provider_id=provider_id, group=name)
        return self._json(200, {"groups": groups, "elapsed_ms": round((time.perf_counter() - started) * 1000)})

    def articles_api(self, data: dict[str, Any]):
        provider_id = str(data.get("provider_id", ""))
        provider = provider_by_id(provider_id)
        group = str(data.get("group", "")).strip()
        if not group:
            raise ValueError("Newsgroup is required")
        limit = max(25, min(2000, int(data.get("limit", DEFAULT_ARTICLE_LIMIT))))
        requested_page = max(1, int(data.get("page", 1) or 1))
        media_only = bool(data.get("media_only", False))
        smart_binaries = bool(data.get("smart_binaries", False))
        progressive = bool(data.get("progressive", False))
        refresh = bool(data.get("refresh", False))
        cache_key = (provider_id, group, limit, requested_page, smart_binaries)
        started = time.perf_counter()

        if not refresh:
            with ARTICLE_PAGE_CACHE_LOCK:
                cached = ARTICLE_PAGE_CACHE.get(cache_key)
            if cached and time.time() - float(cached.get("cached_at", 0) or 0) <= ARTICLE_PAGE_CACHE_TTL_SECONDS:
                payload = dict(cached.get("payload") or {})
                if not progressive and bool(payload.get("smart_binary_pending")):
                    cached = None
                else:
                    grouped = annotate_cached_thumbnail_urls(provider_id, group, list(payload.get("articles") or []))
                    if media_only:
                        grouped = [a for a in grouped if a.get("media")]
                    payload["articles"] = grouped
                    payload["elapsed_ms"] = round((time.perf_counter() - started) * 1000)
                    payload["cache_source"] = "header cache"
                    payload["cache_age_seconds"] = max(0, int(time.time() - float(cached.get("cached_at", 0) or 0)))
                    return self._json(200, payload)

        fetch_start = fetch_end = smart_extra = 0
        background_smart = None
        with BROWSE_HEADER_POOL.lease(provider, group) as client:
            info = client.group(group)
            high = int(info["high"]); low = int(info["low"]); group_count = int(info.get("count", 0) or 0)
            if group_count <= 0 or high < low or (high == 0 and low == 0):
                page_count = 0; page = 1; start_num = end_num = 0; articles = []
            else:
                span = max(1, high - low + 1)
                page_count = max(1, (span + limit - 1) // limit)
                page = min(requested_page, page_count)
                end_num = high - ((page - 1) * limit)
                start_num = max(low, end_num - limit + 1)
                overlap = min(200, max(25, limit // 10))
                fetch_start = max(low, start_num - overlap); fetch_end = min(high, end_num + overlap)
                raw_articles = client.overview(fetch_start, fetch_end)
                if smart_binaries and raw_articles:
                    smart_extra = _smart_binary_expansion_headers(raw_articles)
                    if smart_extra > 0:
                        expanded_start = max(low, fetch_start - smart_extra)
                        if expanded_start < fetch_start:
                            if progressive:
                                background_smart = (expanded_start, fetch_end)
                            else:
                                fetch_start = expanded_start
                                raw_articles = client.overview(fetch_start, fetch_end)
                _apply_cached_name_resolutions(provider_id, group, raw_articles)
                grouped_all = group_articles(raw_articles)
                articles = []
                for item in grouped_all:
                    nums = [int(seg.get("article", 0) or 0) for seg in (item.get("segments") or [])]
                    anchor_num = max(nums) if nums else int(item.get("article", 0) or 0)
                    if start_num <= anchor_num <= end_num:
                        articles.append(item)

        scanned_page_end = page
        if page_count and smart_binaries and smart_extra > 0 and start_num and fetch_start:
            scanned_page_end = min(page_count, max(page, ((high - max(low, fetch_start)) // limit) + 1))
        next_older_page = scanned_page_end + 1 if page_count and scanned_page_end < page_count else 0
        paging = {
            "page": page, "page_count": page_count, "page_size": limit, "start": start_num, "end": end_num,
            "low": low, "high": high, "has_older": bool(next_older_page),
            "has_newer": bool(page_count and page > 1),
            "scanned_page_end": scanned_page_end, "next_older_page": next_older_page,
            "smart_binary_scan": bool(smart_binaries),
        }
        base_payload = {"group": info, "articles": articles, "paging": paging, "elapsed_ms": round((time.perf_counter() - started) * 1000), "cache_source": "provider", "cache_age_seconds": 0, "smart_binary_headers": max(0, (fetch_end - fetch_start + 1) if smart_binaries and fetch_end and fetch_start else 0), "smart_binary_pending": bool(background_smart)}
        with ARTICLE_PAGE_CACHE_LOCK:
            ARTICLE_PAGE_CACHE[cache_key] = {"cached_at": time.time(), "payload": base_payload}
            _trim_article_page_cache_locked()
        if background_smart:
            SMART_BROWSE_EXECUTOR.submit(_finish_progressive_smart_page, provider_id, provider, group, cache_key, info, low, high, page, page_count, limit, start_num, end_num, background_smart[0], background_smart[1])
        payload = dict(base_payload)
        visible_articles = annotate_cached_thumbnail_urls(provider_id, group, articles)
        if media_only:
            visible_articles = [a for a in visible_articles if a.get("media")]
        payload["articles"] = visible_articles
        return self._json(200, payload)

    def article_name_resolution_api(self, data: dict[str, Any]):
        provider_id = str(data.get("provider_id", ""))
        group = str(data.get("group", "")).strip()
        items = data.get("items") or []
        if not provider_id or not group:
            raise ValueError("Provider and newsgroup are required")
        if not isinstance(items, list):
            raise ValueError("Invalid name-resolution request")
        result = resolve_article_names(provider_id, group, items)
        if result.get("resolved"):
            # Header pages are cheap to reload and must not keep an older grouped
            # snapshot after the persistent name cache learns real filenames.
            with ARTICLE_PAGE_CACHE_LOCK:
                stale = [key for key in ARTICLE_PAGE_CACHE if len(key) >= 2 and key[0] == provider_id and key[1] == group]
                for key in stale:
                    ARTICLE_PAGE_CACHE.pop(key, None)
        return self._json(200, result)

    def group_search_start_api(self, data: dict[str, Any]):
        result = GROUP_SEARCH_MANAGER.start(
            str(data.get("provider_id", "")),
            str(data.get("group", "")),
            str(data.get("query", "")),
            data.get("filters") if isinstance(data.get("filters"), dict) else {},
        )
        return self._json(200, {"search": result})

    def group_search_status_api(self, data: dict[str, Any]):
        return self._json(200, {"search": GROUP_SEARCH_MANAGER.status(str(data.get("id", "")))})

    def group_search_results_api(self, data: dict[str, Any]):
        result = GROUP_SEARCH_MANAGER.results(
            str(data.get("id", "")),
            int(data.get("page", 1) or 1),
            int(data.get("page_size", DEFAULT_ARTICLE_LIMIT) or DEFAULT_ARTICLE_LIMIT),
        )
        return self._json(200, result)

    def group_search_cancel_api(self, data: dict[str, Any]):
        return self._json(200, {"search": GROUP_SEARCH_MANAGER.cancel(str(data.get("id", "")))})

    def preview_api(self, data: dict[str, Any]):
        origin_provider_id = str(data.get("provider_id", ""))
        provider = resolve_provider_for_purpose(origin_provider_id, "previews")
        group = str(data.get("group", "")).strip()
        browse_session = str(data.get("browse_session", "")).strip()
        cancel_check = browse_session_cancel_check(origin_provider_id, group, browse_session)
        if cancel_check is not None:
            cancel_check()
        segments = data.get("segments") or []
        if str(provider.get("id", "")) != origin_provider_id:
            segments = [{**seg, "article": None} for seg in segments if isinstance(seg, dict)]
        media = data.get("media")
        if not group:
            raise ValueError("Newsgroup is required")
        if not isinstance(segments, list) or not isinstance(media, dict):
            raise ValueError("Invalid preview request")
        filename = media.get("filename") or f"preview.{media.get('extension', 'bin')}"
        filename = re.sub(r"[^A-Za-z0-9._ -]+", "_", filename).strip() or "preview.bin"
        full_token = preview_cache_token(provider, group, segments, media)
        cached = cached_preview_result(full_token, filename, media)
        if cached:
            return self._json(200, cached)
        settings = json_read(SETTINGS_FILE, {"preview_limit_mb": DEFAULT_PREVIEW_LIMIT_MB})
        max_mb = max(10, min(4096, int(settings.get("preview_limit_mb", DEFAULT_PREVIEW_LIMIT_MB))))
        try:
            result = run_preview_task(prepare_preview, provider, group, segments, media, max_mb, cancel_check)
        except Exception as exc:
            return self._json(422, preview_error_info(exc))
        return self._json(200, result)

    def image_thumbnail_api(self, data: dict[str, Any]):
        origin_provider_id = str(data.get("provider_id", ""))
        provider = resolve_provider_for_purpose(origin_provider_id, "previews")
        group = str(data.get("group", "")).strip()
        browse_session = str(data.get("browse_session", "")).strip()
        cancel_check = browse_session_cancel_check(origin_provider_id, group, browse_session)
        if cancel_check is not None:
            cancel_check()
        segments = data.get("segments") or []
        if str(provider.get("id", "")) != origin_provider_id:
            segments = [{**seg, "article": None} for seg in segments if isinstance(seg, dict)]
        media = data.get("media")
        if not group:
            raise ValueError("Newsgroup is required")
        if not isinstance(segments, list) or not isinstance(media, dict):
            raise ValueError("Invalid image thumbnail request")
        thumb_token = thumbnail_cache_token(provider, group, segments, media)
        cached = None if thumbnail_prefers_full_preview(thumb_token) else cached_thumbnail_result(thumb_token)
        if cached:
            return self._json(200, {"kind": "image", "filename": media.get("filename") or "image", **cached})
        settings = json_read(SETTINGS_FILE, {"preview_limit_mb": DEFAULT_PREVIEW_LIMIT_MB})
        max_mb = max(10, min(4096, int(settings.get("preview_limit_mb", DEFAULT_PREVIEW_LIMIT_MB))))
        requested_lanes = max(1, min(3, int(data.get("thumbnail_lanes", 1) or 1)))
        configured_connections = max(1, int(provider.get("connections", 20) or 20))
        lane_cap = 1 if configured_connections < 16 else (2 if configured_connections < 32 else 3)
        parallel_lanes = min(requested_lanes, lane_cap)
        try:
            result = run_preview_task(prepare_image_thumbnail, provider, group, segments, media, max_mb, cancel_check, parallel_lanes)
        except Exception as exc:
            return self._json(422, preview_error_info(exc))
        return self._json(200, result)

    def video_thumbnail_api(self, data: dict[str, Any]):
        origin_provider_id = str(data.get("provider_id", ""))
        provider = resolve_provider_for_purpose(origin_provider_id, "previews")
        group = str(data.get("group", "")).strip()
        browse_session = str(data.get("browse_session", "")).strip()
        cancel_check = browse_session_cancel_check(origin_provider_id, group, browse_session)
        if cancel_check is not None:
            cancel_check()
        segments = data.get("segments") or []
        if str(provider.get("id", "")) != origin_provider_id:
            segments = [{**seg, "article": None} for seg in segments if isinstance(seg, dict)]
        media = data.get("media")
        if not group:
            raise ValueError("Newsgroup is required")
        if not isinstance(segments, list) or not isinstance(media, dict):
            raise ValueError("Invalid video thumbnail request")
        thumb_token = thumbnail_cache_token(provider, group, segments, media)
        cached = cached_thumbnail_result(thumb_token)
        if cached:
            filename = media.get("filename") or "video"
            ext = str(media.get("extension") or Path(str(filename)).suffix.lstrip(".")).casefold()
            return self._json(200, {
                "kind": "video", "filename": filename, "sample_url": "",
                "thumbnail_url": cached["thumbnail_url"], "thumbnail_token": thumb_token,
                "browser_supported": ext in {"mp4", "m4v", "webm", "mov"},
                "partial": False, "cached": True, "method": "persistent-cache",
            })
        try:
            result = run_preview_task(prepare_video_thumbnail, provider, group, segments, media, cancel_check)
        except Exception as exc:
            return self._json(422, preview_error_info(exc))
        return self._json(200, result)

    def thumbnail_store_api(self, data: dict[str, Any]):
        return self._json(200, store_thumbnail_data(str(data.get("token", "")), str(data.get("data_url", ""))))

    def thumbnail_invalidate_api(self, data: dict[str, Any]):
        token = str(data.get("token", "")).strip().lower()
        if not re.fullmatch(r"[0-9a-f]{32}", token):
            raise ValueError("Invalid thumbnail token")
        removed = False
        visual_blank = bool(data.get("visual_blank"))
        try:
            path = thumbnail_cache_path(token)
            removed = path.exists()
            path.unlink(missing_ok=True)
            marker = thumbnail_full_fallback_path(token)
            small_marker = thumbnail_small_marker_path(token)
            small_marker.unlink(missing_ok=True)
            if visual_blank:
                marker.write_text("full-preview\n", encoding="utf-8")
            elif bool(data.get("clear_fallback")):
                marker.unlink(missing_ok=True)
        except OSError:
            pass
        _thumbnail_catalog_remove(token)
        if visual_blank:
            _thumbnail_catalog_register_full(token, True)
        if removed:
            _mark_thumbnail_stats_dirty()
        return self._json(200, {"ok": True, "removed": removed, "token": token, "visual_blank": visual_blank})

    def cache_clear_api(self, data: dict[str, Any]):
        removed = 0
        for pattern in ("*.jpg", "*.full", "*.small.json"):
            for path in THUMB_CACHE_DIR.glob(pattern):
                try:
                    path.unlink(missing_ok=True)
                    removed += 1
                except OSError:
                    pass
        _thumbnail_catalog_clear()
        _mark_thumbnail_stats_dirty()
        return self._json(200, {"ok": True, "removed": removed, **thumbnail_cache_stats(force=True)})

    def preview_cache_clear_api(self, data: dict[str, Any]):
        removed = 0
        removed_bytes = 0
        errors = 0
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            for path in list(CACHE_DIR.iterdir()):
                try:
                    if path.is_file() or path.is_symlink():
                        try:
                            removed_bytes += int(path.stat().st_size)
                        except OSError:
                            pass
                        path.unlink(missing_ok=True)
                        removed += 1
                except OSError:
                    errors += 1
        except OSError:
            errors += 1
        return self._json(200, {
            "ok": errors == 0,
            "removed": removed,
            "removed_bytes": removed_bytes,
            "errors": errors,
            "folder": str(CACHE_DIR),
        })

    def downloads_add_api(self, data: dict[str, Any]):
        provider_id = str(data.get("provider_id", ""))
        group = str(data.get("group", "")).strip()
        items = data.get("items") or []
        if not isinstance(items, list):
            raise ValueError("Invalid download selection")
        return self._json(200, DOWNLOAD_MANAGER.add(provider_id, group, items))

    def nzb_inspect_upload_api(self):
        provider_id = urllib.parse.unquote(self.headers.get("X-Provider-ID", "")).strip()
        if not provider_id:
            raise ValueError("Choose a provider before importing an NZB")
        provider_by_id(provider_id)
        name = safe_download_name(urllib.parse.unquote(self.headers.get("X-Filename", "Imported.nzb")) or "Imported.nzb")
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 100 * 1024 * 1024:
            raise ValueError("NZB file must be between 1 byte and 100 MB")
        raw = self.rfile.read(length)
        parsed = parse_nzb_bytes(raw, name)
        parsed["source_name"] = name
        token = _nzb_inspect_store(parsed, name)
        files = []
        total_bytes = 0
        total_segments = 0
        groups: set[str] = set()
        for i, entry in enumerate(parsed.get("files") or []):
            size = max(0, int(entry.get("bytes", 0) or 0)); segs = len(entry.get("segments") or [])
            total_bytes += size; total_segments += segs
            for g in entry.get("groups") or ([entry.get("group")] if entry.get("group") else []):
                if g: groups.add(str(g))
            media = entry.get("media") or {}
            filename = str(media.get("filename") or f"File {i+1}")
            ext = str(media.get("extension") or Path(filename).suffix.lstrip('.')).casefold()
            is_par2_volume = bool(entry.get("is_par2_volume"))
            is_auxiliary = bool(entry.get("is_auxiliary") or nzb_auxiliary_file(filename))
            default_selected = (not is_auxiliary and not is_par2_volume)
            files.append({"index": i, "filename": filename, "bytes": size, "segments": segs,
                          "group": str(entry.get("group") or ""), "kind": str(media.get("kind") or "file"),
                          "default_selected": default_selected,
                          "recovery_blocks": max(0, int(entry.get("par2_recovery_blocks", 0) or 0)),
                          "role": ("recovery_par2" if is_par2_volume else "par2" if ext == "par2" else "auxiliary" if is_auxiliary else "payload")})
        return self._json(200, {"ok": True, "token": token, "name": parsed.get("name") or Path(name).stem,
                                "source_name": name, "files": files, "file_count": len(files),
                                "total_bytes": total_bytes, "total_segments": total_segments,
                                "groups": sorted(groups)[:50]})

    def nzb_import_selection_api(self, data: dict[str, Any]):
        provider_id = str(data.get("provider_id") or "").strip()
        if not provider_id:
            raise ValueError("Choose a provider before importing an NZB")
        provider_by_id(provider_id)
        token = str(data.get("token") or "").strip()
        item = _nzb_inspect_get(token, consume=True)
        selected_raw = data.get("selected")
        selected = [int(x) for x in selected_raw if str(x).isdigit()] if isinstance(selected_raw, list) else None
        collection_name = str(data.get("collection_name") or item["parsed"].get("name") or "Imported NZB").strip()
        return self._json(200, DOWNLOAD_MANAGER.add_nzb_selection(provider_id, item["parsed"], selected, collection_name))

    def nzb_import_upload_api(self):
        provider_id = urllib.parse.unquote(self.headers.get("X-Provider-ID", "")).strip()
        if not provider_id:
            raise ValueError("Choose a provider before importing an NZB")
        name = safe_download_name(urllib.parse.unquote(self.headers.get("X-Filename", "Imported.nzb")) or "Imported.nzb")
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 100 * 1024 * 1024:
            raise ValueError("NZB file must be between 1 byte and 100 MB")
        raw = self.rfile.read(length)
        return self._json(200, DOWNLOAD_MANAGER.add_nzb(provider_id, name, raw))

    def downloads_control_api(self, data: dict[str, Any]):
        action = str(data.get("action", "")).strip()
        job_id = str(data.get("id", "")).strip()
        ids = data.get("ids") if isinstance(data.get("ids"), list) else None
        return self._json(200, DOWNLOAD_MANAGER.control(action, job_id, data.get("value"), ids))

    def service_install_api(self, data: dict[str, Any]):
        if sys.platform != 'win32':
            raise ValueError('Background service installation is only available on Windows')
        if SERVICE_MODE:
            return self._json(200, {**service_status_snapshot(), 'already_running': True})

        # A queued or retry-wait item is safe to hand over as long as no worker is
        # actively transferring/post-processing.  Older builds blocked installation
        # merely because a queue existed, making the Install button appear broken.
        snap = DOWNLOAD_MANAGER.snapshot(); counts = snap.get('counts') or {}
        active = sum(int(counts.get(k, 0) or 0) for k in ('downloading','cancelling')) + int(snap.get('post_processing_active',0) or 0)
        if active:
            raise ValueError('Pause or finish the active download/post-processing job before switching NewzDeck to background-service mode.')
        originally_paused = bool(snap.get('paused'))
        handoff_paused = False
        queued = sum(int(counts.get(k, 0) or 0) for k in ('queued','retry_wait'))
        if queued and not originally_paused:
            DOWNLOAD_MANAGER.control('pause_all')
            handoff_paused = True

        try:
            migrated = migrate_provider_secrets_machine_scope()
            try: migrated += MEDIA_AUTOMATION.migrate_secrets_machine_scope()
            except Exception: pass
            _set_tray_autostart(True)
            # Repair is deliberately accepted here too: a stale/partial service
            # registration from an interrupted upgrade should not strand the user.
            helper_action = 'repair' if _service_query_status() != 'not_installed' else 'install'
            _run_service_helper(helper_action, elevated=True, wait=True, timeout=70)
            # v3.5.33 service "repair" intentionally preserves a stopped service so
            # installer upgrades do not enable background mode behind the user's back.
            # The explicit Install Background Service action, however, means take
            # ownership now; start an existing repaired registration here.
            if helper_action == 'repair':
                _run_service_helper('start', elevated=True, wait=True, timeout=40)
            deadline = time.monotonic() + 45.0
            service_url = ''
            stable_health = 0
            while time.monotonic() < deadline:
                status = _service_query_status()
                try:
                    port = int((USER_ROOT / 'newzdeck.port').read_text(encoding='utf-8').strip())
                except Exception:
                    port = 0
                if status == 'running' and port:
                    try:
                        import urllib.request
                        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=1.5) as resp:
                            health = json.loads(resp.read().decode('utf-8'))
                        if health.get('service_mode'):
                            stable_health += 1
                            service_url = f'http://127.0.0.1:{port}'
                            if stable_health >= 3:
                                break
                        else:
                            stable_health = 0
                    except Exception:
                        stable_health = 0
                time.sleep(0.5)
            status = service_status_snapshot()
            if not service_url or stable_health < 3:
                detail = str(status.get('worker_detail') or '').strip()
                suffix = f' {detail}' if detail else ''
                if status.get('status') == 'not_installed':
                    raise ValueError('The Windows service was not installed. The UAC prompt may have been cancelled.')
                raise ValueError('The background service was installed but did not remain healthy long enough to take ownership.' + suffix)

            # Relinquish the desktop queue before the service is allowed to resume it.
            # This prevents two schedulers from touching the same persisted queue.
            DOWNLOAD_MANAGER.stop()
            if handoff_paused:
                try:
                    req = urllib.request.Request(service_url + '/api/downloads/control',
                        data=json.dumps({'action':'resume_all'}).encode('utf-8'),
                        headers={'Content-Type':'application/json'}, method='POST')
                    with urllib.request.urlopen(req, timeout=4.0) as resp:
                        resp.read(1024)
                except Exception as exc:
                    DIAGNOSTICS.event('warning','service',f'Service queue handoff completed but automatic resume failed: {exc}')
            try:
                _launch_tray()
            except Exception:
                pass
            return self._json(200, {**service_status_snapshot(), 'ok': True, 'migrated_credentials': migrated, 'service_url': service_url, 'switch_required': True})
        except Exception:
            if handoff_paused:
                try: DOWNLOAD_MANAGER.control('resume_all')
                except Exception: pass
            raise

    def service_control_api(self, data: dict[str, Any]):
        action = str(data.get('action') or '').strip().lower()
        if sys.platform != 'win32':
            raise ValueError('Background service controls are only available on Windows')
        if action == 'launch_tray':
            _ensure_tray_running()
            if not SERVICE_MODE:
                _set_tray_autostart(True)
            return self._json(200, service_status_snapshot())
        if action == 'tray_autostart':
            desired = bool(data.get('enabled'))
            if SERVICE_MODE:
                _ensure_tray_running()
                tray_helper_request('set_autostart', enabled=desired, timeout=10)
            else:
                _set_tray_autostart(desired)
                if desired: _launch_tray()
            return self._json(200, service_status_snapshot())
        if action in {'restart','remove','repair','stop','start'}:
            helper_action = {'remove':'uninstall'}.get(action, action)
            if action == 'repair':
                migrate_provider_secrets_machine_scope()
                try: MEDIA_AUTOMATION.migrate_secrets_machine_scope()
                except Exception: pass
            if SERVICE_MODE and action in {'stop','restart','remove'}:

                _run_service_helper(helper_action, elevated=False, wait=False, delay_ms=2500)
                return self._json(200, {**service_status_snapshot(), 'control_scheduled': True})
            if SERVICE_MODE:
                _run_service_helper(helper_action, elevated=False, wait=True)
            else:
                _run_service_helper(helper_action, elevated=True, wait=True)
            snap = service_status_snapshot()
            if action == 'start':
                deadline = time.monotonic() + 35
                while time.monotonic() < deadline and not snap.get('service_ready'):
                    time.sleep(0.5); snap = service_status_snapshot()
            return self._json(200, snap)
        raise ValueError('Unknown background service action')

    def choose_download_folder_api(self, data: dict[str, Any]):
        result = _native_folder_picker(str(DOWNLOAD_DIR), 'Choose where NewzDeck saves completed downloads')
        if result.get('cancelled'):
            return self._json(200, {'ok': True, 'cancelled': True, 'folder': str(DOWNLOAD_DIR)})
        path = str(result.get('folder') or '').strip()
        if not path:
            return self._json(200, {'ok': True, 'cancelled': True, 'folder': str(DOWNLOAD_DIR)})
        settings = json_read(SETTINGS_FILE, {})
        settings = settings if isinstance(settings, dict) else {}
        settings['download_folder'] = path
        return self.settings_api(settings)

    def choose_watch_folder_api(self, data: dict[str, Any]):
        current = json_read(SETTINGS_FILE, {})
        current = current if isinstance(current, dict) else {}
        initial_path = str(current.get('watch_folder') or DEFAULT_WATCH_FOLDER)
        result = _native_folder_picker(initial_path, 'Choose the NewzDeck NZB watch folder')
        if result.get('cancelled'):
            return self._json(200, {'ok': True, 'cancelled': True, 'folder': initial_path})
        path = str(result.get('folder') or '').strip()
        if not path:
            return self._json(200, {'ok': True, 'cancelled': True, 'folder': initial_path})
        Path(path).mkdir(parents=True, exist_ok=True)
        current['watch_folder'] = path
        return self.settings_api(current)

    def _add_automation_root(self, kind: str, raw_path: str):
        kind = str(kind or '').strip().lower()
        if kind not in {'tv', 'movie'}:
            raise ValueError('Choose TV or Movie for this root folder.')
        path = str(raw_path or '').strip().strip('"')
        if not path:
            raise ValueError('Choose or enter a root folder path.')
        folder = Path(path)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f'Folder does not exist or is not accessible: {path}')
        normalized = os.path.normpath(str(folder))
        key = 'tv_roots' if kind == 'tv' else 'movie_roots'
        current = MEDIA_AUTOMATION.public_config()
        roots = [str(x or '').strip() for x in current.get(key) or [] if str(x or '').strip()]
        added = False
        if not any(os.path.normcase(x) == os.path.normcase(normalized) for x in roots):
            roots.append(normalized)
            added = True
        config = MEDIA_AUTOMATION.save_config({key: roots})
        return {'ok': True, 'folder': normalized, 'added': added, 'config': config}

    def automation_add_root_api(self, data: dict[str, Any]):
        return self._json(200, self._add_automation_root(str(data.get('kind') or ''), str(data.get('path') or '')))

    def automation_choose_folder_api(self, data: dict[str, Any]):
        initial_path = str(data.get('initial') or '').strip()
        title = str(data.get('title') or 'Choose a NewzDeck media root folder').strip()
        kind = str(data.get('kind') or '').strip().lower()
        result = _native_folder_picker(initial_path, title)
        path = str(result.get('folder') or '').strip()
        cancelled = bool(result.get('cancelled')) or not bool(path)
        if cancelled:
            return self._json(200, {'ok': True, 'cancelled': True, 'folder': '', 'added': False})
        saved = self._add_automation_root(kind, path)
        return self._json(200, {'ok': True, 'cancelled': False, **saved})

    def config_backup_api(self):
        backup = {'format':'NewzDeckConfigBackup', 'version':APP_VERSION, 'created':datetime.now().isoformat(timespec='seconds'), 'settings':json_read(SETTINGS_FILE, {}), 'providers':json_read(PROVIDERS_FILE, []), 'saved_searches':json_read(SAVED_SEARCHES_FILE, []), 'media_automation': {'library': MEDIA_AUTOMATION._library(), 'config': MEDIA_AUTOMATION._config(), 'indexers': MEDIA_AUTOMATION._indexers(), 'profiles': MEDIA_AUTOMATION._profiles()}}
        raw = json.dumps(backup, indent=2, ensure_ascii=False).encode('utf-8')
        name = f"NewzDeck-Config-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Disposition',f'attachment; filename="{name}"'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def config_restore_api(self, data: dict[str, Any]):
        if not isinstance(data, dict) or data.get('format') != 'NewzDeckConfigBackup':
            raise ValueError('This is not a NewzDeck configuration backup')
        settings = data.get('settings'); providers = data.get('providers'); searches = data.get('saved_searches')
        if not isinstance(settings, dict) or not isinstance(providers, list):
            raise ValueError('The configuration backup is incomplete')
        json_write(PROVIDERS_FILE, providers)
        if isinstance(searches, list): json_write(SAVED_SEARCHES_FILE, searches)
        media_auto = data.get('media_automation')
        if isinstance(media_auto, dict):
            if isinstance(media_auto.get('library'), list): json_write(MEDIA_AUTOMATION.library_file, media_auto['library'])
            if isinstance(media_auto.get('config'), dict): json_write(MEDIA_AUTOMATION.config_file, media_auto['config'])
            if isinstance(media_auto.get('indexers'), list): json_write(MEDIA_AUTOMATION.indexers_file, media_auto['indexers'])
            if isinstance(media_auto.get('profiles'), list): json_write(MEDIA_AUTOMATION.profiles_file, media_auto['profiles'])
        return self.settings_api(settings)

    def downloads_open_folder_api(self, data: dict[str, Any]):
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32" and SERVICE_MODE:
            tray_helper_request('open_path', path=str(DOWNLOAD_DIR), timeout=10)
        elif sys.platform == "win32":
            os.startfile(str(DOWNLOAD_DIR))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(DOWNLOAD_DIR)])
        else:
            subprocess.Popen(["xdg-open", str(DOWNLOAD_DIR)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self._json(200, {"ok": True, "folder": str(DOWNLOAD_DIR)})

    def download_items_api(self, data: dict[str, Any]):
        provider = provider_by_id(str(data.get("provider_id", "")))
        group = str(data.get("group", "")).strip()
        items = data.get("items") or []
        if not group:
            raise ValueError("Newsgroup is required")
        if not isinstance(items, list) or not items:
            raise ValueError("Select at least one media item")
        if len(items) > 50:
            raise ValueError("Download up to 50 items at a time")
        settings = json_read(SETTINGS_FILE, {"preview_limit_mb": DEFAULT_PREVIEW_LIMIT_MB})
        max_mb = max(10, min(4096, int(settings.get("preview_limit_mb", DEFAULT_PREVIEW_LIMIT_MB))))
        saved = []
        errors = []
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        for item in items:
            try:
                segments = item.get("segments") or []
                media = item.get("media") or {}
                result = run_preview_task(prepare_preview, provider, group, segments, media, max_mb, cancel_check)
                source = Path(_preview_tokens[result["token"]]["path"])
                name = re.sub(r"[^A-Za-z0-9._ -]+", "_", result["filename"]).strip() or source.name
                dest = DOWNLOAD_DIR / name
                stem, suffix = dest.stem, dest.suffix
                n = 2
                while dest.exists() and dest.stat().st_size != source.stat().st_size:
                    dest = DOWNLOAD_DIR / f"{stem} ({n}){suffix}"
                    n += 1
                if not dest.exists():
                    shutil.copy2(source, dest)
                saved.append({"filename": dest.name, "path": str(dest), "size": dest.stat().st_size})
            except Exception as exc:
                errors.append({"filename": (item.get("media") or {}).get("filename", "Unknown"), "error": str(exc)})
        return self._json(200, {"saved": saved, "errors": errors, "folder": str(DOWNLOAD_DIR)})

    def app_open_data_api(self, data: dict[str, Any]):
        USER_ROOT.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32" and SERVICE_MODE:
            tray_helper_request('open_path', path=str(USER_ROOT), timeout=10)
        elif sys.platform == "win32":
            os.startfile(str(USER_ROOT))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(USER_ROOT)])
        else:
            subprocess.Popen(["xdg-open", str(USER_ROOT)])
        return self._json(200, {"ok": True, "path": str(USER_ROOT)})

    def online_update_install_api(self):
        result = download_verified_online_update()
        if result.get("update_available"):
            staged = Path(str(result.get("path") or ""))
            if not staged.exists():
                raise ValueError("The verified update installer could not be staged")
            _schedule_update_handoff(staged, target_version=str(result.get("version") or APP_VERSION), server_obj=self.server)
            result = {**result, "handoff": True, "message": f"NewzDeck v{result.get('version')} verified. NewzDeck will close, update, restore its background runtime, and reopen automatically."}
        return self._json(200, result)

    def update_install_api(self):
        """Accept a user-selected NewzDeck Setup EXE and hand off to it.

        This intentionally does not download arbitrary software from the internet.
        The user selects the update package locally, the package is copied into the
        version-independent update staging folder, then started after this response.
        """
        if sys.platform != "win32":
            raise ValueError("In-app package installation is currently available on Windows only")
        filename = Path(urllib.parse.unquote(self.headers.get("X-Filename", ""))).name
        low_name = filename.lower()
        valid_setup_name = (low_name.startswith("newzdeck") or low_name.startswith("usenetbrowser")) and "setup" in low_name and low_name.endswith(".exe")
        if not valid_setup_name:
            raise ValueError("Select a NewzDeck Setup.exe update package")
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0 or length > 150 * 1024 * 1024:
            raise ValueError("Update package is empty or too large")
        raw = self.rfile.read(length)
        if len(raw) != length or raw[:2] != b"MZ":
            raise ValueError("The selected file is not a valid Windows executable package")
        UPDATE_DIR.mkdir(parents=True, exist_ok=True)
        staged = UPDATE_DIR / f"NewzDeckSetup-{int(time.time())}.exe"
        staged.write_bytes(raw)
        _schedule_update_handoff(staged, target_version="", server_obj=self.server)
        return self._json(200, {"ok": True, "handoff": True, "message": "Update verified. NewzDeck will close, update, restore its background runtime, and reopen automatically."})

    def settings_api(self, data: dict[str, Any]):
        global DOWNLOAD_DIR
        current = json_read(SETTINGS_FILE, {})
        if not isinstance(current, dict):
            current = {}
        merged = {**current, **data}
        thumb_size = str(merged.get("thumbnail_size", DEFAULT_THUMBNAIL_SIZE)).lower()
        if thumb_size not in {"small", "medium", "large", "xlarge"}:
            thumb_size = DEFAULT_THUMBNAIL_SIZE
        view_mode = str(merged.get("view_mode", DEFAULT_VIEW_MODE)).lower()
        if view_mode not in {"gallery", "list"}:
            view_mode = DEFAULT_VIEW_MODE
        content_filter = str(merged.get("content_filter", DEFAULT_CONTENT_FILTER)).lower()
        if content_filter not in {"images", "videos", "media", "all"}:
            content_filter = DEFAULT_CONTENT_FILTER
        download_organization = str(merged.get("download_organization", DEFAULT_DOWNLOAD_ORGANIZATION)).lower()
        if download_organization not in {"flat", "newsgroup", "kind", "newsgroup_kind"}:
            download_organization = DEFAULT_DOWNLOAD_ORGANIZATION
        raw_favorites = sorted({str(x).strip() for x in (merged.get("favorites") or []) if str(x).strip()})[:500]
        bookmark_folders = []
        seen_folder_ids = set()
        for item in (merged.get("bookmark_folders") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()[:80]
            if not name:
                continue
            folder_id = re.sub(r"[^A-Za-z0-9_-]+", "-", str(item.get("id") or "").strip())[:80]
            if not folder_id or folder_id in seen_folder_ids:
                folder_id = f"folder-{len(bookmark_folders)+1}"
                while folder_id in seen_folder_ids:
                    folder_id += "x"
            seen_folder_ids.add(folder_id)
            groups = []
            seen_groups = set()
            for value in (item.get("groups") or []):
                group = str(value).strip()[:300]
                if group and group not in seen_groups:
                    groups.append(group)
                    seen_groups.add(group)
                    if len(groups) >= 500:
                        break
            bookmark_folders.append({"id": folder_id, "name": name, "groups": groups, "collapsed": bool(item.get("collapsed", False))})
            if len(bookmark_folders) >= 50:
                break
        folder_groups = {group for folder in bookmark_folders for group in folder.get("groups", [])}
        raw_favorites = sorted(set(raw_favorites) | folder_groups)[:500]
        group_read_states = {}
        raw_read_states = merged.get("group_read_states") if isinstance(merged.get("group_read_states"), dict) else {}
        read_items = sorted(raw_read_states.items(), key=lambda kv: float((kv[1] or {}).get("updated_ts", 0) if isinstance(kv[1], dict) else 0), reverse=True)[:100]
        for key, item in read_items:
            if not isinstance(item, dict):
                continue
            safe_key = str(key)[:650]
            seen_articles = []
            for value in item.get("seen_articles", []) if isinstance(item.get("seen_articles"), list) else []:
                try:
                    number = int(value)
                except (TypeError, ValueError):
                    continue
                if number > 0:
                    seen_articles.append(number)
            seen_through = max(0, int(item.get("seen_through", 0) or 0))
            seen_articles = sorted({n for n in seen_articles if n > seen_through})[-1500:]
            unseen_articles = []
            for value in item.get("unseen_articles", []) if isinstance(item.get("unseen_articles"), list) else []:
                try:
                    number = int(value)
                except (TypeError, ValueError):
                    continue
                if 0 < number <= seen_through:
                    unseen_articles.append(number)
            unseen_articles = sorted(set(unseen_articles))[-750:]
            group_read_states[safe_key] = {
                "seen_through": seen_through,
                "seen_articles": seen_articles,
                "unseen_articles": unseen_articles,
                "acknowledged_high": max(0, int(item.get("acknowledged_high", 0) or 0)),
                "updated_ts": max(0, int(float(item.get("updated_ts", 0) or 0))),
            }
        settings = {
            "article_limit": max(25, min(2000, int(merged.get("article_limit", DEFAULT_ARTICLE_LIMIT)))),
            "preview_limit_mb": max(10, min(4096, int(merged.get("preview_limit_mb", DEFAULT_PREVIEW_LIMIT_MB)))),
            "thumbnail_cache_gb": max(0.25, min(20.0, float(merged.get("thumbnail_cache_gb", DEFAULT_THUMB_CACHE_GB)))),
            "concurrent_downloads": PACKAGE_QUEUE_CONCURRENCY,
            "thumbnail_size": thumb_size,
            "continuous_browse": bool(merged.get("continuous_browse", DEFAULT_CONTINUOUS_BROWSE)),
            "view_mode": view_mode,
            "content_filter": content_filter,
            "download_organization": download_organization,
            "download_folder": str(merged.get("download_folder") or DOWNLOAD_DIR),
            "group_related_media": bool(merged.get("group_related_media", DEFAULT_GROUP_RELATED_MEDIA)),
            "group_binary_sets": bool(merged.get("group_binary_sets", DEFAULT_GROUP_BINARY_SETS)),
            "binary_min_size_value": max(0.0, min(1000000.0, float(merged.get("binary_min_size_value", 0.0) or 0.0))),
            "binary_min_size_unit": str(merged.get("binary_min_size_unit") or "MB").upper() if str(merged.get("binary_min_size_unit") or "MB").upper() in {"MB", "GB"} else "MB",
            "favorites": raw_favorites,
            "bookmark_folders": bookmark_folders,
            "recent_groups": [str(x).strip() for x in (merged.get("recent_groups") or []) if str(x).strip()][:20],
            "group_states": dict(list((merged.get("group_states") or {}).items())[-100:]) if isinstance(merged.get("group_states"), dict) else {},
            "blocked_posters": sorted({str(x).strip() for x in (merged.get("blocked_posters") or []) if str(x).strip()})[:500],
            "group_seen_high": dict(list((merged.get("group_seen_high") or {}).items())[-500:]) if isinstance(merged.get("group_seen_high"), dict) else {},
            "group_read_states": group_read_states,
            "browser_tabs": [dict(x) for x in (merged.get("browser_tabs") or []) if isinstance(x, dict)][:20],
            "active_browser_tab": str(merged.get("active_browser_tab") or "")[:80],
            "disk_reserve_gb": max(0.25, min(50.0, float(merged.get("disk_reserve_gb", 1.0) or 1.0))),
            "post_processing": bool(merged.get("post_processing", DEFAULT_POST_PROCESSING)),
            "auto_repair": bool(merged.get("auto_repair", DEFAULT_AUTO_REPAIR)),
            "auto_fetch_par2": bool(merged.get("auto_fetch_par2", DEFAULT_AUTO_FETCH_PAR2)),
            "auto_extract": bool(merged.get("auto_extract", DEFAULT_AUTO_EXTRACT)),
            "cleanup_archives": bool(merged.get("cleanup_archives", DEFAULT_CLEANUP_ARCHIVES)),
            "extract_subfolder": bool(merged.get("extract_subfolder", DEFAULT_EXTRACT_SUBFOLDER)),
            "direct_unpack_mode": str(merged.get("direct_unpack_mode", DEFAULT_DIRECT_UNPACK_MODE) or DEFAULT_DIRECT_UNPACK_MODE).casefold() if str(merged.get("direct_unpack_mode", DEFAULT_DIRECT_UNPACK_MODE) or DEFAULT_DIRECT_UNPACK_MODE).casefold() in {"off","auto","on"} else DEFAULT_DIRECT_UNPACK_MODE,
            "automation_media_cleanup": bool(merged.get("automation_media_cleanup", DEFAULT_AUTOMATION_MEDIA_CLEANUP)),
            "watch_folder_enabled": bool(merged.get("watch_folder_enabled", DEFAULT_WATCH_FOLDER_ENABLED)),
            "watch_folder": str(merged.get("watch_folder") or DEFAULT_WATCH_FOLDER),
            "watch_provider_id": str(merged.get("watch_provider_id") or "")[:120],
            "watch_archive_processed": bool(merged.get("watch_archive_processed", DEFAULT_WATCH_ARCHIVE_PROCESSED)),
            "smart_categories_enabled": bool(merged.get("smart_categories_enabled", DEFAULT_SMART_CATEGORIES)),
            "category_movies_keywords": str(merged.get("category_movies_keywords") or "")[:800],
            "category_movies_folder": safe_folder_name(str(merged.get("category_movies_folder") or "Movies")),
            "category_tv_keywords": str(merged.get("category_tv_keywords") or "")[:800],
            "category_tv_folder": safe_folder_name(str(merged.get("category_tv_folder") or "TV")),
            "category_images_keywords": str(merged.get("category_images_keywords") or "")[:800],
            "category_images_folder": safe_folder_name(str(merged.get("category_images_folder") or "Images")),
            "category_other_folder": safe_folder_name(str(merged.get("category_other_folder") or "Other")),
            "bandwidth_schedule_enabled": bool(merged.get("bandwidth_schedule_enabled", DEFAULT_BANDWIDTH_SCHEDULE_ENABLED)),
            "bandwidth_schedule_start": str(merged.get("bandwidth_schedule_start") or DEFAULT_BANDWIDTH_SCHEDULE_START)[:5],
            "bandwidth_schedule_end": str(merged.get("bandwidth_schedule_end") or DEFAULT_BANDWIDTH_SCHEDULE_END)[:5],
            "bandwidth_schedule_limit_mb_s": max(0.1, min(5000.0, float(merged.get("bandwidth_schedule_limit_mb_s", DEFAULT_BANDWIDTH_SCHEDULE_LIMIT_MB_S) or DEFAULT_BANDWIDTH_SCHEDULE_LIMIT_MB_S))),
            "completion_notification": bool(merged.get("completion_notification", DEFAULT_COMPLETION_NOTIFICATION)),
            "completion_open_folder": bool(merged.get("completion_open_folder", DEFAULT_COMPLETION_OPEN_FOLDER)),
        }
        requested_folder = str(settings.get("download_folder") or "").strip()
        if requested_folder:
            candidate = Path(requested_folder).expanduser()
            candidate.mkdir(parents=True, exist_ok=True)
            if not candidate.is_dir():
                raise ValueError("Download folder is not a directory")
            DOWNLOAD_DIR = candidate
            settings["download_folder"] = str(candidate)
        else:
            DOWNLOAD_DIR = DEFAULT_DOWNLOAD_DIR
            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            settings["download_folder"] = str(DOWNLOAD_DIR)
        json_write(SETTINGS_FILE, settings)
        try:
            DOWNLOAD_MANAGER.request_sync()
        except Exception:
            pass
        return self._json(200, settings)

    def serve_thumbnail(self, token: str):
        if not re.fullmatch(r"[0-9a-f]{32}", token or ""):
            return self.send_error(404)
        path = thumbnail_cache_path(token)
        try:
            st = path.stat()
        except OSError:
            return self.send_error(404)
        if st.st_size <= 0:
            return self.send_error(404)
        now = time.time()
        if now - st.st_mtime > 6 * 3600:
            try:
                os.utime(path, (now, now))
            except OSError:
                pass
        size = st.st_size
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "private, max-age=2592000, immutable")
        self.end_headers()
        with path.open("rb") as f:
            shutil.copyfileobj(f, self.wfile, length=256 * 1024)

    def serve_media(self, token: str, attachment: bool = False):
        with _preview_lock:
            item = _preview_tokens.get(token)
        if not item:
            candidates = list(CACHE_DIR.glob(f"{token}.*"))
            candidates = [p for p in candidates if not p.name.endswith(".part")]
            if not candidates:
                return self.send_error(404)
            path = candidates[0]
            item = {"path": str(path), "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream"}
        path = Path(item["path"])
        if not path.exists():
            return self.send_error(404)
        size = path.stat().st_size
        range_header = self.headers.get("Range")
        start, end = 0, size - 1
        status = 200
        if range_header:
            m = re.match(r"bytes=(\d*)-(\d*)", range_header)
            if m:
                if m.group(1):
                    start = int(m.group(1))
                if m.group(2):
                    end = min(int(m.group(2)), size - 1)
                if not m.group(1) and m.group(2):
                    suffix = int(m.group(2))
                    start = max(0, size - suffix)
                    end = size - 1
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
                status = 206
        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", item.get("mime", "application/octet-stream"))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "private, max-age=3600")
        if attachment:
            safe_name = str(item.get("filename") or path.name).replace("\"", "")
            self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with path.open("rb") as f:
            f.seek(start)
            remaining = length
            while remaining:
                chunk = f.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

def find_available_port(start=DEFAULT_PORT, attempts=25):
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
                return port
            except OSError:
                continue
    raise OSError("Could not find an available local port")

def _desktop_lifecycle_monitor(httpd: ThreadingHTTPServer):
    # The UI may be slow to become interactive during runtime/bootstrap work. A
    # single missed heartbeat must never tear down an otherwise healthy local
    # backend.  A long scheduler gap is also treated as a likely sleep/resume
    # event so a suspended Chromium window gets time to renew its lease.
    startup_deadline = time.monotonic() + 10 * 60.0
    previous_check = time.monotonic()
    resume_grace_until = 0.0
    stale_checks = 0
    while True:
        time.sleep(3.0)
        now = time.monotonic()
        scheduler_gap = now - previous_check
        previous_check = now
        if scheduler_gap > 15.0:
            resume_grace_until = max(resume_grace_until, now + 30.0)
            startup_deadline = max(startup_deadline, now + 60.0)
            stale_checks = 0
            try:
                DIAGNOSTICS.event("info", "desktop-lifecycle", "Desktop resume/scheduling gap detected; lease grace applied", gap_seconds=round(scheduler_gap, 1))
            except Exception:
                pass

        last_heartbeat, saw_heartbeat = desktop_heartbeat_state()
        age = now - last_heartbeat
        if saw_heartbeat:
            if age > 90.0 and now >= resume_grace_until:
                stale_checks += 1
                if stale_checks >= 3:
                    threading.Thread(target=httpd.shutdown, daemon=True).start()
                    return
            else:
                stale_checks = 0
        elif now > startup_deadline and now >= resume_grace_until:
            threading.Thread(target=httpd.shutdown, daemon=True).start()
            return

def _deferred_backend_managers_start() -> None:
    # Give serve_forever a head start so /api/health and the desktop shell are
    # responsive before SAB identity/provider probes or queue reconciliation.
    time.sleep(0.35)
    try:
        starter = getattr(DOWNLOAD_MANAGER, "start_background_threads", None)
        if callable(starter):
            starter()
    except Exception as exc:
        DIAGNOSTICS.event("warning", "sab-engine", f"Deferred engine worker startup failed: {exc}")
    try:
        AUTOMATION_MANAGER.start()
    except Exception as exc:
        DIAGNOSTICS.event("warning", "automation", f"Deferred automation startup failed: {exc}")

def _deferred_preview_maintenance() -> None:
    # Full cache scans are disk housekeeping and can contend with CPython/module
    # startup on Windows. Keep them off the cold-launch critical path.
    time.sleep(12)
    try:
        cleanup_preview_cache(force=True)
    except Exception:
        pass

def _deferred_thumbnail_maintenance() -> None:
    time.sleep(20)
    try:
        cleanup_thumbnail_cache(force=True)
        thumbnail_cache_stats(force=True)
    except Exception:
        pass

def main():
    preferred_port = int(os.environ.get('NEWZDECK_PORT', str(DEFAULT_PORT)) or DEFAULT_PORT)
    port = find_available_port(start=max(1, min(65510, preferred_port)))
    url = f"http://{HOST}:{port}"
    httpd = ThreadingHTTPServer((HOST, port), AppHandler)
    threading.Thread(target=_deferred_backend_managers_start, name="backend-managers-start", daemon=True).start()
    threading.Thread(target=_deferred_preview_maintenance, name="preview-maintenance", daemon=True).start()
    threading.Thread(target=_deferred_thumbnail_maintenance, name="thumbnail-maintenance", daemon=True).start()
    port_file = os.environ.get("NEWZDECK_PORT_FILE", os.environ.get("USENET_BROWSER_PORT_FILE", "")).strip()
    if port_file:
        try:
            Path(port_file).write_text(str(port), encoding="utf-8")
        except OSError:
            pass
    if DESKTOP_MODE:
        threading.Thread(target=_desktop_lifecycle_monitor, args=(httpd,), name="desktop-lifecycle", daemon=True).start()
    elif SERVICE_MODE and TRAY_AUTOSTART_FILE.exists():

        def _ensure_service_tray_after_start():
            deadline = time.monotonic() + 7.0
            while time.monotonic() < deadline:
                try:
                    if TRAY_HEARTBEAT_FILE.exists() and time.time() - TRAY_HEARTBEAT_FILE.stat().st_mtime <= 5:
                        return
                except OSError:
                    pass
                time.sleep(0.5)
            _launch_tray()
        threading.Timer(2.5, _ensure_service_tray_after_start).start()
    safe_print(f"\nNewzDeck v{APP_VERSION}" + (" [Background Service]" if SERVICE_MODE else ""))
    safe_print(f"Local app: {url}")
    safe_print("Press Ctrl+C to stop.\n")
    if os.environ.get("NEWZDECK_NO_OPEN", os.environ.get("USENET_BROWSER_NO_OPEN", "0")) != "1":
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        safe_print("\nStopping...")
    finally:
        DOWNLOAD_MANAGER.stop()
        httpd.server_close()
        if port_file:
            try:
                pf = Path(port_file)
                if pf.exists() and pf.read_text(encoding='utf-8').strip() == str(port):
                    pf.unlink(missing_ok=True)
            except OSError:
                pass

if __name__ == "__main__":
    main()
