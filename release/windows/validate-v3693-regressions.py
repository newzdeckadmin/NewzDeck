from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'a46efec4b470f63da91cfc8ed667f146587edd66fd9f263402f69f51b464f64a',
    'automation_engine.py':'9fb8dbbb1c495c09b65e6da64b91ab72d38c91af3a73d6ccf9981e2645deb2c4',
    'sab_engine.py':'577a018e1a620f1d340988f63d55c4a9d5d31f1b4e2d1ca0c26886ca64f2fb98',
    'static/app.js':'6e7467f6e54eea250fd21126f0933820a49ed9ff57cafb7525bc60d49495a1ee',
    'static/index.html':'06732e3f953f493d482b5ea6b5c1744720f04f0b281e2d2885bc6cf827ae736e',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'40e476c4bdb31f7621083e8b1457df1037a59bcb70993e6f8028abfa5a1896a8',
    'version.txt':'0e94a299e79ae0d20450ed602043edf27ed2dcd6e65d42e415c4e0c5bf5f2081',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.93 roll-forward payload')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.93','version.txt mismatch')
check('APP_VERSION = "3.6.93"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.93';" in app,'UI version mismatch')
check('v=3.6.93-defender-handoff-release-gate-recovery' in index,'asset cache identity mismatch')
check(manifest.get('version')=='3.6.93' and manifest.get('base_version')=='3.6.92' and manifest.get('adapter_version')=='3.6.93','manifest lineage mismatch')
check(manifest.get('release')=='Defender Handoff Release Gate Recovery','release name mismatch')
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
    check(required in workflow,'corrected v3.6.93 release-gate marker missing: '+required)
check("-ArgumentList @('--taskbar-fix')" not in workflow,'runtime smoke still invokes retired Picker --taskbar-fix mode')
check('release/windows/validate-v3692-regressions.py' in workflow,'v3.6.92 architecture guard was dropped')
print('v3.6.93 Defender Handoff Release Gate Recovery regression guard: PASS')
