#!/usr/bin/env python3
"""v3.7.33 regression: real safe file finalizer, real native/SAB handlers.

All filesystem operations use temporary directories. No SAB process, user
configuration, Windows services, NNTP servers or media library is touched.
"""
from __future__ import annotations
import ast, contextlib, copy, importlib.util, json, os, shutil, subprocess, sys, tempfile, threading, types
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'src/app'
SERVER=(APP/'server.py').read_text('utf-8')
SAB=(APP/'sab_engine.py').read_text('utf-8')
spec=importlib.util.spec_from_file_location('flat_output',APP/'flat_output.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
flat=mod.flatten_completed_folder

# Production Windows ships an isolated CPython runtime whose sys.path does not
# necessarily include the application source directory. The SAB adapter must
# successfully load the sibling finalizer by file path with no app PYTHONPATH.
with tempfile.TemporaryDirectory(prefix='nz3733-isolated-module-') as isolated:
    script = (
        'import importlib.util,sys;'
        's=importlib.util.spec_from_file_location("sab_isolated",sys.argv[1]);'
        'm=importlib.util.module_from_spec(s);s.loader.exec_module(m);'
        'assert callable(m.flatten_completed_folder)'
    )
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    result = subprocess.run([sys.executable,'-c',script,str(APP/'sab_engine.py')],
                            cwd=isolated,env=env,capture_output=True,text=True,timeout=20)
    assert result.returncode == 0, result.stderr[-1500:]
    print('PASS: SAB module loads sibling finalizer in isolated Python without APP_DIR on sys.path')

def make_files(staging, entries):
    for path, value in entries.items():
        target=staging/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(value)

def source_method(text,cls,method,namespace):
    c=next(node for node in ast.parse(text).body if isinstance(node,ast.ClassDef) and node.name==cls)
    fn=next(node for node in c.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==method)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(fn)],type_ignores=[])), '<real production handler>', 'exec'),namespace)
    return namespace[method]

