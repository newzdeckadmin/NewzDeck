#!/usr/bin/env python3
"""Production regression guard for strict NewzDeck TV release identity matching and safe compatibility."""
from __future__ import annotations
import ast
import importlib.util
import json
import pathlib
import sys
import tempfile
import typing

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "src" / "app" / "automation_engine.py"
SERVER_PATH = ROOT / "src" / "app" / "server.py"

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
pluribus = {"kind":"tv","title":"Pluribus","library_title":"Pluribus","year":2025}
beast = {"kind":"tv","title":"Beast Games","library_title":"Beast Games","year":2024}
reacher = {"kind":"tv","title":"Reacher","library_title":"Reacher","year":2022}
dark_matter = {"kind":"tv","title":"Dark Matter","library_title":"Dark Matter (US)","country_codes":["US"],"year":2024}

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
    (pluribus, "PLUR1BUS.S01E01.1080p.ATVP.WEB-DL", True),
    (pluribus, "PLUR1BUS.2025.S01E09.2160p.ATVP.WEB-DL", True),
    (beast, "Beast.Games.2026.S02E08.1080p.AMZN.WEB-DL", True),
    (beast, "Beast.Games.2026.S02E10.1080p.AMZN.WEB-DL", True),
    (reacher, "Reacher.2026.S04E06.2160p.AMZN.WEB-DL", True),
    (from_item, "From.2023.S02E10.2160p.MGMP.WEB-DL", True),
    (dark_matter, "Dark.Matter.2024.2024.S01E04.2160p.ATVP.WEB-DL", True),
    (uk, "Love.Island.The.Debrief.2026.S01E02.1080p", False),
    (uk, "Love.Island.Romania.2026.S01E34.1080p", False),
    (uk, "Love.Island.All.Stars.2026.S01E01.1080p", False),
    (from_item, "The.Show.2023.S02E10.FROM.1080p", False),
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
    "def _tv_prefix_matches_candidate(",
    "def _tv_year_decorations(",
    "def _tv_stylized_token_fold(",
    "Stored release/file identity does not strictly match this TV series prefix",
    "def library_integrity_mark_missing(",
    "automatic_storage_reserve_percent",
    "def _prune_grab_reservations(",
]
for marker in required:
    if marker not in source:
        raise SystemExit(f"Missing v3.6.44 production guard marker: {marker}")



# v3.6.44: Mark Missing must never remove the reviewed physical file.
class _DummyDownloadManager:
    pass

with tempfile.TemporaryDirectory(prefix="newzdeck-v3643-integrity-") as td:
    data_dir = pathlib.Path(td)
    media_dir = data_dir / "TV" / "Show" / "Season 1"
    media_dir.mkdir(parents=True)
    media_file = media_dir / "Show - S01E01 - Wrong.mkv"
    media_file.write_bytes(b"NewzDeck v3.6.44 non-destructive review guard")
    library = [{
        "id":"guard-show","kind":"tv","title":"Show","library_title":"Show",
        "seasons":[{"season_number":1,"episodes":[{
            "episode_number":1,"has_file":True,"file_path":str(media_file),"file_quality":"1080p",
            "file_size":media_file.stat().st_size,"file_fingerprint":"guard-fingerprint",
            "quality_source":"newzdeck-import","media_info":{},"cutoff_met":True,
        }]}],
    }]
    (data_dir / "media-library.json").write_text(json.dumps(library), encoding="utf-8")
    engine = module.MediaAutomationEngine(data_dir, lambda value:value, lambda value:value, _DummyDownloadManager(), lambda:[], version="3.6.44")
    result = engine.library_integrity_mark_missing("guard-show",1,1,str(media_file))
    after = json.loads((data_dir / "media-library.json").read_text(encoding="utf-8"))
    episode = after[0]["seasons"][0]["episodes"][0]
    if not media_file.exists() or not result.get("file_preserved"):
        raise SystemExit("Integrity review guard deleted or lost the physical media file.")
    if episode.get("has_file") or episode.get("file_path"):
        raise SystemExit("Integrity review guard did not clear the NewzDeck library association.")
    if episode.get("integrity_excluded_fingerprint") != "guard-fingerprint":
        raise SystemExit("Integrity review guard did not preserve the reviewed fingerprint exclusion.")

# v3.6.44: execute the diagnostics compaction helper without importing server.py,
# whose module-level runtime initialization is intentionally not a unit-test API.
server_source = SERVER_PATH.read_text(encoding="utf-8")
# v3.6.44: the read-only integrity audit must be routed through GET, while
# explicit review actions remain POST-only. This catches the v3.6.43 404 regression.
route = '"/api/automation/library/integrity-audit"'
get_pos = server_source.find("    def do_GET(self):")
post_pos = server_source.find("    def do_POST(self):")
if get_pos < 0 or post_pos < 0 or post_pos <= get_pos:
    raise SystemExit("Could not isolate NewzDeck GET/POST handlers for integrity-route validation.")
get_block = server_source[get_pos:post_pos]
post_block = server_source[post_pos:]
if route not in get_block:
    raise SystemExit("Library Integrity audit endpoint is not registered in the GET handler.")
if route in post_block:
    raise SystemExit("Library Integrity audit endpoint is incorrectly registered in the POST handler.")
for action_route in ('"/api/automation/library/integrity/open-folder"','"/api/automation/library/integrity/mark-missing"'):
    if action_route not in post_block:
        raise SystemExit(f"Library Integrity action route is no longer POST-only/present: {action_route}")

server_tree = ast.parse(server_source)
helper_nodes = [node for node in server_tree.body if isinstance(node, ast.FunctionDef) and node.name in {"_diagnostic_downloads_snapshot","_client_disconnected"}]
if {node.name for node in helper_nodes} != {"_diagnostic_downloads_snapshot","_client_disconnected"}:
    raise SystemExit("Missing v3.6.44 diagnostics/client-disconnect helper.")
helper_ns = {
    "Any": typing.Any,
    "BrokenPipeError": BrokenPipeError,
    "ConnectionResetError": ConnectionResetError,
    "ConnectionAbortedError": ConnectionAbortedError,
}
exec(compile(ast.Module(body=helper_nodes, type_ignores=[]), str(SERVER_PATH), "exec"), helper_ns)
sample_collections = [{"id":str(i),"name":f"Job {i}","display_name":f"Job {i}","status":"completed","post_status":"completed","automation_context":{"oversized":"x" * 2000}} for i in range(200)]
sample = {"collections":sample_collections,"counts":{"completed":200},"telemetry":{"ok":True},"statistics":{"ok":True},"engine":{"name":"SABnzbd"}}
compact = helper_ns["_diagnostic_downloads_snapshot"](sample)
if compact.get("collection_count") != 200 or compact.get("collections_included",999) > 50 or not compact.get("collections_truncated"):
    raise SystemExit("Diagnostics compaction did not bound historical collection evidence.")
if len(json.dumps(compact).encode("utf-8")) >= len(json.dumps(sample).encode("utf-8")) // 3:
    raise SystemExit("Diagnostics compaction did not materially reduce duplicate Downloads history.")
if not helper_ns["_client_disconnected"](BrokenPipeError()) or helper_ns["_client_disconnected"](ValueError("application failure")):
    raise SystemExit("Client-disconnect classifier is too broad or failed to recognize BrokenPipeError.")

print(f"TV identity/reliability regression guard passed ({len(CASES)} TV cases + integrity/diagnostics guards).")
