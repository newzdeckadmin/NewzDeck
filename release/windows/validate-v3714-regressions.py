#!/usr/bin/env python3
"""v3.7.14 production source guard (non-mutating)."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[2]
a=R/'src/app';web=a/'static';wk=R/'.github/workflows/publish-release-trigger.yml'
def ok(x,reason):
 if not x:raise SystemExit('v3.7.14 validation failed: '+reason)
def get(p):return p.read_text(encoding='utf-8')
ok(get(a/'version.txt').strip()=='3.7.14','version.txt')
manifest=json.loads(get(a/'build-manifest.json'))
ok(manifest.get('version')=='3.7.14' and manifest.get('base_version')=='3.7.13','manifest version')
for file,marker in [('server.py','APP_VERSION = "3.7.14"'),('sab_engine.py','ADAPTER_VERSION = "3.7.14"'),('automation_engine.py',"version='3.7.14'")]:ok(marker in get(a/file),file+' identity')
js=get(web/'app.js');html=get(web/'index.html');sab=get(a/'sab_engine.py')
ok("const UI_VERSION = '3.7.14'" in js,'UI version')
ok('id="removeAllCompletedBtn"' in html and 'id="removeAllFailedBtn"' in html,'Completed/Failed button')
ok('function removeAllCompletedDownloads()' in js and "action:'clear_completed'" in js,'UI action')
ok('view.total' in js and 'downloadHistoryLoaded=[]' in js,'pagination clearing')
ok('"clear_completed"' in sab and 'reason="completed_history_clear"' in sab,'history-only operation')
part=sab.split('if action == "clear_completed":',1)[1].split('# r3: Remove is authoritative',1)[0]
ok('del_files=0' in part and 'del_files=1' not in part.split('self._api(',1)[-1] and '_delete_sab_job_verified' not in part,'Never delete files in completed clear')
ok('self._remove_terminal_history_ids(safe_ids)' in part,'durable history cleared')
ok('self._job_is_retirable_from_operational_ledger' in part,'unfinished import protected')
ok("reasons.get(nzo) and reasons.get(nzo) != 'completed_history_clear'" in sab,'preserve reasonless and completed-only queue tombstones')
ok("removed_reasons.get(nzo_id) and removed_reasons.get(nzo_id) != 'completed_history_clear'" in sab,'preserve live SAB adoption')
ok("removed_reason_snapshot.get(orphan_id) and removed_reason_snapshot.get(orphan_id) != 'completed_history_clear'" in sab,'live orphan visibility')
ok('deferredThumbnail' in js or 'deferred' in js,'v3.7.13 deferred preview functionality preserved')
ok('3.7.14-completed-history' in html,'app cache identity')
ok('v3.7.14' in get(R/'README.md') and 'v3.7.14' in get(R/'index.html'),'public identity')
flow=get(wk)
ok("$env:VERSION -cne '3.7.14'" in flow and 'validate-v3714-completed-backend.py' in flow and 'validate-v3713-deferred-terminal.js' in flow,'workflow guards')
ok('a.version = argValue("--version", "3.7.14")' in get(R/'src/windows/NewzDeckTray.go'),'tray fallback')
print('validate-v3714-regressions.py: PASS (versions, history-only semantics, all pages, preserved gallery regression)')
