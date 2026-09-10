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
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8'); index=(APP/'static'/'index.html').read_text(encoding='utf-8'); auto=(APP/'automation_engine.py').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); sab=load_module('newzdeck_v3665_sab_guard',APP/'sab_engine.py')
# 1. Browser-side image HTTP admission is a separate, fixed localhost gate.
for marker in ('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;','function acquireThumbnailHttpAdmission(','function releaseThumbnailHttpAdmission()','function pumpThumbnailHttpAdmission()','thumbHttpActive: 0','thumbHttpQueue: []'):
    check(marker in app,f'Missing v3.6.69 HTTP admission marker: {marker}')
check("await acquireThumbnailHttpAdmission(task,options?.signal||null" in app,'Image thumbnail HTTP does not acquire the admission gate.')
check('finally{releaseThumbnailHttpAdmission()}' in app,'Image thumbnail HTTP does not release admission in finally.')
check(app.count("api('/api/thumbnail/image'")==1,'A direct /api/thumbnail/image path bypasses the centralized admission wrapper.')
check("'speculative',{priority:2,role:'speculative-page'}" in app,'Speculative next-page image warming bypasses admission/demand identity.')
# 2. The gate does not replace or reduce provider/preview concurrency.
for marker in ('function previewStartingConcurrency(connections)','function previewIdleCeiling(connections,floor)','state.thumbConcurrency=Math.max(1,Math.min(80,Math.round(value||1)))','state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'):
    check(marker in app,f'Provider-derived preview scheduling changed unexpectedly: {marker}')
check('THUMBNAIL_HTTP_ADMISSION_LIMIT=5' in app and 'previewIdleCeiling' in app,'HTTP gate is not independent from NNTP scheduling.')
# 3. Demand telemetry distinguishes visible and prefetch work, and admission wait is first-class.
for marker in ("function thumbnailDemandClass(","'visible':'prefetch'","perfRecord('thumbnail_admission'","perfRecord('thumbnail_queue',queueWaitMs,true,{reason:thumbnailDemandClass(task)})"):
    check(marker in app,f'Missing visible/prefetch admission telemetry marker: {marker}')
for stage in ('thumbnail_queue','thumbnail_admission','thumbnail_http','thumbnail_server_pair','thumbnail_transport_gap'):
    check(f'"{stage}"' in server,f'Backend does not accept v3.6.69 client stage {stage}.')
check('"schema_version": 7' in server and '"contract": "passive-runtime-browsing-performance"' in server,'Browsing telemetry current schema/contract missing.')
# 4. Expected browse-session supersession is non-retryable and does not paint a thumbnail failure.
check("'browse_cancelled'" in app and "info.code!=='browse_cancelled'" in app,'Browser still renders expected browse cancellation as a thumbnail failure.')
for name in ('preview_api','image_thumbnail_api','video_thumbnail_api'):
    start=server.index(f'    def {name}('); end=server.find('\n    def ',start+8); block=server[start:end if end>=0 else None]
    check('except BrowseSessionCancelled as exc:' in block and 'preview_error_info(exc)' in block,f'{name} does not normalize initial browse cancellation.')
check("return {'error': str(exc), 'error_code': 'browse_cancelled', 'error_label': 'Browsing request cancelled', 'retryable': False}" in server,'browse_cancelled error contract changed.')
# 5. Preserve proven headers, resolver batching, SAB, Discover and Automation identities.
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in wanted for t in node.targets): body.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3665>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header tuning changed.')
for marker in ('function queueNameResolutionResultRender({manual=false}={})',"reason:'name-resolution-batched-result'","perfRecord('name_resolution_batch'"):
    check(marker in app,f'v3.6.64 resolver batching regressed: {marker}')
check((APP/'version.txt').read_text().strip()=='3.6.69','version.txt mismatch')
check(manifest.get('version')=='3.6.69' and manifest.get('base_version')=='3.6.68' and manifest.get('adapter_version')=='3.6.69','manifest identity mismatch')
check(manifest.get('sab_version')=='5.1.2' and sab.SAB_VERSION=='5.1.2' and sab.TERMINAL_HISTORY_VERSION==3,'SAB/history architecture changed')
check(sab.ADAPTER_VERSION=='3.6.69','SAB adapter identity mismatch')
check("version='3.6.69'" in auto,'Automation default identity mismatch')
check('_discover_library_index_snapshot' in auto and '_flush_metadata_cache_now' in auto,'Discover optimization stack missing')
check('3.6.69-settings-save-contention-recovery' in index,'Static cache marker missing')
check('<div class="version"><b>NewzDeck</b><span>v3.6.69</span></div>' in index,'Visible UI version mismatch')
print('v3.6.69 regression guard: PASS')
