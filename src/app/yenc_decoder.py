"""NewzDeck v3.7.1 in-process yEnc decoder powered by SABCTools 9.6.3.

The Windows release vendors the exact CPython 3.12 SABCTools package beside
server.py. The standalone NewzDeckYenc.exe helper is retired from the shipped
payload; server.py retains a bulk-Python emergency fallback.
"""
from __future__ import annotations

import io
import importlib.util
import os
import sys
import threading
import time
import zlib
from pathlib import Path
from dataclasses import dataclass
from typing import Any

EXPECTED_SABCTOOLS_VERSION = "9.6.3"
DEFAULT_BUFFER_SIZE = 1024 * 1024
_DLL_DIRECTORY_HANDLES = []


class SabctoolsUnavailable(RuntimeError):
    pass


class SabctoolsDecodeError(RuntimeError):
    pass


def _candidate_sabctools_extensions() -> list[Path]:
    candidates: list[Path] = []
    explicit = os.environ.get("NEWZDECK_SABCTOOLS_PYD", "").strip()
    if explicit:
        candidates.append(Path(explicit).expanduser())
    app_dir = Path(__file__).resolve().parent
    package_dir = app_dir / "sabctools"
    if package_dir.is_dir():
        candidates.extend(sorted(package_dir.glob("sabctools*.pyd")))
    seen: set[str] = set()
    out: list[Path] = []
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        key = str(resolved).casefold()
        if key not in seen and candidate.is_file():
            seen.add(key)
            out.append(candidate)
    return out

def _load_sabctools_extension(candidate: Path):
    """Load the *package* that owns a SABCTools native extension.

    Wheels lay out SABCTools as::

        sabctools/__init__.py
        sabctools/sabctools.cp312-win_amd64.pyd

    The version/public API is created by ``__init__.py``; the raw .pyd is the
    ``sabctools.sabctools`` submodule and does not itself expose ``__version__``.
    Loading the .pyd directly as ``sabctools`` therefore produces an incomplete
    module.  Load the package wrapper from the exact wheel directory instead so
    its normal relative import resolves the native extension correctly.
    """
    global _DLL_DIRECTORY_HANDLES
    candidate = candidate.resolve()
    package_dir = candidate.parent
    package_init = package_dir / "__init__.py"
    if not package_init.is_file():
        raise ImportError(f"SABCTools package wrapper not found next to extension: {package_init}")

    # Keep DLL search handles alive for the lifetime of the extension module.
    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        for directory in (package_dir, package_dir.parent):
            try:
                handle = os.add_dll_directory(str(directory))
            except (FileNotFoundError, OSError):
                continue
            _DLL_DIRECTORY_HANDLES.append(handle)

    # Clear a failed/partial prior attempt before importing this exact package.
    for name in [key for key in tuple(sys.modules) if key == "sabctools" or key.startswith("sabctools.")]:
        sys.modules.pop(name, None)

    spec = importlib.util.spec_from_file_location(
        "sabctools",
        package_init,
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create package spec for {package_init}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["sabctools"] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        for name in [key for key in tuple(sys.modules) if key == "sabctools" or key.startswith("sabctools.")]:
            sys.modules.pop(name, None)
        raise
    return module

def _import_sabctools():
    normal_error = None
    try:
        import sabctools  # type: ignore
    except Exception as exc:
        normal_error = exc
        sabctools = None
    if sabctools is None:
        extension_errors = []
        for candidate in _candidate_sabctools_extensions():
            try:
                sabctools = _load_sabctools_extension(candidate)
                break
            except Exception as exc:
                extension_errors.append(f"{candidate}: {exc}")
        if sabctools is None:
            detail = f"normal import: {normal_error}" if normal_error else "normal import unavailable"
            if extension_errors:
                detail += "; private SAB candidates: " + " | ".join(extension_errors)
            raise SabctoolsUnavailable(f"SABCTools import failed ({detail})")
    version = str(getattr(sabctools, "__version__", "") or "")
    if version != EXPECTED_SABCTOOLS_VERSION:
        raise SabctoolsUnavailable(
            f"SABCTools {version!r} is not the exact {EXPECTED_SABCTOOLS_VERSION} build required by NewzDeck 3.7.1"
        )
    return sabctools


def sabctools_info() -> dict[str, Any]:
    try:
        sabctools = _import_sabctools()
    except SabctoolsUnavailable as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": True,
        "version": str(getattr(sabctools, "__version__", "")),
        "simd": str(getattr(sabctools, "simd", "") or ""),
        "openssl_linked": bool(getattr(sabctools, "openssl_linked", False)),
    }


def _normalize_control(line: bytes) -> bytes:
    return bytes(line).rstrip(b"\r\n")


