#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'src' / 'app'
VERSION = '3.7.4'
BASE = '3.7.3'
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
yenc = (APP / 'yenc_decoder.py').read_text(encoding='utf-8')
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
win_readme = (ROOT / 'release/windows/README.md').read_text(encoding='utf-8')
notices = (ROOT / 'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')
source_history = (ROOT / 'docs/SOURCE_RELEASES.md').read_text(encoding='utf-8')
notes = ROOT / 'release/RELEASE_NOTES_v3.7.4.md'

# Runtime/release identity must be coherent.
check((APP / 'version.txt').read_text(encoding='utf-8').strip() == VERSION, 'version.txt != 3.7.4')
check(f'APP_VERSION = "{VERSION}"' in server, 'server APP_VERSION != 3.7.4')
check(f'ADAPTER_VERSION = "{VERSION}"' in sab_engine, 'SAB adapter version != 3.7.4')
check(f"const UI_VERSION = '{VERSION}';" in ui, 'UI_VERSION != 3.7.4')
check(manifest.get('version') == VERSION, 'build-manifest version mismatch')
check(manifest.get('adapter_version') == VERSION, 'build-manifest adapter_version mismatch')
check(manifest.get('base_version') == BASE, 'build-manifest base_version mismatch')
check(manifest.get('sab_version') == '5.1.2', 'build-manifest SAB version changed')
check(manifest.get('sabctools_version') == '9.6.3', 'build-manifest SABCTools version mismatch')
check(manifest.get('sabctools_upstream_commit') == SABCTOOLS_COMMIT, 'build-manifest SABCTools upstream commit changed')

# Tiny stale-current-text cleanup: current code must no longer identify the SABCTools integration as v3.7.1.
check(not yenc.startswith('"""NewzDeck v3.7.1'), 'yenc_decoder.py still presents itself as v3.7.1')
check('required by NewzDeck 3.7.1' not in yenc, 'yenc_decoder.py still has stale v3.7.1 requirement text')
for stale in (
    'v3.7.1 uses in-process SABCTools for the normal queued-download path.',
    '# NewzDeck v3.7.1 in-process SABCTools decoder.',
    '# v3.7.1 defaults to the vendored in-process SABCTools decoder.',
):
    check(stale not in server, f'server.py stale current-behavior text remains: {stale}')
check('argValue("--version", "3.7.4")' in tray, 'tray fallback version is not 3.7.4')
check("version='3.7.4'" in automation and "version='3.7.0'" not in automation, 'Automation engine fallback version is stale')
check('v3.7.0</span>' not in app_html, 'app HTML still exposes v3.7.0 sidebar fallback')
check(app_html.count('3.7.4-release-hygiene') == 3, 'app HTML cache-buster identity is not consistently 3.7.4')
check('<span>v3.7.4</span>' in app_html, 'app HTML visible fallback version is not v3.7.4')

# Preserve v3.7.3 updater/installer lifecycle exactly.
managed_args = 'args = ["/update", "/SILENT", "/SP-", "/NORESTART", "/CLOSEAPPLICATIONS", "/FORCECLOSEAPPLICATIONS"]'
check(managed_args in server, 'managed About & Updates Setup arguments changed')
check('NewzDeckUpdateHandoff-' not in server and '--update-handoff' not in server, 'retired copied update coordinator returned')
check('_launch_verified_setup_update' in server and '_schedule_verified_setup_update' in server, 'direct verified Setup handoff missing')
check('server_obj.shutdown()' in server, 'desktop backend relinquish after Setup launch missing')
check('ManagedSilentUpdate' in installer, 'installer managed-silent-update state missing')
check('function IsManagedSilentUpdate(): Boolean;' in installer, 'managed silent parameter detector missing')
prepare = re.search(r'function PrepareToInstall\(var NeedsRestart: Boolean\): String;\n(.*?)\nend;', installer, re.S)
check(prepare is not None, 'PrepareToInstall block missing')
prepare_text = prepare.group(1)
for marker in ('ManagedSilentUpdate := IsManagedSilentUpdate();', 'CloseInstalledAppWindowForUpdate();', 'CloseExistingTrayForUpgrade();', 'StopExistingServiceForUpgrade();'):
    check(marker in prepare_text, f'installer lifecycle marker missing: {marker}')
