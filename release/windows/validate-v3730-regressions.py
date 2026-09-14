#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "app"
VERSION = "3.7.3"

def check(value, message):
    if not value:
        raise SystemExit(message)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

server = (APP / "server.py").read_text(encoding="utf-8")
sab_engine = (APP / "sab_engine.py").read_text(encoding="utf-8")
ui = (APP / "static/app.js").read_text(encoding="utf-8")
yenc = (APP / "yenc_decoder.py").read_text(encoding="utf-8")
manifest = json.loads((APP / "build-manifest.json").read_text(encoding="utf-8"))
builder = (ROOT / "release/windows/build-portable.py").read_text(encoding="utf-8")
build_release = (ROOT / "release/windows/build-release.ps1").read_text(encoding="utf-8")
installer = (ROOT / "release/windows/NewzDeck.iss").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/publish-release-trigger.yml").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
website = (ROOT / "index.html").read_text(encoding="utf-8")
win_readme = (ROOT / "release/windows/README.md").read_text(encoding="utf-8")
notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
source_history = (ROOT / "docs/SOURCE_RELEASES.md").read_text(encoding="utf-8")

check((APP / "version.txt").read_text(encoding="utf-8").strip() == VERSION, "version.txt != 3.7.3")
check(f'APP_VERSION = "{VERSION}"' in server, "server APP_VERSION != 3.7.3")
check(f'ADAPTER_VERSION = "{VERSION}"' in sab_engine, "SAB adapter version != 3.7.3")
check(f"const UI_VERSION = '{VERSION}';" in ui, "UI_VERSION != 3.7.3")
check(manifest.get("version") == VERSION, "build-manifest version mismatch")
check(manifest.get("adapter_version") == VERSION, "build-manifest adapter_version mismatch")
check(manifest.get("base_version") == "3.7.2", "build-manifest base_version mismatch")
check(manifest.get("sabctools_version") == "9.6.3", "manifest SABCTools version mismatch")

managed_args = 'args = ["/update", "/SILENT", "/SP-", "/NORESTART", "/CLOSEAPPLICATIONS", "/FORCECLOSEAPPLICATIONS"]'
check(managed_args in server, "managed About & Updates Setup arguments are missing")
check('NewzDeckUpdateHandoff-' not in server and '--update-handoff' not in server, "retired copied update coordinator returned")
check('_launch_verified_setup_update' in server and '_schedule_verified_setup_update' in server, "direct verified Setup handoff missing")
check('server_obj.shutdown()' in server, "desktop backend relinquish after Setup launch missing")

check("ManagedSilentUpdate" in installer, "installer managed-silent-update state missing")
check("function IsManagedSilentUpdate(): Boolean;" in installer, "managed silent parameter detector missing")
prepare = re.search(r'function PrepareToInstall\(var NeedsRestart: Boolean\): String;\n(.*?)\nend;', installer, re.S)
check(prepare is not None, "PrepareToInstall block missing")
prepare_text = prepare.group(1)
check("ManagedSilentUpdate := IsManagedSilentUpdate();" in prepare_text, "PrepareToInstall does not identify managed update")
check("CloseInstalledAppWindowForUpdate();" in prepare_text, "managed update does not close app window before install")
check("CloseExistingTrayForUpgrade();" in prepare_text, "tray close/wait missing")
check("StopExistingServiceForUpgrade();" in prepare_text, "service stop/wait missing")
check(prepare_text.index("CloseInstalledAppWindowForUpdate();") < prepare_text.index("CloseExistingTrayForUpgrade();"), "app window is not closed before tray handoff")
check(prepare_text.index("CloseExistingTrayForUpgrade();") < prepare_text.index("StopExistingServiceForUpgrade();"), "tray/service shutdown order changed")

relaunch = re.search(r'procedure RelaunchAppAfterUpdate\(\);\n(.*?)\nend;', installer, re.S)
check(relaunch is not None, "RelaunchAppAfterUpdate block missing")
relaunch_text = relaunch.group(1)
check("if not UpdateMode then" in relaunch_text, "update-mode relaunch guard missing")
check("WizardSilent and not ManagedSilentUpdate" in relaunch_text, "managed silent update relaunch exception missing")
check("Exec(AppExe" in relaunch_text, "NewzDeck relaunch call missing")

curstep = re.search(r'procedure CurStepChanged\(CurStep: TSetupStep\);\n(.*?)\nend;', installer, re.S)
check(curstep is not None, "CurStepChanged block missing")
curstep_text = curstep.group(1)
for marker in ("RepairAndStartExistingService();", "RefreshTrayAutostart();", "RestoreTrayAfterInstall();", "RelaunchAppAfterUpdate();"):
    check(marker in curstep_text, f"installer lifecycle marker missing: {marker}")

check("apply-v371-runtime.py" not in builder, "Portable builder returned to packaging-time runtime transform")
check("apply-v371-runtime.py" not in workflow, "workflow returned to packaging-time runtime transform")
check("_YENC_DECODER_MODULE" in server and "_active_yenc_pipeline_label" in server, "SABCTools server integration missing")
check("SabctoolsDecoder" in yenc and 'EXPECTED_SABCTOOLS_VERSION = "9.6.3"' in yenc, "SABCTools decoder adapter/pin missing")
check("NATIVE_YENC_POOL" not in server and "class _NativeYencWorker" not in server, "retired yEnc subprocess path returned")
check('"NewzDeckYenc.exe": "NewzDeckYenc.go"' not in builder, "Portable builder still builds NewzDeckYenc.exe")
check("NewzDeckYenc.exe" in build_release and "retiredYencDelete" in build_release, "retired helper upgrade cleanup missing")
check('SAB_VERSION = "5.1.2"' in sab_engine, "private SABnzbd baseline changed")
check("validate-v3730-regressions.py" in workflow, "v3.7.3 workflow guard missing")

check("current stable release is **NewzDeck v3.7.3**" in readme, "root README latest release is stale")
check("NewzDeck_v3.7.3_Setup.exe" in readme and "NewzDeck_v3.7.3_SHA256.txt" in readme, "root README asset names are stale")
check("v3.7.3" in website and "v3.7.2" not in website, "website fallback release identity is stale")
check("managed silent-update" in win_readme.casefold(), "Windows build README does not document managed update handoff")
check("## SABCTools 9.6.3" in notices and "GPL-2.0-or-later" in notices, "SABCTools notice regressed")
check("## Current release: v3.7.3" in source_history, "source/release history latest release is stale")

check(sha(APP / "static/styles.css") == "ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d", "styles.css changed")
check(sha(APP / "static/themes.css") == "2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721", "themes.css changed")
check((ROOT / "release/RELEASE_NOTES_v3.7.3.md").is_file(), "v3.7.3 release notes missing")
print("validate-v3730-regressions.py: PASS")