def _restuff_yenc_payload(encoded: bytes) -> bytes:
    """Restore NNTP dot-stuffing while canonicalizing physical lines to CRLF.

    NewzDeck's body_raw() deliberately removes NNTP dot-stuffing before returning
    the BODY payload. SABCTools normally receives wire-format NNTP data, so this
    adapter reconstructs the escaping at the decoder boundary. The adapter deliberately reconstructs the minimal wire framing at the existing
    decode boundary so the proven NNTP fetch pipeline remains unchanged.
    """
    lines = encoded.splitlines()
    stuffed = []
    for line in lines:
        if line.startswith(b"."):
            line = b"." + line
        stuffed.append(line)
    return b"\r\n".join(stuffed)


def build_synthetic_nntp_response(
    begin_line: bytes,
    part_line: bytes | None,
    encoded: bytes,
    end_line: bytes,
) -> bytes:
    chunks = [b"222 0 <newzdeck-decoder@local>", _normalize_control(begin_line)]
    if part_line:
        chunks.append(_normalize_control(part_line))
    payload = _restuff_yenc_payload(encoded)
    if payload:
        chunks.append(payload)
    chunks.append(_normalize_control(end_line))
    chunks.append(b".")
    return b"\r\n".join(chunks) + b"\r\n"


@dataclass(frozen=True)
class DecodeResult:
    data: bytes
    crc32: int
    seconds: float
    backend: str
    details: dict[str, Any]


class SabctoolsDecoder:
    """Thread-safe factory for independent SABCTools Decoder instances.

    Each decode call owns its Decoder. The native C/C++ yEnc transform releases
    the GIL, so NewzDeck's existing ThreadPoolExecutor can execute multiple calls
    concurrently without requiring persistent helper subprocesses.
    """

    def __init__(self, *, buffer_size: int = DEFAULT_BUFFER_SIZE):
        self.buffer_size = max(64 * 1024, int(buffer_size))
        self._lock = threading.Lock()
        self._bytes = 0
        self._seconds = 0.0
        self._failures = 0

    def decode(
        self,
        begin_line: bytes,
        part_line: bytes | None,
        encoded: bytes,
        end_line: bytes,
    ) -> DecodeResult:
        sabctools = _import_sabctools()
        frame = build_synthetic_nntp_response(begin_line, part_line, encoded, end_line)
        started = time.perf_counter()
        try:
            # A bounded reusable native buffer avoids allocating one native decoder
            # buffer as large as the entire article. The bounded buffer keeps allocations controlled while preserving the existing split fetch/decode pipeline.
            decoder = sabctools.Decoder(min(max(self.buffer_size, 64 * 1024), max(len(frame), 64 * 1024)))
            stream = io.BytesIO(frame)
            response = None
            while True:
                count = stream.readinto(decoder)
                if not count:
                    break
                decoder.process(count)
                if decoder:
                    for item in decoder:
                        response = item
            if response is None:
                raise SabctoolsDecodeError("SABCTools did not emit an NNTP response")
            fmt = getattr(response, "format", None)
            yenc_enum = getattr(getattr(sabctools, "EncodingFormat", object), "YENC", None)
            if yenc_enum is not None and fmt != yenc_enum:
                raise SabctoolsDecodeError(f"SABCTools did not identify the response as yEnc (format={fmt!r})")
            raw_data = getattr(response, "data", None)
            if raw_data is None:
                raise SabctoolsDecodeError("SABCTools returned no decoded payload")
            data = bytes(raw_data)
            if not data:
                raise SabctoolsDecodeError("SABCTools decoded an empty payload")
            crc = zlib.crc32(data) & 0xFFFFFFFF
            elapsed = time.perf_counter() - started
            with self._lock:
                self._bytes += len(data)
                self._seconds += elapsed
            return DecodeResult(
                data=data,
                crc32=crc,
                seconds=elapsed,
                backend="sabctools",
                details={
                    "sabctools_version": str(getattr(sabctools, "__version__", "")),
                    "simd": str(getattr(sabctools, "simd", "") or ""),
                    "response_crc": getattr(response, "crc", None),
                    "response_crc_expected": getattr(response, "crc_expected", None),
                    "bytes_decoded": int(getattr(response, "bytes_decoded", len(data)) or len(data)),
                },
            )
        except Exception:
            with self._lock:
                self._failures += 1
            raise

    def stats(self) -> dict[str, Any]:
        info = sabctools_info()
        with self._lock:
            rate = int(self._bytes / self._seconds) if self._seconds > 0 else 0
            return {
                **info,
                "backend": "sabctools",
                "decoded_bytes": self._bytes,
                "decode_seconds": self._seconds,
                "rate_bps": rate,
                "failures": self._failures,
            }
