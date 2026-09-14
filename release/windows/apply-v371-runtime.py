#!/usr/bin/env python3
"""Deterministically transform the frozen v3.7.0 runtime into v3.7.1.

The repository keeps the proven v3.7.0 server/app.js blobs byte-for-byte and
ships this reviewed transformation as part of the source-complete v3.7.1 build.
The Portable builder applies it only after verifying the exact baseline hashes.
"""
from __future__ import annotations
import argparse, hashlib, tempfile
from pathlib import Path

BASE_SERVER_SHA256 = "c6a77e46e4abeafe8c460944828d69efc9c49c3e33aafeb7819e04a9fc697990"
BASE_APP_JS_SHA256 = "3df087fa5aca176db8c84e6f3a9e962600114b1bb9e83470131365ae1d64fc94"
GENERATED_SERVER_SHA256 = "f49793f2a65554a6fe4e8e4a4f823d15b6e47ac338dcd8a73ed40815f72f9061"
GENERATED_APP_JS_SHA256 = "7ffda814018feae44da79af862af4e2b1b1f45d9b19e466bfe9c08fdbfc90f6a"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)


def transform_server(text: str) -> str:
    text = replace_once(text, 'APP_VERSION = "3.7.0"', 'APP_VERSION = "3.7.1"', 'APP_VERSION')

    fallback_old = '''    The normal queued-download path uses NewzDeckYenc.exe so the byte-heavy
    transform does not contend on Python's GIL. This fallback preserves full
    compatibility if the native helper is unavailable.'''
    fallback_new = '''    v3.7.1 uses in-process SABCTools for the normal queued-download path. This
    bulk Python implementation remains as a compatibility/emergency fallback if
    the vendored native module cannot be loaded or rejects an article.'''
    text = replace_once(text, fallback_old, fallback_new, 'Python fallback doc')

    marker = 'class _NativeYencWorker:'
    network_marker = '# Network reads and yEnc decode intentionally use different executors. A queued\n'
    start = text.find(marker)
    end = text.find(network_marker, start)
    if start < 0 or end < 0:
        raise RuntimeError('native yEnc worker section markers are missing')

    module_block = '''# NewzDeck v3.7.1 in-process SABCTools decoder. The standalone NewzDeckYenc.exe
# helper is no longer shipped; pure Python remains the emergency fallback.
_YENC_DECODER_MODULE = None
try:
    _yenc_module_path = APP_DIR / "yenc_decoder.py"
    if _yenc_module_path.is_file():
        _YENC_DECODER_MODULE = _load_app_source_module("newzdeck_yenc_decoder", _yenc_module_path)
except Exception as _yenc_module_exc:
    safe_print(f"NewzDeck SABCTools decoder module unavailable: {_yenc_module_exc}")

_SABCTOOLS_YENC_DECODER = None
_SABCTOOLS_YENC_ERROR = ""

def _requested_yenc_decoder() -> str:
    # v3.7.1 defaults to the vendored in-process SABCTools decoder. ``python``
    # remains available as an explicit diagnostic/emergency fallback.
    requested = os.environ.get("NEWZDECK_YENC_DECODER", "sabctools").strip().casefold()
    return requested if requested in {"sabctools", "auto", "python"} else "sabctools"

def _sabctools_yenc_decoder():
    global _SABCTOOLS_YENC_DECODER, _SABCTOOLS_YENC_ERROR
    if _SABCTOOLS_YENC_DECODER is not None:
        return _SABCTOOLS_YENC_DECODER
    if _YENC_DECODER_MODULE is None:
        _SABCTOOLS_YENC_ERROR = "decoder module is unavailable"
        return None
    info = _YENC_DECODER_MODULE.sabctools_info()
    if not info.get("available"):
        _SABCTOOLS_YENC_ERROR = str(info.get("error") or "SABCTools is unavailable")
        return None
    try:
        _SABCTOOLS_YENC_DECODER = _YENC_DECODER_MODULE.SabctoolsDecoder()
        _SABCTOOLS_YENC_ERROR = ""
    except Exception as exc:
        _SABCTOOLS_YENC_ERROR = str(exc)
        return None
    return _SABCTOOLS_YENC_DECODER

def _active_yenc_pipeline_label() -> str:
    if _requested_yenc_decoder() == "python":
        return "bulk-python-yenc"
    return "sabctools-yenc" if _sabctools_yenc_decoder() is not None else "bulk-python-yenc"

'''
    text = text[:start] + module_block + text[end:]

    # Preserve the existing parser/validation logic and change only the yEnc
    # backend call at the established decode boundary.
    text = replace_once(text,
'''        if raw.startswith(b"=ypart", pos):
            part_eol = raw.find(b"\\n", pos)
            if part_eol < 0:
                raise NntpError("Malformed yEnc =ypart header")
            _parse_yenc_part(raw[pos:part_eol].rstrip(b"\\r"), meta)
            pos = part_eol + 1''',
'''        part_line = None
        if raw.startswith(b"=ypart", pos):
            part_eol = raw.find(b"\\n", pos)
            if part_eol < 0:
                raise NntpError("Malformed yEnc =ypart header")
            part_line = raw[pos:part_eol].rstrip(b"\\r")
            _parse_yenc_part(part_line, meta)
            pos = part_eol + 1''', 'ypart capture')

    text = replace_once(text,
'''        encoded = raw[pos:data_end]
        _parse_yenc_end(raw[yend_start:yend_eol].rstrip(b"\\r"), meta)
        data, crc_value, native, decode_seconds = NATIVE_YENC_POOL.decode(encoded)''',
'''        encoded = raw[pos:data_end]
        end_line = raw[yend_start:yend_eol].rstrip(b"\\r")
        _parse_yenc_end(end_line, meta)
        requested_decoder = _requested_yenc_decoder()
        decoder_backend = "sabctools"
        decoder_fallback_error = ""
        if requested_decoder == "python":
            decode_started = time.perf_counter()
            data, crc_value = _decode_yenc_blob_python(encoded)
            decode_seconds = time.perf_counter() - decode_started
            native = False
            decoder_backend = "python"
        elif requested_decoder in {"sabctools", "auto"} and (sab_decoder := _sabctools_yenc_decoder()) is not None:
            try:
                sab_result = sab_decoder.decode(begin_line, part_line, encoded, end_line)
                data = sab_result.data
                crc_value = sab_result.crc32
                decode_seconds = sab_result.seconds
                native = True
                decoder_backend = "sabctools"
            except Exception as exc:
                decoder_fallback_error = str(exc)[:500]
                decode_started = time.perf_counter()
                data, crc_value = _decode_yenc_blob_python(encoded)
                decode_seconds = time.perf_counter() - decode_started
                native = False
                decoder_backend = "python-fallback"
        else:
            if _SABCTOOLS_YENC_ERROR:
                decoder_fallback_error = _SABCTOOLS_YENC_ERROR[:500]
            decode_started = time.perf_counter()
            data, crc_value = _decode_yenc_blob_python(encoded)
            decode_seconds = time.perf_counter() - decode_started
            native = False
            decoder_backend = "python-fallback"''', 'decoder backend')

    text = replace_once(text,
'''        return data, meta, {"decode_seconds": decode_seconds, "native_decode": native, "crc32": crc_value}''',
'''        return data, meta, {
            "decode_seconds": decode_seconds,
            "native_decode": native,
            "decoder_backend": decoder_backend,
            "decoder_fallback_error": decoder_fallback_error,
            "crc32": crc_value,
        }''', 'decoder telemetry')

    old_label = '"native-yenc" if NATIVE_YENC_POOL.stats().get("available") else "bulk-python-yenc"'
    text = text.replace(old_label, '_active_yenc_pipeline_label()')

    text = replace_once(text,
'''def download_pool_stats() -> dict[str, Any]:
    yenc = NATIVE_YENC_POOL.stats()''',
'''def download_pool_stats() -> dict[str, Any]:
    decoder = _sabctools_yenc_decoder()
    if decoder is not None:
        yenc = decoder.stats()
    else:
        yenc = {"available": False, "backend": "python-fallback", "error": _SABCTOOLS_YENC_ERROR}''', 'download pool decoder stats')

    if 'NATIVE_YENC_POOL' in text or 'class _NativeYencWorker' in text:
        raise RuntimeError('retired native helper references remain in generated server')
    return text


