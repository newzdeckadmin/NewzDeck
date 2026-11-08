#!/usr/bin/env python3
"""NewzDeck v3.7.28 source identity and cross-version CI regression guard."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[2];A=R/'src/app'
def rd(p):return p.read_text(encoding='utf-8')
def check(ok,msg):
 if not ok: raise AssertionError('v3.7.28 gate: '+msg)
s=rd(A/'server.py'); sab=rd(A/'sab_engine.py');ui=rd(A/'static/app.js');auto=rd(A/'automation_engine.py')
manifest=json.loads(rd(A/'build-manifest.json'))
check(rd(A/'version.txt').strip()=='3.7.28','version.txt')
check(tuple(manifest.get(x) for x in ('version','base_version','adapter_version'))==('3.7.28','3.7.27','3.7.28'),'manifest identity')
for marker,t in [('APP_VERSION = "3.7.28"',s),('ADAPTER_VERSION = "3.7.28"',sab),("const UI_VERSION = '3.7.28'",ui),("version='3.7.28'",auto)]:check(marker in t,'runtime identity: '+marker)
ht=rd(A/'static/index.html')
check(ht.count('3.7.28-validation-recovery')==3 and '<span>v3.7.28</span>' in ht,'frontend assets/visible version')
for marker in ('def presentation_pulse(self, limit: int = 500)','_queue_sample_lock','age <= 3.0'):
 check(marker in sab,'preserve bounded SAB sample: '+marker)
for marker in ('/api/downloads/pulse','/api/diagnostics/ping','def _parse_yenc_part(', 'class GroupSearchManager:', '_GROUP_SEARCH_LANES = threading.BoundedSemaphore(4)', 'def parse_overview(lines: Iterable[bytes], *, search_filter:'):
 check(marker in s,'preserve Downloads/Diagnostics/search feature: '+marker)
for marker in ('downloadBulkQueueActive++',"api('/api/downloads/pulse'", "api('/api/diagnostics/ping'", 'downloadLastFullAttemptAt',"browseView?.classList.toggle('all-posts-wide',hideRelatedPane)"):
 check(marker in ui,'preserve Downloads/Diagnostics/Image Sets feature: '+marker)
for marker in ('def _browser_final_loose_name(', 'if action == "clear_completed":'):
 check(marker in sab,'retain SAB/download safety: '+marker)
for marker in ('def _scan_media_cache(', 'st_mtime_ns'):
 check(marker in auto,'retain media cache: '+marker)
workflow=R/'.github/workflows/publish-release-trigger.yml'
if workflow.is_file():
 w=rd(workflow)
 check("$env:VERSION -cne '3.7.28'" in w and 'python release/windows/validate-v3728-regressions.py' in w,'v3.7.28 production gate missing')
 check(not re.search(r'^\s*python release/windows/validate-v372[67]-regressions\.py\s*$',w,re.M),'obsolete version-specific full CI gate executed')
 for marker in ('python release/windows/validate-v3727-download-pulse.py','node release/windows/validate-v3727-download-ui.js','python release/windows/validate-v3726-live-search.py','python release/windows/validate-v3726-early-filter.py','node release/windows/validate-v3725-image-sets-pane.js','python release/windows/validate-v3724-yenc-prefix.py'):
  check(marker in w,'retained targeted regression absent: '+marker)
 tray=R/'src/windows/NewzDeckTray.go'
 if tray.is_file():check('a.version = argValue("--version", "3.7.28")' in rd(tray),'tray identity')
 for rel in ('README.md','index.html'):
  p=R/rel
  if p.is_file():check('v3.7.28' in rd(p),'website/document identity: '+rel)
print('PASS: v3.7.28 recovered Windows release identity and all retained functional guards, no obsolete historical full gate')
