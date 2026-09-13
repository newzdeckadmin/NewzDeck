from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'ae1f258b58e25f05fad2008e5fb02b388812c53cba2edb3260543107fea8ad1d',
    'automation_engine.py':'1c8d6a5400e87c8581e69f849aaa6ab93201339aaf9d4126d2090a181ed5aeb4',
    'sab_engine.py':'35ae4274200fbcfb9baf4e8f08884f518efb56bf247349fde606e3dc36e55209',
    'static/app.js':'e43926f79258a9159b8db2cd35dea475e5ae5a4d2489762c0188f52a706551f7',
    'static/index.html':'0545cc4be9374fa95c90aa10a95676146827b707c3ff3fb8d8454eb5db48ec55',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'build-manifest.json':'d0a54731e665570fb57ed13e18fac80d9382ee59aa41686864bbac143988ad33',
    'version.txt':'42ec12b7fdaa92e46f5520b70d25ac21f06cf2f4268f25c73270a109ecf05d1b',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.95 roll-forward payload')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.95','version.txt mismatch')
check('APP_VERSION = "3.6.95"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.95';" in app,'UI version mismatch')
check('v=3.6.95-light-theme-readability-hotfix' in index,'asset cache identity mismatch')
check(manifest.get('version')=='3.6.95' and manifest.get('base_version')=='3.6.94' and manifest.get('adapter_version')=='3.6.95','manifest lineage mismatch')
check(manifest.get('release')=='Light Theme Readability Hotfix','release name mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')

# v3.6.92 application architecture is intentionally unchanged.
for required in ('def _launch_verified_setup_update(', 'def _schedule_verified_setup_update('):
    check(required in server,'direct verified-Setup updater marker missing: '+required)
for forbidden in ('def _launch_update_handoff(', 'NewzDeckUpdateHandoff-', 'shutil.copy2(PICKER_HELPER_EXE'):
    check(forbidden not in server,'legacy copied handoff returned: '+forbidden)
check(hashlib.sha256(picker.encode()).hexdigest()=='df8b23aea5b8dfc18f43276759f3ef7d69dbd767e35eb191c133f6d8ffd97f46','folder-only Picker source changed')
for forbidden in ('--update-handoff','--close-app-windows','--taskbar-fix','os/exec','ShellExecuteExW','EnumWindows'):
    check(forbidden not in picker,'Picker regained retired behavior: '+forbidden)

# The v3.6.92 failure was a stale smoke test, not an application failure. The
# corrected gate simulates a legacy locked Picker with an inert stand-in binary.
for required in (
    'python release/windows/validate-v3693-regressions.py',
    "$pickerLockSource = Join-Path $env:RUNNER_TEMP 'NewzDeckPickerLockSmoke.go'",
    "go build -trimpath -ldflags='-H windowsgui' -o $pickerExe $pickerLockSource",
    '$pickerProcess = Start-Process -FilePath $pickerExe -PassThru',
    "throw 'Legacy Picker-lock smoke process exited before the upgrade began.'",
):
    check(required in workflow,'corrected v3.6.95 release-gate marker missing: '+required)
check("-ArgumentList @('--taskbar-fix')" not in workflow,'runtime smoke still invokes retired Picker --taskbar-fix mode')
check('release/windows/validate-v3692-regressions.py' in workflow,'v3.6.92 architecture guard was dropped')
print('v3.6.95 Defender Handoff Release Gate Recovery carried-forward guard: PASS')