check(prepare_text.index('CloseInstalledAppWindowForUpdate();') < prepare_text.index('CloseExistingTrayForUpgrade();'), 'app/tray shutdown order changed')
check(prepare_text.index('CloseExistingTrayForUpgrade();') < prepare_text.index('StopExistingServiceForUpgrade();'), 'tray/service shutdown order changed')
for marker in ('RepairAndStartExistingService();', 'RefreshTrayAutostart();', 'RestoreTrayAfterInstall();', 'RelaunchAppAfterUpdate();'):
    check(marker in installer, f'installer restoration marker missing: {marker}')
check('WizardSilent and not ManagedSilentUpdate' in installer, 'managed silent relaunch exception changed')

# Preserve decoder/private SAB and packaging architecture.
check('apply-v371-runtime.py' not in builder and 'apply-v371-runtime.py' not in workflow, 'packaging-time runtime transform returned')
check('_YENC_DECODER_MODULE' in server and '_active_yenc_pipeline_label' in server, 'SABCTools server integration missing')
check('SabctoolsDecoder' in yenc and 'EXPECTED_SABCTOOLS_VERSION = "9.6.3"' in yenc, 'SABCTools decoder adapter/pin missing')
check('NATIVE_YENC_POOL' not in server and 'class _NativeYencWorker' not in server, 'retired yEnc subprocess path returned')
check('"NewzDeckYenc.exe": "NewzDeckYenc.go"' not in builder, 'Portable builder builds retired NewzDeckYenc.exe')
check('NewzDeckYenc.exe' in build_release and 'retiredYencDelete' in build_release, 'retired helper upgrade cleanup missing')
check('SAB_VERSION = "5.1.2"' in sab_engine, 'private SABnzbd baseline changed')

# Canonical workflow/release surfaces advance together.
check('Validate NewzDeck source and v3.7.4 regression guard' in workflow, 'workflow v3.7.4 validation step missing')
check("if ($env:VERSION -cne '3.7.4')" in workflow, 'workflow version gate is not v3.7.4')
check('validate-v374-regressions.py' in workflow, 'v3.7.4 regression guard not wired into workflow')
check('NewzDeck-v374-smoke' in workflow, 'workflow smoke directory is stale')
check('current stable release is **NewzDeck v3.7.4**' in readme, 'root README stable release is stale')
check('NewzDeck_v3.7.4_Setup.exe' in readme and 'NewzDeck_v3.7.4_SHA256.txt' in readme, 'root README asset names are stale')
check('## v3.7.4 maintenance release' in readme, 'root README v3.7.4 section missing')
check(readme_txt.startswith('NewzDeck v3.7.4 - Release Hygiene & Publisher Reliability Maintenance'), 'README.txt release identity is stale')
check(updating.startswith('NewzDeck v3.7.4 update notes'), 'UPDATING.txt release identity is stale')
check(website.count('v3.7.4') >= 4, 'website fallback release identity is stale')
check('## Current release: v3.7.4' in source_history, 'source/release history latest release is stale')
check(notes.is_file(), 'v3.7.4 release notes missing')
check('managed silent-update' in win_readme.casefold(), 'Windows build README lost managed update documentation')
check('## SABCTools 9.6.3' in notices and 'GPL-2.0-or-later' in notices, 'SABCTools notice regressed')

# Presentation/runtime logic specifically frozen for this hygiene release.
check(sha(APP / 'static/styles.css') == 'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d', 'styles.css changed')
check(sha(APP / 'static/themes.css') == '2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721', 'themes.css changed')

print('validate-v374-regressions.py: PASS')
