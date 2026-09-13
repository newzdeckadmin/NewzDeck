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
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
launcher=(ROOT/'src'/'windows'/'NewzDeckLauncher.go').read_text(encoding='utf-8')
installer=(ROOT/'release'/'windows'/'NewzDeck.iss').read_text(encoding='utf-8')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.92','version.txt mismatch')
check('APP_VERSION = "3.6.92"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.92';" in app,'UI version mismatch')
check('v=3.6.92-defender-handoff-reduction-picker-simplification' in index,'asset cache identity mismatch')
check(manifest.get('version')=='3.6.92' and manifest.get('base_version')=='3.6.91' and manifest.get('adapter_version')=='3.6.92','manifest lineage mismatch')
check(manifest.get('release')=='Defender Handoff Reduction & Picker Simplification','release name mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')

# The in-app updater must launch the verified Setup directly. No copied executable handoff may return.
for required in ('def _launch_verified_setup_update(', 'args = ["/update", "/CLOSEAPPLICATIONS", "/FORCECLOSEAPPLICATIONS"]', '_launch_process_in_active_user_session(str(staged), subprocess.list2cmdline(args))', 'subprocess.Popen([str(staged)] + args, cwd=str(staged.parent))', 'def _schedule_verified_setup_update('):
    check(required in server,'direct Setup updater marker missing: '+required)
for forbidden in ('def _launch_update_handoff(', 'NewzDeckUpdateHandoff-', 'shutil.copy2(PICKER_HELPER_EXE', '"--update-handoff"'):
    check(forbidden not in server,'legacy copied update handoff returned: '+forbidden)

# Picker is now intentionally single-purpose.
check(hashlib.sha256(picker.encode()).hexdigest()=='df8b23aea5b8dfc18f43276759f3ef7d69dbd767e35eb191c133f6d8ffd97f46','Picker source differs from reviewed simplified source')
for required in ('func chooseFolder(', 'procSHBrowseForFolderW', 'func writeAtomic(', '--result-file'):
    check(required in picker,'folder-picker marker missing: '+required)
for forbidden in ('--update-handoff','--close-app-windows','os/exec','ShellExecuteExW','EnumWindows','FindWindowW','taskbarFix','closeTray','runElevatedAndWait'):
    check(forbidden not in picker,'Picker regained non-folder behavior: '+forbidden)

# Browser-window maintenance moved to the already-installed launcher.
for required in ('taskbarWMClose', 'func closeNewzDeckBrowserWindows(', 'isNewzDeckBrowserTitle(', 'if arg == "--close-app-windows"'):
    check(required in launcher,'launcher close-window mode missing: '+required)

# Setup must never execute Picker during upgrade. It closes the stale browser window only after overlay via the new launcher.
check("Exec(AppExe, '--close-app-windows'" in installer,'Setup does not use NewzDeck.exe close-window mode after overlay')
for forbidden in ("Exec(Helper, '--close-app-windows'", "Helper := ExpandConstant('{app}\\NewzDeckPicker.exe')"):
    check(forbidden not in installer,'Setup still executes Picker during upgrade: '+forbidden)
for required in ('StopExistingServiceForUpgrade','CloseExistingTrayForUpgrade','StopUpgradeNativeHelpers','RepairAndStartExistingService','RestoreTrayAfterInstall','RelaunchAppAfterUpdate'):
    check(required in installer,'installer upgrade behavior missing: '+required)

# Build provenance keeps normal Picker metadata and the known-good yEnc pipeline.
for required in ('PICKER_GO_LDFLAGS = "-H windowsgui"','if exe == "NewzDeckPicker.exe": return PICKER_GO_LDFLAGS','"source_behavior_changed":True','YENC_ACCEPTED_BINARY_SHA256 = "4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad"'):
    check(required in builder,'builder protection missing: '+required)

for required in ('python release/windows/validate-v3692-regressions.py','Picker source is not folder-picker-only','Launcher source is missing the bounded browser-window close mode',"[bool]$pickerOverride.source_behavior_changed"):
    check(required in workflow,'workflow v3.6.92 release gate missing: '+required)
print('v3.6.92 Defender Handoff Reduction & Picker Simplification regression guard: PASS')
