from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'cf095fa4af834c60d050e56e90aacbddf3d26b2e7e672e1938766725b97a17db',
    'automation_engine.py':'5880a9747dbe5ef4be2bc17685119d82155c1f688d3d10b04ee5c9b1c0513e39',
    'sab_engine.py':'56e5a089f26cfdd3a2b6e40e1838973194220687c191de14f91e1f6953be42c3',
    'static/app.js':'42f5c835e9435b7ceba0ae4664326813c803718de3c9f2dfe6430a40b87c1845',
    'static/index.html':'7c1f68a8aa7b7e6441d142592f6f198dbe8331c2e6dd5c60d4952d1d236296ad',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'build-manifest.json':'623006d630ae88ec859e371561e69e46daeebc55f7c8417847015799e720e1f8',
    'version.txt':'44a1fcae929eb12521b0218135694ad3d84f616ba88ff4914fa1e8ffb45617ea',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.96 payload')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check((APP/'version.txt').read_text().strip()=='3.6.96','version.txt mismatch')
check(manifest.get('version')=='3.6.96' and manifest.get('base_version')=='3.6.95' and manifest.get('adapter_version')=='3.6.96','build manifest lineage mismatch')
check(manifest.get('release')=='Library Article-Aware Sorting','release identity mismatch')

builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
g79=(ROOT/'release'/'windows'/'validate-v3679-regressions.py').read_text(encoding='utf-8')
g80=(ROOT/'release'/'windows'/'validate-v3680-regressions.py').read_text(encoding='utf-8')
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
yenc_blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(yenc_blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go source changed')
check(hashlib.sha256(picker.encode()).hexdigest()=='df8b23aea5b8dfc18f43276759f3ef7d69dbd767e35eb191c133f6d8ffd97f46','reviewed v3.6.96 Picker source changed')
for marker in ('PICKER_GO_LDFLAGS = "-H windowsgui"','if exe == "NewzDeckPicker.exe": return PICKER_GO_LDFLAGS','return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS'):
    check(marker in builder,'Defender helper build invariant missing: '+marker)
obsolete='72b1683baa5097f704a8f28dfec2d2b34ac876f8'
check(obsolete not in g79,'v3.6.79 guard still pins obsolete whole-builder blob')
check(obsolete not in g80,'v3.6.80 guard still pins obsolete whole-builder blob')
for marker in ('python release/windows/validate-v3691-regressions.py','python release/windows/validate-v3692-regressions.py'):
    check(marker in workflow,'canonical workflow protection missing: '+marker)
for forbidden in ('--update-handoff','ShellExecuteExW','os/exec','EnumWindows'):
    check(forbidden not in picker,'Picker regained v3.6.91 handoff/process behavior: '+forbidden)
print('v3.6.91 release-gate compatibility intent carried forward under v3.6.96: PASS')
