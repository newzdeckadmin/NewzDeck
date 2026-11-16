#!/usr/bin/env python3
"""v3.7.31 source identity and retained-reliability gate; no network or writes."""
from pathlib import Path
import ast, json, re
R=Path(__file__).resolve().parents[2];A=R/'src/app'
def read(path):return path.read_text('utf-8')
def check(ok,reason):
    if not ok:raise AssertionError('v3.7.31 gate: '+reason)
s=read(A/'server.py');a=read(A/'automation_engine.py');e=read(A/'sab_engine.py');u=read(A/'static/app.js');h=read(A/'static/index.html');m=json.loads(read(A/'build-manifest.json'))
check(read(A/'version.txt').strip()=='3.7.31','version identity')
check((m['version'],m['base_version'],m['adapter_version'],m['sab_version'],m['sabctools_version'])==('3.7.31','3.7.30','3.7.31','5.1.3','9.6.3'),'manifest identity and unchanged native engine')
for marker,body in [('APP_VERSION = "3.7.31"',s),('ADAPTER_VERSION = "3.7.31"',e),("version='3.7.31'",a),("const UI_VERSION = '3.7.31'",u)]:check(marker in body,'application identity '+marker)
check('v3.7.31' in h and '3.7.31-video-discovery' in h,'HTML version and cache busting')
for marker in ('VIDEO_DISCOVERY_TARGET = 18','VIDEO_DISCOVERY_MAX_HEADER_POSITIONS = 3600','_finish_progressive_video_page(', 'video_discovery_job', 'scan_low - limit','_video_discovery_complete_count(', 'named_buckets.setdefault((normalize_subject', 'VIDEO_MEDIA_EXTS', 'SABCTOOLS_VERSION'):
    # SABCTOOLS_VERSION belongs to GitHub workflow, not server.
    if marker=='SABCTOOLS_VERSION':continue
    check(marker in s,'video discovery safeguard '+marker)
for marker in ('video_discovery:videos','smart_binaries:!videos','a.media?.kind!==\'video\'','if(state.smartBinaryPending)scheduleProgressiveBinaryCompletion','Searching older headers for complete videos','if(state.selectedGroup){state.loadedPages.clear()'):
    check(marker in u,'video UI safeguard '+marker)
for marker in ('metadata_pending_retry_ids','allow_cached_fallback=not fresh','metadata_refresh_error_ts'):check(marker in a,'metadata '+marker)
for marker in ('SAB_VERSION = "5.1.3"','SAB_WINDOWS_X64_SHA256','self.admin_dir = self.root / "admin"'):check(marker in e,'SAB '+marker)
for marker in ('/api/downloads/pulse','/api/diagnostics/ping','def _parse_yenc_part('):check(marker in s,'existing browser/download '+marker)
for f in (A/'server.py',A/'sab_engine.py',A/'automation_engine.py'):ast.parse(read(f),str(f))
workflow=R/'.github/workflows/publish-release-trigger.yml'
if workflow.exists():
    w=read(workflow)
    for t in ("$env:VERSION -cne '3.7.31'",'python release/windows/validate-v3731-release-gate.py','python release/windows/validate-v3731-video-discovery.py','node release/windows/validate-v3731-video-ui.js','python release/windows/validate-v3731-sab-preservation.py','python release/windows/validate-v3729-metadata-refresh.py','node release/windows/validate-v3715-newsgroup-browser.js'):
        check(t in w,'CI regression gate '+t)
    check('python release/windows/validate-v3730-release-gate.py\n' not in w,'obsolete full release gate')
    check('windows-release.yml' not in [p.name for p in (R/'.github/workflows').glob('*.yml')], 'retired Windows workflow')
    tray=R/'src/windows/NewzDeckTray.go'
    if tray.exists():check('a.version = argValue("--version", "3.7.31")' in read(tray),'native tray version')
print('PASS: v3.7.31 version identity, bounded video discovery, thumbnail retention, preserved SAB/metadata/Downloads, no obsolete CI release gate')
