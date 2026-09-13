from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'cf095fa4af834c60d050e56e90aacbddf3d26b2e7e672e1938766725b97a17db',
    'automation_engine.py':'5880a9747dbe5ef4be2bc17685119d82155c1f688d3d10b04ee5c9b1c0513e39',
    'sab_engine.py':'56e5a089f26cfdd3a2b6e40e1838973194220687c191de14f91e1f6953be42c3',
    'static/app.js':'42f5c835e9435b7ceba0ae4664326813c803718de3c9f2dfe6430a40b87c1845',
    'static/index.html':'7c1f68a8aa7b7e6441d142592f6f198dbe8331c2e6dd5c60d4952d1d236296ad',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'build-manifest.json':'623006d630ae88ec859e371561e69e46daeebc55f7c8417847015799e720e1f8',
    'version.txt':'44a1fcae929eb12521b0218135694ad3d84f616ba88ff4914fa1e8ffb45617ea',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.96 roll-forward payload')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.96','version.txt mismatch')
check('APP_VERSION = "3.6.96"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.96';" in app,'UI version mismatch')
check('v=3.6.96-library-article-aware-sorting' in index,'asset cache identity mismatch')
check(manifest.get('version')=='3.6.96' and manifest.get('base_version')=='3.6.95' and manifest.get('adapter_version')=='3.6.96','manifest lineage mismatch')
check(manifest.get('release')=='Library Article-Aware Sorting','release name mismatch')
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
    check(required in workflow,'corrected v3.6.96 release-gate marker missing: '+required)
check("-ArgumentList @('--taskbar-fix')" not in workflow,'runtime smoke still invokes retired Picker --taskbar-fix mode')
check('release/windows/validate-v3692-regressions.py' in workflow,'v3.6.92 architecture guard was dropped')
print('v3.6.96 Defender Handoff Release Gate Recovery carried-forward guard: PASS')
