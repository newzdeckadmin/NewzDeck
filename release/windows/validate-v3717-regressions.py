#!/usr/bin/env python3
"""NewzDeck v3.7.17 regression guard for exact release source and carried-forward features."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]; A=R/'src/app'
def rd(p): return p.read_text(encoding='utf-8')
def gate(ok,msg):
 if not ok: raise AssertionError('v3.7.17 gate: '+msg)
server=rd(A/'server.py');sab=rd(A/'sab_engine.py');app=rd(A/'static/app.js')
manifest=json.loads(rd(A/'build-manifest.json'))
gate(rd(A/'version.txt').strip()=='3.7.17' and manifest['version']=='3.7.17' and manifest['base_version']=='3.7.16','version identities')
gate('APP_VERSION = "3.7.17"' in server and 'ADAPTER_VERSION = "3.7.17"' in sab,'backend versions')
gate("version='3.7.17'" in rd(A/'automation_engine.py') and "const UI_VERSION = '3.7.17'" in app,'UI/Automation versions')
gate('def _browser_final_loose_name(' in sab and 'Restored original loose-image filename' in sab,'scoped rename implementation')
gate('preferred = self._browser_final_loose_name(source.name, expected, staging_name)' in sab,'root completion rename')
gate('self._browser_final_loose_name(original.name, expected, staging_name)' in sab,'staged completion rename')
gate('visible_filename if bool(meta.get("browser_flattened")) and len(flat_names) == 1' in sab,'Completed name')
gate('browser_flat_images=loose' in sab and 'by_collection' in sab,'v3.7.15 queue separation')
gate('if action == "clear_completed":' in sab and 'del_files=0' in sab,'v3.7.14 history-only cleanup')
gate('smart_binaries:true' in app and 'progressive:!append' in app,'v3.7.15 media filtering')
gate('deferredThumbnail' in app or 'deferredRecovery' in app,'v3.7.13 gallery')
gate(rd(A/'static/index.html').count('3.7.17-loose-filenames')==3,'HTML cache')
gate('<span>v3.7.17</span>' in rd(A/'static/index.html'),'HTML sidebar')
flow=rd(R/'.github/workflows/publish-release-trigger.yml')
for marker in ["$env:VERSION -cne '3.7.17'",'validate-v3717-regressions.py','validate-v3717-loose-filenames.py','validate-v3716-video-console.py','validate-v3715-newsgroup-browser.js','validate-v3715-queue-backend.py','validate-v3714-completed-backend.py','validate-v3713-deferred-terminal.js']:
 gate(marker in flow,'workflow '+marker)
gate('a.version = argValue("--version", "3.7.17")' in rd(R/'src/windows/NewzDeckTray.go'),'tray version')
gate('v3.7.17' in rd(R/'README.md') and 'v3.7.17' in rd(R/'index.html'),'release surfaces')
print('validate-v3717-regressions.py: PASS (v3.7.17 scoped naming, preserved legacy features)')
