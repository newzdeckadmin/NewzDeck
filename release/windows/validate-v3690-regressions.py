from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
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
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.95 payload')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check(manifest.get('version')=='3.6.95' and manifest.get('base_version')=='3.6.94' and manifest.get('adapter_version')=='3.6.95','build manifest lineage mismatch')
check(manifest.get('release')=='Light Theme Readability Hotfix','release identity mismatch')
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
print('v3.6.90 Defender Picker build intent carried forward under v3.6.95 with simplified Picker scope: PASS')
