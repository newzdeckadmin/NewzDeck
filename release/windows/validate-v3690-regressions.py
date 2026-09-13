from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'

def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

EXPECTED={
    'server.py':'94f849feb0d8aa35ccec16ab8ad8c041bc07acffe94e8f08fc107fea0ebf77ae',
    'automation_engine.py':'c52d5f93ba6ad24a1045ebda49a2b1973d9fdd43d6e56e973dd0404ff8b5ede7',
    'sab_engine.py':'c899f3d39de00ee5c43f22f1cb0cdef3009449274789753ea4a97d37b864e77c',
    'static/app.js':'8932e47cbbc06e965c2bf02692bab72107179a53a20038d9594dd2a3ee6d781f',
    'static/index.html':'bf357570e16584b46a9ee42a5e103457f4612afd04f3d1cecf269e2db9276ea8',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'51d1981e1cada1d63276409977fddc33379d523ef13199e6fc1e8450421b895a',
    'version.txt':'21a15ffafda3766bf34259e3defea1a151f7c980e409a8a4a9c70b357d504c36',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.91 payload')

manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check((APP/'version.txt').read_text().strip()=='3.6.91','version.txt mismatch')
check(manifest.get('version')=='3.6.91' and manifest.get('base_version')=='3.6.90' and manifest.get('adapter_version')=='3.6.91','build manifest lineage mismatch')
check(manifest.get('release')=='Defender Picker Release Gate Compatibility Fix','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')
check(sha(APP/'static'/'styles.css')=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','frozen stylesheet changed')

builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')

# The Defender remediation is build-only: Picker source behavior must stay at the reviewed v3.6.89 blob.
blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckPicker.go'],text=True).strip()
check(blob=='c25528879ebe302315b0203de21b767d92c3d437','NewzDeckPicker.go source changed during build-only remediation')
for marker in (
    'PICKER_GO_LDFLAGS = "-H windowsgui"',
    'if exe == "NewzDeckPicker.exe": return PICKER_GO_LDFLAGS',
    '"NewzDeckPicker.exe":{',
    '"purpose":"Windows Defender compatibility"',
    '"build_origin":"windows-source-build"',
):
    check(marker in builder,'Picker Defender-compatibility build marker missing: '+marker)
check('DEFAULT_GO_LDFLAGS = "-s -w -H windowsgui -buildid="' in builder,'default helper build profile changed unexpectedly')
check('YENC_GO_LDFLAGS = "-H windowsgui"' in builder,'Defender-accepted yEnc build profile changed')
check('return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS' in builder,
      'Historical v3.6.75 yEnc/default helper routing expression was not preserved')

for marker in (
    'Enforce canonical LF source checkout',
    "git config core.autocrlf false",
    "git config core.eol lf",
    "git checkout --force HEAD -- .",
    '$PSNativeCommandUseErrorActionPreference = $true',
    'python release/windows/validate-v3690-regressions.py',
    "Where-Object { $_ -like 'Source commit:*' }",
):
    check(marker in workflow,'Release-gate hardening marker missing: '+marker)
for marker in (
    "$pickerEntry = @($manifest.newzdeck_owned_binaries) | Where-Object { $_.binary -ceq 'NewzDeckPicker.exe' }",
    "$pickerBuildId = (& go tool buildid $pickerBinary 2>&1).Trim()",
    "$pickerSymbols = @(& go tool nm $pickerBinary 2>&1)",
):
    check(marker in workflow,'Built Picker validation marker missing: '+marker)

# Picker still performs the same legitimate folder/update handoff behaviors; this release must not remove them merely to evade AV.
for marker in ('func chooseFolder(', 'func updateHandoff()', 'case "--update-handoff":', 'runElevatedAndWait', 'closeNewzDeckWindows'):
    check(marker in picker,'Picker behavior unexpectedly removed: '+marker)

print('v3.6.91 Defender Picker Release Gate Compatibility Fix regression guard: PASS')
