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
sab=load('newzdeck_v3680_sab_guard',APP/'sab_engine.py')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

def normalized_hash(text, old, new):
    check(text.count(new)==1,f'Expected exactly one current identity {new} while normalizing')
    return digest_text(text.replace(new,old))
check(normalized_hash(server,'3.6.79','3.6.80')=='52f2f7d64c290a1474b8f62a1496c7be2f14a94dd39143335ccf15f1c3291df0','server.py changed beyond APP_VERSION')
check(normalized_hash(sab_text,'3.6.79','3.6.80')=='64e7b4676d6e8687fbecc49c9cd116edaf9d55cd732834e91ddf614c8ff10046','sab_engine.py changed beyond ADAPTER_VERSION')
check(normalized_hash(automation,'3.6.79','3.6.80')=='47508b722fb9e886e1cee075254575e58748ed67e6db07eda5d6cd56ad066ded','automation_engine.py changed beyond version identity')
check(normalized_hash(app,'3.6.79','3.6.80')=='91d9e5f3f95e153978797363559bd253304a0f3c4c0f9dafdb3fa90e12a9f080','app.js logic changed; v3.6.80 must remain CSS-only')
normalized_index=index.replace('3.6.80-ux-final-consistency-accessibility','3.6.79-ux-feedback-state-clarity').replace('v3.6.80','v3.6.79')
check(digest_text(normalized_index)=='ee9b1501604960263160cf8a4b898c554cf75f6313df53b913fd6196ff6bf242','index.html changed beyond version/cache identity')

marker='/* v3.6.80 UX Polish Phase 4 - Final Consistency & Accessibility */'
check(styles.count(marker)==1,'v3.6.80 Phase 4 stylesheet marker count mismatch')
prefix,suffix=styles.split(marker,1)
check(digest_text(prefix.rstrip('\n')+'\n')=='60ff32537ccb858cba5366a482a70b5cf6d835e369598d2fb0d4b645c5cbb0f4','Pre-v3.6.80 stylesheet baseline changed')
check(digest_text('\n'+marker+suffix)=='5daad7e0a3eb02c37eafa0330ce88ad8de878aa0127b563c46fc6ac9e59587c7','v3.6.80 UX Phase 4 override block changed outside the reviewed payload')
for required in (
    '--ux-focus-ring:rgba(86,205,231,.82);',
    '.modal-card,.settings-modal-card,.automation-modal-card,.automation-item-modal-card,',
    '.nav-item:focus-visible,.settings-nav button:focus-visible,.automation-tabs button:focus-visible,',
    '.primary-btn:disabled,.secondary-btn:disabled,.danger-btn:disabled,',
    '@media(max-width:1180px){',
    '@media(prefers-reduced-motion:reduce){',
): check(required in styles,'UX Phase 4 marker missing: '+required)
for forbidden in (
    'THUMBNAIL_HTTP_ADMISSION_LIMIT','videoThumbConcurrency','VIDEO_THUMB_SAMPLE_MB','max_segments',
    'binary-set-row','gallery-virtual-spacer','article-row{','workspace.all-posts-wide','related-set-card',
    '.articles-toolbar','.groups-pane','.preview-pane','.gallery-grid','.binary-list-summary'
): check(forbidden not in suffix,'UX-only Phase 4 CSS touches protected Newsgroup Browser/performance surface: '+forbidden)

# Defender-clean LF/Linux helper pipeline remains immutable.
builder_blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:release/windows/build-portable.py'],text=True).strip()
check(builder_blob=='72b1683baa5097f704a8f28dfec2d2b34ac876f8','build-portable.py changed from the Defender-clean v3.6.78 pipeline')
yenc_blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(yenc_blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go Git blob changed')
source_bytes=subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:src/windows/NewzDeckYenc.go'])
check(digest_bytes(source_bytes)=='ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd','Canonical LF yEnc source SHA-256 changed')
for required in (
    'YENC_ACCEPTED_SOURCE_SHA256 = "ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd"',
    'YENC_ACCEPTED_BINARY_SHA256 = "4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad"',
    "ap.add_argument('--prebuilt-yenc')", 'canonical_git_source_bytes', 'shutil.copy2(prebuilt_yenc, stage/exe)',
): check(required in builder,'Defender-clean builder protection missing: '+required)
for required in (
    'yenc-helper:', 'runs-on: ubuntu-24.04', 'newzdeck-yenc-defender-lf', 'needs: yenc-helper', '--prebuilt-yenc $yenc',
    'ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd',
    '4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad',
    'python release/windows/validate-v3679-regressions.py','python release/windows/validate-v3680-regressions.py',
): check(required in workflow,'Defender-clean canonical workflow protection missing: '+required)

# Carry forward frozen runtime behavior.
for required in (
    'let videoThumbRequestSeq = 0;', 'video_request_id:requestId',
    "perfRecord('video_thumbnail_client_lifecycle'", 'function resolveThumbnailTaskArticle(task)',
    "perfRecord('thumbnail_task_identity',0,true,{reason:'relocated'})",
    "perfRecord('thumbnail_visible_wait',visibleWaitMs,true", 'const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;',
): check(required in app,'Accepted browser behavior regressed: '+required)
formula='state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'
check(formula in app,'Accepted six-slot Video ceiling changed')
for required in (
    '_BROWSER_VIDEO_ACTIVE_REQUESTS','video_thumbnail_cancel_detect_delay','video_thumbnail_cancel_drain',
    '"schema_version": 11','"contract": "passive-runtime-browsing-performance"',
    'VIDEO_THUMB_SAMPLE_MB = 24','max_segments=12',
    'SETTINGS_SAVE_RETRY_SECONDS = 3.0','SETTINGS_SAVE_RETRYABLE_WINERRORS = frozenset({5, 32, 33})',
): check(required in server,'Accepted backend behavior regressed: '+required)
for required in ('const NAME_RESOLUTION_RENDER_AUTO_SOFT_MS=1400;','const NAME_RESOLUTION_RENDER_AUTO_MAX_MS=3000;','const NAME_RESOLUTION_RENDER_MANUAL_SOFT_MS=1800;','const NAME_RESOLUTION_RENDER_MANUAL_MAX_MS=4200;'):
    check(required in app,'Accepted All Posts resolver behavior regressed: '+required)
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3680>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')
check((APP/'version.txt').read_text().strip()=='3.6.80','version.txt mismatch')
check("const UI_VERSION = '3.6.80'" in app and '3.6.80-ux-final-consistency-accessibility' in index,'UI/cache identity mismatch')
check(manifest.get('version')=='3.6.80' and manifest.get('base_version')=='3.6.79' and manifest.get('adapter_version')=='3.6.80','build manifest identity mismatch')
check(manifest.get('release')=='UX Final Consistency & Accessibility','build manifest release name mismatch')
check(sab.ADAPTER_VERSION=='3.6.80' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.80 final UX consistency/accessibility regression guard: PASS')