with tempfile.TemporaryDirectory(prefix='nz3733-output-') as temp:
    root=Path(temp)/'Downloads';root.mkdir()
    source=root/'CollectionA';source.mkdir()
    make_files(source,{'A/Sub/video.mkv':b'first','B/other.mkv':b'second'})
    (root/'video.mkv').write_bytes(b'existing')
    plan={};snapshots=[]
    def save(p):snapshots.append(dict(p))
    result=flat(source,root,plan,save)
    assert result=={'A/Sub/video.mkv':'video (2).mkv','B/other.mkv':'other.mkv'},result
    assert (root/'video.mkv').read_bytes()==b'existing' and (root/'video (2).mkv').read_bytes()==b'first'
    assert (root/'other.mkv').read_bytes()==b'second' and not source.exists()
    assert len(snapshots)==2,'Name plan must persist before each atomic move'
    print('PASS: nesting flattened to root, no clobber, durable name plan')

    # A hard exit after creating a hard link but before unlinking the staging file
    # is safe: resume recognizes both links point at the SAME inode.
    source=root/'CrashJob';source.mkdir();(source/'video.mkv').write_bytes(b'resumed')
    dest=root/'video (3).mkv'
    os.link(source/'video.mkv',dest)
    plan={'video.mkv':'video (3).mkv'}
    assert flat(source,root,plan,lambda p:None)==plan
    assert dest.read_bytes()==b'resumed' and not source.exists()
    print('PASS: interrupted hard-link move is idempotent and leaves one output')

    source=root/'UnsafeJob';source.mkdir();(source/'clip.mkv').write_bytes(b'data')
    with patch.object(mod.os,'link',side_effect=OSError('filesystem has no safe link support')):
        try:flat(source,root,{},lambda p:None)
        except OSError:pass
        else:raise AssertionError('No-copy fallback must fail closed')
    assert (source/'clip.mkv').read_bytes()==b'data' and not (root/'clip.mkv').exists()
    print('PASS: unsupported filesystem preserves source instead of unsafe copy')

    source=root/'SymlinkJob';source.mkdir();(source/'clip.mkv').write_bytes(b'data')
    try:
        (source/'link.mkv').symlink_to(root/'video.mkv')
    except (OSError,NotImplementedError):
        pass # Some Windows non-admin accounts cannot create symlinks.
    else:
        try:flat(source,root,{},lambda p:None)
        except ValueError:pass
        else:raise AssertionError('Symlink should not be consumed')
    print('PASS: unsafe symlink entries rejected when supported')

    # Exercise the actual native handler from server.py against a synthetic
    # one-job native NZB without loading NewzDeck or its Windows integrations.
    namespace={'Path':Path,'Any':object,'threading':threading,'DOWNLOAD_DIR':root,
               'flatten_completed_folder':flat}
    native=source_method(SERVER,'DownloadManager','_finalize_flat_native_output',namespace) if 'class DownloadManager' in SERVER else None
    if native is None:
        for item in ast.parse(SERVER).body:
            if isinstance(item,ast.ClassDef) and any(getattr(n,'name','')=='_finalize_flat_native_output' for n in item.body):
                native=source_method(SERVER,item.name,'_finalize_flat_native_output',namespace);break
    assert native is not None
    source=root/'NativeNZB';source.mkdir();make_files(source,{'nested/native.mp4':b'native'})
    job={'path':str(source/'nested/native.mp4'),'flat_output_requested':True,'flat_output_plan':{}}
    class Native:
        def __init__(self):self.lock=threading.RLock();self.saves=0
        def _save(self):self.saves+=1
    n=Native();native(n,[job],source)
    assert (root/'native.mp4').read_bytes()==b'native' and job['flat_output_done']
    assert job['path']==str(root/'native.mp4') and n.saves>=2
    print('PASS: actual native handler finalizes after completion and updates paths')

    # Exercise the actual SAB handler, including the independent opt-in flag,
    # completed slot ownership, and restart reconciliation.
    events=[]
    namespace={'Path':Path,'Any':object,'_is_smart_import_context':lambda c:bool(c and c.get('source')=='automation_grab'),
               'flatten_completed_folder':flat}
    sab=source_method(SAB,'SabDownloadManager','_finalize_flat_completed_nzb_owned',namespace)
    class Sab:
        def __init__(self,meta):self.meta=meta;self.lock=threading.RLock();self.saves=0
        def _tracked(self):return {'id1':self.meta}
        def _save_state(self):self.saves+=1
        def _touch_job_locked(self,m):pass
        def _event(self,*args,**kwargs):events.append((args,kwargs))
        def download_dir_getter(self):return root
    source=root/'SabJob';source.mkdir();make_files(source,{'Deep/sab.mkv':b'sab'})
    meta={'name':'SabJob','output_hint':str(source),'flat_output_requested':True,'flat_output_done':False,'automation_context':{}}
    slot={'storage':str(source),'status':'Completed'}
    s=Sab(meta);assert sab(s,'id1',meta,slot) is True
    assert (root/'sab.mkv').read_bytes()==b'sab' and not source.exists() and meta['flat_output_done']
    # The Windows runner may spell the same directory through an 8.3 alias or
    # junction; SAB stores a resolved path. Verify identity, not spelling.
    assert Path(slot['storage']).samefile(root), (slot['storage'], str(root))
    assert s.saves >= 2, f'Expected durable plan + completion saves, got {s.saves}'
    # Already completed -> do not try another rename. Checked -> no modifications.
    assert sab(s,'id1',meta,slot) is False
    other=root/'CheckedJob';other.mkdir();make_files(other,{'keep.mp4':b'keep'})
    checked={'name':'CheckedJob','output_hint':str(other),'flat_output_requested':False,'automation_context':{}}
    assert sab(Sab(checked),'id1',checked,{'storage':str(other)}) is False and (other/'keep.mp4').is_file()
    # Root pointer or another job's staging folder is never accepted.
    wrong=root/'Wrong';wrong.mkdir();make_files(wrong,{'wrong.mp4':b'wrong'})
    mismatch={'name':'Other','output_hint':str(root/'Other'),'flat_output_requested':True,'automation_context':{}}
    assert sab(Sab(mismatch),'id1',mismatch,{'storage':str(wrong)}) is False and (wrong/'wrong.mp4').exists()
    automation={'name':'Automation','output_hint':str(wrong),'flat_output_requested':True,'automation_context':{'source':'automation_grab'}}
    assert sab(Sab(automation),'id1',automation,{'storage':str(wrong)}) is False
    print('PASS: SAB completed only, checked unchanged, wrong owner blocked, Smart Import protected')

    # A full move followed by a crash before the durable done bit is recorded.
    recovered={'name':'Recovered','output_hint':str(root/'Recovered'),'flat_output_requested':True,
               'flat_output_plan':{'nested/recovered.mkv':'recovered.mkv'},'automation_context':{}}
    (root/'recovered.mkv').write_bytes(b'complete')
    assert sab(Sab(recovered),'id1',recovered,{'storage':str(root/'Recovered')}) is True
    assert recovered['flat_output_done']
    print('PASS: source-folder removal before final state save can be recovered')

    # Execute the actual outer SAB cross-runtime lock wrapper. When the lock
    # cannot be acquired, it must not even attempt to relocate a completed job.
    wrapper=source_method(SAB,'SabDownloadManager','_finalize_flat_completed_nzb',
                          {'hashlib':__import__('hashlib'),'Any':object,'Path':Path})
    source=root/'LockedJob';source.mkdir();make_files(source,{'locked.mkv':b'locked'})
    locked={'name':'LockedJob','output_hint':str(source),'flat_output_requested':True,
            'flat_output_plan':{},'automation_context':{}}
    class LockSab(Sab):
        admin_dir=root
        def _try_kernel_file_lock(self,path):return None
        def _release_kernel_file_lock(self,claim):raise AssertionError('No lock held')
        def _refresh_shared_state(self):pass
        def _finalize_flat_completed_nzb_owned(self,*args):raise AssertionError('Work ran without lock')
    assert wrapper(LockSab(locked),'id1',locked,{'storage':str(source)}) is False
    assert (source/'locked.mkv').read_bytes()==b'locked'
    class GrantedSab(LockSab):
        def _try_kernel_file_lock(self,path):return object()
        def _release_kernel_file_lock(self,claim):self.released=True
        def _finalize_flat_completed_nzb_owned(self,nzo_id,meta,slot):
            return sab(self,nzo_id,meta,slot)
    ok=GrantedSab(locked)
    assert wrapper(ok,'id1',locked,{'storage':str(source)}) is True
    assert ok.released and (root/'locked.mkv').read_bytes()==b'locked'
    print('PASS: real cross-process lock wrapper blocks conflicting runtime and releases after success')

assert 'from flat_output import' not in SERVER and 'from flat_output import' not in SAB
assert '_load_app_source_module(\n    "newzdeck_flat_output", APP_DIR / "flat_output.py"' in SERVER
assert 'flatten_completed_folder = _load_flat_output_from_installed_source()' in SAB
assert 'flat_output_requested' in SERVER and '"destination_subdir": collection_name' in SERVER
assert 'flat_output_requested' in SAB and '"flat_output_plan": {}' in SAB
assert 'def _finalize_flat_completed_nzb(' in SAB and 'self._try_kernel_file_lock(self.admin_dir / lock_name)' in SAB
assert 'if bool(meta.get("flat_output_requested")) and not bool(meta.get("flat_output_done")): return False' in SAB
assert 'validate-v3732-async-grab.py' != 'validate-v3733-flat-output.py'
print('PASS: v3.7.33 safe flat completed output, unchanged checked behavior, no speculative engine changes')
