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
    "def start_library_scan(",
    "def library_scan_progress(",
    "self.library_scan_run_lock",
    "files_discovered",
    "eta_seconds",
]
for marker in required:
    if marker not in source:
        raise SystemExit(f"Missing v3.6.46 production guard marker: {marker}")



# v3.6.44: Mark Missing must never remove the reviewed physical file.
class _DummyDownloadManager:
    pass

with tempfile.TemporaryDirectory(prefix="newzdeck-v3643-integrity-") as td:
    data_dir = pathlib.Path(td)
    media_dir = data_dir / "TV" / "Show" / "Season 1"
    media_dir.mkdir(parents=True)
    media_file = media_dir / "Show - S01E01 - Wrong.mkv"
    media_file.write_bytes(b"NewzDeck v3.6.48 non-destructive review guard")
    library = [{
        "id":"guard-show","kind":"tv","title":"Show","library_title":"Show",
        "seasons":[{"season_number":1,"episodes":[{
            "episode_number":1,"has_file":True,"file_path":str(media_file),"file_quality":"1080p",
            "file_size":media_file.stat().st_size,"file_fingerprint":"guard-fingerprint",
            "quality_source":"newzdeck-import","media_info":{},"cutoff_met":True,
        }]}],
    }]
    (data_dir / "media-library.json").write_text(json.dumps(library), encoding="utf-8")
    engine = module.MediaAutomationEngine(data_dir, lambda value:value, lambda value:value, _DummyDownloadManager(), lambda:[], version="3.6.67")
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

# v3.6.46: real Automation scan progress must use an async start/status contract while
# preserving the synchronous compatibility route.
scan_start='"/api/automation/library/scan/start"'
scan_progress='"/api/automation/library/scan/progress"'
scan_sync='"/api/automation/library/scan"'
if scan_progress not in get_block:
    raise SystemExit("Library scan progress endpoint is missing from GET.")
if scan_start not in post_block or scan_sync not in post_block:
    raise SystemExit("Library scan start or synchronous compatibility route is missing from POST.")
app_source=(ROOT / "src" / "app" / "static" / "app.js").read_text(encoding="utf-8")
index_source=(ROOT / "src" / "app" / "static" / "index.html").read_text(encoding="utf-8")
for required_ui in ("pollAutomationScanProgress","renderAutomationScanProgress","/api/automation/library/scan/start","/api/automation/library/scan/progress","eta_seconds","current_item_files"):
    if required_ui not in app_source:
        raise SystemExit(f"Library scan progress UI is missing marker: {required_ui}")
for required_dom in ('id="automationScanProgress"','id="automationScanProgressFill"','id="automationScanProgressMeta"'):
    if required_dom not in index_source:
        raise SystemExit(f"Library scan progress DOM is missing marker: {required_dom}")

with tempfile.TemporaryDirectory(prefix="newzdeck-v3645-scan-") as td:
    engine=module.MediaAutomationEngine(pathlib.Path(td),lambda value:value,lambda value:value,_DummyDownloadManager(),lambda:[],version="3.6.67")
    job=engine.start_library_scan("")
    if not job.get("job_id"):
        raise SystemExit("Library scan start did not return a job ID.")
    import time as _time
    deadline=_time.time()+5
    while _time.time()<deadline:
        current=engine.library_scan_progress(str(job.get("job_id")))
        if current.get("status") in {"completed","failed"}: break
        _time.sleep(0.02)
    if current.get("status")!="completed" or int(current.get("progress_percent") or 0)!=100:
        raise SystemExit(f"Library scan progress smoke test did not complete cleanly: {current}")

