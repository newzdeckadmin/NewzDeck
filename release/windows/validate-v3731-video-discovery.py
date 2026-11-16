#!/usr/bin/env python3
"""Production-function v3.7.31 video discovery regression suite: offline fake NNTP.

Checks real subject/yEnc filename classifiers, multipart regrouping across NNTP
windows, bounded read-only OVER scanning, deterministic paging and generation lock.
No NNTP, downloads, filesystem libraries or NewzDeck startup side effects.
"""
from __future__ import annotations
import ast, email.utils, hashlib, mimetypes, re, secrets, threading, time
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from collections import defaultdict
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/'src/app/server.py').read_text('utf-8')
tree=ast.parse(source)
media_block=source[source.index('MEDIA_RE = re.compile('):source.index('def _smart_binary_expansion_headers(')]
ctx={'__builtins__':__builtins__,'re':re,'Path':Path,'mimetypes':mimetypes,'email':email,'Any':Any,'time':time,'datetime':datetime}
exec(compile(media_block,'production-media-classifier','exec'),ctx)
needed=['_clean_yenc_source_name','_resolution_filename_media','_merge_overview_headers','_video_discovery_complete_count','_finish_progressive_video_page']
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in needed]
assert sorted(n.name for n in selected)==sorted(needed)
mod=ast.Module(body=selected,type_ignores=[])
exec(compile(ast.fix_missing_locations(mod),'production-video-functions','exec'),ctx)

# Real media classifiers, and no artificial archive -> video reinterpretation.
for ext in ('mp4','mkv','avi','webm','mov','m4v','mpg','mpeg','wmv','ts','m2ts','mts','flv','3gp','vob'):
    item=ctx['detect_media'](f'"NICE clip.{ext}" yEnc (1/1)')
    assert item and item['kind']=='video' and item['extension']==ext,(ext,item)
    resolved=ctx['_resolution_filename_media']('clips/sample.'+ext)
    assert resolved and resolved['kind']=='video',(ext,resolved)
    assert resolved['mime'].startswith('video/'),resolved
for ext in ('jpg','png','rar','zip','par2','exe','flac'):
    a=ctx['detect_media']('"movie.'+ext+'" yEnc (1/1)')
    assert a is None or a['kind']!='video',(ext,a)
assert ctx['detect_media']('obfuscated-name-without-extension') is None

for_subject='"vacation.mkv" yEnc '
def make_part(number,part,total=3):
    subject=for_subject+f'({part}/{total})'
    return {'article':number,'message_id':f'<{number}@fake>','subject':subject,'from':'Uploader',
            'date':'Sun, 15 Nov 2026 12:00:00 +0000','bytes':3000000,
            'media':ctx['detect_media'](subject),'multipart':ctx['multipart_info'](subject)}
def make_single(number,ext='mp4'):
    sub=f'"movie{number}.{ext}" yEnc (1/1)'
    return {'article':number,'message_id':f'<{number}@fake>','subject':sub,'from':'Uploader',
            'date':'Sun, 15 Nov 2026 12:00:00 +0000','bytes':4100000,
            'media':ctx['detect_media'](sub),'multipart':ctx['multipart_info'](sub)}
def make_other(number):
    return {'article':number,'message_id':f'<{number}@fake>','subject':'filler','from':'Uploader',
            'date':'Sun, 15 Nov 2026 12:00:00 +0000','bytes':4000,'media':None,'multipart':None}

parts={906:make_part(906,1),905:make_part(905,2),880:make_part(880,3)}
# A separately incomplete video must not become downloadable after a scan.
parts[918]=make_part(918,1,4)
for n in range(795,825):parts[n]=make_single(n,'mpg')
assert not [i for i in ctx['group_articles']([parts[906],parts[905]]) if i.get('complete')]
assert any(i['media']['filename']=='vacation.mkv' and i['complete'] for i in ctx['group_articles']([parts[906],parts[905],parts[880]]) if i.get('media'))

