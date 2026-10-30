#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'src' / 'app'
VERSION = '3.7.6'
BASE = '3.7.5'
SABCTOOLS_COMMIT = '54d7663b9e8f527b5ab196d43f0d5c561a87c1ac'

def check(value, message):
    if not value:
        raise SystemExit(message)

server = (APP / 'server.py').read_text(encoding='utf-8')
sab_engine = (APP / 'sab_engine.py').read_text(encoding='utf-8')
automation = (APP / 'automation_engine.py').read_text(encoding='utf-8')
ui = (APP / 'static/app.js').read_text(encoding='utf-8')
app_html = (APP / 'static/index.html').read_text(encoding='utf-8')
styles = (APP / 'static/styles.css').read_text(encoding='utf-8')
themes = (APP / 'static/themes.css').read_text(encoding='utf-8')
manifest = json.loads((APP / 'build-manifest.json').read_text(encoding='utf-8'))
tray = (ROOT / 'src/windows/NewzDeckTray.go').read_text(encoding='utf-8')
workflow = (ROOT / '.github/workflows/publish-release-trigger.yml').read_text(encoding='utf-8')
readme = (ROOT / 'README.md').read_text(encoding='utf-8')
readme_txt = (ROOT / 'README.txt').read_text(encoding='utf-8')
updating = (ROOT / 'UPDATING.txt').read_text(encoding='utf-8')
source_history = (ROOT / 'docs/SOURCE_RELEASES.md').read_text(encoding='utf-8')
website = (ROOT / 'index.html').read_text(encoding='utf-8')
installer = (ROOT / 'release/windows/NewzDeck.iss').read_text(encoding='utf-8')
builder = (ROOT / 'release/windows/build-portable.py').read_text(encoding='utf-8')
build_release = (ROOT / 'release/windows/build-release.ps1').read_text(encoding='utf-8')
notices = (ROOT / 'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')

check((APP / 'version.txt').read_text(encoding='utf-8').strip() == VERSION, 'version.txt != 3.7.6')
check(f'APP_VERSION = "{VERSION}"' in server, 'server APP_VERSION != 3.7.6')
check(f'ADAPTER_VERSION = "{VERSION}"' in sab_engine, 'SAB adapter version != 3.7.6')
check(f"const UI_VERSION = '{VERSION}';" in ui, 'UI_VERSION != 3.7.6')
check("version='3.7.6'" in automation, 'Automation fallback identity != 3.7.6')
check('argValue("--version", "3.7.6")' in tray, 'tray fallback identity != 3.7.6')
check(manifest.get('version') == VERSION and manifest.get('adapter_version') == VERSION, 'build-manifest identity mismatch')
check(manifest.get('base_version') == BASE, 'build-manifest base_version mismatch')
check(manifest.get('sab_version') == '5.1.2', 'private SAB version changed')
check(manifest.get('sabctools_version') == '9.6.3', 'SABCTools version changed')
check(manifest.get('sabctools_upstream_commit') == SABCTOOLS_COMMIT, 'SABCTools upstream commit changed')
check(app_html.count('3.7.6-resizable-newsgroups-pane') == 3, 'app HTML cache-buster identity mismatch')
check('<span>v3.7.6</span>' in app_html, 'visible app version fallback is stale')

# New splitter contract.
for marker in (
    "const GROUPS_PANE_WIDTH_KEY = 'newzdeckGroupsPaneWidth';",
    'const GROUPS_PANE_DEFAULT_WIDTH = 320;',
    'const GROUPS_PANE_MIN_WIDTH = 240;',
    'const GROUPS_PANE_MAX_WIDTH = 640;',
    'function groupsPaneWidthBounds(',
    'function clampGroupsPaneWidth(',
    'function applyGroupsPaneWidth(',
    'function initGroupsPaneResizer()',
    "groupsPaneResizer:$('groupsPaneResizer')",
    "initGroupsPaneResizer();",
    'data-group="${escapeHtml(g.name)}"',
    'title="${escapeHtml(g.name)}"',
):
    check(marker in ui, f'Newsgroups-pane JS marker missing: {marker}')

for marker in (
    '--groups-pane-width:320px',
    'grid-template-columns:var(--groups-pane-width) minmax(500px,1fr) minmax(290px,390px)',
    '.groups-pane-resizer{',
    'body.groups-pane-resizing',
    'cursor:col-resize',
):
    check(marker in styles, f'Newsgroups-pane CSS marker missing: {marker}')