# v3.6.46: Quality Profile rank must be authoritative over indexer reliability
# and custom-format score, while materially larger same-tier releases receive a
# bounded preference rather than an unconditional largest-file rule.
with tempfile.TemporaryDirectory(prefix="newzdeck-v3646-ranking-") as td:
    engine=module.MediaAutomationEngine(pathlib.Path(td),lambda value:value,lambda value:value,_DummyDownloadManager(),lambda:[],version="3.6.67")
    profile=module.DEFAULT_PROFILES[1]
    item={"kind":"tv","title":"Love Island","library_title":"Love Island (UK)","country_codes":["GB"],"title_ambiguous":True,"year":2015}
    now=__import__('time').time()
    runtime={"indexer_health":{
        "nzbgeek":{"name":"NZBGeek","failures":[],"successes":[now]},
        "nzbfinder":{"name":"NZBFinder","failures":[now]*20,"successes":[]},
    }}
    rows=[]
    samples=[
        ("Love.Island.S03E01.720p.WEB.x265-FAST",int(6.0*1024**3),"NZBGeek"),
        ("Love.Island.S03E01.1080p.WEB-DL.H264-SMALL",int(2.0*1024**3),"NZBFinder"),
        ("Love.Island.S03E01.1080p.WEB-DL.H264-LARGE",int(5.0*1024**3),"NZBFinder"),
    ]
    for title,size,indexer in samples:
        row={"title":title,"size":size,"indexer":indexer,"published":int(now)}
        row.update(engine._evaluate_release(title,size,profile,item=item,season=3,episode=1,current_quality="Unknown"))
        row["automatic_eligible"]=bool(row.get("accepted"))
        rows.append(row)
    engine._apply_release_selection_preferences(rows,profile,runtime,now=now)
    ordered=sorted(rows,key=lambda x:engine._release_selection_sort_key(x,profile),reverse=True)
    if not str((ordered[0].get("parsed") or {}).get("quality") or "").startswith("1080p"):
        raise SystemExit(f"Quality Profile rank was overridden by lower-tier scoring/reliability: {[(x.get('title'),x.get('profile_quality_rank'),x.get('selection_score')) for x in ordered]}")
    rank720=next(i for i,x in enumerate(ordered) if str((x.get("parsed") or {}).get("quality") or "").startswith("720p"))
    if rank720<2:
        raise SystemExit("720p release ranked above a valid 1080p WEB-DL in the 1080p Balanced profile.")
    small=next(x for x in rows if "SMALL" in str(x.get("title")))
    large=next(x for x in rows if "LARGE" in str(x.get("title")))
    if int(large.get("selection_size_bonus") or 0)<=int(small.get("selection_size_bonus") or 0) or int(large.get("selection_score") or 0)<=int(small.get("selection_score") or 0):
        raise SystemExit("Same-tier file-size preference did not favor the materially larger otherwise-comparable release.")
    if max(int(x.get("selection_size_bonus") or 0) for x in rows)>10:
        raise SystemExit("File-size preference exceeded its bounded 10-point ceiling.")
    if engine._indexer_penalty(runtime,"NZBFinder",now)>12:
        raise SystemExit("Indexer reliability penalty exceeded the v3.6.46 12-point ceiling.")

    # Exercise the public Interactive Search ranking path as well as the helper.
    library_item={**item,"id":"love-island-uk","quality_profile_id":"quality-1080p","seasons":[{"season_number":3,"episodes":[{"episode_number":1,"name":"Episode 1","monitored":True,"has_file":False}]}]}
    engine._library=lambda:[library_item]
    engine._profiles=lambda:[profile]
    engine._indexers=lambda:[{"name":"NZBGeek","enabled":True},{"name":"NZBFinder","enabled":True}]
    engine._auto_runtime=lambda:runtime
    engine._sync_automatic_failures=lambda _rt:False
    def _fake_search(indexer,_item,_season,_episode):
        name=str(indexer.get("name") or "")
        if name=="NZBGeek":
            return [{"title":"Love.Island.S03E01.720p.WEB.x265-FAST","size":int(6.0*1024**3),"indexer":name,"guid":"720","published":int(now)}]
        return [
            {"title":"Love.Island.S03E01.1080p.WEB-DL.H264-SMALL","size":int(2.0*1024**3),"indexer":name,"guid":"1080-small","published":int(now)},
            {"title":"Love.Island.S03E01.1080p.WEB-DL.H264-LARGE","size":int(5.0*1024**3),"indexer":name,"guid":"1080-large","published":int(now)},
        ]
    engine._search_indexer=_fake_search
    search=engine.search_releases("love-island-uk",3,1)
    ranked=list(search.get("releases") or [])
    if not ranked or str(ranked[0].get("guid") or "")!="1080-large" or not ranked[0].get("recommended"):
        raise SystemExit(f"Interactive Search did not recommend the larger 1080p WEB-DL: {[(x.get('guid'),x.get('profile_quality_rank'),x.get('selection_score')) for x in ranked]}")
    if next((i for i,x in enumerate(ranked) if str(x.get("guid") or "")=="720"),-1)<2:
        raise SystemExit("Interactive Search integration path still allowed 720p to outrank a safe 1080p tier.")



