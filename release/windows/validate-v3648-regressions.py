#!/usr/bin/env python3
"""NewzDeck v3.6.72 carried production guards, including v3.6.48 real-world regressions."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "app"
AUTOMATION_PATH = APP / "automation_engine.py"
SAB_PATH = APP / "sab_engine.py"
SERVER_PATH = APP / "server.py"
APP_JS_PATH = APP / "static" / "app.js"
INDEX_PATH = APP / "static" / "index.html"


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


auto = load_module("newzdeck_v3649_auto_guard", AUTOMATION_PATH)
sab = load_module("newzdeck_v3649_sab_guard", SAB_PATH)
match = auto._tv_release_identity_match

love_island = {
    "kind":"tv", "title":"Love Island", "library_title":"Love Island (UK)",
    "country_codes":["GB"], "title_ambiguous":True, "year":2015,
}
dark_matter = {
    "kind":"tv", "title":"Dark Matter", "library_title":"Dark Matter (US)",
    "country_codes":["US"], "title_ambiguous":True, "year":2024,
}
all_stars = {
    "kind":"tv", "title":"Love Island: All Stars", "library_title":"Love Island: All Stars",
    "country_codes":["GB"], "title_ambiguous":False, "year":2024,
}

# Exact historical false-positive releases retained in the 2026-09-07 production
# diagnostics. These are permanent negative fixtures: later episode-title words
# must never satisfy the series identity prefix.
PRODUCTION_REJECTS = [
    (dark_matter, "Dark.S02E02.Dark.Matter.2160p.NF.WEB-DL.DDP.5.1.HEVC-S0NiC"),
    (love_island, "Love.Island.The.Morning.After.S03E09.1080p.ITV.WEB-DL.AAC2.0.H.264-7VFr33104D"),
    (love_island, "The.Morning.Show.2019.S03E05.Love.Island.1080p.ATVP.WEB-DL.10bit.DDP5.1.Atmos.x265-YELLO"),
    (love_island, "The.Morning.Show.2019.S03E05.Love.Island.1080p.DS4K.ATVP.Webrip.x265.10bit.EAC3.5.1.Atmos.GokiTAoE"),
    (love_island, "Love.Island.The.Morning.After.S03E03.1080p.ITV.WEB-DL.AAC2.0.H.264-7VFr33104D"),
    (love_island, "The.Bradshaw.Bunch.S02E01.Love.Island.1080p.AMZN.WEB-DL.DDP2.0.H.264-NTb"),
    (love_island, "The.Bradshaw.Bunch.S02E01.Love.Island.PROPER.1080p.WEBRip.x264-KOMPOST"),
    (love_island, "Love.Island.Romania.S01E34.1080p.WEB-DL.AAC2.0.H.264-playWEB"),
    (love_island, "Love.Island.The.Debrief.S01E30.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E28.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E27.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E26.Episode.26.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E24.Episode.24.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E23.Episode.23.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E22.Episode.22.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E20.Episode.20.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E19.Episode.19.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E18.Episode.18.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E16.Episode.16.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E15.Episode.15.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E14.Episode.14.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E12.Episode.12.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E11.Episode.11.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E09.Episode.9.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E08.Episode.8.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Love.Island.The.Debrief.S01E06.Episode.6.1080p.AMZN.WEB-DL.DDP2.0.H.264-Kitsune"),
    (love_island, "Larva.Family.S01E05.Crazy.Love.Island.Ping-pong.EAC3.5.1.1080p.WEBRip.X265-iVy"),
    (love_island, "Love.Island.The.Debrief.S01E02.1080p.ITV.WEB-DL.AAC2.0.H.264-Pr1M371M3"),
    (love_island, "The.Curse.of.Love.Island.S01E01.1080p.AMZN.WEB-DL.DDP5.1.H.264-RAWR"),
]
for item, title in PRODUCTION_REJECTS:
    if match(title, item):
        raise SystemExit(f"Historical false positive became eligible again: {title}")
if match("Love.Island.All.Stars.The.Morning.After.S03E12.1080p.ITV.WEB-DL.AAC2.0.H.264-Pr1M371M3", all_stars):
    raise SystemExit("Love Island: All Stars companion-show identity regression returned.")
if not match("Love.Island.All.Stars.S03E12.1080p.ITV.WEB-DL.AAC2.0.H.264-GROUP", all_stars):
    raise SystemExit("Valid Love Island: All Stars episode no longer matches.")

class DummyDownloadManager:
    pass

# Library Integrity: preserve v3.6.48 duplicate semantics and prove v3.6.49 cache
# reuse/invalidation against persisted input signatures.
with tempfile.TemporaryDirectory(prefix="newzdeck-v3649-integrity-") as td:
    data_dir = pathlib.Path(td)
    separate_a = data_dir / "Show.S01E01.mkv"
    separate_b = data_dir / "Show.S01E02.mkv"
    shared = data_dir / "Show.S01E03-E04.mkv"
    for path in (separate_a, separate_b, shared):
        path.write_bytes(b"guard")
    library = [{
        "id":"guard-show", "kind":"tv", "title":"Show", "library_title":"Show", "monitored":True,
        "seasons":[{"season_number":1,"episodes":[
            {"episode_number":1,"has_file":True,"file_path":str(separate_a),"file_fingerprint":"same-episode-bytes"},
            {"episode_number":2,"has_file":True,"file_path":str(separate_b),"file_fingerprint":"same-episode-bytes"},
            {"episode_number":3,"has_file":True,"file_path":str(shared),"file_fingerprint":"shared-multi-episode"},
            {"episode_number":4,"has_file":True,"file_path":str(shared),"file_fingerprint":"shared-multi-episode"},
        ]}],
    }]
    (data_dir / "media-library.json").write_text(json.dumps(library), encoding="utf-8")
    engine = auto.MediaAutomationEngine(data_dir, lambda value:value, lambda value:value, DummyDownloadManager(), lambda:[], version="3.6.72")
    audit1 = engine.library_integrity_audit()
    audit2 = engine.library_integrity_audit()
    if audit1.get("cache_hit") or not audit2.get("cache_hit"):
        raise SystemExit(f"Library Integrity cache did not miss-then-hit: {audit1.get('cache_hit')} / {audit2.get('cache_hit')}")
    if int(audit1.get("same_title_cross_episode_duplicate_fingerprints") or 0) != 1:
        raise SystemExit(f"Same-title cross-episode duplicate was not isolated correctly: {audit1}")
    shared_rows = [x for x in audit1.get("duplicates") or [] if x.get("fingerprint") == "shared-multi-episode"]
    if not shared_rows or shared_rows[0].get("needs_review"):
        raise SystemExit("One shared multi-episode media path was incorrectly marked for review.")
    library[0]["seasons"][0]["episodes"][1]["file_fingerprint"] = "different-bytes"
    (data_dir / "media-library.json").write_text(json.dumps(library), encoding="utf-8")
    audit3 = engine.library_integrity_audit()
    if audit3.get("cache_hit") or int(audit3.get("same_title_cross_episode_duplicate_fingerprints") or 0) != 0:
        raise SystemExit("Library Integrity cache did not invalidate after persisted library mutation.")

    # Hot Automation runtime state must use compact JSON while preserving its model.
    engine._save_auto_runtime({"targets":{"tv:guard:s01e001":{"status":"waiting","updated_ts":9999999999,"last_candidates":[{"title":"A"}]}}})
    raw=(data_dir / "automation-runtime.json").read_text(encoding="utf-8")
    if "\n" in raw or ": " in raw:
        raise SystemExit("automation-runtime.json is still pretty-printed instead of compact hot-state JSON.")
    if json.loads(raw)["targets"]["tv:guard:s01e001"]["status"] != "waiting":
        raise SystemExit("Compact Automation runtime write changed data semantics.")


def make_sab(root: pathlib.Path, legacy: pathlib.Path | None = None):
    return sab.SabDownloadManager(
        user_root=root / "user", app_dir=root / "app",
        download_dir_getter=lambda: root / "completed",
        settings_getter=lambda: {}, providers_getter=lambda: [],
        secret_unprotect=lambda value:value, parse_nzb=lambda data,name:{},
        diagnostics=None, legacy_statistics_file=legacy, start_threads=False,
    )

# Retired native downloads.json compaction: only terminal per-article details go.
with tempfile.TemporaryDirectory(prefix="newzdeck-v3649-legacy-") as td:
    root=pathlib.Path(td); legacy=root / "downloads.json"
    legacy.write_text(json.dumps({"statistics":{"total_downloaded_bytes":123},"jobs":[
        {"id":"done","status":"completed","filename":"done.mkv","segments":[{"id":1},{"id":2}],"segment_errors":[{"x":1}],"recovery_sources":{"a":1}},
        {"id":"live","status":"queued","filename":"live.mkv","segments":[{"id":3}]},
    ]}),encoding="utf-8")
    manager=make_sab(root,legacy)
    compact=json.loads(legacy.read_text(encoding="utf-8"))
    done=next(x for x in compact["jobs"] if x["id"]=="done")
    live=next(x for x in compact["jobs"] if x["id"]=="live")
    if done.get("segments") or int(done.get("legacy_segments_compacted") or 0)!=2:
        raise SystemExit("Terminal legacy segment payload was not compacted safely.")
    if len(live.get("segments") or [])!=1:
        raise SystemExit("Non-terminal legacy resume segment state was incorrectly compacted.")
    if int(manager._legacy_compaction_segments)!=2:
        raise SystemExit("Legacy compaction telemetry is incorrect.")

# Smart Import output ownership: the historical Big Brother Canada context must
# never consume a Love Island _UNPACK_ directory merely because history.storage
# points there. The matching Big Brother _UNPACK_ form remains valid.
with tempfile.TemporaryDirectory(prefix="newzdeck-v3649-output-") as td:
    root=pathlib.Path(td); (root / "completed").mkdir(parents=True)
    manager=make_sab(root)
    context={"source":"automation_grab","release_title":"Big.Brother.Canada.S07E29.1080p.WEB-DL-GROUP"}
    meta={"name":"Big.Brother.Canada.S07E29.1080p.WEB-DL-GROUP","source_name":"Big.Brother.Canada.S07E29.1080p.WEB-DL-GROUP.nzb","automation_context":context}
    good=root / "completed" / "_UNPACK_Big.Brother.Canada.S07E29.1080p.WEB-DL-GROUP"
    bad=root / "completed" / "_UNPACK_Love.Island.S05E11.1080p.WEB-DL-GROUP"
    good.mkdir(); bad.mkdir()
    (good / "episode.mkv").write_bytes(b"good")
    (bad / "episode.mkv").write_bytes(b"bad")
    files,stage,_=manager._resolve_automation_output("good-job",meta,{"storage":str(good),"filename":meta["name"]})
    if not files or stage!=good:
        raise SystemExit("Valid matching _UNPACK_ Automation output no longer resolves.")
    (good / "episode.mkv").unlink(); good.rmdir()
    files,stage,_=manager._resolve_automation_output("wrong-job",meta,{"storage":str(bad),"filename":meta["name"]})
    if files:
        raise SystemExit("Cross-job Love Island output was accepted for Big Brother Canada Automation context.")

# Scoped Downloads view must keep global counts while bounding terminal payloads.
with tempfile.TemporaryDirectory(prefix="newzdeck-v3649-view-") as td:
    root=pathlib.Path(td); manager=make_sab(root)
    fake_jobs=[
        {"id":"live","collection_id":"live","status":"downloading","post_status":""},
        *[{"id":f"done-{i}","collection_id":f"done-{i}","status":"completed","post_status":"","completed_ts":1000-i} for i in range(80)],
        {"id":"bad","collection_id":"bad","status":"failed","post_status":""},
    ]
    fake={"jobs":fake_jobs,"collections":[{"id":x["id"]} for x in fake_jobs],"counts":{"downloading":1,"completed":80,"failed":1},"telemetry":{}}
    manager.snapshot=lambda *args, **kwargs: fake
    manager._terminal_history={"version":2,"rows":{x["id"]:{**x,"collection_name":x["id"],"filename":x["id"],"details_loaded":False,"created_ts":0,"completed_ts":x.get("completed_ts",0)} for x in fake_jobs if x["status"] in {"completed","failed"}}}
    with manager._terminal_history_lock:
        manager._rebuild_terminal_history_indexes_locked()
    live=manager.snapshot_view("live",limit=50)
    completed=manager.snapshot_view("completed",limit=50)
    failed=manager.snapshot_view("failed",limit=50)
    if [x["id"] for x in live["jobs"]] != ["live"]:
        raise SystemExit("Live Downloads scope contains terminal history.")
    if len(completed["jobs"])!=50 or not completed["view"]["has_more"] or completed["view"]["total"]!=80:
        raise SystemExit("Completed history paging is not bounded/deterministic.")
    if failed["view"].get("matching_ids") != ["bad"]:
        raise SystemExit("Scoped Downloads view lost failed-id coverage.")
    for key,value in fake["counts"].items():
        if int((completed.get("counts") or {}).get(key) or 0)!=int(value or 0):
            raise SystemExit("Scoped Downloads view lost global counts.")

if not sab.SabDownloadManager._engine_warning_informational("Direct Unpack was automatically enabled for this job"):
    raise SystemExit("Normal SAB Direct Unpack notice is still classified as a warning.")

sab_source=SAB_PATH.read_text(encoding="utf-8")
server_source=SERVER_PATH.read_text(encoding="utf-8")
app_source=APP_JS_PATH.read_text(encoding="utf-8")
index_source=INDEX_PATH.read_text(encoding="utf-8")
for marker in (
    'ADAPTER_VERSION = "3.6.72"', 'def snapshot_view(', 'snapshot_p95_ms',
    '_provider_health_cached_snapshot', 'legacy_terminal_segments_compacted_by',
    'Rejected SAB completed path whose identity belongs to another Automation job',
):
    if marker not in sab_source:
        raise SystemExit(f"Missing v3.6.72 SAB/runtime marker: {marker}")
for marker in (
    'APP_VERSION = "3.6.72"', 'scope=str((query.get("scope")',
    'X-NewzDeck-JSON-Serialize-Ms', "runtime_source']='sabnzbd'",
):
    if marker not in server_source:
        raise SystemExit(f"Missing v3.6.72 server marker: {marker}")
for marker in (
    "const UI_VERSION = '3.6.72';", "downloadHistoryLimit:50",
    "scope=terminalView?state.downloadFilter:'live'", "data-download-history-more",
    "Downloads snapshot latency", "SAB runtime",
):
    if marker not in app_source:
        raise SystemExit(f"Missing v3.6.72 UI marker: {marker}")
for marker in ("v3.6.72", "3.6.72-browse-timeout-error-attribution"):
    if marker not in index_source:
        raise SystemExit(f"Missing v3.6.72 HTML identity marker: {marker}")

print(f"v3.6.72 carried-forward supplemental regression guard passed ({len(PRODUCTION_REJECTS)} historical identity rejects + data-plane/runtime/cache/output ownership guards).")
