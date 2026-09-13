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
sab=load('newzdeck_v3679_sab_guard',APP/'sab_engine.py')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

def normalized_hash(text, old, new):
    check(text.count(new)==1,f'Expected exactly one current identity {new} while normalizing')
    return digest_text(text.replace(new,old))

marker='/* v3.6.79 UX Polish Phase 3 - Feedback & State Clarity */'
phase4='/* v3.6.80 UX Polish Phase 4 - Final Consistency & Accessibility */'
check(styles.count(marker)==1,'v3.6.93 Phase 3 stylesheet marker count mismatch')
check(styles.count(phase4)==1,'v3.6.93 Phase 4 stylesheet marker count mismatch')
prefix,suffix=styles.split(marker,1)
phase3_body,_phase4_tail=suffix.split(phase4,1)
check(digest_text(prefix.rstrip('\n')+'\n')=='62d5bd56651caa48cf9536f3524cad6b8a26c5dbb978a2d2f7fe24244481eb71','Pre-v3.6.93 stylesheet baseline changed')
check(digest_text('\n'+marker+phase3_body.rstrip('\n')+'\n')=='0093a6e7cfc7b4a2f120fbd245de23d691baa31551f26b989ebe964f7afc369c','v3.6.93 UX Phase 3 override block changed outside the reviewed payload')
for required in (
    '--ux-state-success:rgba(90,211,157,.72);',
    '.toast.success{border-left-color:var(--ux-state-success)}',
    '.metadata-error,.release-indexer-error,.health-error,.download-error{',
    '.discover-empty,.downloads-empty,.automation-empty,.automation-health-empty,.diag-empty{',
    '.automation-item-activity{',
    'button.is-busy{cursor:progress;',
    '@media(max-width:620px){',
): check(required in styles,'UX Phase 3 marker missing: '+required)
for forbidden in (
    'THUMBNAIL_HTTP_ADMISSION_LIMIT','videoThumbConcurrency','VIDEO_THUMB_SAMPLE_MB','max_segments',
    'binary-set-row','gallery-virtual-spacer','article-row{','workspace.all-posts-wide','related-set-card',
    '.articles-toolbar','.groups-pane','.preview-pane','.gallery-grid','.binary-list-summary'
): check(forbidden not in phase3_body,'UX-only Phase 3 CSS touches protected Newsgroup Browser/performance surface: '+forbidden)

# v3.6.78 Defender-clean LF/Linux helper pipeline is immutable in this UX-only release.
# The reviewed Defender helper pipeline may evolve without weakening its protected invariants.
for required in (
    'DEFAULT_GO_LDFLAGS = "-s -w -H windowsgui -buildid="',
    'YENC_GO_LDFLAGS = "-H windowsgui"',
    'PICKER_GO_LDFLAGS = "-H windowsgui"',
    'if exe == "NewzDeckPicker.exe": return PICKER_GO_LDFLAGS',
    'return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS',
): check(required in builder,'Defender helper build invariant missing: '+required)
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
    'python release/windows/validate-v3678-regressions.py','python release/windows/validate-v3679-regressions.py',
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
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3679>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')
check((APP/'version.txt').read_text().strip()=='3.6.93','version.txt mismatch')
check("const UI_VERSION = '3.6.93'" in app and '3.6.93-defender-handoff-release-gate-recovery' in index,'UI/cache identity mismatch')
check(manifest.get('version')=='3.6.93' and manifest.get('base_version')=='3.6.92' and manifest.get('adapter_version')=='3.6.93','build manifest identity mismatch')
check(manifest.get('release')=='Defender Handoff Release Gate Recovery','build manifest release name mismatch')
check(sab.ADAPTER_VERSION=='3.6.93' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.93 UX feedback/state-clarity regression guard: PASS')
