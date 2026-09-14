#!/usr/bin/env python3
"""Build a deterministic NewzDeck Windows Portable ZIP from public source."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "app"
WIN = ROOT / "src" / "windows"
ASSETS = ROOT / "src" / "assets"

HELPERS = {
    "NewzDeck.exe": "NewzDeckLauncher.go",
    "NewzDeckService.exe": "NewzDeckService.go",
    "NewzDeckTray.exe": "NewzDeckTray.go",
    "NewzDeckPicker.exe": "NewzDeckPicker.go",
    "NewzDeckThumb.exe": "NewzDeckThumb.go",
}

DEFAULT_GO_LDFLAGS = "-s -w -H windowsgui -buildid="
PICKER_GO_LDFLAGS = "-H windowsgui"
SABCTOOLS_VERSION = "9.6.3"
SABCTOOLS_COMMIT = "54d7663b9e8f527b5ab196d43f0d5c561a87c1ac"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd, **kw):
    print("+", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, **kw)


def helper_ldflags(exe: str) -> str:
    if exe == "NewzDeckPicker.exe":
        return PICKER_GO_LDFLAGS
    return DEFAULT_GO_LDFLAGS


def copy_app(stage: pathlib.Path, sabctools_package: pathlib.Path):
    for rel in [
        "server.py",
        "sab_engine.py",
        "automation_engine.py",
        "yenc_decoder.py",
        "build-manifest.json",
        "start.bat",
        "version.txt",
    ]:
        shutil.copy2(APP / rel, stage / rel)
    shutil.copytree(APP / "static", stage / "static")
    run([
        sys.executable, str(ROOT / "release" / "windows" / "apply-v371-runtime.py"),
        "--server", str(stage / "server.py"),
        "--app-js", str(stage / "static" / "app.js"),
    ])
    shutil.copy2(ASSETS / "NewzDeck.ico", stage / "NewzDeck.ico")
    shutil.copy2(ROOT / "README.txt", stage / "README.txt")
    shutil.copy2(ROOT / "UPDATING.txt", stage / "UPDATING.txt")
    shutil.copy2(ROOT / "LICENSE", stage / "LICENSE.txt")
    shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", stage / "THIRD_PARTY_NOTICES.txt")
    shutil.copytree(ROOT / "licenses", stage / "licenses")

    if not sabctools_package.is_dir():
        raise SystemExit(f"SABCTools package directory does not exist: {sabctools_package}")
    init_py = sabctools_package / "__init__.py"
    pyds = sorted(sabctools_package.glob("sabctools.cp312-win_amd64.pyd"))
    if not init_py.is_file() or len(pyds) != 1:
        raise SystemExit("SABCTools package must contain __init__.py and exactly one cp312 win_amd64 native extension")
    target = stage / "sabctools"
    shutil.copytree(sabctools_package, target)


def build_go(stage: pathlib.Path):
    env = os.environ.copy()
    env.update(GOOS="windows", GOARCH="amd64", CGO_ENABLED="0")
    version = subprocess.check_output(["go", "version"], text=True).strip()
    if "go1.23.2" not in version:
        raise SystemExit(f"Go 1.23.2 is required for the canonical Windows build; found {version}")
    for exe, src in HELPERS.items():
        ldflags = helper_ldflags(exe)
        run(["go", "build", "-trimpath", f"-ldflags={ldflags}", "-o", str(stage / exe), str(WIN / src)], env=env, cwd=str(ROOT))


def validate_source(version: str):
    actual = (APP / "version.txt").read_text(encoding="utf-8").strip()
    if actual != version:
        raise SystemExit(f"version.txt is {actual}, expected {version}")
    # server.py/app.js are deliberately frozen at the v3.7.0 baseline in the
    # public tree; the canonical transformation is hash-pinned and self-tested.
    run([sys.executable, str(ROOT / "release" / "windows" / "apply-v371-runtime.py"), "--self-test"])
    run([
        sys.executable, "-m", "py_compile",
        str(APP / "server.py"), str(APP / "sab_engine.py"),
        str(APP / "automation_engine.py"), str(APP / "yenc_decoder.py"),
    ])
    node = shutil.which("node")
    if node:
        run([node, "--check", str(APP / "static" / "app.js")])
    else:
        print("warning: node not found; JavaScript syntax check skipped locally")


def write_manifest(stage: pathlib.Path, version: str):
    mappings = []
    for exe, src in HELPERS.items():
        mappings.append({
            "binary": exe,
            "sha256": sha(stage / exe),
            "source": f"src/windows/{src}",
            "source_sha256": sha(WIN / src),
        })

    sab_dir = stage / "sabctools"
    sab_files = []
    for path in sorted(sab_dir.rglob("*")):
        if path.is_file():
            sab_files.append({
                "path": path.relative_to(stage).as_posix(),
                "sha256": sha(path),
            })

    manifest = {
        "product": "NewzDeck",
        "version": version,
        "license": "GPL-3.0-only",
        "build": {
            "go": "1.23.2", "goos": "windows", "goarch": "amd64",
            "cgo_enabled": False, "ldflags": DEFAULT_GO_LDFLAGS,
        },
        "binary_build_overrides": {
            "NewzDeckPicker.exe": {
                "purpose": "Windows Defender false-positive reduction and folder-picker-only scope",
                "source_behavior_changed": True,
                "go": "1.23.2", "goos": "windows", "goarch": "amd64",
                "cgo_enabled": False, "trimpath": True,
                "ldflags": PICKER_GO_LDFLAGS,
                "difference_from_default": "normal Go build ID and symbol/debug metadata retained; -s, -w, and empty buildid removed",
                "build_origin": "windows-source-build",
            }
        },
        "newzdeck_owned_binaries": mappings,
        "retired_legacy_binaries": ["NewzDeckBootstrap.exe", "NewzDeckCore.exe", "NewzDeckYenc.exe"],
        "vendored_python_packages": [{
            "name": "sabctools",
            "version": SABCTOOLS_VERSION,
            "upstream_repository": "sabnzbd/sabctools",
            "upstream_commit": SABCTOOLS_COMMIT,
            "python_abi": "cp312",
            "platform": "win_amd64",
            "files": sab_files,
        }],
        "generated_application": [
            {"path": "server.py", "sha256": sha(stage / "server.py"), "transform": "release/windows/apply-v371-runtime.py"},
            {"path": "static/app.js", "sha256": sha(stage / "static" / "app.js"), "transform": "release/windows/apply-v371-runtime.py"},
        ],
        "application_source": [
            {"path": "src/app/server.py", "sha256": sha(APP / "server.py")},
            {"path": "src/app/sab_engine.py", "sha256": sha(APP / "sab_engine.py")},
            {"path": "src/app/automation_engine.py", "sha256": sha(APP / "automation_engine.py")},
            {"path": "src/app/yenc_decoder.py", "sha256": sha(APP / "yenc_decoder.py")},
            {"path": "src/app/static/app.js", "sha256": sha(APP / "static" / "app.js")},
            {"path": "src/app/static/index.html", "sha256": sha(APP / "static" / "index.html")},
            {"path": "src/app/static/styles.css", "sha256": sha(APP / "static" / "styles.css")},
            {"path": "src/app/static/themes.css", "sha256": sha(APP / "static" / "themes.css")},
            {"path": "src/app/static/tmdb-logo.svg", "sha256": sha(APP / "static" / "tmdb-logo.svg")},
        ],
    }
    (stage / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def deterministic_zip(stage: pathlib.Path, out: pathlib.Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(stage.rglob("*"), key=lambda x: x.relative_to(stage).as_posix().lower()):
            if not p.is_file():
                continue
            rel = p.relative_to(stage).as_posix()
            info = zipfile.ZipInfo(rel, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 & 0xFFFF) << 16
            z.writestr(info, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--sabctools-package", required=True)
    ns = ap.parse_args()
    version = ns.version
    sabctools_package = pathlib.Path(ns.sabctools_package).resolve()
    validate_source(version)
    with tempfile.TemporaryDirectory(prefix="newzdeck-build-") as td:
        stage = pathlib.Path(td) / "payload"
        stage.mkdir()
        copy_app(stage, sabctools_package)
        build_go(stage)
        write_manifest(stage, version)
        out = pathlib.Path(ns.output).resolve()
        deterministic_zip(stage, out)
        with zipfile.ZipFile(out) as z:
            bad = z.testzip()
            names = set(z.namelist())
        if bad:
            raise SystemExit(f"ZIP CRC failure: {bad}")
        required = list(HELPERS) + [
            "server.py", "yenc_decoder.py", "version.txt", "LICENSE.txt",
            "SOURCE_MANIFEST.json", "static/tmdb-logo.svg", "sabctools/__init__.py",
            "sabctools/sabctools.cp312-win_amd64.pyd",
        ]
        missing = [x for x in required if x not in names]
        if missing:
            raise SystemExit(f"missing payload entries: {missing}")
        forbidden = {"NewzDeckBootstrap.exe", "NewzDeckCore.exe", "NewzDeckYenc.exe", "PORTABLE_TESTING.txt", "start.sh"}
        present = sorted(forbidden & names)
        if present:
            raise SystemExit(f"production payload contains forbidden entries: {present}")
        print(f"Portable: {out}")
        print(f"SHA-256: {sha(out)}")


if __name__ == "__main__":
    main()
