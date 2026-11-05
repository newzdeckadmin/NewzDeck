#!/usr/bin/env python3
"""NewzDeck v3.7.17: scoped SAB staging basename restoration behavior."""
from __future__ import annotations
import importlib.util
import pathlib
import sys
import tempfile
import threading
import types

SRC=pathlib.Path(__file__).resolve().parents[2]/'src/app/sab_engine.py'
spec=importlib.util.spec_from_file_location('newzdeck_sab_filename_test', SRC)
sab=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=sab
spec.loader.exec_module(sab)
BASE='NewzDeck Loose 9f90e233b029'
PREFERRED='Family Holiday - 002.jpg'

def eq(a,b,msg):
    if a!=b: raise AssertionError(f'{msg}: got {a!r} expected {b!r}')

def case(name, originals, expected, stage_name=BASE, *, root_file=False, existing=(), want=None):
    with tempfile.TemporaryDirectory(prefix='newzdeck-flat-') as d:
        root=pathlib.Path(d)
        source=root if root_file else root/stage_name
        if not root_file: source.mkdir()
        for x in originals: (source/x).write_bytes(b'\xff\xd8\xfftest')
        for x in existing: (root/x).write_bytes(b'untouched original')
        instance=object.__new__(sab.SabDownloadManager)
        instance.download_dir_getter=lambda:root
        instance.lock=threading.RLock()
        meta={
            'name':expected[0] if expected else 'Fallback',
            'browser_flat_images':True,'browser_flattened':False,
            'browser_flat_filenames':expected,'browser_flat_staging_name':stage_name,
            'browser_group':'alt.binaries.images'
        }
        jobs={'job-123':meta}
        instance._tracked=lambda:jobs
        instance._touch_job_locked=lambda m:None
        instance._save_state=lambda:None
        instance._event=lambda *a,**kw:None
        instance._browser_name_recovery_after_flatten=lambda *args:args[-1]
        slot={'storage':str(root/originals[0] if root_file else source),'status':'Completed'}
        result=instance._flatten_completed_browser_images('job-123',meta,slot)
        eq(result,True,name+' success')
        result_files=sorted(f.name for f in root.iterdir() if f.is_file())
        eq(result_files,sorted((want or originals)+list(existing)),name+' names')
        for x in existing: eq((root/x).read_bytes(),b'untouched original',name+' collision untouched')
        eq(sorted(meta['browser_flattened_files']),sorted(want or originals),name+' history tracked')
        eq(pathlib.Path(slot['storage']).samefile(root),True,name+' history storage identity')

f=sab.SabDownloadManager._browser_final_loose_name
assert f(BASE+'.jpg',[PREFERRED],BASE)==PREFERRED
assert f(BASE+' (2).jpg',[PREFERRED],BASE)==PREFERRED
assert f(BASE+'.jpg',[PREFERRED],'NewzDeck Loose abcdabcdabcd')==BASE+'.jpg'
assert f(BASE+'.jpg',[PREFERRED.replace('.jpg','.png')],BASE)==BASE+'.jpg'
assert f(BASE+'.jpg',['file.bin'],BASE)==BASE+'.jpg'
assert f(BASE+'.jpg',[],BASE)==BASE+'.jpg'
assert f(BASE+'.jpg',[PREFERRED,'second.jpg'],BASE)==BASE+'.jpg'
assert f('Already Correct.jpg',[PREFERRED],BASE)=='Already Correct.jpg'
assert f(BASE+'.mkv',['Video.mkv'],BASE)==BASE+'.mkv'
assert f(BASE+'.jpg',['../Travel.jpg'],BASE)=='Travel.jpg'
case('stage rename', [BASE+'.jpg'], [PREFERRED],want=[PREFERRED])
case('direct-root rename', [BASE+'.jpg'], [PREFERRED],root_file=True,want=[PREFERRED])
case('collision', [BASE+'.jpg'],[PREFERRED],existing=[PREFERRED],want=['Family Holiday - 002 (2).jpg'])
case('no rename for ordinary decoded name',['Already Correct.jpg'],[PREFERRED])
case('different staging token',[BASE+'.jpg'],[PREFERRED],stage_name='NewzDeck Loose abcdef123456')
case('opaque expected name',[BASE+'.jpg'],['file.bin'])
case('multi-file payload',[BASE+'.jpg','second.jpg'],[PREFERRED])
# A confirmed Completed UI display name must follow the recorded flattened name, not SAB's staging title.
text=SRC.read_text(encoding='utf-8')
assert 'visible_filename if bool(meta.get("browser_flattened")) and len(flat_names) == 1' in text
print('validate-v3717-loose-filenames.py: PASS (scoped staging name, root/stage, collisions, failures, truthful Completed labels)')
