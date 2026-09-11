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
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8'); index=(APP/'static'/'index.html').read_text(encoding='utf-8'); auto=(APP/'automation_engine.py').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); sab=load_module('newzdeck_v3664_sab_guard',APP/'sab_engine.py')
# 1. Result-driven filename resolution remains correct but rapid result batches are coalesced.
start=app.index('async function resolveObfuscatedNames({manual=false}={}){'); end=app.index('\nfunction binaryNameResolutionInfo',start); resolver=app[start:end]
for marker in ('function queueNameResolutionResultRender({manual=false}={})','function flushNameResolutionResultRender()','nameResolutionResultRenderBatches>=target',"reason:'name-resolution-batched-result'","perfRecord('name_resolution_batch'"):
    check(marker in app,f'Missing v3.6.71 result-batching marker: {marker}')
check("renderArticles({preserveScroll:true,reason:'name-resolution-result'})" not in resolver,'Per-response full name-resolution render returned.')
check('queueNameResolutionResultRender({manual:true})' in resolver and 'queueNameResolutionResultRender()' in resolver,'Manual/automatic resolver paths are not routed through the batcher.')
check('flushNameResolutionResultRender();state.nameResolutionInFlight=false' in resolver,'Manual completion does not flush pending visible changes.')
schedule_start=app.index('function scheduleObfuscatedNameResolution(){'); schedule_end=app.index('\nfunction nameResolutionPayload',schedule_start); schedule=app[schedule_start:schedule_end]
check('clearNameResolutionResultRenderQueue()' not in schedule,'Automatic resolver scheduling discards a pending result batch before it can render.')
check('state.searchMode||!isAllPostsMode()' in app[app.index('function flushNameResolutionResultRender()'):app.index('function queueNameResolutionResultRender')],'Pending result render is not discarded after leaving All Posts mode/search context.')
# 2. Thumbnail request pairing must compare client HTTP and Python time from the exact response.
for marker in ("perfRecord('thumbnail_server_pair'","perfRecord('thumbnail_transport_gap'",'thumbnail_server_ms','recordPairedThumbnailTransport'):
    check(marker in app or marker in server,f'Missing paired thumbnail timing marker: {marker}')
for stage in ('thumbnail_server_pair','thumbnail_transport_gap','name_resolution_batch'):
    check(f'"{stage}"' in server,f'Backend does not accept v3.6.71 client stage {stage}.')
check('timed_payload' in server and 'thumbnail_server_ms' in server,'Image-thumbnail responses do not carry paired server elapsed time.')
# 3. Endpoint concurrency is a passive gauge/peak, not a concurrency change.
for marker in ('_BROWSER_PERF_THUMBNAIL_ACTIVE','_BROWSER_PERF_THUMBNAIL_PEAK','_browse_thumbnail_endpoint_enter(mode)','_browse_thumbnail_endpoint_leave(mode)','"thumbnail_endpoint_concurrency": thumbnail_concurrency'):
    check(marker in server,f'Missing thumbnail endpoint concurrency telemetry: {marker}')
check('"schema_version": 9' in server and '"contract": "passive-runtime-browsing-performance"' in server,'Browsing telemetry current schema/contract missing.')
# 4. Preserve proven header tuning and progressive seed reuse.
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in wanted for t in node.targets): body.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
    elif isinstance(node,ast.FunctionDef) and node.name=='_merge_overview_headers': body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3664>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header tuning changed.')
ids=[int(x['article']) for x in ns['_merge_overview_headers']([{'article':n} for n in range(1401,2201)],[{'article':n} for n in range(601,1402)])]
check(ids==list(range(601,2201)) and len(ids)==len(set(ids)),'Progressive seed reuse regressed.')
# 5. Release identity and unrelated architecture remain coherent.
check((APP/'version.txt').read_text().strip()=='3.6.71','version.txt mismatch')
check(manifest.get('version')=='3.6.71' and manifest.get('base_version')=='3.6.70' and manifest.get('adapter_version')=='3.6.71','manifest identity mismatch')
check(manifest.get('sab_version')=='5.1.2' and sab.SAB_VERSION=='5.1.2' and sab.TERMINAL_HISTORY_VERSION==3,'SAB/history architecture changed')
check(sab.ADAPTER_VERSION=='3.6.71','SAB adapter identity mismatch')
check("version='3.6.71'" in auto,'Automation default identity mismatch')
check('_discover_library_index_snapshot' in auto and '_flush_metadata_cache_now' in auto,'Discover optimization stack missing')
check('3.6.71-video-thumbnail-decode-suppression' in index,'Static cache marker missing')
check('<div class="version"><b>NewzDeck</b><span>v3.6.71</span></div>' in index,'Visible UI version mismatch')
print('v3.6.71 regression guard: PASS')
