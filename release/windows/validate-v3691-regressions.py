from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'

def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

EXPECTED={
    'server.py': '94f849feb0d8aa35ccec16ab8ad8c041bc07acffe94e8f08fc107fea0ebf77ae',
    'automation_engine.py': 'c52d5f93ba6ad24a1045ebda49a2b1973d9fdd43d6e56e973dd0404ff8b5ede7',
    'sab_engine.py': 'c899f3d39de00ee5c43f22f1cb0cdef3009449274789753ea4a97d37b864e77c',
    'static/app.js': '8932e47cbbc06e965c2bf02692bab72107179a53a20038d9594dd2a3ee6d781f',
    'static/index.html': 'bf357570e16584b46a9ee42a5e103457f4612afd04f3d1cecf269e2db9276ea8',
    'static/styles.css': 'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json': '51d1981e1cada1d63276409977fddc33379d523ef13199e6fc1e8450421b895a',
    'version.txt': '21a15ffafda3766bf34259e3defea1a151f7c980e409a8a4a9c70b357d504c36'
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.91 payload')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check((APP/'version.txt').read_text().strip()=='3.6.91','version.txt mismatch')
check(manifest.get('version')=='3.6.91' and manifest.get('base_version')=='3.6.90' and manifest.get('adapter_version')=='3.6.91','build manifest lineage mismatch')
check(manifest.get('release')=='Defender Picker Release Gate Compatibility Fix','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')

builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
g79=(ROOT/'release'/'windows'/'validate-v3679-regressions.py').read_text(encoding='utf-8')
g80=(ROOT/'release'/'windows'/'validate-v3680-regressions.py').read_text(encoding='utf-8')

picker_blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckPicker.go'],text=True).strip()
yenc_blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(picker_blob=='c25528879ebe302315b0203de21b767d92c3d437','NewzDeckPicker.go source changed')
check(yenc_blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go source changed')
for marker in (
    'DEFAULT_GO_LDFLAGS = "-s -w -H windowsgui -buildid="',
    'YENC_GO_LDFLAGS = "-H windowsgui"',
    'PICKER_GO_LDFLAGS = "-H windowsgui"',
    'if exe == "NewzDeckPicker.exe": return PICKER_GO_LDFLAGS',
    'return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS',
    '"build_origin":"windows-source-build"',
): check(marker in builder,'Defender helper build invariant missing: '+marker)

obsolete='72b1683baa5097f704a8f28dfec2d2b34ac876f8'
check(obsolete not in g79,'v3.6.79 guard still pins obsolete whole-builder blob')
check(obsolete not in g80,'v3.6.80 guard still pins obsolete whole-builder blob')
for guard,name in ((g79,'v3.6.79'),(g80,'v3.6.80')):
    for marker in ('PICKER_GO_LDFLAGS = "-H windowsgui"','return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS'):
        check(marker in guard,f'{name} guard does not validate reviewed helper invariant: {marker}')

for marker in (
    'Enforce canonical LF source checkout',
    '$PSNativeCommandUseErrorActionPreference = $true',
    'python release/windows/validate-v3690-regressions.py',
    'python release/windows/validate-v3691-regressions.py',
    '$pickerBuildId = (& go tool buildid $pickerBinary 2>&1).Trim()',
    '$pickerSymbols = @(& go tool nm $pickerBinary 2>&1)',
): check(marker in workflow,'Canonical workflow protection missing: '+marker)

check(sha(APP/'static'/'styles.css')=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','frozen stylesheet changed')
print('v3.6.91 Defender Picker Release Gate Compatibility Fix regression guard: PASS')
