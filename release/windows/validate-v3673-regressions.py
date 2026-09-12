from __future__ import annotations
import ast, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def check(c,m):
    if not c: raise AssertionError(m)
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8'); index=(APP/'static'/'index.html').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); sab=load('newzdeck_v3673_sab_guard',APP/'sab_engine.py')
# Stable thumbnail task identity is narrow and applies to ordinary gallery work as well as Related Media covers.
for marker in (
    'function resolveThumbnailTaskArticle(task)',
    "const stableKey=String(task?.sourceArticleKey||'')",
    'articleKey(a)!==stableKey',
    'state.articles.findIndex(x=>articleKey(x)===stableKey)',
    "perfRecord('thumbnail_task_identity',0,true,{reason:'relocated'})",
    "perfRecord('thumbnail_task_identity',0,true,{reason:'stale-missing'})",
    "perfRecord('thumbnail_task_identity',0,true,{reason:'incompatible-media'})",
    "!['image','video'].includes(a.media.kind)",
    'a.media.kind!==task.kind',
    'task.index=liveIndex',
    'scoreIndex=found>=0?found:-1',
    'if(!resolveThumbnailTaskArticle(task)){state.thumbQueued.delete(task.qkey||task.pkey);continue}',
    'const a=resolveThumbnailTaskArticle(task);if(!a)return;',
): check(marker in app,'v3.6.78 stable thumbnail identity marker missing: '+marker)
check("if(task.role==='set-cover'&&task.sourceArticleKey" not in app,'Old set-cover-only stable-key relocation remains')
# Schema 10 keeps total queue age and partitions offscreen dwell from actual visible wait without changing the scheduler score formula.
for marker in (
    'firstVisibleAt:Number(priority??1)===0?queuedAt:0',
    'if(visible&&!Number(task.firstVisibleAt||0))task.firstVisibleAt=now;',
    "perfRecord('thumbnail_queue',queueWaitMs,true",
    "perfRecord('thumbnail_prefetch_dwell',prefetchDwellMs,true",
    "perfRecord('thumbnail_visible_wait',visibleWaitMs,true",
    'prefetchDwellMs=Math.max(0,(firstVisibleAt||queueStartedAt)-queuedAt)',
    'visibleWaitMs=firstVisibleAt?Math.max(0,queueStartedAt-firstVisibleAt):0',
): check(marker in app,'v3.6.78 queue visibility telemetry marker missing: '+marker)
for stage in ('thumbnail_prefetch_dwell','thumbnail_visible_wait','thumbnail_task_identity'):
    check(f'"{stage}"' in server,'Server does not accept schema-10 client stage: '+stage)
check('"schema_version": 11' in server and '"contract": "passive-runtime-browsing-performance"' in server,'Browsing telemetry schema 10/contract missing')
# The established scheduling score and accepted performance limits are frozen.
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
# v3.6.71/72 browser-decode suppression and transport attribution remain intact.
for marker in (
    "clientPermanent=['browser-decode-failed','ffmpeg-required'].includes(code)",
    "policyCode=failureReason==='browser-decode-failed'?'browser-decode':failureReason",
    "function friendlyTransportErrorMessage(message,path='',source='network')",
    "if(articles&&timeout)return 'The news provider timed out while NewzDeck was loading article headers. Browsing can continue; try again if needed.'",
): check(marker in app,'Accepted v3.6.71/v3.6.72 behavior regressed: '+marker)
# Header strategy remains frozen.
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3673>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')
# Release identities and download engine remain coherent.
check((APP/'version.txt').read_text().strip()=='3.6.78','version.txt mismatch')
check("const UI_VERSION = '3.6.78'" in app and '3.6.78-defender-lf-build-pipeline' in index,'UI/cache identity mismatch')
check(manifest.get('version')=='3.6.78' and manifest.get('base_version')=='3.6.77' and manifest.get('adapter_version')=='3.6.78','build manifest identity mismatch')
check(sab.ADAPTER_VERSION=='3.6.78' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.78 regression guard: PASS')
