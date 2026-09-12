from __future__ import annotations
import copy, hashlib, importlib.util, json, sys, tempfile, time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'

def check(c,m):
    if not c: raise AssertionError(m)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

EXPECTED={
    'server.py':'3d45cec7ab9d836a7ff2cadc5ed8f8caab75e911aece19acd729e79d2c6bf7e5',
    'automation_engine.py':'eba353ca751ec259262918444f7d96e0a04262ffc9c8ca934e438e9ba702478e',
    'sab_engine.py':'262406b082712c73ffcce8b30d0de15247d9e5a93b6fb82c7132ad7db22e3680',
    'static/app.js':'2d41baf1935dc99015d4c401c2bdd610b4486477ee3429abca808af4eb5dfb54',
    'static/index.html':'53259051490170fa79acf0b11454d1b96f5049e79ea7a6a690f1319f05559183',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'2d06e148b86ee2da4cf98f0e3f0caa099efb5e8294ab66e01b31df4cb07cb519',
    'version.txt':'428801e7d19029d5cacd7d5f906a4c329d88b4b3efa3eaeee183b9cf5aec3d40',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.87 payload')

auto=load('newzdeck_v3687_automation_guard',APP/'automation_engine.py')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.87','version.txt mismatch')
check('APP_VERSION = "3.6.87"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.87';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.87' and manifest.get('base_version')=='3.6.86' and manifest.get('adapter_version')=='3.6.87','build manifest lineage mismatch')
check(manifest.get('release')=='Dynamic Range Evidence Authority Fix','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')
check('v=3.6.87-dynamic-range-evidence-authority-fix' in index,'v3.6.87 asset cache identity missing')
check(sha(APP/'static'/'styles.css')=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','frozen stylesheet changed')

# v3.6.87 must separate release provenance from intrinsic traits proven by the
# actual imported media file. False probe booleans are evidence, not missing data.
for required in (
    "probe_dynamic_range=all(k in media for k in ('dolby_vision','hdr10_plus','hdr_present'))",
    "info['dolby_vision']=dv",
    "info['hdr10_plus']=plus",
    "info['hdr_present']=hdr_present",
    "info['hdr10']=bool(media.get('hdr10')) if 'hdr10' in media else False",
    "else: info['hdr']='SDR/Unknown'",
    'the v3.6.86 cache-snapshot performance fix is',
):
    check(required in automation,'v3.6.87 evidence-authority marker missing: '+required)

class DummyDownloadManager: pass
root=Path(tempfile.mkdtemp(prefix='newzdeck-v3687-guard-'))
engine=auto.MediaAutomationEngine(root,lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.87')
p4=copy.deepcopy(auto.DEFAULT_PROFILES[0]); p1080=copy.deepcopy(auto.DEFAULT_PROFILES[1])

# Exact production class reported by the user: the existing 2160p WEB-DL is
# physically SDR/non-DV, but persisted post provenance says DV. A DV-only result
# at the same base quality MUST be an upgrade, not "same quality tier".
current_rec={
    'episode_number':1,'name':'Episode 1','air_date':'2026-01-08','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL','file_fingerprint':'his-hers-current',
    'release_traits':auto.parse_release('His.and.Hers.S01E01.2160p.NF.WEB-DL.DV.HEVC-OLD'),
    'media_info':{
        'resolution':'2160p','video_codec':'HEVC/x265','hdr':'SDR/Unknown','audio_codec':'DD+',
        'dolby_vision':False,'hdr10_plus':False,'hdr_present':False,
    },
}
current_item={'id':'his-hers','kind':'tv','title':'HIS & HERS','year':2026,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':1,'monitored':True,'episodes':[current_rec]}]}
quality_cache={'his-hers-current':{'quality':'2160p WEB-DL','source':'newzdeck-import','release_title':'His.and.Hers.S01E01.2160p.NF.WEB-DL.DV.HDR.HEVC-EVENMOREOPTIMISTIC'}}
current_info=engine._record_release_info(current_rec,'2160p WEB-DL',quality_cache)
check(str(current_info.get('source'))=='WEB-DL','Actual-media override destroyed release provenance source identity')
check(engine._dynamic_range_rank(current_info)==4,'Successful SDR media probe did not override optimistic DV provenance')
check(not current_info.get('dolby_vision') and not current_info.get('hdr_present'),'Corrected current trait view still claims DV/HDR')
status=engine._quality_upgrade_status('2160p WEB-DL',p4,current_info)
check(status.get('wanted') and status.get('reason_code')=='dynamic_range_upgrade','Actual SDR current file is not Wanted for preferred dynamic range')

incoming_title='His.&.Hers.S01E01.2026.2160p.NF.WEB-DL.DDP5.1.Atmos.DV.H.265-HHWEB'
incoming=auto.parse_release(incoming_title)
check(engine._dynamic_range_rank(incoming)==1,'DV-only candidate parser classification changed')
better,why=engine._is_quality_upgrade(incoming,'2160p WEB-DL',p4,current_info)
check(better and why=='dynamic range improves','DV-only candidate was rejected against actual SDR current media')
ev=engine._evaluate_release(incoming_title,7*1024**3,p4,item=current_item,season=1,episode=1,current_quality='2160p WEB-DL',current_info=current_info)
check(ev.get('accepted'),f'DV-only candidate remains rejected: {ev.get("rejections")}')
check(any('dynamic range improves' in str(x) for x in ev.get('reasons') or []),'Accepted DV-only upgrade lacks dynamic-range explanation')

# The complete progression still matters: actual HDR -> DV, actual DV -> DV+HDR,
# and actual DV+HDR is terminal. These are based on media evidence even if the
# original release title disagrees.
def info_for(dv,hdr,provenance):
    rec={'file_quality':'2160p WEB-DL','release_traits':auto.parse_release(provenance),'media_info':{'dolby_vision':dv,'hdr10_plus':False,'hdr_present':hdr,'hdr':'probe'}}
    return engine._record_release_info(rec,'2160p WEB-DL',{})
hdr_info=info_for(False,True,'Show.S01E01.2160p.WEB-DL.DV.HDR.HEVC-GRP')
dv_info=info_for(True,False,'Show.S01E01.2160p.WEB-DL.HEVC-GRP')
dvhdr_info=info_for(True,True,'Show.S01E01.2160p.WEB-DL.HEVC-GRP')
dv_candidate=auto.parse_release('Show.S01E01.2160p.WEB-DL.DV.HEVC-GRP')
dvhdr_candidate=auto.parse_release('Show.S01E01.2160p.WEB-DL.DV.HDR.HEVC-GRP')
check(engine._is_quality_upgrade(dv_candidate,'2160p WEB-DL',p4,hdr_info)==(True,'dynamic range improves'),'Actual HDR -> DV progression regressed')
check(engine._is_quality_upgrade(dv_candidate,'2160p WEB-DL',p4,dv_info)[0] is False,'Same DV state incorrectly treated as an upgrade')
check(engine._is_quality_upgrade(dvhdr_candidate,'2160p WEB-DL',p4,dv_info)==(True,'dynamic range improves'),'Actual DV -> DV+HDR progression regressed')
check(engine._quality_upgrade_status('2160p WEB-DL',p4,dvhdr_info).get('wanted') is False,'Actual DV+HDR current file is not terminal')

# A failed/inaccessible probe has no authoritative boolean triplet, so provenance
# remains the fallback instead of treating Unknown as proof of SDR.
failed_probe={'file_quality':'2160p WEB-DL','release_traits':auto.parse_release('Show.S01E01.2160p.WEB-DL.DV.HEVC-GRP'),'media_info':{'resolution':'2160p','hdr':'Unknown','video_codec':'Unknown','audio_codec':'Unknown'}}
failed_info=engine._record_release_info(failed_probe,'2160p WEB-DL',{})
check(engine._dynamic_range_rank(failed_info)==1,'Failed probe incorrectly erased provenance DV evidence')

# Exercise Interactive Search itself, not only the helper. It must use the same
# corrected current trait dictionary once for all candidates and retain v3.6.86's
# one-cache-read performance fix.
engine._library=lambda:[copy.deepcopy(current_item)]
engine._profiles=lambda:[copy.deepcopy(p4)]
engine._indexers=lambda:[{'id':'synthetic','name':'Synthetic','enabled':True}]
rows=[{'title':incoming_title,'size':7*1024**3,'guid':'dv-only','download_url':'https://example.invalid/dv','published':time.time()-86400,'indexer':'Synthetic'},
      {'title':'His.&.Hers.S01E01.2026.2160p.NF.WEB-DL.DDP5.1.Atmos.DV.HDR.H.265-HHWEB','size':8*1024**3,'guid':'dv-hdr','download_url':'https://example.invalid/dvhdr','published':time.time()-86400,'indexer':'Synthetic'}]
engine._search_indexer=lambda idx,item,season,episode:copy.deepcopy(rows)
engine._auto_runtime=lambda:{'targets':{}}
engine._save_auto_runtime=lambda value:None
engine._sync_automatic_failures=lambda value:False
reads={'n':0}
def read_cache(): reads['n']+=1; return quality_cache
engine._media_quality_cache=read_cache
search=engine.search_releases('his-hers',1,1)
check(reads['n']==1,f'Interactive Search reread media quality cache {reads["n"]} times')
by_guid={str(r.get('guid')):r for r in search.get('releases') or []}
check(by_guid.get('dv-only',{}).get('accepted'),'Interactive Search still rejects the user-reported DV-only upgrade')
check(by_guid.get('dv-hdr',{}).get('accepted'),'Interactive Search rejects DV+HDR upgrade against actual SDR media')

# v3.6.84/v3.6.86 semantics and frozen unrelated architecture remain protected.
check(engine._dynamic_range_upgrade_target(p1080) is None,'1080p Balanced Allow policies became mandatory again')
for required in (
    "Where-Object { $_ -like 'Source commit:*' }",
    "-replace '^Source commit:\\s*',''",
    'python release/windows/validate-v3685-regressions.py',
    'python release/windows/validate-v3686-regressions.py',
    'python release/windows/validate-v3687-regressions.py',
):
    check(required in workflow,'Canonical release workflow marker missing: '+required)
for required in ('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;','state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'):
    check(required in app,'Frozen Newsgroup Browser value changed: '+required)
for required in ('VIDEO_THUMB_SAMPLE_MB = 24','max_segments=12','BROWSE_OVERVIEW_CHUNK_HEADERS = 800','BROWSE_FIRST_PAINT_HEADERS = 800','BROWSE_LARGE_PAGE_THRESHOLD = 1000'):
    check(required in server,'Frozen backend/browser value changed: '+required)
print('v3.6.87 Dynamic Range Evidence Authority Fix regression guard: PASS')
