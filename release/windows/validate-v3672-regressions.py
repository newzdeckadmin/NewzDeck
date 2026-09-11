from __future__ import annotations
import ast, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def check(c,m):
 if not c: raise AssertionError(m)
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8'); index=(APP/'static'/'index.html').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); sab=load('newzdeck_v3672_sab_guard',APP/'sab_engine.py')
# Source-aware transport attribution.
for marker in (
 "function friendlyTransportErrorMessage(message,path='',source='network')",
 "if(source==='http')",
 "articles=route==='/api/articles'",
 "if(articles&&timeout)return 'The news provider timed out while NewzDeck was loading article headers. Browsing can continue; try again if needed.'",
 "if(articles&&reset)return 'The news provider reset the connection while NewzDeck was loading article headers. Browsing can continue; try again if needed.'",
 "friendlyTransportErrorMessage(msg,path,'http')",
 "if(e instanceof Error&&!e?.status)e.message=friendlyTransportErrorMessage(e.message,path,'network')",
 "NewzDeck's local backend could not be reached. It may still be starting; try again in a moment.",
 "NewzDeck's local backend did not respond in time. Try again in a moment.",
): check(marker in app,'v3.6.72 transport-attribution marker missing: '+marker)
check('const unavailable=/(?:winerror|errno)' not in app,'Old broad timeout-to-local-service translator remains')
check("A required local service was temporarily unavailable" not in app,'Retired misleading generic local-service toast remains')
# v3.6.71 decode suppression remains, but policy telemetry reasons are compact enough for the 48-char server contract.
for marker in (
 "clientPermanent=['browser-decode-failed','ffmpeg-required'].includes(code)",
 "['decode_failed','browser-decode-failed','ffmpeg-required'].includes(info.code)",
 "if(state.unsupportedMediaKeys.has(pkey))return false;",
 "policyCode=failureReason==='browser-decode-failed'?'browser-decode':failureReason",
 "reason:`${demand}-${sampleClass}-${policyCode}-nr`",
 "perfRecord('video_thumbnail_policy',0,true",
): check(marker in app,'v3.6.72 Video policy marker missing: '+marker)
check('-nonretryable' not in app,'Long v3.6.71 Video policy suffix remains')
for demand in ('visible-item','visible-set-cover','prefetch-item'):
 for sample in ('partial','complete'):
  for code in ('browser-decode','ffmpeg-required'):
   reason=f'{demand}-{sample}-{code}-nr'
   check(len(reason)<=48,f'Video policy reason exceeds 48 chars: {reason}')
check('"schema_version": 9' in server and '"contract": "passive-runtime-browsing-performance"' in server,'Browsing telemetry schema 9/contract changed')
# Accepted browsing behavior stays frozen.
check('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;' in app,'Image HTTP admission changed')
formula='state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'
check(formula in app,'Accepted six-slot Video ceiling changed')
check('VIDEO_THUMB_SAMPLE_MB = 24' in server,'24 MB Video sample limit changed')
check('max_segments=12' in server,'12-segment Video sample cap changed')
for marker in ('const NAME_RESOLUTION_RENDER_AUTO_SOFT_MS=1400;','const NAME_RESOLUTION_RENDER_AUTO_MAX_MS=3000;','const NAME_RESOLUTION_RENDER_MANUAL_SOFT_MS=1800;','const NAME_RESOLUTION_RENDER_MANUAL_MAX_MS=4200;'):
 check(marker in app,'Accepted All Posts resolver behavior regressed: '+marker)
for marker in ('SETTINGS_SAVE_RETRY_SECONDS = 3.0','SETTINGS_SAVE_RETRYABLE_WINERRORS = frozenset({5, 32, 33})'):
 check(marker in server,'Accepted settings reliability behavior regressed: '+marker)
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
 elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3672>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')
check((APP/'version.txt').read_text().strip()=='3.6.72','version.txt mismatch')
check("const UI_VERSION = '3.6.72'" in app and '3.6.72-browse-timeout-error-attribution' in index,'UI/cache identity mismatch')
check(manifest.get('version')=='3.6.72' and manifest.get('base_version')=='3.6.71' and manifest.get('adapter_version')=='3.6.72','build manifest identity mismatch')
check(sab.ADAPTER_VERSION=='3.6.72' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.72 regression guard: PASS')
