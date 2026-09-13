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
check((APP/'version.txt').read_text().strip()=='3.7.0','version.txt mismatch')
check(manifest.get('version')=='3.7.0' and manifest.get('base_version')=='3.6.99' and manifest.get('adapter_version')=='3.7.0','build manifest lineage mismatch')
check(manifest.get('release')=='Production Milestone & Repository Hygiene','release identity mismatch')

builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
g79=(ROOT/'release'/'windows'/'validate-v3679-regressions.py').read_text(encoding='utf-8')
g80=(ROOT/'release'/'windows'/'validate-v3680-regressions.py').read_text(encoding='utf-8')
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
yenc_blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(yenc_blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go source changed')
check(hashlib.sha256(picker.encode()).hexdigest()=='df8b23aea5b8dfc18f43276759f3ef7d69dbd767e35eb191c133f6d8ffd97f46','reviewed v3.7.0 Picker source changed')
for marker in ('PICKER_GO_LDFLAGS = "-H windowsgui"','if exe == "NewzDeckPicker.exe": return PICKER_GO_LDFLAGS','return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS'):
    check(marker in builder,'Defender helper build invariant missing: '+marker)
obsolete='72b1683baa5097f704a8f28dfec2d2b34ac876f8'
check(obsolete not in g79,'v3.6.79 guard still pins obsolete whole-builder blob')
check(obsolete not in g80,'v3.6.80 guard still pins obsolete whole-builder blob')
for marker in ('python release/windows/validate-v3691-regressions.py','python release/windows/validate-v3692-regressions.py'):
    check(marker in workflow,'canonical workflow protection missing: '+marker)
for forbidden in ('--update-handoff','ShellExecuteExW','os/exec','EnumWindows'):
    check(forbidden not in picker,'Picker regained v3.6.91 handoff/process behavior: '+forbidden)
print('v3.6.91 release-gate compatibility intent carried forward under v3.7.0: PASS')
