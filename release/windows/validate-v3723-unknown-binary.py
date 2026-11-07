#!/usr/bin/env python3
"""v3.7.23 bounded unknown article recognition and safe .part export tests.

Runs without a provider, app startup, downloading, disk-library modifications or Windows.
"""
import ast
import hashlib
import io
import mimetypes
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any
import json
import zlib

SRC = Path(__file__).resolve().parents[2] / 'src/app/server.py'
root = ast.parse(SRC.read_text(encoding='utf-8'))
needed = {'_unknown_target', '_unknown_magic', '_unknown_classify', 'inspect_unknown_article',
          '_UnknownLimitedClient', '_UnknownLimitedBuffer', 'save_unknown_fragment',
          '_generated_unresolved_media', '_clean_yenc_source_name', '_resolution_filename_media'}
nodes = [node for node in root.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in needed]
assert {n.name for n in nodes} == needed

class FakeNntp:
    prefix = (b'\xff\xd8\xff' + b'JFIF' + b'img', {'yenc_found': True, 'size': 10})
    calls = []
    def __init__(self, *args, **kwargs):
        self.calls.append(('open', args[0]))
    def connect(self): pass
    def group(self, name): self.calls.append(('group', name))
    def abort(self): pass
    def close(self): pass
    def body_yenc_decoded_prefix(self, target, *, max_decoded, max_wire):
        assert max_decoded <= 16384 and max_wire <= 98304
        self.calls.append(('probe', target))
        return self.prefix
    def body_iter(self, article):
        for line in (b'=ybegin size=4 name=opaque', b'__', b'=yend size=4'):
            yield line

namespace = {
    '__name__': 'newzdeck_v3723_test', 'Any': Any, 'Path': Path, 're': re, 'json': json,
    'hashlib': hashlib, 'mimetypes': mimetypes, 'time': time, 'io': io, 'os': os, 'zlib': zlib,
    'NntpClient': FakeNntp, 'UNKNOWN_FRAGMENT_MAX': 4*1024*1024,
    'provider_by_id': lambda provider: {'id': provider, 'host': 'offline.invalid', 'port': 119,
                                       'ssl': False, 'username': '', 'password_protected': ''},
    'unprotect_secret': lambda secret: secret, 'NAME_RESOLUTION_SOCKET_TIMEOUT': 2,
    '_store_name_resolution_entries': lambda entries: namespace.setdefault('_entries', []).extend(entries),
    '_name_resolution_cache_key': lambda provider, group, article: provider+'|'+group+'|'+str(article['message_id']),
    'safe_download_name': lambda value: value,
}
code = compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(SRC), 'exec')
exec(code, namespace)

magic = namespace['_unknown_magic']
assert magic(b'\xff\xd8\xff\xe0' + b'\0'*10)['extension'] == 'jpg'
assert magic(b'\x89PNG\r\n\x1a\n' + b'\0'*10)['kind'] == 'image'
assert magic(b'GIF89a' + b'\0'*10)['extension'] == 'gif'
assert magic(b'RIFF'+b'\0'*4+b'WEBP' + b'\0'*5)['extension'] == 'webp'
assert magic(b'\0\0\0\x18ftypisom' + b'\0'*10)['kind'] == 'video'
assert magic(b'\0\0\0\x18ftypavif' + b'\0'*10)['kind'] == 'image'
assert magic(b'PK\x03\x04' + b'\0'*10)['extension'] == 'zip'
assert magic(b'MZ' + b'\0'*10)['extension'] == 'exe'
assert magic(b'\xaa\xbb\xcc') is None

status = namespace['_unknown_classify']
article = {'article': 128, 'message_id': 'a@offline.invalid', 'subject': '46c9abc908d3', 'bytes': 775000,
           'segments': [{'article':128, 'message_id':'a@offline.invalid', 'part':1, 'bytes':775000}],
           'segment_count':1, 'segment_total':1, 'complete':True}
assert status({'yenc_found':True, 'size':775000}, article)['can_queue']
assert status({'yenc_found':True, 'size':5000000, 'begin':1, 'end':775000}, article)['status'] == 'fragment'
assert not status({'yenc_found':True, 'part':7, 'total':12}, article)['can_queue']
assert status({'yenc_found':False}, article)['status'] == 'unknown_encoding'
assert not status({'yenc_found':True}, {**article, 'segment_total':12})['can_queue']
assert not status({'yenc_found':True}, {**article, 'multipart_fragment':True})['can_queue']