for marker in (
    'id="groupsPaneResizer"',
    'role="separator"',
    'aria-orientation="vertical"',
    'aria-label="Resize Newsgroups column"',
):
    check(marker in app_html, f'Newsgroups-pane HTML marker missing: {marker}')

# v3.7.5 Related Media fix must remain intact.
for marker in (
    'function mediaSetNormalizeBase',
    'function mediaSetPosterKey',
    'function mediaSetSequenceBase',
    'liveCards.get(memberKey)',
    'data-article-key="${escapeHtml(key)}"',
):
    check(marker in ui, f'v3.7.5 Related Media marker missing: {marker}')
check((ROOT / 'release/windows/validate-media-set-key.js').is_file(), 'v3.7.5 media-set regression test missing')

# Managed update/runtime baseline remains protected.
managed_args = 'args = ["/update", "/SILENT", "/SP-", "/NORESTART", "/CLOSEAPPLICATIONS", "/FORCECLOSEAPPLICATIONS"]'
check(managed_args in server, 'managed About & Updates Setup arguments changed')
check('NewzDeckUpdateHandoff-' not in server and '--update-handoff' not in server, 'retired copied update coordinator returned')
check('_launch_verified_setup_update' in server and '_schedule_verified_setup_update' in server, 'verified Setup handoff missing')
check('server_obj.shutdown()' in server, 'desktop backend relinquish after Setup launch missing')
check('SAB_VERSION = "5.1.2"' in sab_engine, 'private SABnzbd baseline changed')
check('"NewzDeckYenc.exe": "NewzDeckYenc.go"' not in builder, 'retired NewzDeckYenc build returned')
check('NewzDeckYenc.exe' in build_release and 'retiredYencDelete' in build_release, 'retired helper upgrade cleanup missing')
check('## SABCTools 9.6.3' in notices and 'GPL-2.0-or-later' in notices, 'SABCTools notice regressed')
for marker in ('ManagedSilentUpdate','CloseInstalledAppWindowForUpdate();','CloseExistingTrayForUpgrade();','StopExistingServiceForUpgrade();',
               'RepairAndStartExistingService();','RefreshTrayAutostart();','RestoreTrayAfterInstall();','RelaunchAppAfterUpdate();'):
    check(marker in installer, f'installer lifecycle marker missing: {marker}')

# Release gates and documentation.
check('Validate NewzDeck source and v3.7.6 regression guard' in workflow, 'workflow v3.7.6 validation step missing')
check("if ($env:VERSION -cne '3.7.6')" in workflow, 'workflow version gate != 3.7.6')
check('validate-v376-regressions.py' in workflow, 'v3.7.6 regression validator not wired')
check('node release/windows/validate-media-set-key.js' in workflow, 'v3.7.5 media-set test no longer wired')
check('node release/windows/validate-groups-pane-resizer.js' in workflow, 'Newsgroups splitter behavioral test not wired')
check('NewzDeck-v376-smoke' in workflow, 'workflow smoke directory is stale')
check('current stable release is **NewzDeck v3.7.6**' in readme, 'README stable version stale')
check('NewzDeck_v3.7.6_Setup.exe' in readme and 'NewzDeck_v3.7.6_SHA256.txt' in readme, 'README asset names stale')
check('## v3.7.6 resizable Newsgroups pane' in readme, 'README v3.7.6 section missing')
check(readme_txt.startswith('NewzDeck v3.7.6 - Resizable Newsgroups Pane'), 'README.txt identity stale')
check(updating.startswith('NewzDeck v3.7.6 update notes'), 'UPDATING.txt identity stale')
check('## Current release: v3.7.6' in source_history, 'source release history stale')
check(website.count('v3.7.6') >= 4, 'website fallback version stale')
check((ROOT / 'release/RELEASE_NOTES_v3.7.6.md').is_file(), 'v3.7.6 release notes missing')
check((ROOT / 'release/windows/validate-groups-pane-resizer.js').is_file(), 'splitter behavioral validator missing')

# Theme definitions are intentionally untouched.
check('html[data-theme="midnight"]' in themes and 'html[data-theme="light"]' in themes, 'themes.css unexpectedly changed or damaged')

print('validate-v376-regressions.py: PASS')
