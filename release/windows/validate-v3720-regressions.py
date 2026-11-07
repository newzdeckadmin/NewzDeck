#!/usr/bin/env python3
"""v3.7.20 exact version, date-based classifier, and preserved feature gates."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]; A=R/'src/app'
def rd(p):return p.read_text(encoding='utf-8')
def gate(ok,msg):
 if not ok:raise AssertionError('v3.7.20 source gate: '+msg)
js=rd(A/'static/app.js');auto=rd(A/'automation_engine.py');sab=rd(A/'sab_engine.py');server=rd(A/'server.py');m=json.loads(rd(A/'build-manifest.json'))
gate(rd(A/'version.txt').strip()=='3.7.20' and m['version']=='3.7.20' and m['base_version']=='3.7.19' and m['adapter_version']=='3.7.20','version/manifest identities')
gate('APP_VERSION = "3.7.20"' in server and 'ADAPTER_VERSION = "3.7.20"' in sab and "version='3.7.20'" in auto and "const UI_VERSION = '3.7.20'" in js,'runtime source version identities')
for fragment in ['const leadingDate=stem.match','if(!matched&&!hasDateTail){','function mediaSetKey(a)','function mediaSetSubjectSequence(value)','function mediaSetSequenceBase(a)','mediaSetPosterKey(a.from)']:
 gate(fragment in js,'Image Sets classifier missing: '+fragment)
for fragment in ['def _scan_media_cache(', 'def _analyze_scanned_media(', 'def _save_scan_media_cache(', 'st_mtime_ns', 'if scan_cache_changed:']:
 gate(fragment in auto,'v3.7.19 disk-I/O optimization missing: '+fragment)
gate("'media_info':traits,'cutoff_met':self._quality_cutoff_met(q,profile,traits)" in auto,'preserved metadata result reuse missing')
gate('def _browser_final_loose_name(' in sab and 'Restored original loose-image filename' in sab,'v3.7.17 filename restore missing')
gate('if action == "clear_completed":' in sab and 'del_files=0' in sab,'v3.7.14 safe Completed cleanup missing')
gate('browser_flat_images=loose' in sab and 'by_collection' in sab,'v3.7.15 bulk jobs missing')
gate('smart_binaries:true' in js and 'progressive:!append' in js,'v3.7.15 media filter missing')
gate('deferredThumbnail' in js or 'deferredRecovery' in js,'v3.7.13 gallery recovery missing')
html=rd(A/'static/index.html');gate(html.count('3.7.20-date-sets')==3 and '<span>v3.7.20</span>' in html,'browser version/cache busting')
wf=rd(R/'.github/workflows/publish-release-trigger.yml')
for marker in ["$env:VERSION -cne '3.7.20'", 'validate-v3720-regressions.py', 'validate-v3720-date-sequences.js', 'validate-v3719-library-io.py', 'validate-v3717-loose-filenames.py', 'validate-v3716-video-console.py', 'validate-v3715-newsgroup-browser.js', 'validate-v3715-queue-backend.py', 'validate-v3714-completed-backend.py']:
 gate(marker in wf,'Windows CI gate missing: '+marker)
gate('a.version = argValue("--version", "3.7.20")' in rd(R/'src/windows/NewzDeckTray.go'),'tray version')
gate('v3.7.20' in rd(R/'README.md') and 'v3.7.20' in rd(R/'index.html'),'release site and README identities')
print('validate-v3720-regressions.py: PASS (version identities, date-prefix detection, preserved runtime and release gates)')
