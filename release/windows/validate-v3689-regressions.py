from __future__ import annotations
import copy, hashlib, importlib.util, json, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'

def check(c,m):
    if not c: raise AssertionError(m)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

EXPECTED={
    'server.py':'659fcda33ba2b8dacbb2622700ce13d238dbc8a8c7a3610cf0f2ca2fce10a5bc',
    'automation_engine.py':'b52472c91b28beb30ec39397c2eada73b3578cf9248ba05786369a2a94c36f5e',
    'sab_engine.py':'adb5181ab4d7378107c486a4c03297baf1c8e54b6d85290ea108687970604a85',
    'static/app.js':'39e41639201214aa7b7ef4cf657d3562485729d3befdb752882a21de7b0310c0',
    'static/index.html':'b7dd2a6baa418aaadabb6f7b6b3e97314f24d38e1bb5032ce73851af5d3afb2b',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'aacab78324f152feec6f89fabb8bb57b29206f7b27860642c036dfba9d088897',
    'version.txt':'1e7cca510709f95886df2e13480dc49fc97318ccb7d705f9d5a2975ab43e33e7',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.89 payload')

auto=load('newzdeck_v3689_automation_guard',APP/'automation_engine.py')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))

check((APP/'version.txt').read_text().strip()=='3.6.89','version.txt mismatch')
check('APP_VERSION = "3.6.89"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.89';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.89' and manifest.get('base_version')=='3.6.88' and manifest.get('adapter_version')=='3.6.89','build manifest lineage mismatch')
check(manifest.get('release')=='Duplicate Fingerprint Reconciliation Fix','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')
check('v=3.6.89-duplicate-fingerprint-reconciliation-fix' in index,'v3.6.89 asset cache identity missing')
check(sha(APP/'static'/'styles.css')=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','frozen stylesheet changed')

for required in (
    "'duplicate_fingerprint_verified':action=='DUPLICATE'",
    "entry['duplicate_fingerprint_verified']=True",
    "'quality_source':'newzdeck-duplicate-proof'",
    "self._remember_media_quality(existing,existing_quality,release_title)",
    "record['cutoff_met']=self._quality_cutoff_met(existing_quality,profile,self._record_release_info(record,existing_quality))",
    "'dynamic_range_import_trusted':True",
):
    check(required in automation,'v3.6.89 duplicate reconciliation marker missing: '+required)

class DummyDownloadManager: pass
p4=copy.deepcopy(auto.DEFAULT_PROFILES[0])
false_probe={'resolution':'2160p','video_codec':'HEVC/x265','hdr':'Unknown','audio_codec':'DD+','dolby_vision':False,'hdr10_plus':False,'hdr_present':False}

def make_engine(label:str):
    root=Path(tempfile.mkdtemp(prefix=f'newzdeck-v3689-{label}-'))
    data=root/'data'; data.mkdir(); tvroot=root/'TV'; tvroot.mkdir()
    engine=auto.MediaAutomationEngine(data,lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.89')
    (data/'quality-profiles.json').write_text(json.dumps([p4]),encoding='utf-8')
    (data/'media-automation-config.json').write_text(json.dumps({'tv_roots':[str(tvroot)],'movie_roots':[],'plex_organize_enabled':True,'plex_cleanup_staging':False}),encoding='utf-8')
    engine._probe_media_traits=lambda _path:dict(false_probe)
    return root,data,tvroot,engine

def legacy_episode(number:int,path:Path,engine):
    return {
        'episode_number':number,'name':f'Episode {number}','air_date':'2026-01-01','monitored':True,
        'has_file':True,'file_path':str(path),'file_quality':'2160p WEB-DL','file_size':path.stat().st_size,
        'file_fingerprint':engine._media_fingerprint(path),'quality_source':'existing-library',
        'release_traits':auto.parse_release(f'Test.Show.S01E{number:02d}.2160p.WEB-DL.DV-OLD'),
        'media_info':dict(false_probe),
    }

# Exact production reproduction: the selected DV+HDR release downloads, but its
# media bytes are already the exact library file. DUPLICATE must transfer the
# selected release provenance to the existing file, satisfy the profile, and stay
# satisfied after serializing/reloading the library.
root,data,tvroot,engine=make_engine('dvhdr-duplicate')
series=tvroot/'Test Show'/'Season 1'; series.mkdir(parents=True)
existing=series/'Test Show - S01E01 - Pilot.mkv'; payload=b'IDENTICAL-DVHDR-PAYLOAD-'*8192; existing.write_bytes(payload)
ep=legacy_episode(1,existing,engine)
item={'id':'test-show','kind':'tv','title':'Test Show','year':2026,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','root_folder':str(tvroot),
      'seasons':[{'season_number':1,'monitored':True,'episodes':[ep]}]}
(data/'media-library.json').write_text(json.dumps([item]),encoding='utf-8')
source=root/'Test.Show.S01E01.2160p.WEB-DL.DV.HDR-GRP.mkv'; source.write_bytes(payload)
release='Test.Show.S01E01.2160p.WEB-DL.DV.HDR-GRP'
ctx={'source':'automation_grab','item_id':'test-show','title':'Test Show','kind':'tv','season':1,'episode':1,'episode_title':'Pilot','release_title':release,'release_quality':'2160p WEB-DL','target_key':'tv:test-show:S01E01'}
result=engine.import_completed_download(ctx,[str(source)])
check(result.get('ok') and result.get('imported_count')==0 and result.get('kept_existing')==1,f'Fingerprint-identical Smart Import did not reconcile as duplicate: {result}')
check(any(str(x.get('action'))=='DUPLICATE' for x in result.get('inspection') or []),'Import Inspector did not report DUPLICATE')
saved=json.loads((data/'media-library.json').read_text(encoding='utf-8'))
saved_ep=saved[0]['seasons'][0]['episodes'][0]
check(saved_ep.get('dynamic_range_import_trusted') is True,'Fingerprint-proven duplicate did not become trusted import provenance')
check(saved_ep.get('duplicate_fingerprint_verified') is True,'Fingerprint proof was not persisted on duplicate reconciliation')
check(saved_ep.get('quality_source')=='newzdeck-duplicate-proof','Duplicate reconciliation did not identify its evidence source')
check(str((saved_ep.get('release_traits') or {}).get('hdr'))=='Dolby Vision + HDR','DV+HDR release provenance was not transferred to existing identical file')
check(saved_ep.get('cutoff_met') is True,'Fingerprint-proven DV+HDR duplicate did not satisfy cutoff')
post=engine._record_release_info(saved_ep,'2160p WEB-DL',engine._media_quality_cache())
check(engine._dynamic_range_rank(post)==0 and not post.get('_dynamic_range_unconfirmed'),'Duplicate-proven DV+HDR record is still unconfirmed/lower-ranked')
cache=engine._media_quality_cache(); fp=str(saved_ep.get('file_fingerprint') or '')
check(str((cache.get(fp) or {}).get('release_title') or '')==release,'Existing fingerprint was not rebound to selected release provenance')
check(not engine.wanted().get('upgrades'),'Fingerprint-proven terminal upgrade still appears in Wanted after disk reload')
check(int((engine.summary().get('counts') or {}).get('upgrades') or 0)==0,'Summary upgrade count retained satisfied duplicate target')

# If the byte-identical corrective release is DV-only, Wanted should correctly
# remain for the higher DV+HDR target, but the just-proven DV state must no longer
# be marked unconfirmed or accept the same-rank DV replacement again.
root2,data2,tvroot2,engine2=make_engine('dv-duplicate')
series2=tvroot2/'Test Show'/'Season 1'; series2.mkdir(parents=True)
existing2=series2/'Test Show - S01E02 - Second.mkv'; payload2=b'IDENTICAL-DV-PAYLOAD-'*8192; existing2.write_bytes(payload2)
ep2=legacy_episode(2,existing2,engine2)
item2={'id':'test-show-2','kind':'tv','title':'Test Show','year':2026,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','root_folder':str(tvroot2),
       'seasons':[{'season_number':1,'monitored':True,'episodes':[ep2]}]}
(data2/'media-library.json').write_text(json.dumps([item2]),encoding='utf-8')
source2=root2/'Test.Show.S01E02.2160p.WEB-DL.DV-GRP.mkv'; source2.write_bytes(payload2)
ctx2={'source':'automation_grab','item_id':'test-show-2','title':'Test Show','kind':'tv','season':1,'episode':2,'episode_title':'Second','release_title':'Test.Show.S01E02.2160p.WEB-DL.DV-GRP','release_quality':'2160p WEB-DL','target_key':'tv:test-show-2:S01E02'}
r2=engine2.import_completed_download(ctx2,[str(source2)])
check(r2.get('ok') and r2.get('kept_existing')==1,'DV-only duplicate reconciliation failed')
saved2=json.loads((data2/'media-library.json').read_text(encoding='utf-8'))[0]['seasons'][0]['episodes'][0]
info2=engine2._record_release_info(saved2,'2160p WEB-DL',engine2._media_quality_cache())
check(engine2._dynamic_range_rank(info2)==1 and not info2.get('_dynamic_range_unconfirmed'),'DV-only duplicate did not become trusted confirmed DV')
check(engine2._quality_upgrade_status('2160p WEB-DL',p4,info2).get('wanted') is True,'DV-only duplicate should still want DV+HDR fallback')
same_dv=auto.parse_release('Test.Show.S01E02.2160p.WEB-DL.DV-OTHER')
check(engine2._is_quality_upgrade(same_dv,'2160p WEB-DL',p4,info2)[0] is False,'Trusted fingerprint-proven DV still allows repeated same-rank DV correction')
dvhdr=auto.parse_release('Test.Show.S01E02.2160p.WEB-DL.DV.HDR-OTHER')
check(engine2._is_quality_upgrade(dvhdr,'2160p WEB-DL',p4,info2)==(True,'dynamic range improves'),'DV -> DV+HDR progression regressed after duplicate reconciliation')

# KEEP_EXISTING must preserve provenance already attached to the existing file.
root3,data3,tvroot3,engine3=make_engine('keep-existing')
series3=tvroot3/'Test Show'/'Season 1'; series3.mkdir(parents=True)
existing3=series3/'Test Show - S01E03 - Third.mkv'; existing3.write_bytes(b'TRUSTED-EXISTING-'*8192)
trusted_traits=auto.parse_release('Test.Show.S01E03.2160p.WEB-DL.DV.HDR-TRUSTED')
ep3={'episode_number':3,'name':'Third','air_date':'2026-01-01','monitored':True,'has_file':True,'file_path':str(existing3),'file_quality':'2160p WEB-DL','file_size':existing3.stat().st_size,
     'file_fingerprint':engine3._media_fingerprint(existing3),'quality_source':'newzdeck-import','release_traits':trusted_traits,'dynamic_range_import_trusted':True,'dynamic_range_imported_at':'2026-09-12T00:00:00+00:00','media_info':dict(false_probe),'cutoff_met':True}
item3={'id':'test-show-3','kind':'tv','title':'Test Show','year':2026,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','root_folder':str(tvroot3),
       'seasons':[{'season_number':1,'monitored':True,'episodes':[ep3]}]}
(data3/'media-library.json').write_text(json.dumps([item3]),encoding='utf-8')
source3=root3/'Test.Show.S01E03.2160p.WEB-DL-GRP.mkv'; source3.write_bytes(b'DIFFERENT-SDR-PAYLOAD-'*8192)
ctx3={'source':'automation_grab','item_id':'test-show-3','title':'Test Show','kind':'tv','season':1,'episode':3,'episode_title':'Third','release_title':'Test.Show.S01E03.2160p.WEB-DL-GRP','release_quality':'2160p WEB-DL','target_key':'tv:test-show-3:S01E03'}
r3=engine3.import_completed_download(ctx3,[str(source3)])
check(r3.get('ok') and r3.get('kept_existing')==1 and any(str(x.get('action'))=='KEEP_EXISTING' for x in r3.get('inspection') or []),f'KEEP_EXISTING fixture did not exercise preservation path: {r3}')
saved3=json.loads((data3/'media-library.json').read_text(encoding='utf-8'))[0]['seasons'][0]['episodes'][0]
check(saved3.get('dynamic_range_import_trusted') is True,'KEEP_EXISTING erased trusted import state')
check(str((saved3.get('release_traits') or {}).get('hdr'))=='Dolby Vision + HDR','KEEP_EXISTING erased existing DV+HDR release traits')
check(saved3.get('cutoff_met') is True,'KEEP_EXISTING regressed satisfied cutoff state')
check(not engine3.wanted().get('upgrades'),'KEEP_EXISTING reintroduced a satisfied target into Wanted')

# Exact production-form release naming from the reported loop must still parse
# as terminal Dolby Vision + HDR rather than plain Dolby Vision.
reported=auto.parse_release('Dark.Matter.S02E02.Hybrid.MULTI.2160p.WEB-DL.DV.HDR.DDP5.1.Atmos.H265-AOC')
check(str(reported.get('quality') or '')=='2160p WEB-DL','Reported duplicate release lost 2160p WEB-DL identity')
check(engine._dynamic_range_rank(reported)==0 and reported.get('dolby_vision') and reported.get('hdr_present'),'Reported DV.HDR release is not recognized as Dolby Vision + HDR fallback')

# Frozen performance/browser/third-party behavior.
p1080=copy.deepcopy(auto.DEFAULT_PROFILES[1])
check(engine._dynamic_range_upgrade_target(p1080) is None,'1080p Balanced Allow-only dynamic range became mandatory')
check('cache=quality_cache if isinstance(quality_cache,dict) else self._media_quality_cache()' in automation,'v3.6.86 cache snapshot path changed')
for required in ('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;','state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'):
    check(required in app,'Frozen Newsgroup Browser value changed: '+required)
for required in ('VIDEO_THUMB_SAMPLE_MB = 24','max_segments=12','BROWSE_OVERVIEW_CHUNK_HEADERS = 800','BROWSE_FIRST_PAINT_HEADERS = 800','BROWSE_LARGE_PAGE_THRESHOLD = 1000'):
    check(required in server,'Frozen backend/browser value changed: '+required)
workflow=ROOT/'.github'/'workflows'/'publish-release-trigger.yml'
if workflow.exists():
    w=workflow.read_text(encoding='utf-8')
    for required in ("Where-Object { $_ -like 'Source commit:*' }","-replace '^Source commit:\\s*',''",'python release/windows/validate-v3688-regressions.py','python release/windows/validate-v3689-regressions.py'):
        check(required in w,'Canonical release workflow marker missing: '+required)
print('v3.6.89 Duplicate Fingerprint Reconciliation Fix regression guard: PASS')
