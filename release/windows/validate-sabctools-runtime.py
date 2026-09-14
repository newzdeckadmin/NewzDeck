#!/usr/bin/env python3
from __future__ import annotations
import argparse, io, sys, zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ESCAPE = {0, 9, 10, 13, 61}


def yenc_encode(data: bytes, line_length: int = 128) -> bytes:
    out = bytearray(); col = 0
    for value in data:
        encoded = (value + 42) & 0xff
        if encoded in ESCAPE:
            out.extend((61, (encoded + 64) & 0xff)); col += 2
        else:
            out.append(encoded); col += 1
        if col >= line_length:
            out.extend(b"\r\n"); col = 0
    if out.endswith(b"\r\n"):
        del out[-2:]
    return bytes(out)


def frame(data: bytes) -> bytes:
    crc = zlib.crc32(data) & 0xffffffff
    return b"\r\n".join([
        b"222 0 <newzdeck-v371@local>", b"",
        f"=ybegin part=1 total=1 line=128 size={len(data)} name=test.bin".encode(),
        f"=ypart begin=1 end={len(data)}".encode(),
        yenc_encode(data),
        f"=yend size={len(data)} pcrc32={crc:08x}".encode(), b".", b"",
    ])


def decode(sabctools, raw: bytes) -> bytes:
    dec = sabctools.Decoder(max(64 * 1024, min(1024 * 1024, len(raw))))
    stream = io.BytesIO(raw); response = None
    while True:
        n = stream.readinto(dec)
        if not n: break
        dec.process(n)
        if dec:
            for item in dec:
                response = item
    if response is None or response.data is None:
        raise RuntimeError("SABCTools emitted no decoded yEnc response")
    if response.format != sabctools.EncodingFormat.YENC:
        raise RuntimeError(f"unexpected format: {response.format!r}")
    if response.crc is None:
        raise RuntimeError(f"SABCTools CRC mismatch; expected {response.crc_expected!r}")
    return bytes(response.data)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--target', required=True)
    ns = ap.parse_args(); sys.path.insert(0, str(Path(ns.target).resolve()))
    import sabctools  # type: ignore
    if sys.version_info[:3] != (3, 12, 10):
        raise SystemExit(f"wrong Python: {sys.version}")
    if str(getattr(sabctools, '__version__', '')) != '9.6.3':
        raise SystemExit(f"wrong SABCTools: {getattr(sabctools, '__version__', None)!r}")
    print('Python:', sys.version)
    print('SABCTools:', sabctools.__version__)
    print('SIMD:', getattr(sabctools, 'simd', None))
    print('OpenSSL linked:', getattr(sabctools, 'openssl_linked', None))
    corpus = [
        bytes(range(256)) * 4,
        b"\x00\x09\x0a\x0d=" * 4096,
        bytes((i * 37 + 11) & 0xff for i in range(700 * 1024)),
    ]
    for payload in corpus:
        if decode(sabctools, frame(payload)) != payload:
            raise SystemExit('SABCTools correctness mismatch')
    raw = frame(corpus[-1])
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: decode(sabctools, raw), range(32)))
    if any(result != corpus[-1] for result in results):
        raise SystemExit('SABCTools concurrent correctness mismatch')
    print('SABCTools exact 9.6.3 CP312 yEnc/CRC/concurrency gate: PASS')
    return 0

if __name__ == '__main__': raise SystemExit(main())