# v3.6.47: Selected Episodes monitoring must keep explicit old episode choices
# authoritative without implicitly monitoring other seasons or requiring backlog mode.
with tempfile.TemporaryDirectory(prefix="newzdeck-v3647-selected-") as td:
    engine=module.MediaAutomationEngine(pathlib.Path(td),lambda value:value,lambda value:value,_DummyDownloadManager(),lambda:[],version="3.6.67")
    item={"id":"selected-show","kind":"tv","title":"Selected Show","monitored":True,"monitor_mode":"all","quality_profile_id":"quality-1080p","seasons":[]}
    for sn in range(1,5):
        item["seasons"].append({"season_number":sn,"monitored":True,"episodes":[
            {"episode_number":1,"air_date":"2020-01-01","monitored":True,"has_file":False,"cutoff_met":False},
            {"episode_number":2,"air_date":"2020-01-02","monitored":True,"has_file":False,"cutoff_met":False},
        ]})
    library=[item]
    engine._library=lambda:library
    engine._save_library=lambda _value:None
    engine._profiles=lambda:[module.DEFAULT_PROFILES[1]]
    engine.public_config=lambda:{"automatic_grab_enabled":True,"automatic_upgrades_enabled":True,"automatic_backlog_enabled":False,"automatic_enabled_at":__import__('time').time()}

    # First entry into Selected Episodes starts from an empty explicit selection,
    # never from the previous All/Future/Missing derived monitoring state.
    engine.update_media({"id":"selected-show","monitor_mode":"selected","monitored":True})
    if item.get("selected_episodes") != [] or any(ep.get("monitored") for season in item["seasons"] for ep in season["episodes"]):
        raise SystemExit("Selected Episodes did not begin with an empty explicit selection.")

    # Selecting Season 3 must select only that season, even though the episodes are old.
    engine.update_media({"id":"selected-show","season_number":3,"season_monitored":True})
    if item.get("selected_episodes") != ["3:1","3:2"]:
        raise SystemExit(f"Selected season keys were not persisted correctly: {item.get('selected_episodes')}")
    if not all(ep.get("monitored") for ep in item["seasons"][2]["episodes"]):
        raise SystemExit("Selected Season 3 episodes were not monitored.")
    if any(ep.get("monitored") for season in item["seasons"][:2]+item["seasons"][3:] for ep in season["episodes"]):
        raise SystemExit("Selected Season 3 implicitly monitored another season.")

    wanted=engine.wanted()
    selected_missing=[(int(x.get("season") or 0),int(x.get("episode") or 0),str((x.get("automation_policy") or {}).get("status") or "")) for x in wanted.get("missing") or []]
    if selected_missing != [(3,1,"eligible"),(3,2,"eligible")]:
        raise SystemExit(f"Explicit old Selected Episodes were not immediately Automation-eligible: {selected_missing}")

    # A full selected season may use the conservative season-pack fallback.
    packs=engine._season_pack_rows([dict(x,auto_type="missing") for x in wanted.get("missing") or []],{"selected-show":item})
    if len(packs)!=1 or int(packs[0].get("season") or 0)!=3:
        raise SystemExit(f"Fully selected Season 3 did not preserve safe season-pack fallback: {packs}")

    # A partial selection must never escalate into downloading the whole season pack.
    engine.update_media({"id":"selected-show","season_number":3,"episode_number":2,"episode_monitored":False})
    wanted=engine.wanted()
    remaining=[(int(x.get("season") or 0),int(x.get("episode") or 0)) for x in wanted.get("missing") or []]
    if remaining != [(3,1)]:
        raise SystemExit(f"Individual Selected Episode filtering failed: {remaining}")
    if engine._season_pack_rows([dict(x,auto_type="missing") for x in wanted.get("missing") or []],{"selected-show":item}):
        raise SystemExit("Partial Selected Episodes incorrectly allowed a whole-season pack.")

    # The dormant explicit selection survives another monitoring mode and is restored
    # when the user returns to Selected Episodes.
    engine.update_media({"id":"selected-show","monitor_mode":"all","monitored":True})
    engine.update_media({"id":"selected-show","monitor_mode":"selected","monitored":True})
    if item.get("selected_episodes") != ["3:1"] or not item["seasons"][2]["episodes"][0].get("monitored") or item["seasons"][2]["episodes"][1].get("monitored"):
        raise SystemExit("Selected Episode choices were not restored after switching monitoring modes.")

app_selected_source = (ROOT / "src" / "app" / "static" / "app.js").read_text(encoding="utf-8")
for marker in ("value:'selected'","label:'Selected episodes'","syncSelectedEpisodeSelectionUi","Click Save first; then choose seasons or episodes below"):
    if marker not in app_selected_source:
        raise SystemExit(f"Missing Selected Episodes UI marker: {marker}")



