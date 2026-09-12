from __future__ import annotations
import ast, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def check(c,m):
    if not c: raise AssertionError(m)
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8'); index=(APP/'static'/'index.html').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); sab=load('newzdeck_v3674_sab_guard',APP/'sab_engine.py')
# v3.6.78 is diagnostics-only: request/session correlation and cancellation drain evidence.
for marker in (
    'let videoThumbRequestSeq = 0;',
    'video_request_id:requestId',
    'client_video_active:Number(state.thumbVideoActive||0)',
    'client_thumb_active:Number(state.thumbActive||0)',
    "perfRecord('video_thumbnail_client_lifecycle'",
    "perfRecord('video_thumbnail_client_cancel'",
): check(marker in app,'v3.6.78 client cancellation telemetry marker missing: '+marker)
for marker in (
    '_BROWSER_VIDEO_ACTIVE_REQUESTS', '_BROWSER_VIDEO_RECENT_REQUESTS',
    'def _mark_video_requests_superseded(', 'def _video_request_cancel_detected(', 'def _video_request_end(',
    'video_thumbnail_cancel_detect_delay', 'video_thumbnail_cancel_drain',
    'video_requests_superseded', 'video_cancel_detected', 'video_requests_finished_after_superseded',
    'video_cancel_not_detected_before_completion', '"video_thumbnail_cancellation"',
    '"current_active"', '"superseded_active"', '"current_peak"', '"superseded_peak"',
    'browse_session_cancel_check(origin_provider_id, group, browse_session, lambda: _video_request_cancel_detected(request_id))',
): check(marker in server,'v3.6.78 server cancellation telemetry marker missing: '+marker)
check('"schema_version": 11' in server and '"contract": "passive-runtime-browsing-performance"' in server,'Browsing telemetry schema 11/contract missing')
# Stable identity and schema-10 visible-wait behavior are preserved.
for marker in (
    'function resolveThumbnailTaskArticle(task)',
    "perfRecord('thumbnail_task_identity',0,true,{reason:'relocated'})",
    "perfRecord('thumbnail_task_identity',0,true,{reason:'stale-missing'})",
    "perfRecord('thumbnail_task_identity',0,true,{reason:'incompatible-media'})",
    "perfRecord('thumbnail_prefetch_dwell',prefetchDwellMs,true",
    "perfRecord('thumbnail_visible_wait',visibleWaitMs,true",
): check(marker in app,'Accepted v3.6.73 behavior regressed: '+marker)
# No tuning changes are allowed in this diagnostics release.
check('return(visible?0:1)*1e9+Math.max(0,distance)*1000+Math.max(0,sizePenalty-ageCredit);' in app,'Thumbnail scheduler scoring formula changed')
check('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;' in app,'Image HTTP admission changed')
formula='state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'
check(formula in app,'Accepted six-slot Video ceiling changed')
check('VIDEO_THUMB_SAMPLE_MB = 24' in server,'24 MB Video sample limit changed')
check('max_segments=12' in server,'12-segment Video sample cap changed')
for marker in ('const NAME_RESOLUTION_RENDER_AUTO_SOFT_MS=1400;','const NAME_RESOLUTION_RENDER_AUTO_MAX_MS=3000;','const NAME_RESOLUTION_RENDER_MANUAL_SOFT_MS=1800;','const NAME_RESOLUTION_RENDER_MANUAL_MAX_MS=4200;'):
    check(marker in app,'Accepted All Posts resolver behavior regressed: '+marker)
for marker in ('SETTINGS_SAVE_RETRY_SECONDS = 3.0','SETTINGS_SAVE_RETRYABLE_WINERRORS = frozenset({5, 32, 33})'):
    check(marker in server,'Accepted settings reliability behavior regressed: '+marker)
# Header strategy is frozen.
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3674>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')
check((APP/'version.txt').read_text().strip()=='3.6.78','version.txt mismatch')
check("const UI_VERSION = '3.6.78'" in app and '3.6.78-defender-lf-build-pipeline' in index,'UI/cache identity mismatch')
check(manifest.get('version')=='3.6.78' and manifest.get('base_version')=='3.6.77' and manifest.get('adapter_version')=='3.6.78','build manifest identity mismatch')
check(sab.ADAPTER_VERSION=='3.6.78' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.78 regression guard: PASS')
