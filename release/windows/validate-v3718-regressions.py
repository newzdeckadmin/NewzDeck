#!/usr/bin/env python3
"""v3.7.18 CI path-identity recovery and carried-forward source regression guard."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]; A=R/'src/app'
def rd(p):return p.read_text(encoding='utf-8')
def gate(ok,msg):
 if not ok:raise AssertionError('v3.7.18 release gate: '+msg)
server=rd(A/'server.py'); sab=rd(A/'sab_engine.py'); app=rd(A/'static/app.js')
manifest=json.loads(rd(A/'build-manifest.json'))
gate(rd(A/'version.txt').strip()=='3.7.18' and manifest['version']=='3.7.18' and manifest['base_version']=='3.7.17','version identities')
gate('APP_VERSION = "3.7.18"' in server and 'ADAPTER_VERSION = "3.7.18"' in sab,'backend identities')
gate("version='3.7.18'" in rd(A/'automation_engine.py') and "const UI_VERSION = '3.7.18'" in app,'UI and automation identities')
gate('def _browser_final_loose_name(' in sab and 'Restored original loose-image filename' in sab,'preserved filename fix')
gate('preferred = self._browser_final_loose_name(source.name, expected, staging_name)' in sab,'root filename fix')
gate('self._browser_final_loose_name(original.name, expected, staging_name)' in sab,'staged filename fix')
gate('visible_filename if bool(meta.get("browser_flattened")) and len(flat_names) == 1' in sab,'truthful Completed filenames')
gate('browser_flat_images=loose' in sab and 'by_collection' in sab,'v3.7.15 queue grouping')
gate('if action == "clear_completed":' in sab and 'del_files=0' in sab,'v3.7.14 history-only cleanup')
gate('smart_binaries:true' in app and 'progressive:!append' in app,'v3.7.15 media filter')
gate('deferredThumbnail' in app or 'deferredRecovery' in app,'v3.7.13 preview recovery')
html=rd(A/'static/index.html')
gate(html.count('3.7.18-path-regression')==3 and '<span>v3.7.18</span>' in html,'HTML version/cache identity')
test=rd(R/'release/windows/validate-v3717-loose-filenames.py')
gate("pathlib.Path(slot['storage']).samefile(root)" in test,'Windows 8.3 path alias check must compare directory identity')
gate("eq(slot['storage'],str(root)" not in test,'fragile lexical path equality must be removed')
workflow=rd(R/'.github/workflows/publish-release-trigger.yml')
for marker in ["$env:VERSION -cne '3.7.18'",'validate-v3718-regressions.py','validate-v3717-loose-filenames.py','validate-v3716-video-console.py','validate-v3715-newsgroup-browser.js','validate-v3715-queue-backend.py','validate-v3714-completed-backend.py','validate-v3713-deferred-terminal.js']:
 gate(marker in workflow,'workflow includes '+marker)
gate('a.version = argValue("--version", "3.7.18")' in rd(R/'src/windows/NewzDeckTray.go'),'tray version')
gate('v3.7.18' in rd(R/'README.md') and 'v3.7.18' in rd(R/'index.html'),'release surfaces')
print('validate-v3718-regressions.py: PASS (Windows directory identity, v3.7.17 filename fix, preserved features)')
