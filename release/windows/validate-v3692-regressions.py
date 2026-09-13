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
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
launcher=(ROOT/'src'/'windows'/'NewzDeckLauncher.go').read_text(encoding='utf-8')
installer=(ROOT/'release'/'windows'/'NewzDeck.iss').read_text(encoding='utf-8')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.96','version.txt mismatch')
check('APP_VERSION = "3.6.96"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.96';" in app,'UI version mismatch')
check('v=3.6.96-library-article-aware-sorting' in index,'asset cache identity mismatch')
check(manifest.get('version')=='3.6.96' and manifest.get('base_version')=='3.6.95' and manifest.get('adapter_version')=='3.6.96','manifest lineage mismatch')
check(manifest.get('release')=='Library Article-Aware Sorting','release name mismatch')
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
    check(required in workflow,'workflow v3.6.96 release gate missing: '+required)
print('v3.6.96 Defender Handoff Release Gate Recovery carried-forward guard: PASS')
