#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "app"
VERSION = "3.7.2"

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
workflow = (ROOT / ".github/workflows/publish-release-trigger.yml").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
website = (ROOT / "index.html").read_text(encoding="utf-8")
win_readme = (ROOT / "release/windows/README.md").read_text(encoding="utf-8")
notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
source_history = (ROOT / "docs/SOURCE_RELEASES.md").read_text(encoding="utf-8")

check((APP / "version.txt").read_text(encoding="utf-8").strip() == VERSION, "version.txt != 3.7.2")
check(f'APP_VERSION = "{VERSION}"' in server, "server APP_VERSION != 3.7.2")
check(f'ADAPTER_VERSION = "{VERSION}"' in sab_engine, "SAB adapter version != 3.7.2")
check(f"const UI_VERSION = '{VERSION}';" in ui, "UI_VERSION != 3.7.2")
check(manifest.get("version") == VERSION, "build-manifest version mismatch")
check(manifest.get("adapter_version") == VERSION, "build-manifest adapter_version mismatch")
check(manifest.get("base_version") == "3.7.1", "build-manifest base_version mismatch")
check(manifest.get("sabctools_version") == "9.6.3", "manifest SABCTools version mismatch")
check(manifest.get("sabctools_upstream_commit") == "54d7663b9e8f527b5ab196d43f0d5c561a87c1ac", "manifest SABCTools commit mismatch")

# v3.7.2 makes the public source exactly match the shipped runtime. The old
# v3.7.1 transformer remains only as historical provenance and must not be in
# either current build path.
check("apply-v371-runtime.py" not in builder, "Portable builder still mutates v3.7.0 source at build time")
check("apply-v371-runtime.py" not in workflow, "Production workflow still invokes the v3.7.1 runtime transformer")
check("APP_VERSION" in builder and "ADAPTER_VERSION" in builder and "UI_VERSION" in builder, "Portable source identity gate is incomplete")

# Preserve the proven in-process SABCTools architecture from v3.7.1.
check("_YENC_DECODER_MODULE" in server and "_active_yenc_pipeline_label" in server, "SABCTools server integration missing")
check("SabctoolsDecoder" in yenc and "EXPECTED_SABCTOOLS_VERSION = \"9.6.3\"" in yenc, "SABCTools decoder adapter/pin missing")
check("NATIVE_YENC_POOL" not in server and "class _NativeYencWorker" not in server, "retired yEnc subprocess path returned")
check('"NewzDeckYenc.exe": "NewzDeckYenc.go"' not in builder, "Portable builder still builds NewzDeckYenc.exe")
check("sabctools.cp312-win_amd64.pyd" in builder, "Portable SABCTools payload requirement missing")
check("NewzDeckYenc.exe" in build_release and "retiredYencDelete" in build_release, "installed-upgrade retired-helper cleanup missing")
check("SAB_VERSION = \"5.1.2\"" in sab_engine, "private SABnzbd baseline changed")

# Release pipeline must validate every identity independently so a repeat of the
# v3.7.1 UI/backend adapter mismatch cannot publish.
check("validate-v3720-regressions.py" in workflow, "v3.7.2 workflow guard missing")
check("ADAPTER_VERSION" in workflow and "APP_VERSION" in workflow and "UI_VERSION" in workflow, "workflow identity coherence checks missing")
check("SABCTOOLS_VERSION: '9.6.3'" in workflow, "workflow SABCTools version pin missing")
check("54d7663b9e8f527b5ab196d43f0d5c561a87c1ac" in workflow, "workflow SABCTools commit pin missing")
check("yenc-helper:" not in workflow and "newzdeck-yenc-defender-lf" not in workflow, "retired yEnc helper workflow returned")

# User-facing release surfaces must advance with the release source itself.
check("current stable release is **NewzDeck v3.7.2**" in readme, "root README latest release is stale")
check("NewzDeck_v3.7.2_Setup.exe" in readme and "NewzDeck_v3.7.2_SHA256.txt" in readme, "root README asset names are stale")
check("v3.7.2" in website and "v3.7.0" not in website, "website fallback release identity is stale")
check("five NewzDeck-owned Windows executables" in win_readme, "Windows build README binary count is stale")
check("SABCTools 9.6.3" in win_readme, "Windows build README SABCTools architecture missing")
check("## SABCTools 9.6.3" in notices and "GPL-2.0-or-later" in notices, "SABCTools third-party notice missing")
check((ROOT / "licenses/SABCTOOLS-LICENSE.md").is_file(), "SABCTools license text is missing")
check("## Current release: v3.7.2" in source_history, "source/release history latest release is stale")

# Frozen UI styling/theme files stay untouched by this hotfix.
check(sha(APP / "static/styles.css") == "ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d", "styles.css changed")
check(sha(APP / "static/themes.css") == "2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721", "themes.css changed")
check((ROOT / "release/RELEASE_NOTES_v3.7.2.md").is_file(), "v3.7.2 release notes missing")
print("validate-v3720-regressions.py: PASS")