inspect = namespace['inspect_unknown_article']
FakeNntp.prefix = (b'\xff\xd8\xff'+b'JFIF', {'yenc_found':True, 'size':775000})
result = inspect('example', 'alt.binaries.example', article)
assert result['can_queue'] and result['signature']['kind'] == 'image' and result['media']['filename'].endswith('.jpg')
assert result['media']['generated_name']
assert len(namespace.get('_entries', [])) == 1
assert FakeNntp.calls[-1] == ('probe', 128)
FakeNntp.prefix = (b'\0'*8, {'yenc_found':True, 'part':4, 'total':33, 'size':23000000})
fragment = inspect('example', 'alt.binaries.example', article)
assert fragment['status'] == 'fragment' and not fragment['can_queue'] and fragment['can_save_fragment']
assert len(namespace['_entries']) == 1, 'Do not cache a type for a middle part'
FakeNntp.prefix = (b'MZ' + b'\0'*8, {'yenc_found':True, 'size':775000})
exe = inspect('example', 'alt.binaries.example', article)
assert exe['media'] is None, 'Never classify an executable as previewable media'
FakeNntp.prefix = (b'\xff\xd8\xff', {'yenc_found':False})
assert inspect('example', 'alt.binaries.example', article)['status'] == 'unknown_encoding'
FakeNntp.prefix = (b'', {'yenc_found':True, 'size':775000})
assert not inspect('example', 'alt.binaries.example', article)['can_queue'], 'Header-only article falsely queueable'
for invalid in ({'article':'0'}, {'article':'12\r\nGROUP evil'}, {'message_id':'a@b\r\nquit'}, {'message_id':'<unclosed'}):
    try: namespace['_unknown_target'](invalid)
    except ValueError: pass
    else: raise AssertionError('Rejected unsafe article reference: '+repr(invalid))

# Explicit fragment export is content-bound, CRC checked, collision safe, and
# writes no existing file. Reconstruct a 4-byte decoded article using a fake
# decoder - the real parser is covered by the prior yEnc regression suite.
content = b'\xff\xd8\xff\x01'
def decode_fake(client, segment, stage, **kwargs):
    assert kwargs['apply_part_offset'] is False
    stage.write(content)
    return len(content), {'encoding':'yenc','saw_end':True,'pcrc32':f'{zlib.crc32(content)&0xffffffff:08x}'}
namespace['retrieve_segment_into_file'] = decode_fake
with tempfile.TemporaryDirectory(prefix='newzdeck-v3723-test-') as td:
    namespace['DOWNLOAD_DIR'] = Path(td)
    save = namespace['save_unknown_fragment']
    first = save('example','alt.binaries.example',article)
    second = save('example','alt.binaries.example',article)
    assert first['filename'].endswith('.part') and second['filename'].endswith(' (2).part')
    assert Path(first['path']).read_bytes() == content
    assert Path(second['path']).read_bytes() == content
    assert first['signature']['kind']=='image'
    bad = lambda *a,**kw:(len(content), {'encoding':'yenc','saw_end':True,'pcrc32':'00000000'})
    namespace['retrieve_segment_into_file'] = lambda client,seg,stage,**kw: (stage.write(content), bad()[1])
    old_files = {p.name for p in Path(td).rglob('*.part')}
    try: save('example','alt.binaries.example',article)
    except ValueError as exc: assert 'CRC32' in str(exc)
    else: raise AssertionError('CRC mismatch accepted')
    assert {p.name for p in Path(td).rglob('*.part')} == old_files
    try: save('example','alt.binaries.example',{**article,'bytes':9*1024*1024})
    except ValueError: pass
    else: raise AssertionError('Oversized article accepted')
    limited = namespace['_UnknownLimitedBuffer']()
    try: limited.write(b'\0'*(4*1024*1024+1))
    except ValueError: pass
    else: raise AssertionError('Oversize decoded article accepted')
print('validate-v3723-unknown-binary.py: PASS (signatures, no size guessing, multipart safety, opt-in probes, bounded export, collisions, CRC)')
