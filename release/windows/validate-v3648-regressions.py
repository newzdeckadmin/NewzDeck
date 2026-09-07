#!/usr/bin/env python3
"""NewzDeck v3.6.48 production guards from real v3.6.47 diagnostics."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "app"
AUTOMATION_PATH = APP / "automation_engine.py"
SAB_PATH = APP / "sab_engine.py"
APP_JS_PATH = APP / "static" / "app.js"

spec = importlib.util.spec_from_file_location("newzdeck_v3648_guard", AUTOMATION_PATH)
if spec is None or spec.loader is None:
    raise SystemExit(f"Could not load {AUTOMATION_PATH}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
match = module._tv_release_identity_match

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

# Exact historical false-positive/attempted releases retained in the user's
# 2026-09-07 v3.6.47 diagnostics. Every one must remain rejected.
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

# The exact All Stars companion-show form that Library Integrity found 25 times
# must remain rejected while a real All Stars episode remains accepted.
if match("Love.Island.All.Stars.The.Morning.After.S03E12.1080p.ITV.WEB-DL.AAC2.0.H.264-Pr1M371M3", all_stars):
    raise SystemExit("Love Island: All Stars companion-show identity regression returned.")
if not match("Love.Island.All.Stars.S03E12.1080p.ITV.WEB-DL.AAC2.0.H.264-GROUP", all_stars):
    raise SystemExit("Valid Love Island: All Stars episode no longer matches.")

class _DummyDownloadManager:
    pass

# v3.6.48: identical bytes in two different physical episode files of the same
# series must require review. One shared physical file mapped to multiple episodes
# remains informational so legitimate multi-episode media is not falsely flagged.
with tempfile.TemporaryDirectory(prefix="newzdeck-v3648-integrity-") as td:
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
    engine = module.MediaAutomationEngine(data_dir, lambda value:value, lambda value:value, _DummyDownloadManager(), lambda:[], version="3.6.48")
    audit = engine.library_integrity_audit()
    if int(audit.get("same_title_cross_episode_duplicate_fingerprints") or 0) != 1:
        raise SystemExit(f"Same-title cross-episode duplicate was not isolated correctly: {audit}")
    rows = list(audit.get("same_title_cross_episode_duplicates") or [])
    if not rows or not rows[0].get("needs_review") or "different episodes" not in str(rows[0].get("review_reason") or ""):
        raise SystemExit(f"Same-title duplicate review reason is missing: {rows}")
    shared_rows = [x for x in audit.get("duplicates") or [] if x.get("fingerprint") == "shared-multi-episode"]
    if not shared_rows or shared_rows[0].get("needs_review"):
        raise SystemExit("One shared multi-episode media path was incorrectly marked for review.")

sab_source = SAB_PATH.read_text(encoding="utf-8")
for marker in (
    'ADAPTER_VERSION = "3.6.48"',
    'self._snapshot_cache_seconds = 0.40',
    'snapshot_sab_reconcile_last_ms',
    'snapshot_sab_reconcile_max_ms',
    'snapshot_provider_health_last_ms',
    'snapshot_provider_health_max_ms',
    'snapshot_other_last_ms',
    'self._last_error == "SAB Queue/History reader is busy"',
    'engine["last_error_recovered"] = True',
):
    if marker not in sab_source:
        raise SystemExit(f"Missing v3.6.48 Downloads runtime marker: {marker}")

app_source = APP_JS_PATH.read_text(encoding="utf-8")
for marker in (
    "const UI_VERSION = '3.6.48';",
    "const ms=delay==null?(visible?(busy?500:1250):1500):delay;",
    "avoidable localhost/SAB contention",
    "same_title_cross_episode_duplicates",
    "SAME-SERIES EPISODE DUPLICATES",
):
    if marker not in app_source:
        raise SystemExit(f"Missing v3.6.48 Downloads polling marker: {marker}")

print(f"v3.6.48 regression guard passed ({len(PRODUCTION_REJECTS)} exact historical false positives + Library Integrity + Downloads runtime guards).")
