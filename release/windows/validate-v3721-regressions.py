#!/usr/bin/env python3
"""NewzDeck v3.7.21 Image Sets visibility/source identity regression guard."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'src/app'
def rd(p):return p.read_text(encoding='utf-8')
def check(test,what):
 if not test:raise AssertionError('v3.7.21 source regression: '+what)
js=rd(APP/'static/app.js');auto=rd(APP/'automation_engine.py');sab=rd(APP/'sab_engine.py');server=rd(APP/'server.py');m=json.loads(rd(APP/'build-manifest.json'))
check(rd(APP/'version.txt').strip()=='3.7.21' and (m['version'],m['base_version'],m['adapter_version'])==('3.7.21','3.7.20','3.7.21'),'exact release versions')
for mark in ['APP_VERSION = "3.7.21"' , 'ADAPTER_VERSION = "3.7.21"']:
 check(mark in (server+sab),'runtime version marker: '+mark)
check("version='3.7.21'" in auto and "const UI_VERSION = '3.7.21'" in js,'Automation/browser version')
for mark in ['const leadingDate=stem.match','const hasDateTail=','if(!matched&&!hasDateTail)','function mediaSetKey(a)','mediaSetPosterKey(a.from)','members.length>=3']:
 check(mark in js,'v3.7.20 date recognition still present: '+mark)
for mark in ['if(!members.some(x=>x.a?.complete))suppressedGroups++;else groups.push(group)',
             'const coverFailed=state.mediaSetBrokenKeys.has(group.key);',
             'if(!state.mediaSetBrokenKeys.has(group.key)&&!hasLoadedCover',
             'if(role===\'set-cover\'&&info.code===\'media_set_unavailable\')',
             'Cover probes cannot decide visibility of the original downloadable article',
             'Only an individual preview may suppress its article',
             'turn Image Sets OFF to browse individually']:
 check(mark in js,'unavailable group visibility fix missing: '+mark)
check("if(state.mediaSetBrokenKeys.has(key)||!members.some(x=>x.a?.complete))" not in js,'disappearing group condition still active')
check("if(card)card.remove();renderRelatedMediaPane(null,{incremental:true});return}" not in js,'old hide entire group failure path still active')
for mark in ['def _scan_media_cache(', 'def _analyze_scanned_media(', 'def _save_scan_media_cache(', 'st_mtime_ns']:
 check(mark in auto,'v3.7.19 media disk-I/O optimization missing')
check('def _browser_final_loose_name(' in sab and 'Restored original loose-image filename' in sab,'v3.7.17 name restore missing')
check('if action == "clear_completed":' in sab and 'del_files=0' in sab,'v3.7.14 safe history removal missing')
check('browser_flat_images=loose' in sab and 'by_collection' in sab,'v3.7.15 queueing missing')
check('deferredThumbnail' in js or 'deferredRecovery' in js,'v3.7.13 gallery protection missing')
html=rd(APP/'static/index.html');check(html.count('3.7.21-visible-sets')==3 and '<span>v3.7.21</span>' in html,'browser cache bust/version missing')
wf=rd(ROOT/'.github/workflows/publish-release-trigger.yml')
for mark in ["$env:VERSION -cne '3.7.21'",'validate-v3721-regressions.py','validate-v3721-visible-sets.js','validate-v3720-date-sequences.js','validate-v3719-library-io.py','validate-v3717-loose-filenames.py','validate-v3716-video-console.py','validate-v3715-newsgroup-browser.js','validate-v3714-completed-backend.py']:
 check(mark in wf,'CI gate missing: '+mark)
check('a.version = argValue("--version", "3.7.21")' in rd(ROOT/'src/windows/NewzDeckTray.go'),'tray identity')
check('v3.7.21' in rd(ROOT/'README.md') and 'v3.7.21' in rd(ROOT/'index.html'),'release/docs identity')
print('validate-v3721-regressions.py: PASS (Image Set visibility, dated sequence, release identities, prior fixes)')
