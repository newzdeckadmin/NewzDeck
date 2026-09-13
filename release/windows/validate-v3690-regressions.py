from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'

def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

EXPECTED={
    'server.py':'c599e5baec178f686621d5d5353230c100f87b3a165866866fd02d1ef496ebe2',
    'automation_engine.py':'2251d62400d9b1c23604696f82549977aa9c64d18d2e60299a7af3fbcbe9e9cb',
    'sab_engine.py':'b77650ff20c4a08cadbd6e224be5c76ed45bbdbf7ed81586fc30f6fda684bb81',
    'static/app.js':'e3e41ad9ddd8ed948061aa81e3c859d387e30bcf2656615ee15f6805ef808a65',
    'static/index.html':'e751cbde9917a79e8678a59644f68ac5478c81a13e13d2aa504b8f0d8c1c4721',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'02074a2f67e5b3917fb1decd1774970a96b4318a74b9832bcb341fa64f2f0a5d',
    'version.txt':'cc2988a3a8006e8e61ddbbf5e331599b132a78e4cd609805981982406f28396f',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.90 payload')

manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check((APP/'version.txt').read_text().strip()=='3.6.90','version.txt mismatch')
check(manifest.get('version')=='3.6.90' and manifest.get('base_version')=='3.6.89' and manifest.get('adapter_version')=='3.6.90','build manifest lineage mismatch')
check(manifest.get('release')=='Windows Defender Picker Compatibility & Release Gate Hardening','release identity mismatch')
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

print('v3.6.90 Windows Defender Picker Compatibility & Release Gate Hardening regression guard: PASS')
