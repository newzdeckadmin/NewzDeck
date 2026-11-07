#!/usr/bin/env python3
"""NewzDeck v3.7.24 regression: exercise the real NNTP yEnc prefix reader.

No network, no running NewzDeck, no application-data writes. Loads only the
relevant functions/method from server.py via its Python AST.
"""
from __future__ import annotations
import ast
import re
import sys
from pathlib import Path
from typing import Any

class NntpError(Exception):
    pass

def encode_yenc(data: bytes) -> bytes:
    out = bytearray()
    for byte in data:
        coded = (byte + 42) & 0xff
        if coded in (0, 10, 13, 61):
            out.extend((61, (coded + 64) & 0xff))
        else:
            out.append(coded)
    return bytes(out)

def load_reader(server_path: Path):
    tree = ast.parse(server_path.read_text(encoding='utf-8'), filename=str(server_path))
    funcs = {'_control_view', '_parse_yenc_begin', '_parse_yenc_part', '_parse_yenc_end', '_decode_yenc_data_line'}
    needed = []
    yenc_table = None
    method = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in funcs:
            needed.append(node)
        elif isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id=='_YENC_DECODE_TABLE' for target in node.targets):
                yenc_table = node
        elif isinstance(node, ast.ClassDef) and node.name == 'NntpClient':
            method = next((x for x in node.body if isinstance(x, ast.FunctionDef) and x.name == 'body_yenc_decoded_prefix'), None)
    assert len(needed) == len(funcs), f'Missing helper(s): {funcs - {n.name for n in needed}}'
    assert method and yenc_table, 'Could not locate yEnc reader/table'
    # Exercise the ORIGINAL method with only network I/O replaced by deterministic test input.
    fixture_class = ast.ClassDef(name='PrefixClient', bases=[], keywords=[], body=[method], decorator_list=[])
    module = ast.Module(body=[yenc_table, *needed, fixture_class], type_ignores=[])
    namespace = {
        'Any': Any, 're': re, 'NntpError': NntpError,
        'NAME_RESOLUTION_ARCHIVE_PROBE_BYTES': 65536,
        'NAME_RESOLUTION_ARCHIVE_WIRE_MAX_BYTES': 131072,
    }
    exec(compile(ast.fix_missing_locations(module), str(server_path), 'exec'), namespace)
    cls = namespace['PrefixClient']
    def init(self, lines, status=222):
        self.lines = iter(lines)
        self.status = status
        self.commands = []
    def send(self, cmd): self.commands.append(cmd)
    def read_status(self): return self.status, 'test status'
    def readline(self): return next(self.lines)
    cls.__init__ = init
    cls._send = send
    cls._read_status = read_status
    cls._readline = readline
    return cls

def run(server_path: Path):
    C = load_reader(server_path)
    content = b'\xff\xd8\xff\x00\x0a\r=\x7e'
    encoded = encode_yenc(content)
    common = [b'=ybegin part=3 total=12 line=128 size=8400000 name=obscured.jpg',
              b'=ypart begin=1500001 end=1500008', encoded,
              b'=yend size=8 part=3 pcrc32=12345678', b'.']
    # This was a NameError on published v3.7.23.
    c = C(common)
    data, meta = c.body_yenc_decoded_prefix(880, max_decoded=16384, max_wire=98304)
    assert data == content, (data, content)
    assert c.commands == ['BODY 880']
    assert (meta['part'],meta['total'],meta['size']) == (3,12,8400000)
    assert (meta['begin'],meta['end']) == (1500001,1500008)
    assert meta['yenc_found'] is True
    assert (meta['end_size'],meta['end_part'],meta['pcrc32']) == (8,3,'12345678')
    # Complete single-file yEnc article with no =ypart must still work.
    c = C([b'=ybegin line=128 size=8 name=whole.jpg', encoded, b'=yend size=8', b'.'])
    data, meta = c.body_yenc_decoded_prefix('<sample@usenet.invalid>', max_decoded=16384, max_wire=98304)
    assert data == content and meta['yenc_found'] and meta['name'] == 'whole.jpg'
    assert 'begin' not in meta and 'end' not in meta
    # Multipart offset >1 with data that doesn't contain a recognizable file header.
    c = C([b'=ybegin part=9 total=20 line=128 size=14000000 name=random',
           b'=ypart begin=6000001 end=6000008', encoded, b'.'])
    data, meta = c.body_yenc_decoded_prefix(882, max_decoded=16384, max_wire=98304)
    assert data == content and (meta['part'],meta['total'],meta['begin']) == (9,20,6000001)
    # Existing handling of unsuccessful BODY status should remain intact.
    c = C([], status=430)
    try:
        c.body_yenc_decoded_prefix(999)
    except NntpError as exc:
        assert '430' in str(exc)
    else:
        raise AssertionError('Missing BODY status check')
    print('PASS: actual NNTP yEnc prefix parser (multipart, single, escape bytes, missing yend, error status)')

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else root/'src/app/server.py'
    run(path)
