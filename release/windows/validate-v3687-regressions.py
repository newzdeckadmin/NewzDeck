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
    'server.py':'94f849feb0d8aa35ccec16ab8ad8c041bc07acffe94e8f08fc107fea0ebf77ae',
    'automation_engine.py':'c52d5f93ba6ad24a1045ebda49a2b1973d9fdd43d6e56e973dd0404ff8b5ede7',
    'sab_engine.py':'c899f3d39de00ee5c43f22f1cb0cdef3009449274789753ea4a97d37b864e77c',
    'static/app.js':'8932e47cbbc06e965c2bf02692bab72107179a53a20038d9594dd2a3ee6d781f',
    'static/index.html':'bf357570e16584b46a9ee42a5e103457f4612afd04f3d1cecf269e2db9276ea8',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'51d1981e1cada1d63276409977fddc33379d523ef13199e6fc1e8450421b895a',
    'version.txt':'21a15ffafda3766bf34259e3defea1a151f7c980e409a8a4a9c70b357d504c36',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.91 payload')

auto=load('newzdeck_v3687_carried_guard',APP/'automation_engine.py')
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8'); styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
check((APP/'version.txt').read_text().strip()=='3.6.91','version.txt mismatch')
check('APP_VERSION = "3.6.91"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.91';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.91' and manifest.get('base_version')=='3.6.90','build manifest lineage mismatch')
check('v=3.6.91-defender-picker-release-gate-compatibility-fix' in index,'v3.6.89 asset cache identity missing')
check(sha(APP/'static'/'styles.css')=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','frozen stylesheet changed')

# Preserve the v3.6.87 user-visible requirement even though v3.6.89 refines the
# evidence implementation: an old same-tier current file whose DV provenance is
# not positively confirmed must not make a real DV replacement fail as "same tier".
class DummyDownloadManager: pass
root=Path(tempfile.mkdtemp(prefix='newzdeck-v3687-carried-'))
engine=auto.MediaAutomationEngine(root,lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.91')
p4=copy.deepcopy(auto.DEFAULT_PROFILES[0]); p1080=copy.deepcopy(auto.DEFAULT_PROFILES[1])
current_rec={
    'episode_number':1,'name':'Episode 1','air_date':'2026-01-08','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL','file_fingerprint':'his-hers-current',
    'release_traits':auto.parse_release('His.and.Hers.S01E01.2160p.NF.WEB-DL.DV.HEVC-OLD'),
    'media_info':{'resolution':'2160p','video_codec':'HEVC/x265','hdr':'Unknown','audio_codec':'DD+',
                  'dolby_vision':False,'hdr10_plus':False,'hdr_present':False},
}
current_item={'id':'his-hers','kind':'tv','title':'HIS & HERS','year':2026,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':1,'monitored':True,'episodes':[current_rec]}]}
quality_cache={'his-hers-current':{'quality':'2160p WEB-DL','source':'newzdeck-import','release_title':'His.and.Hers.S01E01.2160p.NF.WEB-DL.DV.HEVC-OLD'}}
current_info=engine._record_release_info(current_rec,'2160p WEB-DL',quality_cache)
check(str(current_info.get('source'))=='WEB-DL','Release provenance source identity was lost')
check(engine._dynamic_range_rank(current_info)==1,'Legacy DV provenance was erased instead of retained as uncertain')
check(current_info.get('_dynamic_range_unconfirmed') is True,'Legacy optimistic DV state is not marked unconfirmed')
incoming_title='His.&.Hers.S01E01.2026.2160p.NF.WEB-DL.DDP5.1.Atmos.DV.H.265-HHWEB'
incoming=auto.parse_release(incoming_title)
better,why=engine._is_quality_upgrade(incoming,'2160p WEB-DL',p4,current_info)
check(better and 'unconfirmed current trait' in why,'DV-only corrective candidate is again rejected as same quality tier')
ev=engine._evaluate_release(incoming_title,7*1024**3,p4,item=current_item,season=1,episode=1,current_quality='2160p WEB-DL',current_info=current_info)
check(ev.get('accepted'),f'DV-only candidate remains rejected: {ev.get("rejections")}')

# Stronger positive file evidence still promotes understated provenance, and the
# intended HDR -> DV -> DV+HDR progression remains intact.
def info_for(title,dv,hdr):
    rec={'file_quality':'2160p WEB-DL','release_traits':auto.parse_release(title),
         'media_info':{'dolby_vision':dv,'hdr10_plus':False,'hdr_present':hdr,'hdr':'probe'}}
    return engine._record_release_info(rec,'2160p WEB-DL',{})
hdr_info=info_for('Show.S01E01.2160p.WEB-DL.HDR-GRP',False,True)
dv_info=info_for('Show.S01E01.2160p.WEB-DL.DV-GRP',True,False)
dvhdr_info=info_for('Show.S01E01.2160p.WEB-DL.DV.HDR-GRP',True,True)
dv_candidate=auto.parse_release('Show.S01E01.2160p.WEB-DL.DV.HEVC-GRP')
dvhdr_candidate=auto.parse_release('Show.S01E01.2160p.WEB-DL.DV.HDR.HEVC-GRP')
check(engine._is_quality_upgrade(dv_candidate,'2160p WEB-DL',p4,hdr_info)[0] is True,'HDR -> DV progression regressed')
check(engine._is_quality_upgrade(dvhdr_candidate,'2160p WEB-DL',p4,dv_info)==(True,'dynamic range improves'),'DV -> DV+HDR progression regressed')
check(engine._quality_upgrade_status('2160p WEB-DL',p4,dvhdr_info).get('wanted') is False,'DV+HDR current file is not terminal')

# Interactive Search still resolves one current view for all candidates and the
# v3.6.86 quality-cache snapshot performance guarantee remains.
engine._library=lambda:[copy.deepcopy(current_item)]
engine._profiles=lambda:[copy.deepcopy(p4)]
engine._indexers=lambda:[{'id':'synthetic','name':'Synthetic','enabled':True}]
rows=[{'title':incoming_title,'size':7*1024**3,'guid':'dv-only','download_url':'https://example.invalid/dv','published':time.time()-86400,'indexer':'Synthetic'},
      {'title':'His.&.Hers.S01E01.2026.2160p.NF.WEB-DL.DDP5.1.Atmos.DV.HDR.H.265-HHWEB','size':8*1024**3,'guid':'dv-hdr','download_url':'https://example.invalid/dvhdr','published':time.time()-86400,'indexer':'Synthetic'}]
engine._search_indexer=lambda idx,item,season,episode:copy.deepcopy(rows)
engine._auto_runtime=lambda:{'targets':{}}; engine._save_auto_runtime=lambda value:None; engine._sync_automatic_failures=lambda value:False
reads={'n':0}
def read_cache(): reads['n']+=1; return quality_cache
engine._media_quality_cache=read_cache
search=engine.search_releases('his-hers',1,1)
check(reads['n']==1,f'Interactive Search reread media quality cache {reads["n"]} times')
by_guid={str(r.get('guid')):r for r in search.get('releases') or []}
check(by_guid.get('dv-only',{}).get('accepted'),'Interactive Search again rejects legacy corrective DV-only upgrade')
check(by_guid.get('dv-hdr',{}).get('accepted'),'Interactive Search rejects DV+HDR upgrade')

check(engine._dynamic_range_upgrade_target(p1080) is None,'1080p Balanced Allow policies became mandatory again')
for required in ("Where-Object { $_ -like 'Source commit:*' }","-replace '^Source commit:\\s*',''",'python release/windows/validate-v3687-regressions.py','python release/windows/validate-v3688-regressions.py'):
    check(required in workflow,'Canonical release workflow marker missing: '+required)
for required in ('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;','state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'):
    check(required in app,'Frozen Newsgroup Browser value changed: '+required)
for required in ('VIDEO_THUMB_SAMPLE_MB = 24','max_segments=12','BROWSE_OVERVIEW_CHUNK_HEADERS = 800','BROWSE_FIRST_PAINT_HEADERS = 800','BROWSE_LARGE_PAGE_THRESHOLD = 1000'):
    check(required in server,'Frozen backend/browser value changed: '+required)
print('v3.6.87 Dynamic Range Evidence Authority user-visible behavior carried forward under v3.6.91: PASS')
