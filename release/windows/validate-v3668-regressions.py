from __future__ import annotations
import ast, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def check(c,m):
 if not c: raise AssertionError(m)
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); sab=load('newzdeck_v3668_sab_guard',APP/'sab_engine.py')
# Bounded All Posts name-resolution render accumulator.
for marker in (
 'const NAME_RESOLUTION_RENDER_AUTO_SOFT_MS=1400;',
 'const NAME_RESOLUTION_RENDER_AUTO_MAX_MS=3000;',
 'const NAME_RESOLUTION_RENDER_MANUAL_SOFT_MS=1800;',
 'const NAME_RESOLUTION_RENDER_MANUAL_MAX_MS=4200;',
 'function nameResolutionResultRenderPolicy()',
 'function scheduleNameResolutionResultRenderFlush()',
 'state.nameResolutionResultRenderBatches>=target',
 "perfRecord('name_resolution_batch'",
 "perfRecord('name_resolution_render_wait'",
 "reason:'name-resolution-batched-result'",
): check(marker in app,'v3.6.80 resolver accumulator marker missing: '+marker)
check('state.nameResolutionResultRenderFirstAt=Date.now()' in app,'Resolver accumulator no longer anchors a fixed first-result deadline')
check('else if(manual)state.nameResolutionResultRenderManual=true' in app,'Manual resolver batches do not upgrade the active accumulator policy')
check('finally{if(group===state.selectedGroup&&providerId===state.providerId)flushNameResolutionResultRender();' in app,'Manual pass no longer flushes pending resolver results at completion')
# Schema 7 adds wait telemetry without removing prior telemetry.
check('"schema_version": 11' in server and '"contract": "passive-runtime-browsing-performance"' in server,'Browsing telemetry schema 7/contract missing')
check('"name_resolution_batch", "name_resolution_render_wait", "preview"' in server,'Resolver wait stage is not admitted beside existing batch telemetry')
for stage in ('thumbnail_admission','thumbnail_server_pair','thumbnail_transport_gap','video_thumbnail_http','video_thumbnail_server_pair','video_thumbnail_transport_gap','name_resolution_batch'):
 check(stage in server,'Prior browsing telemetry regressed: '+stage)
# Accepted Image/Video concurrency stays fixed.
check('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;' in app,'Image HTTP admission changed')
formula='state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'
check(formula in app,'Accepted six-slot Video ceiling changed')
# Header strategy remains fixed.
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
 elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3668>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')
check((APP/'version.txt').read_text().strip()=='3.6.80','version.txt mismatch')
check(manifest.get('version')=='3.6.80' and manifest.get('base_version')=='3.6.79' and manifest.get('adapter_version')=='3.6.80','build manifest identity mismatch')
check(sab.ADAPTER_VERSION=='3.6.80' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.80 regression guard: PASS')
