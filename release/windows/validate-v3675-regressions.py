from __future__ import annotations
import ast, importlib.util, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def check(c,m):
    if not c: raise AssertionError(m)
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
sab=load('newzdeck_v3675_sab_guard',APP/'sab_engine.py')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

# v3.6.75 yEnc build compatibility protections are carried forward in v3.6.76. The native yEnc decoder source must
# stay byte-for-byte at the accepted v3.6.74 Git blob identity.
blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go Git blob changed; v3.6.75 yEnc compatibility protection regressed')

# The Defender-compatible helper keeps normal Go build metadata. Every other
# NewzDeck-owned native helper keeps the historical stripped profile.
for marker in (
    'DEFAULT_GO_LDFLAGS = "-s -w -H windowsgui -buildid="',
    'YENC_GO_LDFLAGS = "-H windowsgui"',
    'return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS',
    "run(['go','build','-trimpath',f'-ldflags={ldflags}'",
    '"binary_build_overrides":{',
    '"purpose":"Windows Defender compatibility"',
    '"source_behavior_changed":False',
):
    check(marker in builder,'v3.6.76 portable-builder guard missing: '+marker)
check("run(['go','build','-trimpath','-ldflags=-s -w -H windowsgui -buildid='" not in builder,
      'Portable builder still applies the stripped profile unconditionally to all helpers')

# The canonical publisher must execute this guard and prove the actual generated
# yEnc helper is not stripped before it can publish Setup/Portable assets.
for marker in (
    'python release/windows/validate-v3675-regressions.py',
    "$yencEntry = @($manifest.newzdeck_owned_binaries) | Where-Object { $_.binary -ceq 'NewzDeckYenc.exe' }",
    "$yencOverride = $manifest.binary_build_overrides.PSObject.Properties['NewzDeckYenc.exe'].Value",
    "$yencSymbols = @(& go tool nm $yencBinary 2>&1)",
):
    check(marker in workflow,'Canonical release workflow missing v3.6.76 Defender-compatibility verification: '+marker)

# Carry forward the accepted v3.6.74 browsing/diagnostics architecture unchanged.
for marker in (
    'let videoThumbRequestSeq = 0;',
    'video_request_id:requestId',
    "perfRecord('video_thumbnail_client_lifecycle'",
    'function resolveThumbnailTaskArticle(task)',
    "perfRecord('thumbnail_task_identity',0,true,{reason:'relocated'})",
    "perfRecord('thumbnail_visible_wait',visibleWaitMs,true",
):
    check(marker in app,'Accepted browsing behavior regressed: '+marker)
for marker in (
    '_BROWSER_VIDEO_ACTIVE_REQUESTS',
    'video_thumbnail_cancel_detect_delay',
    'video_thumbnail_cancel_drain',
    '"schema_version": 11',
    '"contract": "passive-runtime-browsing-performance"',
):
    check(marker in server,'Accepted schema-11 diagnostics behavior regressed: '+marker)

check('return(visible?0:1)*1e9+Math.max(0,distance)*1000+Math.max(0,sizePenalty-ageCredit);' in app,'Thumbnail scheduler scoring formula changed')
check('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;' in app,'Image HTTP admission changed')
formula='state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'
check(formula in app,'Accepted six-slot Video ceiling changed')
check('VIDEO_THUMB_SAMPLE_MB = 24' in server,'24 MB Video sample limit changed')
check('max_segments=12' in server,'12-segment Video sample cap changed')
for marker in ('const NAME_RESOLUTION_RENDER_AUTO_SOFT_MS=1400;','const NAME_RESOLUTION_RENDER_AUTO_MAX_MS=3000;','const NAME_RESOLUTION_RENDER_MANUAL_SOFT_MS=1800;','const NAME_RESOLUTION_RENDER_MANUAL_MAX_MS=4200;'):
    check(marker in app,'Accepted All Posts resolver behavior regressed: '+marker)
for marker in ('SETTINGS_SAVE_RETRY_SECONDS = 3.0','SETTINGS_SAVE_RETRYABLE_WINERRORS = frozenset({5, 32, 33})'):
    check(marker in server,'Accepted Settings reliability behavior regressed: '+marker)

tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3675>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')

check((APP/'version.txt').read_text().strip()=='3.6.76','version.txt mismatch')
check("const UI_VERSION = '3.6.76'" in app and '3.6.76-ux-readability-visual-rhythm' in index,'UI/cache identity mismatch')
check(manifest.get('version')=='3.6.76' and manifest.get('base_version')=='3.6.75' and manifest.get('adapter_version')=='3.6.76','build manifest identity mismatch')
check(manifest.get('release')=='UX Readability & Visual Rhythm','build manifest release name mismatch')
check(sab.ADAPTER_VERSION=='3.6.76' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.76 regression guard: PASS')
