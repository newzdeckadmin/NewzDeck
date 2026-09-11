from __future__ import annotations
import ast, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'src' / 'app'
def load_module(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f'Could not load {path}')
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module); return module
def check(condition: bool, message: str):
    if not condition: raise AssertionError(message)
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8'); index=(APP/'static'/'index.html').read_text(encoding='utf-8'); auto=(APP/'automation_engine.py').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); sab=load_module('newzdeck_v3666_sab_guard',APP/'sab_engine.py')
# 1. Known immediate/permanent preview failures are specific and non-retryable; unknowns remain retryable.
permanent_codes=('segments_missing','segment_reference_missing','segment_limit_exceeded','preview_too_large','media_not_previewable','video_sample_empty','article_missing','multipart_incomplete','decode_failed','browse_cancelled')
for code in permanent_codes:
    check(f"'error_code': '{code}'" in server,f'Missing v3.6.72 failure class: {code}')
check("'error_code': 'segment_fetch_failed'" in server and "'retryable': True" in server,'Transient segment-fetch classification missing.')
check("'error_code': 'provider_temporary'" in server and "'retryable': True" in server,'Provider-temporary classification missing.')
check("return {'error': text, 'error_code': 'preview_failed', 'error_label': 'Preview unavailable', 'retryable': True}" in server,'Unknown preview failures are no longer conservatively retryable.')
for code in permanent_codes:
    check(code in app,'Frontend definitive-failure handling is missing '+code)
# 2. Video endpoint telemetry mirrors paired Image evidence without adding a new admission/tuning gate.
for marker in ('def _browse_video_thumbnail_endpoint_enter','def _browse_video_thumbnail_endpoint_leave','video_thumbnail_endpoint_concurrency','video_thumbnail_requests','video_thumbnail_failures','video_thumbnail_failure_code_','video_thumbnail_cache_lookup','video_thumbnail_endpoint_total','video_thumbnail_body','video_thumbnail_frame'):
    check(marker in server,f'Missing Video telemetry marker: {marker}')
check('perf_stage_prefix="video_thumbnail"' in server and 'f"{perf_stage_prefix}_executor_wait"' in server and 'f"{perf_stage_prefix}_worker"' in server,'Video executor/worker phase telemetry is not wired through run_preview_task.')
check('"schema_version": 9' in server and '"contract": "passive-runtime-browsing-performance"' in server,'Browsing telemetry schema 6/contract missing.')
for stage in ('video_thumbnail_http','video_thumbnail_post','video_thumbnail_server_pair','video_thumbnail_transport_gap'):
    check(f'\"{stage}\"' in server,f'Backend does not accept Video client stage {stage}.')
check('thumbnail_server_ms' in server[server.index('    def video_thumbnail_api'):server.index('    def thumbnail_store_api')],'Video endpoint does not emit paired backend elapsed time.')
for marker in ("fetchVideoThumbnail(a,task)","video-${demand}-primary","perfRecord('video_thumbnail_http'","recordPairedVideoThumbnailTransport(total,data?.thumbnail_server_ms,true,reason)","perfRecord('video_thumbnail_post'"):
    check(marker in app,f'Missing Video browser trace marker: {marker}')
check("api('/api/thumbnail/video'" in app,'Video thumbnail endpoint call missing.')
# 3. Preserve proven Image admission and all provider/video concurrency tuning.
for marker in ('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;','function acquireThumbnailHttpAdmission(','function previewStartingConcurrency(connections)','function previewIdleCeiling(connections,floor)','state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'):
    check(marker in app,f'Proven v3.6.65 scheduling changed: {marker}')
check(app.count("api('/api/thumbnail/image'")==1,'Direct Image thumbnail path bypasses centralized v3.6.65 gate.')
check('VIDEO_THUMB_SAMPLE_MB = 24' in server and 'max_segments=12' in server,'Video sample size/segment cap changed.')
# 4. Preserve headers, resolver batching, SAB/Automation/Discover identities.
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in wanted for t in node.targets): body.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3666>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header tuning changed.')
for marker in ('function queueNameResolutionResultRender({manual=false}={})',"reason:'name-resolution-batched-result'","perfRecord('name_resolution_batch'"):
    check(marker in app,f'Resolver batching regressed: {marker}')
check((APP/'version.txt').read_text().strip()=='3.6.72','version.txt mismatch')
check(manifest.get('version')=='3.6.72' and manifest.get('base_version')=='3.6.71' and manifest.get('adapter_version')=='3.6.72','manifest identity mismatch')
check(manifest.get('sab_version')=='5.1.2' and sab.SAB_VERSION=='5.1.2' and sab.TERMINAL_HISTORY_VERSION==3,'SAB/history architecture changed')
check(sab.ADAPTER_VERSION=='3.6.72','SAB adapter identity mismatch')
check("version='3.6.72'" in auto,'Automation default identity mismatch')
check('_discover_library_index_snapshot' in auto and '_flush_metadata_cache_now' in auto,'Discover optimization stack missing')
check('3.6.72-browse-timeout-error-attribution' in index,'Static cache marker missing')
check('<div class="version"><b>NewzDeck</b><span>v3.6.72</span></div>' in index,'Visible UI version mismatch')
print('v3.6.72 regression guard: PASS')
