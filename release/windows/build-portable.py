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
    "NewzDeckYenc.exe": "NewzDeckYenc.go",
}

DEFAULT_GO_LDFLAGS = "-s -w -H windowsgui -buildid="
YENC_GO_LDFLAGS = "-H windowsgui"
YENC_ACCEPTED_SOURCE_SHA256 = "ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd"
YENC_ACCEPTED_BINARY_SHA256 = "4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)

def sha(path: pathlib.Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical_git_source_bytes(rel: str) -> bytes:
    return subprocess.check_output(['git','-C',str(ROOT),'show',f'HEAD:{rel}'])

def run(cmd, **kw):
    print('+',' '.join(map(str,cmd)))
    subprocess.run(cmd, check=True, **kw)

def helper_ldflags(exe: str) -> str:
    # v3.6.75: Defender compatibility is intentionally scoped only to the
    # unchanged native yEnc helper. Retaining normal Go build metadata avoids
    # the false-positive signature observed with the stripped historical build.
    return YENC_GO_LDFLAGS if exe == "NewzDeckYenc.exe" else DEFAULT_GO_LDFLAGS

def copy_app(stage: pathlib.Path):
    # Production payload intentionally excludes development/acceptance launchers
    # such as start.sh and PORTABLE_TESTING.txt.
    for rel in ["server.py","sab_engine.py","automation_engine.py","build-manifest.json","start.bat","version.txt"]:
        shutil.copy2(APP/rel, stage/rel)
    shutil.copytree(APP/"static", stage/"static")
    shutil.copy2(ASSETS/"NewzDeck.ico", stage/"NewzDeck.ico")
    shutil.copy2(ROOT/"README.txt", stage/"README.txt")
    shutil.copy2(ROOT/"UPDATING.txt", stage/"UPDATING.txt")
    shutil.copy2(ROOT/"LICENSE", stage/"LICENSE.txt")
    shutil.copy2(ROOT/"THIRD_PARTY_NOTICES.md", stage/"THIRD_PARTY_NOTICES.txt")
    shutil.copytree(ROOT/"licenses", stage/"licenses")

def build_go(stage: pathlib.Path, prebuilt_yenc: pathlib.Path | None = None):
    env=os.environ.copy(); env.update(GOOS='windows',GOARCH='amd64',CGO_ENABLED='0')
    version=subprocess.check_output(['go','version'],text=True).strip()
    if 'go1.23.2' not in version:
        raise SystemExit(f'Go 1.23.2 is required for the canonical Windows build; found {version}')
    for exe,src in HELPERS.items():
        if exe == 'NewzDeckYenc.exe' and prebuilt_yenc is not None:
            source_bytes=canonical_git_source_bytes(f'src/windows/{src}')
            if sha_bytes(source_bytes) != YENC_ACCEPTED_SOURCE_SHA256:
                raise SystemExit('Canonical Git yEnc source SHA-256 changed; refusing prebuilt helper handoff')
            if not prebuilt_yenc.is_file():
                raise SystemExit(f'Prebuilt yEnc helper does not exist: {prebuilt_yenc}')
            if sha(prebuilt_yenc) != YENC_ACCEPTED_BINARY_SHA256:
                raise SystemExit('Prebuilt yEnc helper SHA-256 does not match the Defender-accepted binary')
            shutil.copy2(prebuilt_yenc, stage/exe)
            continue
        ldflags=helper_ldflags(exe)
        run(['go','build','-trimpath',f'-ldflags={ldflags}','-o',str(stage/exe),str(WIN/src)],env=env,cwd=str(ROOT))

def validate_source(version: str):
    actual=(APP/'version.txt').read_text(encoding='utf-8').strip()
    if actual != version: raise SystemExit(f'version.txt is {actual}, expected {version}')
    run([sys.executable,'-m','py_compile',str(APP/'server.py'),str(APP/'sab_engine.py'),str(APP/'automation_engine.py')])
    node=shutil.which('node')
    if node: run([node,'--check',str(APP/'static'/'app.js')])
    else: print('warning: node not found; JavaScript syntax check skipped locally')

def write_manifest(stage: pathlib.Path, version: str, prebuilt_yenc: pathlib.Path | None = None):
    mappings=[]
    for exe,src in HELPERS.items():
        source_sha256 = sha_bytes(canonical_git_source_bytes(f'src/windows/{src}')) if exe == 'NewzDeckYenc.exe' else sha(WIN/src)
        mappings.append({"binary":exe,"sha256":sha(stage/exe),"source":f"src/windows/{src}","source_sha256":source_sha256})
    manifest={
        "product":"NewzDeck","version":version,"license":"GPL-3.0-only",
        "build":{"go":"1.23.2","goos":"windows","goarch":"amd64","cgo_enabled":False,"ldflags":DEFAULT_GO_LDFLAGS},
        "binary_build_overrides":{
            "NewzDeckYenc.exe":{
                "purpose":"Windows Defender compatibility",
                "source_behavior_changed":False,
                "go":"1.23.2",
                "goos":"windows",
                "goarch":"amd64",
                "cgo_enabled":False,
                "trimpath":True,
                "ldflags":YENC_GO_LDFLAGS,
                "difference_from_default":"normal Go build ID and symbol/debug metadata retained; -s, -w, and empty buildid removed",
                "canonical_git_source_sha256":YENC_ACCEPTED_SOURCE_SHA256,
                "accepted_binary_sha256":YENC_ACCEPTED_BINARY_SHA256,
                "build_origin":"linux-lf-prebuilt" if prebuilt_yenc else "local-source-build"
            }
        },
        "newzdeck_owned_binaries":mappings,
        "retired_legacy_binaries":["NewzDeckBootstrap.exe","NewzDeckCore.exe"],
        "application_source":[
            {"path":"src/app/server.py","sha256":sha(APP/'server.py')},
            {"path":"src/app/sab_engine.py","sha256":sha(APP/'sab_engine.py')},
            {"path":"src/app/automation_engine.py","sha256":sha(APP/'automation_engine.py')},
            {"path":"src/app/static/app.js","sha256":sha(APP/'static'/'app.js')},
            {"path":"src/app/static/index.html","sha256":sha(APP/'static'/'index.html')},
            {"path":"src/app/static/styles.css","sha256":sha(APP/'static'/'styles.css')},
            {"path":"src/app/static/tmdb-logo.svg","sha256":sha(APP/'static'/'tmdb-logo.svg')},
        ],
    }
    (stage/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+"\n",encoding='utf-8')

def deterministic_zip(stage: pathlib.Path, out: pathlib.Path):
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(stage.rglob('*'),key=lambda x:x.relative_to(stage).as_posix().lower()):
            if not p.is_file(): continue
            rel=p.relative_to(stage).as_posix()
            info=zipfile.ZipInfo(rel,FIXED_ZIP_TIME)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o644 & 0xFFFF)<<16
            z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--version',required=True);ap.add_argument('--output',required=True);ap.add_argument('--prebuilt-yenc')
    ns=ap.parse_args(); version=ns.version; prebuilt_yenc=pathlib.Path(ns.prebuilt_yenc).resolve() if ns.prebuilt_yenc else None
    validate_source(version)
    with tempfile.TemporaryDirectory(prefix='newzdeck-build-') as td:
        stage=pathlib.Path(td)/'payload';stage.mkdir()
        copy_app(stage);build_go(stage,prebuilt_yenc);write_manifest(stage,version,prebuilt_yenc)
        out=pathlib.Path(ns.output).resolve();deterministic_zip(stage,out)
        with zipfile.ZipFile(out) as z: bad=z.testzip(); names=set(z.namelist())
        if bad: raise SystemExit(f'ZIP CRC failure: {bad}')
        missing=[x for x in list(HELPERS)+['server.py','version.txt','LICENSE.txt','SOURCE_MANIFEST.json','static/tmdb-logo.svg'] if x not in names]
        if missing: raise SystemExit(f'missing payload entries: {missing}')
        forbidden={'NewzDeckBootstrap.exe','NewzDeckCore.exe','PORTABLE_TESTING.txt','start.sh'}
        present=sorted(forbidden & names)
        if present: raise SystemExit(f'production payload contains forbidden entries: {present}')
        print(f'Portable: {out}')
        print(f'SHA-256: {sha(out)}')

if __name__=='__main__': main()
