#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'src' / 'app'

def check(value, message):
    if not value: raise SystemExit(message)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

check((APP/'version.txt').read_text().strip() == '3.7.1', 'version.txt != 3.7.1')
server=(APP/'server.py').read_text(encoding='utf-8')
yenc=(APP/'yenc_decoder.py').read_text(encoding='utf-8')
ui=(APP/'static/app.js').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
builder=(ROOT/'release/windows/build-portable.py').read_text(encoding='utf-8')
build_release=(ROOT/'release/windows/build-release.ps1').read_text(encoding='utf-8')
workflow=(ROOT/'.github/workflows/publish-release-trigger.yml').read_text(encoding='utf-8')
sab_engine=(APP/'sab_engine.py').read_text(encoding='utf-8')

check('APP_VERSION = "3.7.0"' in server, 'frozen server baseline identity changed')
check("const UI_VERSION = '3.7.0';" in ui, 'frozen app.js baseline identity changed')
check(sha(APP/'server.py') == 'c6a77e46e4abeafe8c460944828d69efc9c49c3e33aafeb7819e04a9fc697990', 'server.py v3.7.0 baseline changed')
check(sha(APP/'static/app.js') == '3df087fa5aca176db8c84e6f3a9e962600114b1bb9e83470131365ae1d64fc94', 'app.js v3.7.0 baseline changed')
check(manifest.get('version') == '3.7.1' and manifest.get('base_version') == '3.7.0', 'manifest lineage mismatch')
check(manifest.get('sabctools_version') == '9.6.3', 'manifest SABCTools version mismatch')
check(manifest.get('sabctools_upstream_commit') == '54d7663b9e8f527b5ab196d43f0d5c561a87c1ac', 'manifest SABCTools commit mismatch')
check('EXPECTED_SABCTOOLS_VERSION = "9.6.3"' in yenc, 'decoder exact SABCTools pin missing')
check('SabctoolsDecoder' in yenc and 'build_synthetic_nntp_response' in yenc, 'decoder adapter missing')
transform=(ROOT/'release/windows/apply-v371-runtime.py').read_text(encoding='utf-8')
check('GENERATED_SERVER_SHA256 = "f49793f2a65554a6fe4e8e4a4f823d15b6e47ac338dcd8a73ed40815f72f9061"' in transform, 'generated server pin missing')
check('GENERATED_APP_JS_SHA256 = "7ffda814018feae44da79af862af4e2b1b1f45d9b19e466bfe9c08fdbfc90f6a"' in transform, 'generated UI pin missing')
check('NEWZDECK_YENC_DECODER", "sabctools"' in transform, 'SABCTools default transform missing')
check('DOWNLOAD_DECODE_EXECUTOR' in server and 'ThreadPoolExecutor' in server, 'split decode executor baseline missing')
check('"NewzDeckYenc.exe": "NewzDeckYenc.go"' not in builder, 'Portable builder still builds yEnc helper')
check('--sabctools-package' in builder and 'sabctools.cp312-win_amd64.pyd' in builder, 'Portable SABCTools packaging missing')
check('NewzDeckYenc.exe' in build_release and 'retiredYencDelete' in build_release, 'installed-upgrade yEnc cleanup missing')
check('SABCTOOLS_VERSION: \'9.6.3\'' in workflow, 'workflow SABCTools version pin missing')
check('54d7663b9e8f527b5ab196d43f0d5c561a87c1ac' in workflow, 'workflow SABCTools commit pin missing')
check('yenc-helper:' not in workflow and 'newzdeck-yenc-defender-lf' not in workflow, 'old yEnc helper job remains')
check('validate-sabctools-runtime.py' in workflow, 'exact SABCTools runtime gate missing')
check('SAB_VERSION = "5.1.2"' in sab_engine, 'private SABnzbd baseline changed')
check(sha(APP/'static/styles.css') == 'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d', 'styles.css changed')
check(sha(APP/'static/themes.css') == '2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721', 'themes.css changed')
check((ROOT/'release/RELEASE_NOTES_v3.7.1.md').is_file(), 'v3.7.1 release notes missing')
print('validate-v3710-regressions.py: PASS')
