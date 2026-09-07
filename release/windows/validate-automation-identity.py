#!/usr/bin/env python3
"""Production regression guard for strict NewzDeck TV release identity matching."""
from __future__ import annotations
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "src" / "app" / "automation_engine.py"

spec = importlib.util.spec_from_file_location("newzdeck_automation_identity_guard", MODULE_PATH)
if spec is None or spec.loader is None:
    raise SystemExit(f"Could not load {MODULE_PATH}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
match = module._tv_release_identity_match

uk = {"kind":"tv","title":"Love Island","library_title":"Love Island (UK)","country_codes":["GB"],"title_ambiguous":True,"year":2015}
usa = {"kind":"tv","title":"Love Island USA","library_title":"Love Island USA","country_codes":["US"],"title_ambiguous":False,"year":2019}
from_item = {"kind":"tv","title":"FROM","library_title":"FROM","country_codes":["US"],"year":2022}
sugar = {"kind":"tv","title":"Sugar","library_title":"Sugar","year":2024}
swat = {"kind":"tv","title":"S.W.A.T.","library_title":"S.W.A.T."}

CASES = [
    (uk, "Love.Island.S03E05.1080p.WEB-DL", True),
    (uk, "Love.Island.UK.S03E05.1080p.WEB-DL", True),
    (uk, "Love.Island.GB.S03E05.1080p.WEB-DL", True),
    (uk, "Love.Island.2015.S03E05.1080p.WEB-DL", True),
    (uk, "Love.Island.UK.S12.1080p.WEB-DL", True),
    (uk, "Love.Island.Complete.Season.12.1080p.WEB-DL", True),
    (uk, "The.Morning.Show.S03E05.Love.Island.1080p.WEB-DL", False),
    (uk, "The.Bradshaw.Bunch.S02E01.Love.Island.1080p.WEB-DL", False),
    (uk, "Larva.Family.S01E05.Crazy.Love.Island.Ping-pong.1080p", False),
    (uk, "Love.Island.The.Debrief.S01E02.1080p", False),
    (uk, "Love.Island.Romania.S01E34.1080p", False),
    (uk, "Love.Island.USA.S01E01.1080p", False),
    (usa, "Love.Island.USA.S07E01.1080p", True),
    (usa, "Love.Island.US.S07E01.1080p", True),
    (usa, "Love.Island.S07E01.1080p", False),
    (from_item, "FROM.S02E01.1080p.WEB-DL", True),
    (from_item, "Sugar.2024.S02E01.Home.Away.from.Home.1080p", False),
    (sugar, "Sugar.2024.S02E01.1080p.WEB-DL", True),
    (swat, "SWAT.S07E01.1080p.WEB-DL", True),
]

failed = []
for item, title, expected in CASES:
    actual = bool(match(title, item))
    if actual != expected:
        failed.append((item.get("title"), title, expected, actual))

if failed:
    for item, title, expected, actual in failed:
        print(f"FAIL: {item!r} / {title!r}: expected {expected}, got {actual}", file=sys.stderr)
    raise SystemExit(1)

source = MODULE_PATH.read_text(encoding="utf-8")
required = [
    "def _tv_release_prefix_tokens(",
    "def _tv_allowed_series_prefixes(",
    "Stored release/file identity does not strictly match this TV series prefix",
    "automatic_storage_reserve_percent",
    "def _prune_grab_reservations(",
]
for marker in required:
    if marker not in source:
        raise SystemExit(f"Missing v3.6.42 production guard marker: {marker}")

print(f"TV identity regression guard passed ({len(CASES)} cases).")
