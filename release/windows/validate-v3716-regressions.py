#!/usr/bin/env python3
"""v3.7.16 release gate: version coherence and preserved prior fixes."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]; A=R/'src/app'
def read(p):return p.read_text(encoding='utf-8')
def check(ok,msg):
 if not ok:raise AssertionError('v3.7.16 gate: '+msg)
app=read(A/'static/app.js'); sab=read(A/'sab_engine.py');server=read(A/'server.py')
m=json.loads(read(A/'build-manifest.json'))
check(read(A/'version.txt').strip()=='3.7.16' and m['version']=='3.7.16' and m['base_version']=='3.7.15','manifest/version')
check('APP_VERSION = "3.7.16"' in server and 'ADAPTER_VERSION = "3.7.16"' in sab,'backend identity')
check("version='3.7.16'" in read(A/'automation_engine.py') and "const UI_VERSION = '3.7.16'" in app,'automation/client identity')
check('smart_binaries:true' in app and 'progressive:!append' in app,'v3.7.15 unified media scanning')
check('else if(additive||isAllPostsMode())' in app and 'const packageBatches=new Map(),loose=[]' in app,'v3.7.15 selection/queue')
check('browser_flat_images=loose' in sab and 'by_collection' in sab,'v3.7.15 individual files')
check('if action == "clear_completed":' in sab and 'del_files=0' in sab,'v3.7.14 safe completed history')
check('deferredThumbnail' in app or 'deferredRecovery' in app,'v3.7.13 deferred preview')
check(read(A/'static/index.html').count('3.7.16-video-console')==3,'HTML cache version')
check('<span>v3.7.16</span>' in read(A/'static/index.html'),'HTML sidebar version')
flow=read(R/'.github/workflows/publish-release-trigger.yml')
for marker in ["$env:VERSION -cne '3.7.16'",'validate-v3716-regressions.py','validate-v3716-video-console.py','validate-v3715-newsgroup-browser.js','validate-v3715-queue-backend.py','validate-v3714-completed-backend.py','validate-v3713-deferred-terminal.js']:
 check(marker in flow,'workflow '+marker)
check('a.version = argValue("--version", "3.7.16")' in read(R/'src/windows/NewzDeckTray.go'),'tray fallback')
check('v3.7.16' in read(R/'README.md') and 'v3.7.16' in read(R/'index.html'),'public release identity')
print('validate-v3716-regressions.py: PASS (version, silent video, v3.7.15 queue, v3.7.14 history, v3.7.13 previews)')