class FakeClient:
    def __init__(self):self.calls=[];self.body_calls=0;self.fail=False
    def group(self,_):return {'name':'test.group','low':601,'high':1000,'count':400}
    def overview_chunked(self,start,end):
        self.calls.append((start,end))
        if self.fail:raise TimeoutError('provider timed out')
        return [parts.get(n,make_other(n)) for n in range(start,end+1)]
    def body(self,*a):self.body_calls+=1;raise AssertionError('BODY forbidden in header-only scan')

class Pool:
    def __init__(self):self.client=FakeClient()
    @contextmanager
    def lease(self,*args):yield self.client

class Diagnostics:
    events=[]
    def event(self,*args,**kwargs):self.events.append((args,kwargs))
pool=Pool();cache={};lock=threading.RLock()
ctx.update({'BROWSE_HEADER_POOL':pool,'ARTICLE_PAGE_CACHE':cache,'ARTICLE_PAGE_CACHE_LOCK':lock,
 'VIDEO_DISCOVERY_TARGET':18,'VIDEO_DISCOVERY_MAX_HEADER_POSITIONS':3600,'VIDEO_DISCOVERY_MAX_PAGES':8,
 '_apply_cached_name_resolutions':lambda *a:None,
 '_browse_perf_add':lambda *a:None,'_browse_perf_counter':lambda *a:None,
 '_overview_chunk_ranges':lambda lo,hi:[(lo,hi)],'DIAGNOSTICS':Diagnostics(),'time':time})
key=('provider','test.group',100,1,False,True)
def seed():return [parts.get(n,make_other(n)) for n in range(891,1001)]
def prepare(token):cache[key]={'cached_at':time.time(),'payload':{'smart_binary_pending':True,'video_discovery_pending':True,'video_discovery_job':token}}
def worker(token='new'):
    return ctx['_finish_progressive_video_page']('provider',{},'test.group',key,{'name':'test.group'},601,1000,1,4,100,901,1000,891,1000,seed(),token)
prepare('new');worker();payload=cache[key]['payload']
assert payload['smart_binary_pending'] is False and payload['video_discovery_pending'] is False,payload
assert payload['paging']['video_matches']>=18,payload['paging']
assert payload['paging']['scanned_page_end']==2,payload['paging']
assert payload['paging']['next_older_page']==3,payload['paging']
assert len(pool.client.calls)==1 and pool.client.calls[0]==(791,890),pool.client.calls
assert pool.client.body_calls==0
videos=payload['articles']
assert any(item['media']['filename']=='vacation.mkv' and item['complete'] and item['segment_count']==3 for item in videos),videos
assert any(item['media']['filename']=='vacation.mkv' and not item['complete'] and item['segment_total']==4 for item in videos), 'Separate incompatible multipart totals'
assert not any(item['complete'] and item['media']['filename']=='vacation.mkv' and item['segment_count']<3 for item in videos)
assert any(not item['complete'] for item in videos), 'Unresolved fragment remains explicitly incomplete'

# A second, stale worker must never replace refreshed pending or completed data.
prepare('newer');original=dict(cache[key]['payload']);worker('older');assert cache[key]['payload']==original
# Failure unblocks UI and does not invent complete videos.
prepare('failure');pool.client=FakeClient();pool.client.fail=True;worker('failure')
assert cache[key]['payload']['video_discovery_pending'] is False
assert 'timed out' in cache[key]['payload']['smart_binary_background_error']
# Empty/newsgroup ending stops safely without an infinite loop.
parts.clear();pool.client=FakeClient();ctx['VIDEO_DISCOVERY_TARGET']=99
prepare('empty');worker('empty');p=cache[key]['payload'];assert p['paging']['next_older_page']==0 and p['paging']['scanned_page_end']==4,p['paging']
assert pool.client.body_calls==0 and len(pool.client.calls)<=4,pool.client.calls
print('PASS: 15 video formats; original yEnc names; no archive overclassification; real multipart reconstruction across pages; bounded header-only scan; safe fragments; page coverage; stale refresh; provider failure; end of group')
