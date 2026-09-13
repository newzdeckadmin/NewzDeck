from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'5dd4c5c788c3938696bce02109a81f2780d3ffe6a8d7abbc638e2a42ad9247a5',
    'automation_engine.py':'3cc4416de258bfeb178c33a320d6b2054d725cd1055b5eb7e2f84dcebae55ff4',
    'sab_engine.py':'1fdc35a95eaee66329db62b488cae546c085a4394499d31e6789dfb89b97587e',
    'static/app.js':'e9e6f64523bab10dbf703a7e55585bd492428db1e48ea9e415614d7fc1e219b3',
    'static/index.html':'ca8c2bb83aaaf15c707cb455b0b5ec0cbc6207b0f390274573eeb5bc03b07e58',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'build-manifest.json':'ca372b916ea5c3343a34c5ec3a59da0a9270757d54f839968c4b38b9aac9d845',
    'version.txt':'e08fa63b65c0de91e88bad41a162947e84cc18bf1939e98dde337ea0c2a76dc8',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.94 roll-forward payload')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.94','version.txt mismatch')
check('APP_VERSION = "3.6.94"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.94';" in app,'UI version mismatch')
check('v=3.6.94-themes-color-schemes' in index,'asset cache identity mismatch')
check(manifest.get('version')=='3.6.94' and manifest.get('base_version')=='3.6.93' and manifest.get('adapter_version')=='3.6.94','manifest lineage mismatch')
check(manifest.get('release')=='Themes & Color Schemes','release name mismatch')
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
    check(required in workflow,'corrected v3.6.94 release-gate marker missing: '+required)
check("-ArgumentList @('--taskbar-fix')" not in workflow,'runtime smoke still invokes retired Picker --taskbar-fix mode')
check('release/windows/validate-v3692-regressions.py' in workflow,'v3.6.92 architecture guard was dropped')
print('v3.6.94 Defender Handoff Release Gate Recovery carried-forward guard: PASS')
