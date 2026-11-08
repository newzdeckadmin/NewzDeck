#!/usr/bin/env python3
"""Production overview parser selective fast-path vs complete parsing."""
from __future__ import annotations
import ast, email.header, pathlib, re
from typing import Any, Iterable
root=pathlib.Path(__file__).resolve().parents[2]
src=(root/'src/app/server.py').read_text(encoding='utf-8');tree=ast.parse(src)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parse_overview')
counters={'media':0, 'multipart':0}
def decode(value):
    chunks=email.header.decode_header(value)
    return ''.join(c.decode(enc or 'utf-8',errors='replace') if isinstance(c,bytes) else c for c,enc in chunks)
def detect(subject):
    counters['media']+=1
    name=subject.split()[-1] if '.' in subject else ''
    return {'filename':name, 'extension':name.split('.')[-1] if name else '',
            'kind':'image' if name.endswith('.png') else 'file'} if name else None
def multipart(subject):
    counters['multipart']+=1
    return None
namespace={'re':re,'decode_header_value':decode,'detect_media':detect,'multipart_info':multipart,'Any':Any,'Iterable':Iterable}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(root/'src/app/server.py'),'exec'),namespace)
parse=namespace['parse_overview']
lines=[]
def make(n,subj,poster,bytes_count):
    return f'{n}\t{subj}\t{poster}\tSat, 07 Nov 2026 12:00:00 GMT\t<id{n}@nntp.test>\t\t{bytes_count}\t150'.encode()
lines.extend([
 make(1,'MyHolidayPhoto.png','Alice',2050000),
 make(2,'SomeRandomName.png','Bob',250000),
 make(3,'=?UTF-8?B?Q2Fmw6kgUGhvdG8ucG5n?=','Cyril',1750000),
 make(4,'JustAnObfuscatedBinary','Alice',775000),
 make(5,'Archive.zip','Alice',6000000),
 make(6,'Video.mp4','Bob',8000000),
])
all_articles=parse(lines);assert len(all_articles)==6
for criteria in [
 {'query':'photo'},
 {'query':'CAFÉ'},
 {'query':'<id4@nntp.test>'},
 {'poster':'alice'},
 {'min_bytes':1500000},
 {'max_bytes':800000},
 {'query':'photo','poster':'cyril','min_bytes':1000000,'max_bytes':2000000},
 {'query':'nonexistent'},
 {}]:
 expected=[]
 for article in all_articles:
    q=criteria.get('query','').strip().casefold();p=criteria.get('poster','').strip().casefold()
    if q and q not in '\n'.join(str(v or '') for v in (article['subject'],article['from'],(article['media'] or {}).get('filename'),article['message_id'])).casefold():continue
    if p and p not in article['from'].casefold():continue
    if criteria.get('min_bytes',0) and article['bytes']<criteria['min_bytes']:continue
    if criteria.get('max_bytes',0) and article['bytes']>criteria['max_bytes']:continue
    expected.append(article['article'])
 counters.update(media=0,multipart=0)
 got=parse(lines,search_filter=criteria)
 assert [x['article'] for x in got]==expected,(criteria,got,expected)
 assert counters['media']==len(expected)==counters['multipart'],(criteria,counters)
print('PASS: selective parsing matches full search semantics, including RFC 2047 names and obfuscated posts')
