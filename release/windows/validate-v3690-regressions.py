from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'c6a77e46e4abeafe8c460944828d69efc9c49c3e33aafeb7819e04a9fc697990',
    'automation_engine.py':'ee3cf8243a593e4fd1c45f040f3a4056a7a8507e27015107401354482c782c78',
    'sab_engine.py':'1b80fe99a1dc42dce9f464095ef14b2227bc100a5c2a83d1b7059b97ae1152ef',
    'static/app.js':'3df087fa5aca176db8c84e6f3a9e962600114b1bb9e83470131365ae1d64fc94',
    'static/index.html':'018ce4260c885c0cf0360c163c5ef76ca7cbfdf5c83b4034f73c2b6255178e61',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'build-manifest.json':'b717797975a554d068a3527626d9207aa56ec2e6f107147abdb9ef312898d724',
    'version.txt':'84746b20a3a72f6ff85a629706e50507c1bd200907456b76dd808a2a5ca0efba',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.7.0 payload')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check(manifest.get('version')=='3.7.0' and manifest.get('base_version')=='3.6.99' and manifest.get('adapter_version')=='3.7.0','build manifest lineage mismatch')
check(manifest.get('release')=='Production Milestone & Repository Hygiene','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')

picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
check(hashlib.sha256(picker.encode('utf-8')).hexdigest()=='df8b23aea5b8dfc18f43276759f3ef7d69dbd767e35eb191c133f6d8ffd97f46','reviewed Picker source changed')
for required in ('func chooseFolder(', 'procSHBrowseForFolderW', '--result-file', '--started-file'):
    check(required in picker,'folder-picker behavior missing: '+required)
for forbidden in ('--update-handoff','--close-app-windows','os/exec','ShellExecuteExW','EnumWindows','taskbarFix','closeNewzDeckWindows'):
    check(forbidden not in picker,'Picker regained non-folder behavior: '+forbidden)

builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
for marker in (
    'DEFAULT_GO_LDFLAGS = "-s -w -H windowsgui -buildid="',
    'YENC_GO_LDFLAGS = "-H windowsgui"',
    'PICKER_GO_LDFLAGS = "-H windowsgui"',
    'if exe == "NewzDeckPicker.exe": return PICKER_GO_LDFLAGS',
    'return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS',
    '"source_behavior_changed":True',
): check(marker in builder,'Picker/yEnc build invariant missing: '+marker)

workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
for marker in (
    'Enforce canonical LF source checkout',
    '$PSNativeCommandUseErrorActionPreference = $true',
    'python release/windows/validate-v3690-regressions.py',
    'python release/windows/validate-v3691-regressions.py',
    'python release/windows/validate-v3692-regressions.py',
    '$pickerBuildId = (& go tool buildid $pickerBinary 2>&1).Trim()',
    '$pickerSymbols = @(& go tool nm $pickerBinary 2>&1)',
): check(marker in workflow,'release-gate marker missing: '+marker)
print('v3.6.90 Defender Picker build intent carried forward under v3.7.0 with simplified Picker scope: PASS')
