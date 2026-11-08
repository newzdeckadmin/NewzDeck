#!/usr/bin/env python3
"""NewzDeck v3.7.26 release identity and retained-feature source guard."""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[2];a=r/'src/app'
def rd(p):return p.read_text(encoding='utf-8')
def require(condition,message):
 if not condition:raise AssertionError('v3.7.26 release gate: '+message)
srv=rd(a/'server.py');ui=rd(a/'static/app.js');sab=rd(a/'sab_engine.py');auto=rd(a/'automation_engine.py')
manifest=json.loads(rd(a/'build-manifest.json'));html=rd(a/'static/index.html')
require(rd(a/'version.txt').strip()=='3.7.26','version.txt')
require(tuple(manifest.get(x) for x in ('version','base_version','adapter_version'))==('3.7.26','3.7.25','3.7.26'),'manifest identity')
for marker,data in [('APP_VERSION = "3.7.26"',srv),("const UI_VERSION = '3.7.26'",ui),('ADAPTER_VERSION = "3.7.26"',sab),("version='3.7.26'",auto)]:
 require(marker in data,'runtime version: '+marker)
require(html.count('3.7.26-high-speed-search')==3 and '<span>v3.7.26</span>' in html,'asset IDs or visible version')
for marker in [
 'class GroupSearchManager:', 'CHUNK_SIZE = 5000','MIN_CHUNK_SIZE = 2500','MAX_CHUNK_SIZE = 8000',
 '_GROUP_SEARCH_LANES = threading.BoundedSemaphore(4)',
 'job["scanned_headers"] += end - start + 1',
 'raise NntpError(f"Search failed while scanning headers {start}-{end}: {last_error}")',
 'def parse_overview(lines: Iterable[bytes], *, search_filter:',
 'return parse_overview(lines, search_filter=search_filter)',
 'search_filter=quick_filter',
 'client.abort()',
]: require(marker in srv,'search integrity: '+marker)
for marker in [
 'function startEntireGroupSearchPolling()',
 'state.groupSearchLiveRefreshPending=true',
 'loadEntireGroupSearchResults(1,{silent:true})',
 'state.articlePage===1&&!state.selectedArticleKey',
 'els.articlesList.scrollTop<60',
 'async function loadEntireGroupSearchResults(page=1,{silent=false}={})',
]:require(marker in ui,'progressive search UI: '+marker)
# No new persistent search results/header index or schema migration.
start=srv.index('class GroupSearchManager:');end=srv.index('def normalize_search_filters(',start)
search=srv[start:end]
for marker in ('json_write(', 'sqlite3.connect(', 'SAVED_SEARCHES_FILE', 'open(', 'write_text('):
 require(marker not in search,'a persistent search/index operation appeared: '+marker)
# The previously protected binary/gallery/automation and downloaded-media behavior.
for marker in ['def inspect_unknown_article(', 'def save_unknown_fragment(', 'class _UnknownLimitedClient',
               'def _unknown_magic(', '/api/articles/inspect-unknown','/api/articles/save-fragment',
               '_parse_yenc_part(control, meta)']:
 require(marker in srv,'retained unknown-binary/yEnc feature: '+marker)
for marker in ['function inspectUnknownArticle(', 'function saveUnknownFragment(',
               'function updateBrowseModeControls()',
               'const hideRelatedPane=all||!state.groupRelatedMedia;',
               "browseView?.classList.toggle('all-posts-wide',hideRelatedPane)",
               'function mediaSetKey(a)', 'const leadingDate=stem.match']:
 require(marker in ui,'retained UI/Image Sets feature: '+marker)
for marker in ['def _browser_final_loose_name(', 'browser_flattened_files',
               'permitted_media_exts = image_exts | AUTOMATION_MEDIA_EXTS',
               'if action == "clear_completed":']:
 require(marker in sab,'retained download/SAB safety: '+marker)
for marker in ['def _scan_media_cache(', 'def _analyze_scanned_media(',
               'def _save_scan_media_cache(', 'st_mtime_ns']:
 require(marker in auto,'retained library scan cache: '+marker)
workflow=r/'.github/workflows/publish-release-trigger.yml'
if workflow.is_file():
 w=rd(workflow)
 for marker in ["$env:VERSION -cne '3.7.26'",'validate-v3726-regressions.py',
                'validate-v3726-live-search.py','validate-v3726-early-filter.py',
                'validate-v3726-search-ui.js','validate-v3725-image-sets-pane.js',
                'validate-v3724-yenc-prefix.py','validate-v3723-unknown-binary.py',
                'validate-v3722-loose-video.py','validate-v3719-library-io.py']:
  require(marker in w,'Windows CI guard: '+marker)
 tray=r/'src/windows/NewzDeckTray.go'
 if tray.is_file():require('a.version = argValue("--version", "3.7.26")' in rd(tray),'tray identity')
 for path in ('README.md','index.html'):
  p=r/path
  if p.is_file():require('v3.7.26' in rd(p),'documentation/website identity: '+path)
print('validate-v3726-regressions.py: PASS (source identity, bounded live scanning, no persistent index, retained features)')
