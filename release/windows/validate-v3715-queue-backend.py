#!/usr/bin/env python3
"""Exercise the real SabDownloadManager.add implementation with a fake SAB submitter."""
from __future__ import annotations
import ast
from pathlib import Path
import re
from typing import Any
from tempfile import TemporaryDirectory
ROOT=Path(__file__).resolve().parents[2]
tree=ast.parse((ROOT/'src/app/sab_engine.py').read_text(encoding='utf-8'))
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SabDownloadManager')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='add')
module=ast.Module(body=[method],type_ignores=[])
namespace={'Any':Any,'Path':Path,'SAB_VERSION':'5.1.2','_safe_name':lambda v: re.sub(r'[\\/:*?"<>|]+','_',v)[:140],'build_nzb_bytes':lambda name,items: repr((name,len(items))).encode()}
exec(compile(ast.fix_missing_locations(module), '<isolated sab add>', 'exec'),namespace)
class Stub:
    add=namespace['add']
    def __init__(self,fail=None):self.calls=[];self.fail=fail
    def _submit_nzb(self,provider_id,source_name,raw,**kw):
        self.calls.append((provider_id,source_name,raw,kw))
        if self.fail and self.fail in source_name:raise RuntimeError('simulated SAB error')
        return {'added':[{'id':f'job-{len(self.calls)}'}]}
def item(key,name,*,source='browser_loose',collection=''):
    return {'client_key':key,'media':{'filename':name,'kind':'image'},'segments':[{'message_id':f'<{key}@example.org>', 'part':1,'bytes':1500}],'source':source,'collection_id':collection}
s=Stub();r=s.add('test-provider','alt.test',[item('1','one.jpg'),item('2','two.png'),item('3','three.mp4')]);assert len(s.calls)==3 and len(r['added'])==3,r
assert all(k['browser_flat_images'] and k['file_count']==1 for _,_,_,k in s.calls),s.calls
assert [x['client_key'] for x in r['added']]==['1','2','3']
s=Stub();r=s.add('p','alt.test',[item('1','one.rar',source='browser_set',collection='c1'),item('2','two.par2',source='browser_set',collection='c1'),item('3','free.jpg')]);assert len(s.calls)==2,(r,s.calls)
assert s.calls[0][-1]['file_count']==2 and not s.calls[0][-1]['browser_flat_images']
assert s.calls[1][-1]['file_count']==1 and s.calls[1][-1]['browser_flat_images']
assert len(r['added'])==3
s=Stub(fail='two.png');r=s.add('p','alt.test',[item('1','one.jpg'),item('2','two.png'),item('3','three.jpg')]);assert len(r['added'])==2 and [x['client_key'] for x in r['failed']]==['2'],r
assert len(s.calls)==3 and r['warnings'],'partial failure must be reported without hiding successful submissions'
try:Stub(fail='one.jpg').add('p','alt.test',[item('1','one.jpg')]);raise AssertionError('all-failed should raise')
except RuntimeError as e:assert 'simulated SAB error' in str(e)
print('validate-v3715-queue-backend.py: PASS (individual loose jobs, intentional packages, partial failures, all-failed guard)')
