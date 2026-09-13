from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
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
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.93 payload')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check(manifest.get('version')=='3.6.93' and manifest.get('base_version')=='3.6.92' and manifest.get('adapter_version')=='3.6.93','build manifest lineage mismatch')
check(manifest.get('release')=='Defender Handoff Release Gate Recovery','release identity mismatch')
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
print('v3.6.90 Defender Picker build intent carried forward under v3.6.93 with simplified Picker scope: PASS')
