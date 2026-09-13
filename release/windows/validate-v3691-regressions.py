from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'357858ad4cd91505fcff16078c40a767f6ed94d4d57be23e4d1de7020bf58975',
    'automation_engine.py':'139b9ecd44f9b53566beb2eee34efdc9cf2167f1fa050ce3c18feb3af893b87f',
    'sab_engine.py':'8f035c1fb872d17b076a5de47de7c998a402cdba3d0d3c62b33cee9c223c1ab9',
    'static/app.js':'bef3b27dd8504af32bda95eb4382cfc3c84e15c368c70adf06ff7ae58f5afb8f',
    'static/index.html':'19c1c1f45473756bea4ebe5a45ed79a42107e5b3f4acd8e152419f86849b5ce4',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'cba40b9f4d17e7ff0b4470cb2f67c4d070da44884577011158df4fd81d7613e5',
    'version.txt':'5f092e5c32d95689840a26f5e7cfc0e62bd09eced00236d0d073d1122bd14486',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.92 payload')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
check((APP/'version.txt').read_text().strip()=='3.6.92','version.txt mismatch')
check(manifest.get('version')=='3.6.92' and manifest.get('base_version')=='3.6.91' and manifest.get('adapter_version')=='3.6.92','build manifest lineage mismatch')
check(manifest.get('release')=='Defender Handoff Reduction & Picker Simplification','release identity mismatch')

builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
g79=(ROOT/'release'/'windows'/'validate-v3679-regressions.py').read_text(encoding='utf-8')
g80=(ROOT/'release'/'windows'/'validate-v3680-regressions.py').read_text(encoding='utf-8')
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
yenc_blob=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:src/windows/NewzDeckYenc.go'],text=True).strip()
check(yenc_blob=='38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15','NewzDeckYenc.go source changed')
check(hashlib.sha256(picker.encode()).hexdigest()=='df8b23aea5b8dfc18f43276759f3ef7d69dbd767e35eb191c133f6d8ffd97f46','reviewed v3.6.92 Picker source changed')
for marker in ('PICKER_GO_LDFLAGS = "-H windowsgui"','if exe == "NewzDeckPicker.exe": return PICKER_GO_LDFLAGS','return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS'):
    check(marker in builder,'Defender helper build invariant missing: '+marker)
obsolete='72b1683baa5097f704a8f28dfec2d2b34ac876f8'
check(obsolete not in g79,'v3.6.79 guard still pins obsolete whole-builder blob')
check(obsolete not in g80,'v3.6.80 guard still pins obsolete whole-builder blob')
for marker in ('python release/windows/validate-v3691-regressions.py','python release/windows/validate-v3692-regressions.py'):
    check(marker in workflow,'canonical workflow protection missing: '+marker)
for forbidden in ('--update-handoff','ShellExecuteExW','os/exec','EnumWindows'):
    check(forbidden not in picker,'Picker regained v3.6.91 handoff/process behavior: '+forbidden)
print('v3.6.91 release-gate compatibility intent carried forward under v3.6.92: PASS')
