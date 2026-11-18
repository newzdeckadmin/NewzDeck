#!/usr/bin/env python3
"""Current v3.7.32 full identity gate; retain older feature-specific tests."""
from pathlib import Path
import json, re
ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'src/app'
def get(p):return (ROOT/p).read_text('utf-8')
def check(ok,msg):
 if not ok:raise AssertionError('v3.7.32 release gate: '+msg)
m=json.loads(get('src/app/build-manifest.json'))
check(get('src/app/version.txt').strip()=='3.7.32','runtime version')
check((m['version'],m['base_version'],m['adapter_version'],m['sab_version'],m['sabctools_version'])==('3.7.32','3.7.31','3.7.32','5.1.3','9.6.3'),'manifest')
for path,needle in [('src/app/server.py','APP_VERSION = "3.7.32"'),('src/app/sab_engine.py','ADAPTER_VERSION = "3.7.32"'),('src/app/automation_engine.py',"version='3.7.32'"),('src/app/static/app.js',"const UI_VERSION = '3.7.32'")]:check(needle in get(path),path+' version')
check('3.7.32' in get('src/app/static/index.html'),'UI cache busting')
s=get('src/app/server.py');js=get('src/app/static/app.js');sab=get('src/app/sab_engine.py')
for marker in ['class ManualGrabOperations:',"if data.get('async_grab') is True:","/api/automation/releases/grab/status","GRAB_OPERATIONS.start(data)","GRAB_OPERATIONS.get(identifier)",'MEDIA_AUTOMATION.grab_release(data)']:
 check(marker in s,'asynchronous API '+marker)
for marker in ["client_request_id",'pollManualGrabOperation','already_queued','reservation_only','pending_engine_handoff','grabRequestIdentity']:
 check(marker in js,'UI state '+marker)
for marker in ['_terminal_history_scope_for_row','post in {"", "completed", "not_needed", "disabled"}',"completed_history_clear"]:
 check(marker in sab,'history safety '+marker)
check((ROOT/'release/RELEASE_NOTES_v3.7.32.md').is_file(),'release notes')
wf=ROOT/'.github/workflows/publish-release-trigger.yml'
if wf.exists():
 w=wf.read_text('utf-8')
 for marker in ["$env:VERSION -cne '3.7.32'",r"^\d+\.\d+\.\d+$",'validate-v3732-release-gate.py','validate-v3732-async-grab.py','validate-v3732-history.py','validate-v3732-grab-ui.js','validate-v3732-sab-preservation.py','validate-v3731-video-discovery.py','validate-v3729-metadata-refresh.py']:
  check(marker in w,'current workflow gate '+marker)
 check('python release/windows/validate-v3731-release-gate.py\n' not in w,'stale current-version full gate')
 check('windows-release.yml' not in w,'retired duplicate workflow')
 build=ROOT/'release/windows/build-release.ps1'
 if build.exists():check(r"^\d+\.\d+\.\d+$" in build.read_text('utf8'),'installer version validation')
 iss=ROOT/'release/windows/NewzDeck.iss'
 if iss.exists():
  ins=iss.read_text('utf8');check('VersionInfoVersion={#AppVersion}.0' in ins,'three-part Windows version resource')
 tray=ROOT/'src/windows/NewzDeckTray.go'
 if tray.exists():check('a.version = argValue("--version", "3.7.32")' in tray.read_text('utf8'),'native tray version')
print('PASS: v3.7.32 version identity, preserved SAB/video/metadata, async Grab API, correct history classification, guarded canonical Windows three-part release gates')
