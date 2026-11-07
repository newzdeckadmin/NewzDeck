#!/usr/bin/env python3
"""Source/version/retained-fix gate for NewzDeck v3.7.23 production Windows CI."""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[2]; a=r/'src/app'
def rd(p):return p.read_text(encoding='utf-8')
def require(ok,msg):
 if not ok:raise AssertionError('v3.7.23 release gate: '+msg)
srv=rd(a/'server.py'); ui=rd(a/'static/app.js'); sab=rd(a/'sab_engine.py'); auto=rd(a/'automation_engine.py')
manifest=json.loads(rd(a/'build-manifest.json')); html=rd(a/'static/index.html'); workflow=rd(r/'.github/workflows/publish-release-trigger.yml')
require(rd(a/'version.txt').strip()=='3.7.23','version.txt')
require(tuple(manifest.get(x) for x in ('version','base_version','adapter_version'))==('3.7.23','3.7.22','3.7.23'),'manifest identity')
for marker,data in [('APP_VERSION = "3.7.23"',srv),("const UI_VERSION = '3.7.23'",ui),('ADAPTER_VERSION = "3.7.23"',sab),("version='3.7.23'",auto)]:require(marker in data,'runtime version: '+marker)
for marker in ['def inspect_unknown_article(','def save_unknown_fragment(','class _UnknownLimitedClient','def _unknown_magic(','/api/articles/inspect-unknown','/api/articles/save-fragment','if int(item.get("bytes") or 0) > UNKNOWN_FRAGMENT_MAX:', 'os.O_EXCL','CRC32 mismatch','meta["yenc_found"] = saw_begin']:
 require(marker in srv,'missing unknown-binary server safeguard '+marker)
for marker in ['function inspectUnknownArticle(', 'function saveUnknownFragment(', 'article-row-inspect','article-row-save-fragment','function isUnresolvedDownloadCandidate(', 'a.unknown_inspection.can_queue', 'function nameResolutionCandidates(','function scheduleObfuscatedNameResolution(']:
 require(marker in ui,'missing browser safeguard '+marker)
for marker in ['def _browser_final_loose_name(', 'permitted_media_exts = image_exts | AUTOMATION_MEDIA_EXTS','NewzDeck Loose [0-9a-f]{12}', 'browser_flat_images=loose','Restored original loose-media filename','browser_flattened_files','if action == "clear_completed":','del_files=0']:
 require(marker in sab,'missing retained v3.7.22 or earlier SAB safeguard '+marker)
for marker in ['const leadingDate=stem.match','if(!matched&&!hasDateTail)','if(!members.some(x=>x.a?.complete))suppressedGroups++;else groups.push(group)','function mediaSetKey(a)','Cover probes cannot decide visibility of the original downloadable article']:
 require(marker in ui,'Image Sets/date-set regression '+marker)
for marker in ['def _scan_media_cache(','def _analyze_scanned_media(','def _save_scan_media_cache(','st_mtime_ns']:
 require(marker in auto,'media-scan disk-I/O cache '+marker)
require(html.count('3.7.23-unknown-binary')==3 and '<span>v3.7.23</span>' in html,'static cache and version')
require('a.version = argValue("--version", "3.7.23")' in rd(r/'src/windows/NewzDeckTray.go'),'tray identity')
for marker in ["$env:VERSION -cne '3.7.23'",'validate-v3723-regressions.py','validate-v3723-unknown-binary.py','validate-v3723-unknown-ui.js','validate-v3722-loose-video.py','validate-v3721-visible-sets.js','validate-v3720-date-sequences.js','validate-v3719-library-io.py','validate-v3717-loose-filenames.py','validate-v3716-video-console.py','validate-v3715-newsgroup-browser.js','validate-v3714-completed-backend.py']:
 require(marker in workflow,'Windows Actions source guard '+marker)
require('v3.7.23' in rd(r/'README.md') and 'v3.7.23' in rd(r/'index.html'),'readme/website release identity')
print('validate-v3723-regressions.py: PASS (versions, on-demand binary safety, all retained production fixes, Windows gates)')