# v3.6.47: SAB remains authoritative for repair; NewzDeck must persist and classify
# only observable Verify/PAR2/Repair evidence and must not invent recovery-block counts.
SAB_PATH = ROOT / "src" / "app" / "sab_engine.py"
sab_source = SAB_PATH.read_text(encoding="utf-8")
sab_tree = ast.parse(sab_source)
repair_nodes = [node for node in sab_tree.body if isinstance(node, ast.FunctionDef) and node.name in {"_sab_text","_duration_seconds","_sab_stage_log_lines","_sab_repair_telemetry"}]
if {node.name for node in repair_nodes} != {"_sab_text","_duration_seconds","_sab_stage_log_lines","_sab_repair_telemetry"}:
    raise SystemExit("Missing v3.6.47 SAB repair telemetry helpers.")
sab_ns = {"Any": typing.Any, "re": __import__('re')}
exec(compile(ast.Module(body=repair_nodes, type_ignores=[]), str(SAB_PATH), "exec"), sab_ns)
repair = sab_ns["_sab_repair_telemetry"]
repair_cases = [
    ({"status":"Completed","stage_log":["Verifying: 10/10","All files are correct"]}, "verified", ""),
    ({"status":"Completed","stage_log":["Repair is required","Repairing: 10/10","Repair successful"]}, "repaired", ""),
    ({"status":"Fetching","action_line":"Fetching: additional PAR2 recovery blocks"}, "repairing", ""),
    ({"status":"Failed","fail_message":"Aborted, cannot be completed - https://sabnzbd.org/not-complete"}, "unrecoverable", "unrecoverable"),
    ({"status":"Failed","fail_message":"Unpacking failed: incorrect password"}, "failed_password", "password"),
    ({"status":"Failed","fail_message":"Unpacking failed: archive is corrupt"}, "failed_unpack", "unpack"),
    ({"status":"Failed","fail_message":"Post-processing failed: disk full / no space left"}, "failed_filesystem", "filesystem"),
]
for slot, expected_outcome, expected_class in repair_cases:
    row = repair(slot)
    if row.get("repair_outcome") != expected_outcome or row.get("failure_class") != expected_class:
        raise SystemExit(f"SAB repair classification failed for {slot}: {row}")
if not repair(repair_cases[2][0]).get("par2_fetch_observed"):
    raise SystemExit("SAB Fetching state did not record PAR2/recovery fetch observation.")
for slot, _outcome, _cls in repair_cases:
    if repair(slot).get("recovery_blocks_reported") is not False:
        raise SystemExit("SAB repair telemetry invented recovery-block count availability.")

for marker in (
    'SAB_VERSION = "5.1.2"',
    'ADAPTER_VERSION = "3.6.67"',
    'SABnzbd-5.1.2-win64-bin.zip',
    '0a48cc87023f054130758a114158e0f17f32152e8ff9158eef49cf73be04be46',
    'def _upgrade_running_sab_if_needed(',
    'self._api("shutdown", timeout=3.0)',
    'repair_telemetry',
    'recovery_blocks_reported',
):
    if marker not in sab_source:
        raise SystemExit(f"Missing v3.6.47 SAB/repair production marker: {marker}")
upgrade_start = sab_source.find('    def _upgrade_running_sab_if_needed(')
upgrade_end = sab_source.find('    def _launch(self)', upgrade_start)
upgrade_block = sab_source[upgrade_start:upgrade_end]
if '.kill(' in upgrade_block or '.terminate(' in upgrade_block:
    raise SystemExit("Managed SAB version-upgrade path contains a force terminate/kill operation.")
if upgrade_block.find('self._provision_engine()') > upgrade_block.find('self._api("shutdown", timeout=3.0)'):
    raise SystemExit("Managed SAB upgrade does not provision/verify the replacement before graceful shutdown.")

app_source = (ROOT / "src" / "app" / "static" / "app.js").read_text(encoding="utf-8")
for marker in ("PAR2 REPAIRED","PAR2 UNRECOVERABLE","SAB repair history","Not reported by SAB","repair_outcome","failure_class"):
    if marker not in app_source:
        raise SystemExit(f"Missing v3.6.47 Downloads repair-visibility UI marker: {marker}")

print(f"TV identity/reliability regression guard passed ({len(CASES)} TV cases + integrity/diagnostics/library-scan/quality-selection/selected-episodes/PAR2-repair guards).")
