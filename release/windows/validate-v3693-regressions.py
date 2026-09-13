from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'115b49c5c656e5d9366746d6adba166a0fc8d3770d6b33847aff48c4dc570e4f',
    'automation_engine.py':'67da05374cb70a305ccafd3251ce27a806f9521bfb211ce657596ae7708b0098',
    'sab_engine.py':'7c84060a3316a014bd859d54f46606f1a3b2f94d4df34f5297a22078d4d5f75e',
    'static/app.js':'5d9400336a87c0503ef7a1e15cfdea744c1ea0865be37f0c6a1cf3ed666c9e11',
    'static/index.html':'d77a224e530a4fa8cbfecad88db14321255729adf843feb4fb0e7186e656ea5d',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'build-manifest.json':'36fd81bfb09be9b1ae23225520719010a43601b60f8467d13e89cd07b06223ac',
    'version.txt':'7d1e1967d448824bd388968ce6c1665293b9be823deae8e870a46963874fd903',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.99 roll-forward payload')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.99','version.txt mismatch')
check('APP_VERSION = "3.6.99"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.99';" in app,'UI version mismatch')
check('v=3.6.99-final-ux-backup-restore' in index,'asset cache identity mismatch')
check(manifest.get('version')=='3.6.99' and manifest.get('base_version')=='3.6.96' and manifest.get('adapter_version')=='3.6.99','manifest lineage mismatch')
check(manifest.get('release')=='Final UX & Backup/Restore','release name mismatch')
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
    check(required in workflow,'corrected v3.6.99 release-gate marker missing: '+required)
check("-ArgumentList @('--taskbar-fix')" not in workflow,'runtime smoke still invokes retired Picker --taskbar-fix mode')
check('release/windows/validate-v3692-regressions.py' in workflow,'v3.6.92 architecture guard was dropped')
print('v3.6.99 Defender Handoff Release Gate Recovery carried-forward guard: PASS')
