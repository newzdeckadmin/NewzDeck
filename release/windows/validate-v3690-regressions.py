from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
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
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.94 payload')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check(manifest.get('version')=='3.6.94' and manifest.get('base_version')=='3.6.93' and manifest.get('adapter_version')=='3.6.94','build manifest lineage mismatch')
check(manifest.get('release')=='Themes & Color Schemes','release identity mismatch')
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
print('v3.6.90 Defender Picker build intent carried forward under v3.6.94 with simplified Picker scope: PASS')
