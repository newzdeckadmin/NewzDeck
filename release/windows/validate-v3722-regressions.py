#!/usr/bin/env python3
"""NewzDeck v3.7.22 source, identity, and carried-forward safety release guard."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]
A=R/'src/app'
def rd(path):return path.read_text(encoding='utf-8')
def require(ok,msg):
 if not ok:raise AssertionError('v3.7.22 regression guard: '+msg)
js=rd(A/'static/app.js');auto=rd(A/'automation_engine.py');sab=rd(A/'sab_engine.py');server=rd(A/'server.py');m=json.loads(rd(A/'build-manifest.json'));wf=rd(R/'.github/workflows/publish-release-trigger.yml')
require(rd(A/'version.txt').strip()=='3.7.22','version.txt')
require((m['version'],m['base_version'],m['adapter_version'])==('3.7.22','3.7.21','3.7.22'),'manifest version/base/adapter')
for marker,source in [('APP_VERSION = "3.7.22"',server),('ADAPTER_VERSION = "3.7.22"',sab),("version='3.7.22'",auto),("const UI_VERSION = '3.7.22'",js)]:require(marker in source,'runtime version '+marker)
for marker in ['def _browser_final_loose_name(', 'permitted_media_exts = image_exts | AUTOMATION_MEDIA_EXTS', 'NewzDeck Loose [0-9a-f]{12}', 'browser_flat_images=loose', 'if len(staged) == 1 else original.name', 'Restored original loose-media filename', 'browser_flattened_files']:
 require(marker in sab,'video and image staging guard '+marker)
for marker in ['if action == "clear_completed":','del_files=0','by_collection','browser_flat_images=loose']:
 require(marker in sab,'preserved SAB safeguard '+marker)
for marker in ['const leadingDate=stem.match','if(!matched&&!hasDateTail)','if(!members.some(x=>x.a?.complete))suppressedGroups++;else groups.push(group)','const coverFailed=state.mediaSetBrokenKeys.has(group.key);','function mediaSetKey(a)','Cover probes cannot decide visibility of the original downloadable article']:
 require(marker in js,'v3.7.20/21 Image Sets behavior '+marker)
for marker in ['def _scan_media_cache(','def _analyze_scanned_media(','def _save_scan_media_cache(','st_mtime_ns']:
 require(marker in auto,'v3.7.19 disk I/O '+marker)
require('deferredThumbnail' in js or 'deferredRecovery' in js,'v3.7.13 gallery safeguard')
html=rd(A/'static/index.html');require(html.count('3.7.22-video-names')==3 and '<span>v3.7.22</span>' in html,'HTML cache bust/version')
require('a.version = argValue("--version", "3.7.22")' in rd(R/'src/windows/NewzDeckTray.go'),'tray version')
for marker in ["$env:VERSION -cne '3.7.22'",'validate-v3722-regressions.py','validate-v3722-loose-video.py','validate-v3721-visible-sets.js','validate-v3720-date-sequences.js','validate-v3719-library-io.py','validate-v3717-loose-filenames.py','validate-v3716-video-console.py','validate-v3715-newsgroup-browser.js','validate-v3714-completed-backend.py']:
 require(marker in wf,'Windows CI missing '+marker)
require('v3.7.22' in rd(R/'README.md') and 'v3.7.22' in rd(R/'index.html'),'README/site version')
print('validate-v3722-regressions.py: PASS (video restoration and preserved features/version guards)')