def transform_app_js(text: str) -> str:
    return replace_once(text, "const UI_VERSION = '3.7.0';", "const UI_VERSION = '3.7.1';", 'UI_VERSION')


def apply(server_path: Path, app_js_path: Path) -> None:
    if sha(server_path) != BASE_SERVER_SHA256:
        raise RuntimeError(f'server.py baseline SHA-256 mismatch: {sha(server_path)}')
    if sha(app_js_path) != BASE_APP_JS_SHA256:
        raise RuntimeError(f'app.js baseline SHA-256 mismatch: {sha(app_js_path)}')
    server_path.write_text(transform_server(server_path.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
    app_js_path.write_text(transform_app_js(app_js_path.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
    if sha(server_path) != GENERATED_SERVER_SHA256:
        raise RuntimeError(f'generated server.py SHA-256 mismatch: {sha(server_path)}')
    if sha(app_js_path) != GENERATED_APP_JS_SHA256:
        raise RuntimeError(f'generated app.js SHA-256 mismatch: {sha(app_js_path)}')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--server')
    ap.add_argument('--app-js')
    ap.add_argument('--self-test', action='store_true')
    ns = ap.parse_args()
    if ns.self_test:
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix='newzdeck-v371-transform-') as td:
            td = Path(td)
            server = td / 'server.py'; app_js = td / 'app.js'
            server.write_bytes((root/'src/app/server.py').read_bytes())
            app_js.write_bytes((root/'src/app/static/app.js').read_bytes())
            apply(server, app_js)
            compile(server.read_bytes(), str(server), 'exec')
        print('apply-v371-runtime.py self-test: PASS')
        return 0
    if not ns.server or not ns.app_js:
        ap.error('--server and --app-js are required unless --self-test is used')
    apply(Path(ns.server), Path(ns.app_js))
    return 0

if __name__ == '__main__': raise SystemExit(main())
