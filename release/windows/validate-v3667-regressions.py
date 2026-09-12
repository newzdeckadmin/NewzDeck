from __future__ import annotations
import ast, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def check(c,m):
 if not c: raise AssertionError(m)
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8'); index=(APP/'static'/'index.html').read_text(encoding='utf-8'); auto=(APP/'automation_engine.py').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); sab=load('newzdeck_v3667_sab_guard',APP/'sab_engine.py')
# Controlled v3.6.77 Video-only concurrency change.
formula='state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'
check(formula in app,'v3.6.77 high-connection Video ceiling formula missing')
check('connections>=48?6:connections>=24?3:connections>=12?2:1' in app,'lower Video connection tiers changed')
check('state.videoThumbConcurrency' in app and 'state.thumbConcurrency' in app,'Video ceiling no longer bounded by overall preview budget')
check("api('/api/thumbnail/video'" in app,'Video thumbnail endpoint missing')
check('THUMBNAIL_HTTP_ADMISSION_LIMIT=5' in app,'Image HTTP admission limit changed')
check(app.count("api('/api/thumbnail/image'")==1,'Image path bypasses centralized gate')
# Preserve v3.6.66 Video observability and no Video HTTP admission gate.
for marker in ('video_thumbnail_endpoint_concurrency','video_thumbnail_requests','video_thumbnail_failures','video_thumbnail_body','video_thumbnail_frame','"schema_version": 11'):
 check(marker in server,'Video/schema telemetry regressed: '+marker)
for stage in ('video_thumbnail_http','video_thumbnail_post','video_thumbnail_server_pair','video_thumbnail_transport_gap'):
 check(stage in server,'Video client timing stage missing: '+stage)
check('VIDEO_THUMB_SAMPLE_MB = 24' in server and 'max_segments=12' in server,'Video sample size/segment cap changed')
# Preserve browsing/SAB/Automation identities.
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
 elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3667>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')
for marker in ('function queueNameResolutionResultRender({manual=false}={})',"reason:'name-resolution-batched-result'","perfRecord('name_resolution_batch'"):
 check(marker in app,'Resolver batching regressed: '+marker)
check((APP/'version.txt').read_text().strip()=='3.6.77','version.txt mismatch')
check(manifest.get('version')=='3.6.77' and manifest.get('base_version')=='3.6.76' and manifest.get('adapter_version')=='3.6.77','manifest identity mismatch')
check(manifest.get('sab_version')=='5.1.2' and sab.SAB_VERSION=='5.1.2' and sab.TERMINAL_HISTORY_VERSION==3 and sab.ADAPTER_VERSION=='3.6.77','SAB/history identity changed')
check("version='3.6.77'" in auto,'Automation identity mismatch')
check('_discover_library_index_snapshot' in auto and '_flush_metadata_cache_now' in auto,'Discover optimization stack missing')
check('3.6.77-ux-layout-control-consistency' in index and '<div class="version"><b>NewzDeck</b><span>v3.6.77</span></div>' in index,'UI/cache identity mismatch')
print('v3.6.77 regression guard: PASS')
