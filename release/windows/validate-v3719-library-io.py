#!/usr/bin/env python3
"""v3.7.19: real temporary-media functional tests for the scan-content cache."""
from pathlib import Path
import os,sys,tempfile,importlib.util,json,ast,types,time
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'src/app/automation_engine.py'
spec=importlib.util.spec_from_file_location('newzdeck_v3719_automation_test',SRC)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def ok(c,msg):
    if not c:raise AssertionError('v3.7.19 library I/O: '+msg)

with tempfile.TemporaryDirectory(prefix='newzdeck-v3719-io-') as d:
    root=Path(d);obj=mod.MediaAutomationEngine.__new__(mod.MediaAutomationEngine) if hasattr(mod,'MediaAutomationEngine') else None
    if obj is None:
        candidates=[v for v in vars(mod).values() if isinstance(v,type) and hasattr(v,'_analyze_scanned_media')]
        ok(len(candidates)==1,'single Automation class detected')
        obj=candidates[0].__new__(candidates[0])
    obj.media_scan_cache_file=root/'media-scan-cache.json'
    obj.media_quality_cache_file=root/'media-quality-cache.json'
    media=root/'Library'/'Show.S01E01.1080p.mkv';media.parent.mkdir(parents=True)
    media.write_bytes(b'\x1aE\xdf\xa3'+b'demonstration video content'*300)
    counts={'traits':0,'fp':0,'resolution':0}
    real_t=obj._probe_media_traits;real_f=obj._media_fingerprint;real_r=obj._probe_media_resolution
    def traits(self,path):counts['traits']+=1;return real_t(path)
    def fingerprint(self,path):counts['fp']+=1;return real_f(path)
    def resolution(self,path):counts['resolution']+=1;return real_r(path)
    obj._probe_media_traits=types.MethodType(traits,obj)
    obj._media_fingerprint=types.MethodType(fingerprint,obj)
    obj._probe_media_resolution=types.MethodType(resolution,obj)
    cache=obj._scan_media_cache();qc={}
    first=obj._analyze_scanned_media(media,qc,None,cache)
    ok(first[-1] and first[2],'new media analyzed and cached')
    ok(counts['traits']==1 and counts['fp']==1 and counts['resolution']==1,'first scan has one traits probe, one fingerprint, one resolution probe')
    obj._save_scan_media_cache(cache)
    stamp=obj.media_scan_cache_file.stat().st_mtime_ns
    second=obj._analyze_scanned_media(media,qc,{'file_path':str(media),'file_size':media.stat().st_size,'file_quality':'1080p','quality_source':'library-record'},cache)
    ok(not second[-1] and second[2]==first[2] and second[3]==first[3],'unchanged media uses cached evidence')
    ok(counts['traits']==1 and counts['fp']==1 and counts['resolution']==1,'unchanged file incurs no content reads')
    ok(obj.media_scan_cache_file.stat().st_mtime_ns==stamp,'no cache file rewrite on unchanged file')
    persisted=obj._scan_media_cache()
    third=obj._analyze_scanned_media(media,qc,None,persisted)
    ok(not third[-1] and third[2]==first[2],'restart reuses persisted scan evidence')
    ok(counts['traits']==1 and counts['fp']==1,'restart also avoids content reads')
    old_stat=media.stat();media.write_bytes(media.read_bytes().replace(b'demonstration',b'XXXXXXXXXXXXX'))
    ok(media.stat().st_size==old_stat.st_size,'same-size content replacement fixture')
    os.utime(media,ns=(old_stat.st_atime_ns,old_stat.st_mtime_ns+10_000_000_000))
    fresh=obj._analyze_scanned_media(media,qc,{'file_path':str(media),'file_size':old_stat.st_size,'file_quality':'Unrelated Old Quality'},persisted)
    ok(fresh[-1] and fresh[2]!=first[2],'changed content with same size invalidates fingerprint')
    ok(counts['traits']==2 and counts['fp']==2,'changed content reanalyzed once')
    ok(fresh[0]!='Unrelated Old Quality','changed same-size file does not inherit stale quality')
    obj._save_scan_media_cache(persisted)
    sibling=root/'Other'/'Show.S01E01.1080p.mkv';sibling.parent.mkdir(parents=True);sibling.write_bytes(b'other video')
    changed=obj._analyze_scanned_media(sibling,qc,None,persisted)
    ok(changed[-1] and changed[2]!=fresh[2],'different path not conflated')
    before=len(persisted);sibling.unlink()
    missing=obj._analyze_scanned_media(sibling,qc,None,persisted)
    ok(missing[2]=='' and len(persisted)==before,'removed file cannot be returned from cache')
    obj.media_scan_cache_file.write_text('{bad json',encoding='utf-8')
    ok(obj._scan_media_cache()=={},'corrupted cache safely rebuilt')
    obj.media_scan_cache_file.unlink()
    obj._save_scan_media_cache(persisted)
    ok(json.loads(obj.media_scan_cache_file.read_text(encoding='utf-8'))['schema']==1,'rebuildable cache has explicit schema')
    ok(len(obj._scan_media_cache())==2,'persisted key count')

source=SRC.read_text(encoding='utf-8');tree=ast.parse(source)
scan=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='scan_library')
scantext=ast.get_source_segment(source,scan)
ok(scantext.count('self._analyze_scanned_media(')==2,'both TV and movie scans use the shared cache')
ok('self._probe_media_traits(f)' not in scantext,'no repeated raw traits probing in scanned candidate paths')
ok('if scan_cache_changed:' in scantext,'save cache only when newly analyzed')
ok('files_by_root' in scantext and 'root.rglob' in scantext,'maintain real directory discovery for additions and deletions')
print('validate-v3719-library-io.py: PASS (cold scan, warm scan no media reads, persisted reuse, changed same-size media, source isolation, missing files, corrupted cache, TV/movie scan paths)')
