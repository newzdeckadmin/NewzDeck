from __future__ import annotations
import ast, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def check(c,m):
    if not c: raise AssertionError(m)
def digest_bytes(data): return hashlib.sha256(data).hexdigest()
def digest_text(text): return digest_bytes(text.encode('utf-8'))
server=(APP/'server.py').read_text(encoding='utf-8')
sab_text=(APP/'sab_engine.py').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
sab=load('newzdeck_v3678_sab_guard',APP/'sab_engine.py')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

def normalized_hash(text, old, new):
    check(text.count(new)==1,f'Expected exactly one current identity {new} while normalizing')
    return digest_text(text.replace(new,old))
check(normalized_hash(server,'3.6.77','3.6.79')=='9db02a0a4d06582be1c32b68c0768454dd017b0b8debffa5f3a201546c03e0b9','server.py changed beyond APP_VERSION')
check(normalized_hash(sab_text,'3.6.77','3.6.79')=='1e94b1ed8522712fb6c3c7f51b1819eb75c9bb51b8b4f7b7d2578b635309cc1b','sab_engine.py changed beyond ADAPTER_VERSION')
check(normalized_hash(automation,'3.6.77','3.6.79')=='33f7f7cb6869ca7b0517d812d825f0adbaf56fcde14035a903b45e9783540cba','automation_engine.py changed beyond version identity')
check(normalized_hash(app,'3.6.77','3.6.79')=='5aec1504180bfc33334b828b93c95cc4f47f77995374df36101dcfa149532b3e','app.js logic changed in build-pipeline-only hotfix')
normalized_index=index.replace('3.6.79-ux-feedback-state-clarity','3.6.77-ux-layout-control-consistency').replace('v3.6.79','v3.6.77')
check(digest_text(normalized_index)=='981137eb1ba005f6a30f128ed19c83c139843206d0521ec6e3d7b8ee57debfab','index.html changed beyond version/cache identity')
phase3='/* v3.6.79 UX Polish Phase 3 - Feedback & State Clarity */'
check(styles.count(phase3)==1,'v3.6.79 Phase 3 stylesheet marker count mismatch')
styles_prefix,_phase3_tail=styles.split(phase3,1)
check(digest_text(styles_prefix.rstrip('\n')+'\n')=='62d5bd56651caa48cf9536f3524cad6b8a26c5dbb978a2d2f7fe24244481eb71','v3.6.78 UX stylesheet baseline changed')


blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go Git blob changed')
source_bytes=subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:src/windows/NewzDeckYenc.go'])
check(digest_bytes(source_bytes)=='ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd','Canonical LF yEnc source SHA-256 changed')
for marker in (
    'YENC_ACCEPTED_SOURCE_SHA256 = "ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd"',
    'YENC_ACCEPTED_BINARY_SHA256 = "4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad"',
    "ap.add_argument('--prebuilt-yenc')",
    'canonical_git_source_bytes',
    'shutil.copy2(prebuilt_yenc, stage/exe)',
    '"build_origin":"linux-lf-prebuilt" if prebuilt_yenc else "local-source-build"',
): check(marker in builder,'v3.6.79 builder protection missing: '+marker)
for marker in (
    'yenc-helper:', 'runs-on: ubuntu-24.04', 'actions/upload-artifact@v6', 'actions/download-artifact@v6',
    'newzdeck-yenc-defender-lf', 'needs: yenc-helper', '--prebuilt-yenc $yenc',
    'ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd',
    '4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad',
    'python release/windows/validate-v3678-regressions.py',
): check(marker in workflow,'v3.6.79 canonical workflow protection missing: '+marker)

# Carry forward frozen runtime behavior.
for marker in (
    'let videoThumbRequestSeq = 0;', 'video_request_id:requestId',
    "perfRecord('video_thumbnail_client_lifecycle'", 'function resolveThumbnailTaskArticle(task)',
    "perfRecord('thumbnail_task_identity',0,true,{reason:'relocated'})",
    "perfRecord('thumbnail_visible_wait',visibleWaitMs,true", 'const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;',
): check(marker in app,'Accepted browser behavior regressed: '+marker)
formula='state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'
check(formula in app,'Accepted six-slot Video ceiling changed')
for marker in (
    '_BROWSER_VIDEO_ACTIVE_REQUESTS','video_thumbnail_cancel_detect_delay','video_thumbnail_cancel_drain',
    '"schema_version": 11','"contract": "passive-runtime-browsing-performance"',
    'VIDEO_THUMB_SAMPLE_MB = 24','max_segments=12',
    'SETTINGS_SAVE_RETRY_SECONDS = 3.0','SETTINGS_SAVE_RETRYABLE_WINERRORS = frozenset({5, 32, 33})',
): check(marker in server,'Accepted backend behavior regressed: '+marker)
for marker in ('const NAME_RESOLUTION_RENDER_AUTO_SOFT_MS=1400;','const NAME_RESOLUTION_RENDER_AUTO_MAX_MS=3000;','const NAME_RESOLUTION_RENDER_MANUAL_SOFT_MS=1800;','const NAME_RESOLUTION_RENDER_MANUAL_MAX_MS=4200;'):
    check(marker in app,'Accepted All Posts resolver behavior regressed: '+marker)
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3678>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')
check((APP/'version.txt').read_text().strip()=='3.6.79','version.txt mismatch')
check("const UI_VERSION = '3.6.79'" in app and '3.6.79-ux-feedback-state-clarity' in index,'UI/cache identity mismatch')
check(manifest.get('version')=='3.6.79' and manifest.get('base_version')=='3.6.78' and manifest.get('adapter_version')=='3.6.79','build manifest identity mismatch')
check(manifest.get('release')=='UX Feedback & State Clarity','build manifest release name mismatch')
check(sab.ADAPTER_VERSION=='3.6.79' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.79 Defender LF build-pipeline regression guard: PASS')
