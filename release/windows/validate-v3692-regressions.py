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
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
launcher=(ROOT/'src'/'windows'/'NewzDeckLauncher.go').read_text(encoding='utf-8')
installer=(ROOT/'release'/'windows'/'NewzDeck.iss').read_text(encoding='utf-8')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.7.0','version.txt mismatch')
check('APP_VERSION = "3.7.0"' in server,'server version mismatch')
check("const UI_VERSION = '3.7.0';" in app,'UI version mismatch')
check('v=3.7.0-production-milestone-repository-hygiene' in index,'asset cache identity mismatch')
check(manifest.get('version')=='3.7.0' and manifest.get('base_version')=='3.6.99' and manifest.get('adapter_version')=='3.7.0','manifest lineage mismatch')
check(manifest.get('release')=='Production Milestone & Repository Hygiene','release name mismatch')
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
    check(required in workflow,'workflow v3.7.0 release gate missing: '+required)
print('v3.7.0 Defender Handoff Release Gate Recovery carried-forward guard: PASS')
