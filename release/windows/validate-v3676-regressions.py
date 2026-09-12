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
sab=load('newzdeck_v3676_sab_guard',APP/'sab_engine.py')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

# UX-only proof: all runtime logic files must normalize byte-for-byte to the
# canonical v3.6.75 production release after removing only the version identity.
def normalized_hash(text, old, new):
    check(text.count(new)==1,f'Expected exactly one current identity {new} while normalizing')
    return digest_text(text.replace(new,old))
check(normalized_hash(server,'3.6.75','3.6.76')=='afa455cbaf78c4fbe1f335941ee92fdd9d6b1c49d0cd0610660b259eb3c92b11','server.py changed beyond APP_VERSION')
check(normalized_hash(sab_text,'3.6.75','3.6.76')=='cde69646f933636f6af39ef7c40fd0e57a8829ba2485e8e80d7af99c42bc4121','sab_engine.py changed beyond ADAPTER_VERSION')
check(normalized_hash(automation,'3.6.75','3.6.76')=='1a1d6c451924d401bc7e5db84be12a54c201830d161d645496ea1bf4b1a8592a','automation_engine.py changed beyond version identity')
check(normalized_hash(app,'3.6.75','3.6.76')=='53d86a699e0ddb62d47c681e2565c791b27b5b067b9ab93ad73d9308e6469114','app.js logic changed; v3.6.76 must be UX/CSS-only')
normalized_index=index.replace('3.6.76-ux-readability-visual-rhythm','3.6.75-windows-defender-compatibility').replace('v3.6.76','v3.6.75')
check(digest_text(normalized_index)=='68d189298d648d812eae1e320dc9b96e92ea7dbd79d13426cb04a74a1f316a4a','index.html changed beyond version/cache identity')

# The stylesheet must be the exact v3.6.75 production CSS followed by one
# guarded visual-only override block.
marker='/* v3.6.76 UX Polish Phase 1 - Readability & Visual Rhythm */'
check(styles.count(marker)==1,'v3.6.76 UX stylesheet marker count mismatch')
prefix,suffix=styles.split(marker,1)
check(digest_text(prefix.rstrip('\n')+'\n')=='14dda592762274237cde3fec91abbce0175f7c30fd46460cdfb897c0f4e5cab4','Pre-v3.6.76 stylesheet baseline changed')
check(digest_text('\n'+marker+suffix)=='9e4ef1570f499aac230dd8a38b0889cb85af0bbf8dd83f80690f510014990e95','v3.6.76 UX override block changed outside the reviewed payload')
for marker2 in (
    '--ux-copy:12px;',
    '.discover-card-copy h3{font-size:13.5px!important;',
    '.automation-card-body>p{font-size:12px!important;',
    '.download-statistics-head p{font-size:11.5px;',
    '.settings-section>p{font-size:13px;',
    '.empty-state p,.automation-empty p,.diag-empty,.metadata-hint{font-size:12.25px;',
): check(marker2 in styles,'UX polish marker missing: '+marker2)
# Do not allow the Phase 1 suffix to touch performance-sensitive browser geometry/classes.
for forbidden in ('THUMBNAIL_HTTP_ADMISSION_LIMIT','videoThumbConcurrency','VIDEO_THUMB_SAMPLE_MB','max_segments','binary-set-row','gallery-virtual-spacer','article-row{','workspace.all-posts-wide','related-set-card'):
    check(forbidden not in suffix,'UX-only CSS suffix touches protected browser/performance surface: '+forbidden)

# v3.6.75 Defender-compatible yEnc build remains exactly frozen.
check(digest_text(builder)=='a0c23db400246a97cac85769ccc3cd4cf98fd830a85089b7580cece540234f2f','build-portable.py changed in UX-only release')
blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go source blob changed')
for marker2 in (
    'DEFAULT_GO_LDFLAGS = "-s -w -H windowsgui -buildid="',
    'YENC_GO_LDFLAGS = "-H windowsgui"',
    'return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS',
    '"purpose":"Windows Defender compatibility"',
): check(marker2 in builder,'Defender-compatible yEnc build protection missing: '+marker2)
for marker2 in ('python release/windows/validate-v3676-regressions.py',"$yencSymbols = @(& go tool nm $yencBinary 2>&1)"):
    check(marker2 in workflow,'Canonical release workflow protection missing: '+marker2)

# Carry forward frozen runtime behavior from v3.6.75.
for marker2 in (
    'let videoThumbRequestSeq = 0;', 'video_request_id:requestId',
    "perfRecord('video_thumbnail_client_lifecycle'", 'function resolveThumbnailTaskArticle(task)',
    "perfRecord('thumbnail_task_identity',0,true,{reason:'relocated'})",
    "perfRecord('thumbnail_visible_wait',visibleWaitMs,true",
    'const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;',
): check(marker2 in app,'Accepted browser behavior regressed: '+marker2)
formula='state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'
check(formula in app,'Accepted six-slot Video ceiling changed')
for marker2 in (
    '_BROWSER_VIDEO_ACTIVE_REQUESTS','video_thumbnail_cancel_detect_delay','video_thumbnail_cancel_drain',
    '"schema_version": 11','"contract": "passive-runtime-browsing-performance"',
    'VIDEO_THUMB_SAMPLE_MB = 24','max_segments=12',
    'SETTINGS_SAVE_RETRY_SECONDS = 3.0','SETTINGS_SAVE_RETRYABLE_WINERRORS = frozenset({5, 32, 33})',
): check(marker2 in server,'Accepted backend behavior regressed: '+marker2)
for marker2 in ('const NAME_RESOLUTION_RENDER_AUTO_SOFT_MS=1400;','const NAME_RESOLUTION_RENDER_AUTO_MAX_MS=3000;','const NAME_RESOLUTION_RENDER_MANUAL_SOFT_MS=1800;','const NAME_RESOLUTION_RENDER_MANUAL_MAX_MS=4200;'):
    check(marker2 in app,'Accepted All Posts resolver behavior regressed: '+marker2)

tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3676>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')

check((APP/'version.txt').read_text().strip()=='3.6.76','version.txt mismatch')
check("const UI_VERSION = '3.6.76'" in app and '3.6.76-ux-readability-visual-rhythm' in index,'UI/cache identity mismatch')
check(manifest.get('version')=='3.6.76' and manifest.get('base_version')=='3.6.75' and manifest.get('adapter_version')=='3.6.76','build manifest identity mismatch')
check(manifest.get('release')=='UX Readability & Visual Rhythm','build manifest release name mismatch')
check(sab.ADAPTER_VERSION=='3.6.76' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.76 UX-only regression guard: PASS')
