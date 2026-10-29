#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'src' / 'app'
VERSION = '3.7.5'
BASE = '3.7.4'
SABCTOOLS_COMMIT = '54d7663b9e8f527b5ab196d43f0d5c561a87c1ac'

def check(value, message):
    if not value:
        raise SystemExit(message)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

server = (APP / 'server.py').read_text(encoding='utf-8')
sab_engine = (APP / 'sab_engine.py').read_text(encoding='utf-8')
automation = (APP / 'automation_engine.py').read_text(encoding='utf-8')
ui = (APP / 'static/app.js').read_text(encoding='utf-8')
app_html = (APP / 'static/index.html').read_text(encoding='utf-8')
manifest = json.loads((APP / 'build-manifest.json').read_text(encoding='utf-8'))
tray = (ROOT / 'src/windows/NewzDeckTray.go').read_text(encoding='utf-8')
builder = (ROOT / 'release/windows/build-portable.py').read_text(encoding='utf-8')
build_release = (ROOT / 'release/windows/build-release.ps1').read_text(encoding='utf-8')
installer = (ROOT / 'release/windows/NewzDeck.iss').read_text(encoding='utf-8')
workflow = (ROOT / '.github/workflows/publish-release-trigger.yml').read_text(encoding='utf-8')
readme = (ROOT / 'README.md').read_text(encoding='utf-8')
readme_txt = (ROOT / 'README.txt').read_text(encoding='utf-8')
updating = (ROOT / 'UPDATING.txt').read_text(encoding='utf-8')
website = (ROOT / 'index.html').read_text(encoding='utf-8')
notices = (ROOT / 'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')
source_history = (ROOT / 'docs/SOURCE_RELEASES.md').read_text(encoding='utf-8')
notes = ROOT / 'release/RELEASE_NOTES_v3.7.5.md'
media_test = ROOT / 'release/windows/validate-media-set-key.js'

check((APP / 'version.txt').read_text(encoding='utf-8').strip() == VERSION, 'version.txt != 3.7.5')
check(f'APP_VERSION = "{VERSION}"' in server, 'server APP_VERSION != 3.7.5')
check(f'ADAPTER_VERSION = "{VERSION}"' in sab_engine, 'SAB adapter version != 3.7.5')
check(f"const UI_VERSION = '{VERSION}';" in ui, 'UI_VERSION != 3.7.5')
check("version='3.7.5'" in automation, 'Automation fallback identity != 3.7.5')
check('argValue("--version", "3.7.5")' in tray, 'tray fallback identity != 3.7.5')
check(manifest.get('version') == VERSION and manifest.get('adapter_version') == VERSION, 'build-manifest identity mismatch')
check(manifest.get('base_version') == BASE, 'build-manifest base_version mismatch')
check(manifest.get('sab_version') == '5.1.2', 'private SAB version changed')
check(manifest.get('sabctools_version') == '9.6.3', 'SABCTools version changed')
check(manifest.get('sabctools_upstream_commit') == SABCTOOLS_COMMIT, 'SABCTools upstream commit changed')
check(app_html.count('3.7.5-related-media-grouping') == 3, 'app HTML cache-buster identity mismatch')
check('<span>v3.7.5</span>' in app_html, 'app HTML visible fallback is stale')

for marker in (
    'function mediaSetNormalizeBase',
    'function mediaSetPosterKey',
    'function mediaSetSequenceBase',
    'mediaSetSequenceBase(a)',
    'data-article-key="${escapeHtml(key)}"',
    "grid.querySelectorAll('.media-card[data-article-key]')",
    'liveCards.get(memberKey)',
):
    check(marker in ui, f'Related Media grouping marker missing: {marker}')
check('group.members.length>=3' in ui, 'Related Media promotion threshold changed')
check("return`${articleGroup(a)}|${a.media.kind}|${seq.normalized}|${mediaSetPosterKey(a.from)}`" in ui, 'set key no longer preserves group/kind/base/poster isolation')
check('.media-card[data-index="${member.index}"]' not in ui, 'incremental set promotion still removes cards by stored member index')
check(media_test.is_file(), 'media-set behavioral regression test missing')

managed_args = 'args = ["/update", "/SILENT", "/SP-", "/NORESTART", "/CLOSEAPPLICATIONS", "/FORCECLOSEAPPLICATIONS"]'
check(managed_args in server, 'managed About & Updates Setup arguments changed')
check('NewzDeckUpdateHandoff-' not in server and '--update-handoff' not in server, 'retired copied update coordinator returned')
check('_launch_verified_setup_update' in server and '_schedule_verified_setup_update' in server, 'verified Setup handoff missing')
check('server_obj.shutdown()' in server, 'desktop backend relinquish after Setup launch missing')
for marker in ('ManagedSilentUpdate','CloseInstalledAppWindowForUpdate();','CloseExistingTrayForUpgrade();','StopExistingServiceForUpgrade();',
               'RepairAndStartExistingService();','RefreshTrayAutostart();','RestoreTrayAfterInstall();','RelaunchAppAfterUpdate();'):
    check(marker in installer, f'installer lifecycle marker missing: {marker}')
check('WizardSilent and not ManagedSilentUpdate' in installer, 'managed silent relaunch exception changed')
check('SAB_VERSION = "5.1.2"' in sab_engine, 'private SABnzbd baseline changed')
check('"NewzDeckYenc.exe": "NewzDeckYenc.go"' not in builder, 'retired NewzDeckYenc build returned')
check('NewzDeckYenc.exe' in build_release and 'retiredYencDelete' in build_release, 'retired helper upgrade cleanup missing')
check('## SABCTools 9.6.3' in notices and 'GPL-2.0-or-later' in notices, 'SABCTools notice regressed')

check('Validate NewzDeck source and v3.7.5 regression guard' in workflow, 'workflow v3.7.5 validation step missing')
check("if ($env:VERSION -cne '3.7.5')" in workflow, 'workflow version gate is not v3.7.5')
check('validate-v375-regressions.py' in workflow, 'v3.7.5 validator not wired into workflow')
check('node release/windows/validate-media-set-key.js' in workflow, 'media-set behavioral test not wired into workflow')
check('NewzDeck-v375-smoke' in workflow, 'workflow smoke directory is stale')
check('current stable release is **NewzDeck v3.7.5**' in readme, 'README stable release is stale')
check('NewzDeck_v3.7.5_Setup.exe' in readme and 'NewzDeck_v3.7.5_SHA256.txt' in readme, 'README asset names are stale')
check('## v3.7.5 Related Media grouping fix' in readme, 'README v3.7.5 section missing')
check(readme_txt.startswith('NewzDeck v3.7.5 - Related Media Grouping Reliability'), 'README.txt identity is stale')
check(updating.startswith('NewzDeck v3.7.5 update notes'), 'UPDATING.txt identity is stale')
check(website.count('v3.7.5') >= 4, 'website fallback version is stale')
check('## Current release: v3.7.5' in source_history, 'source release history is stale')
check(notes.is_file(), 'v3.7.5 release notes missing')

check(sha(APP / 'static/styles.css') == 'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d', 'styles.css changed')
check(sha(APP / 'static/themes.css') == '2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721', 'themes.css changed')

print('validate-v375-regressions.py: PASS')
