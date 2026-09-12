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
sab=load('newzdeck_v3677_sab_guard',APP/'sab_engine.py')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

# Phase 2 is presentation-only: runtime logic normalizes exactly to v3.6.76.
def normalized_hash(text, old, new):
    check(text.count(new)==1,f'Expected exactly one current identity {new} while normalizing')
    return digest_text(text.replace(new,old))
check(normalized_hash(server,'3.6.76','3.6.77')=='7376e78b5f8da0868712aad2d1a297e06688d34c6427fe6db5f042955767a443','server.py changed beyond APP_VERSION')
check(normalized_hash(sab_text,'3.6.76','3.6.77')=='f2c92f1ec593eb633d77570137af90ce0f057aed39b2771e2d7aa30057aa7687','sab_engine.py changed beyond ADAPTER_VERSION')
check(normalized_hash(automation,'3.6.76','3.6.77')=='b832afbd5c7b339d5092817d5b6a243136922139c95efec00bba2e69e750d94d','automation_engine.py changed beyond version identity')
check(normalized_hash(app,'3.6.76','3.6.77')=='92cc57995e8b45725d70ed13071142729bc59ea7f2e3721bf5428ed29a26d169','app.js logic changed; v3.6.77 must remain UX/CSS-only')
normalized_index=index.replace('3.6.77-ux-layout-control-consistency','3.6.76-ux-readability-visual-rhythm').replace('v3.6.77','v3.6.76')
check(digest_text(normalized_index)=='5e000db6d33524cbf6348dd493955ba3af387f844f400126e51ca0ae7d112eb9','index.html changed beyond version/cache identity')

# The stylesheet must be exact v3.6.76 plus one reviewed Phase 2 suffix.
marker='/* v3.6.77 UX Polish Phase 2 - Layout & Control Consistency */'
check(styles.count(marker)==1,'v3.6.77 UX stylesheet marker count mismatch')
prefix,suffix=styles.split(marker,1)
check(digest_text(prefix.rstrip('\n')+'\n')=='08489cb6b9b6581584b98976609f66d57880f165f374b84ee811a5f92b6eaf15','Pre-v3.6.77 stylesheet baseline changed')
check(digest_text('\n'+marker+suffix)=='13afd01b65cd9ff7d568e74fcac91a998aa49ae257a51b030c1b439109b8699e','v3.6.77 UX override block changed outside the reviewed payload')
for marker2 in (
    '--ux-control-height:40px;',
    '.primary-btn,.secondary-btn,.danger-btn{',
    '.automation-modal-card{width:min(1020px,calc(100vw - 48px))}',
    '.settings-content{padding:26px 28px}',
    '.download-tab{height:34px;min-height:34px;padding:0 12px}',
    '@media(max-width:620px){',
): check(marker2 in styles,'UX Phase 2 marker missing: '+marker2)
for forbidden in (
    'THUMBNAIL_HTTP_ADMISSION_LIMIT','videoThumbConcurrency','VIDEO_THUMB_SAMPLE_MB','max_segments',
    'binary-set-row','gallery-virtual-spacer','article-row{','workspace.all-posts-wide','related-set-card',
    '.articles-toolbar','.groups-pane','.preview-pane'
): check(forbidden not in suffix,'UX-only CSS suffix touches protected Newsgroup Browser/performance surface: '+forbidden)

# v3.6.75 Defender-compatible yEnc build remains frozen.
check(digest_text(builder)=='a0c23db400246a97cac85769ccc3cd4cf98fd830a85089b7580cece540234f2f','build-portable.py changed in UX-only release')
blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go source blob changed')
for marker2 in (
    'DEFAULT_GO_LDFLAGS = "-s -w -H windowsgui -buildid="',
    'YENC_GO_LDFLAGS = "-H windowsgui"',
    'return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS',
    '"purpose":"Windows Defender compatibility"',
): check(marker2 in builder,'Defender-compatible yEnc build protection missing: '+marker2)
for marker2 in ('python release/windows/validate-v3677-regressions.py',"$yencSymbols = @(& go tool nm $yencBinary 2>&1)"):
    check(marker2 in workflow,'Canonical release workflow protection missing: '+marker2)

# Carry forward frozen runtime behavior.
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
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3677>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')

check((APP/'version.txt').read_text().strip()=='3.6.77','version.txt mismatch')
check("const UI_VERSION = '3.6.77'" in app and '3.6.77-ux-layout-control-consistency' in index,'UI/cache identity mismatch')
check(manifest.get('version')=='3.6.77' and manifest.get('base_version')=='3.6.76' and manifest.get('adapter_version')=='3.6.77','build manifest identity mismatch')
check(manifest.get('release')=='UX Layout & Control Consistency','build manifest release name mismatch')
check(sab.ADAPTER_VERSION=='3.6.77' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.77 UX-only regression guard: PASS')
