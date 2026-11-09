#!/usr/bin/env python3
"""Full v3.7.30 identity gate; older FULL version gates must never execute."""
from pathlib import Path
import ast,json,re
R=Path(__file__).resolve().parents[2];A=R/'src/app'
def read(p):return p.read_text('utf-8')
def check(cond,msg):
 if not cond:raise AssertionError('v3.7.30 release gate: '+msg)
s=read(A/'server.py');e=read(A/'sab_engine.py');a=read(A/'automation_engine.py');u=read(A/'static/app.js');h=read(A/'static/index.html');m=json.loads(read(A/'build-manifest.json'))
check(read(A/'version.txt').strip()=='3.7.30','version.txt')
check((m.get('version'),m.get('base_version'),m.get('adapter_version'),m.get('sab_version'),m.get('sabctools_version'))==('3.7.30','3.7.29','3.7.30','5.1.3','9.6.3'),'manifest')
for fragment,body in [('APP_VERSION = "3.7.30"',s),('ADAPTER_VERSION = "3.7.30"',e),("version='3.7.30'",a),("const UI_VERSION = '3.7.30'",u)]:check(fragment in body,fragment)
check(h.count('3.7.30-sab513-security')==3 and '<span>v3.7.30</span>' in h,'UI version and cache bust')
for marker in ('metadata_refresh_schema','metadata_pending_retry_ids','def _metadata_refresh_worker(self, *, retry_ids:','allow_cached_fallback=not fresh','metadata_refresh_error_ts'):check(marker in a,'metadata '+marker)
for marker in ('/api/downloads/pulse','/api/diagnostics/ping','_GROUP_SEARCH_LANES = threading.BoundedSemaphore(4)','def _parse_yenc_part('):check(marker in s,'server '+marker)
for marker in ('def presentation_pulse(self, limit: int = 500)','def _browser_final_loose_name(','if action == "clear_completed":'):check(marker in e,'SAB '+marker)
for marker in ("api('/api/downloads/pulse'","browseView?.classList.toggle('all-posts-wide',hideRelatedPane)",'metadata_refresh_error','Awaiting verified home-release metadata'):check(marker in u,'UI '+marker)
for p in ('server.py','sab_engine.py','automation_engine.py'):ast.parse(read(A/p),filename=p)
if (R/'THIRD_PARTY_NOTICES.md').exists():
 t=read(R/'THIRD_PARTY_NOTICES.md');check('## SABnzbd 5.1.3' in t and '## SABCTools 9.6.3' in t and '## SABnzbd 5.1.2' not in t,'licenses')
if (R/'.github/workflows/publish-release-trigger.yml').exists():
 w=read(R/'.github/workflows/publish-release-trigger.yml')
 for marker in ("$env:VERSION -cne '3.7.30'",'python release/windows/validate-v3730-release-gate.py','python release/windows/validate-v3730-sab-upgrade.py','python release/windows/validate-v3729-metadata-refresh.py','node release/windows/validate-v3729-metadata-ui.js','python release/windows/validate-v3727-download-pulse.py','python release/windows/validate-v3726-live-search.py'):check(marker in w,'CI '+marker)
 check(not re.search(r'^\s*python release/windows/validate-v372[6789]-regressions\.py\s*$',w,re.M),'old full release gate')
 if (R/'src/windows/NewzDeckTray.go').exists():check('a.version = argValue("--version", "3.7.30")' in read(R/'src/windows/NewzDeckTray.go'),'tray identity')
 for p in ('README.md','index.html','docs/SOURCE_RELEASES.md'):
  if (R/p).exists():check('v3.7.30' in read(R/p),'docs '+p)
print('PASS: v3.7.30 release identity, SAB pin, metadata/download safeguards, current-only release gate')
