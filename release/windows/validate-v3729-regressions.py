#!/usr/bin/env python3
"""v3.7.29 source and production CI guard; older full version gates are forbidden."""
import json,re,ast
from pathlib import Path
R=Path(__file__).resolve().parents[2];A=R/'src/app'
def rd(p):return p.read_text(encoding='utf-8')
def require(x,m):
    if not x:raise AssertionError('v3.7.29 release gate: '+m)
server=rd(A/'server.py');sab=rd(A/'sab_engine.py');auto=rd(A/'automation_engine.py');ui=rd(A/'static/app.js');ht=rd(A/'static/index.html')
manifest=json.loads(rd(A/'build-manifest.json'))
require(rd(A/'version.txt').strip()=='3.7.29','version.txt')
require((manifest.get('version'),manifest.get('base_version'),manifest.get('adapter_version'))==('3.7.29','3.7.28','3.7.29'),'manifest identity')
for text,body in [('APP_VERSION = "3.7.29"',server),('ADAPTER_VERSION = "3.7.29"',sab),("version='3.7.29'",auto),("const UI_VERSION = '3.7.29'",ui)]:require(text in body,'runtime identity '+text)
require(ht.count('3.7.29-metadata-reliability')==3 and '<span>v3.7.29</span>' in ht,'frontend asset revision/visible version')
for marker in ('requested_id=str(ident or', 'item_id=str(item.get(\'id\')', 'only_ids:list[str]|None=None', 'metadata_refresh_schema', 'metadata_pending_retry_ids', 'last_metadata_wanted_transition_ts', 'def _metadata_refresh_worker(self, *, retry_ids:', 'allow_cached_fallback=not fresh', 'def refresh_media_metadata(self,ident:str):', 'metadata_refresh_error_ts'):
    require(marker in auto,'metadata hardening missing: '+marker)
require('fetched[ident]' not in auto[auto.index('    def refresh_monitored_metadata('):auto.index('    def _auto_release_matches(')],'loop-filter regression: mutable ident used to index refreshed title')
for marker in ('/api/downloads/pulse','/api/diagnostics/ping','_GROUP_SEARCH_LANES = threading.BoundedSemaphore(4)','def parse_overview(lines: Iterable[bytes], *, search_filter:','def _parse_yenc_part('):
    require(marker in server,'preserve Downloads/search backend: '+marker)
for marker in ('def presentation_pulse(self, limit: int = 500)', 'age <= 3.0','def _browser_final_loose_name(', 'if action == "clear_completed":'):
    require(marker in sab,'preserve SAB/Downloads safety: '+marker)
for marker in ('downloadBulkQueueActive++',"api('/api/downloads/pulse'", "api('/api/diagnostics/ping'", "browseView?.classList.toggle('all-posts-wide',hideRelatedPane)", 'metadata_refresh_error', 'Awaiting verified home-release metadata'):
    require(marker in ui,'preserve Downloads/Image Sets/metadata UI: '+marker)
ast.parse(auto);ast.parse(server);ast.parse(sab)
w=R/'.github/workflows/publish-release-trigger.yml'
if w.is_file():
    workflow=rd(w)
    require("$env:VERSION -cne '3.7.29'" in workflow and 'python release/windows/validate-v3729-regressions.py' in workflow,'production version gate missing')
    require(not re.search(r'^\s*python release/windows/validate-v372[678]-regressions\.py\s*$',workflow,re.M),'older version-specific full regression gate called')
    for marker in ('python release/windows/validate-v3729-metadata-refresh.py','node release/windows/validate-v3729-metadata-ui.js','python release/windows/validate-v3727-download-pulse.py','python release/windows/validate-v3726-live-search.py','python release/windows/validate-v3724-yenc-prefix.py'):
        require(marker in workflow,'targeted CI regression missing: '+marker)
    go=R/'src/windows/NewzDeckTray.go'
    if go.is_file():require('a.version = argValue("--version", "3.7.29")' in rd(go),'tray version')
    for p in ('README.md','index.html'):
        if (R/p).is_file():require('v3.7.29' in rd(R/p),'docs/website version: '+p)
print('PASS: v3.7.29 release identity, complete metadata/title sweep, new runtime/error guards, retained download/search regressions and cross-version CI safety')
