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
check((APP/'version.txt').read_text().strip()=='3.6.99','version.txt mismatch')
check(manifest.get('version')=='3.6.99' and manifest.get('base_version')=='3.6.96' and manifest.get('adapter_version')=='3.6.99','build manifest lineage mismatch')
check(manifest.get('release')=='Final UX & Backup/Restore','release identity mismatch')

builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
g79=(ROOT/'release'/'windows'/'validate-v3679-regressions.py').read_text(encoding='utf-8')
g80=(ROOT/'release'/'windows'/'validate-v3680-regressions.py').read_text(encoding='utf-8')
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
yenc_blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(yenc_blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go source changed')
check(hashlib.sha256(picker.encode()).hexdigest()=='df8b23aea5b8dfc18f43276759f3ef7d69dbd767e35eb191c133f6d8ffd97f46','reviewed v3.6.99 Picker source changed')
for marker in ('PICKER_GO_LDFLAGS = "-H windowsgui"','if exe == "NewzDeckPicker.exe": return PICKER_GO_LDFLAGS','return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS'):
    check(marker in builder,'Defender helper build invariant missing: '+marker)
obsolete='72b1683baa5097f704a8f28dfec2d2b34ac876f8'
check(obsolete not in g79,'v3.6.79 guard still pins obsolete whole-builder blob')
check(obsolete not in g80,'v3.6.80 guard still pins obsolete whole-builder blob')
for marker in ('python release/windows/validate-v3691-regressions.py','python release/windows/validate-v3692-regressions.py'):
    check(marker in workflow,'canonical workflow protection missing: '+marker)
for forbidden in ('--update-handoff','ShellExecuteExW','os/exec','EnumWindows'):
    check(forbidden not in picker,'Picker regained v3.6.91 handoff/process behavior: '+forbidden)
print('v3.6.91 release-gate compatibility intent carried forward under v3.6.99: PASS')
