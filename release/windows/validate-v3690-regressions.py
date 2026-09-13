from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
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
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.99 payload')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check(manifest.get('version')=='3.6.99' and manifest.get('base_version')=='3.6.96' and manifest.get('adapter_version')=='3.6.99','build manifest lineage mismatch')
check(manifest.get('release')=='Final UX & Backup/Restore','release identity mismatch')
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
print('v3.6.90 Defender Picker build intent carried forward under v3.6.99 with simplified Picker scope: PASS')
