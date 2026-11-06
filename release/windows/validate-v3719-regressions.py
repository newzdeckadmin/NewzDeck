#!/usr/bin/env python3
"""v3.7.19 exact release identity, I/O optimization and preserved feature gates."""
from pathlib import Path
import json,ast
R=Path(__file__).resolve().parents[2]; A=R/'src/app'
def rd(p):return p.read_text(encoding='utf-8')
def gate(x,msg):
 if not x:raise AssertionError('v3.7.19 source gate: '+msg)
a=rd(A/'automation_engine.py');sab=rd(A/'sab_engine.py');sv=rd(A/'server.py');app=rd(A/'static/app.js');m=json.loads(rd(A/'build-manifest.json'))
gate(rd(A/'version.txt').strip()=='3.7.19' and m['version']=='3.7.19' and m['base_version']=='3.7.18' and m['adapter_version']=='3.7.19','manifest/version identity')
gate('APP_VERSION = "3.7.19"' in sv and 'ADAPTER_VERSION = "3.7.19"' in sab and "version='3.7.19'" in a and "const UI_VERSION = '3.7.19'" in app,'source version identities')
for token in ['def _scan_media_cache(', 'def _analyze_scanned_media(', 'def _save_scan_media_cache(', 'st_mtime_ns','_write_compact(self.media_scan_cache_file','resolution_hint=', 'if scan_cache_changed:']:
 gate(token in a,'Automation cache guard: '+token)
gate("'media_info':traits,'cutoff_met':self._quality_cutoff_met(q,profile,traits)" in a,'single metadata result reused for display and quality')
gate('def _browser_final_loose_name(' in sab and 'Restored original loose-image filename' in sab,'v3.7.17 filename restoration')
gate('if action == "clear_completed":' in sab and 'del_files=0' in sab,'v3.7.14 history-only cleanup')
gate('browser_flat_images=loose' in sab and 'by_collection' in sab,'v3.7.15 queued-file grouping')
gate('smart_binaries:true' in app and 'progressive:!append' in app,'v3.7.15 media filtering')
gate('deferredThumbnail' in app or 'deferredRecovery' in app,'v3.7.13 preview recovery')
html=rd(A/'static/index.html');gate(html.count('3.7.19-disk-io')==3 and '<span>v3.7.19</span>' in html,'browser cache-buster')
workflow=rd(R/'.github/workflows/publish-release-trigger.yml')
for token in ["$env:VERSION -cne '3.7.19'",'validate-v3719-regressions.py','validate-v3719-library-io.py','validate-v3717-loose-filenames.py','validate-v3716-video-console.py','validate-v3715-newsgroup-browser.js','validate-v3715-queue-backend.py','validate-v3714-completed-backend.py']:
 gate(token in workflow,'Windows CI gate missing '+token)
gate('a.version = argValue("--version", "3.7.19")' in rd(R/'src/windows/NewzDeckTray.go'),'tray version')
gate('v3.7.19' in rd(R/'README.md') and 'v3.7.19' in rd(R/'index.html'),'release surfaces')
print('validate-v3719-regressions.py: PASS (version identities, persistent analysis cache, preserved gallery/queue/filename/Completed behavior)')
