#!/usr/bin/env python3
"""NewzDeck v3.7.15 production-source regression guard; read-only."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]
a=R/'src/app'; app=(a/'static/app.js').read_text(encoding='utf-8'); sab=(a/'sab_engine.py').read_text(encoding='utf-8')
check=lambda pred,msg: pred or (_ for _ in ()).throw(AssertionError('v3.7.15: '+msg))
check((a/'version.txt').read_text(encoding='utf-8').strip()=='3.7.15','version identity')
m=json.loads((a/'build-manifest.json').read_text(encoding='utf-8'));check(m['version']=='3.7.15' and m['base_version']=='3.7.14','manifest')
check('APP_VERSION = "3.7.15"' in (a/'server.py').read_text(encoding='utf-8'),'server version')
check('ADAPTER_VERSION = "3.7.15"' in sab,'SAB adapter version')
check("version='3.7.15'" in (a/'automation_engine.py').read_text(encoding='utf-8'),'automation version')
check("const UI_VERSION = '3.7.15'" in app,'client version')
check('smart_binaries:true' in app and 'progressive:!append' in app,'equal-mode smart reconstruction')
check('else if(additive||isAllPostsMode())' in app,'additive All Posts selection')
check('const packageBatches=new Map(),loose=[]' in app,'individually batched loose files')
check('client_key:articleKey(a)' in app and 'submittedKeys.add' in app,'partial-submit accounting')
check('browser_flat_images=loose' in sab and 'by_collection' in sab,'separate SAB jobs')
check('if action == "clear_completed":' in sab and 'del_files=0' in sab,'v3.7.14 completed history-only guard')
check('deferredThumbnail' in app or 'deferredRecovery' in app,'v3.7.13 previews present')
html=(a/'static/index.html').read_text(encoding='utf-8');check(html.count('3.7.15-newsgroup-browse')==3 and '<span>v3.7.15</span>' in html,'client html/cache')
flow=(R/'.github/workflows/publish-release-trigger.yml').read_text(encoding='utf-8')
for marker in ["$env:VERSION -cne '3.7.15'",'validate-v3715-queue-backend.py','validate-v3715-newsgroup-browser.js','validate-v3714-completed-backend.py','validate-v3714-completed-ui.js','validate-v3713-deferred-terminal.js']:
 check(marker in flow,'workflow '+marker)
check('a.version = argValue("--version", "3.7.15")' in (R/'src/windows/NewzDeckTray.go').read_text(encoding='utf-8'),'tray version')
check('v3.7.15' in (R/'README.md').read_text(encoding='utf-8') and 'v3.7.15' in (R/'index.html').read_text(encoding='utf-8'),'public version')
print('validate-v3715-regressions.py: PASS (versions, unified browse, separate queue, prior history and preview guards)')
