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
    'server.py':'c599e5baec178f686621d5d5353230c100f87b3a165866866fd02d1ef496ebe2',
    'automation_engine.py':'2251d62400d9b1c23604696f82549977aa9c64d18d2e60299a7af3fbcbe9e9cb',
    'sab_engine.py':'b77650ff20c4a08cadbd6e224be5c76ed45bbdbf7ed81586fc30f6fda684bb81',
    'static/app.js':'e3e41ad9ddd8ed948061aa81e3c859d387e30bcf2656615ee15f6805ef808a65',
    'static/index.html':'e751cbde9917a79e8678a59644f68ac5478c81a13e13d2aa504b8f0d8c1c4721',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'02074a2f67e5b3917fb1decd1774970a96b4318a74b9832bcb341fa64f2f0a5d',
    'version.txt':'cc2988a3a8006e8e61ddbbf5e331599b132a78e4cd609805981982406f28396f',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.90 payload')

auto=load('newzdeck_v3688_automation_guard',APP/'automation_engine.py')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))

check((APP/'version.txt').read_text().strip()=='3.6.90','version.txt mismatch')
check('APP_VERSION = "3.6.90"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.90';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.90' and manifest.get('base_version')=='3.6.89' and manifest.get('adapter_version')=='3.6.90','build manifest lineage mismatch')
check(manifest.get('release')=='Windows Defender Picker Compatibility & Release Gate Hardening','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')
check('v=3.6.90-windows-defender-picker-release-gate-hardening' in index,'v3.6.89 asset cache identity missing')
check(sha(APP/'static'/'styles.css')=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','frozen stylesheet changed')

for required in (
    "dynamic_range_import_trusted':True",
    "'_dynamic_range_unconfirmed'=", # checked below by alternate literal because assignment syntax differs
):
    if required.endswith('='):
        continue
    check(required in automation,'v3.6.89 Smart Import trust marker missing: '+required)
check("info['_dynamic_range_unconfirmed']=True" in automation,'unconfirmed legacy dynamic-range marker missing')
check('dynamic range replacement verifies an unconfirmed current trait' in automation,'same-rank legacy correction path missing')
check('positive probe is the strongest' in automation and 'A positive probe may still promote a trusted imported release' in automation and 'partial positive sample is not proof' in automation,'confidence-aware positive-probe guard missing')

class DummyDownloadManager: pass
root=Path(tempfile.mkdtemp(prefix='newzdeck-v3688-guard-'))
data=root/'data'; data.mkdir(); tvroot=root/'TV'; tvroot.mkdir()
engine=auto.MediaAutomationEngine(data,lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.90')
p4=copy.deepcopy(auto.DEFAULT_PROFILES[0]); p1080=copy.deepcopy(auto.DEFAULT_PROFILES[1])
(data/'quality-profiles.json').write_text(json.dumps([p4]),encoding='utf-8')
(data/'media-automation-config.json').write_text(json.dumps({'tv_roots':[str(tvroot)],'movie_roots':[],'plex_organize_enabled':True,'plex_cleanup_staging':False}),encoding='utf-8')

# Legacy v3.6.87-style record: release provenance says DV but the lightweight probe
# did not positively confirm it. The trait remains usable for Wanted display, but
# it is marked unconfirmed so a corrective same-rank DV candidate is not rejected.
legacy_rec={
    'episode_number':1,'name':'Pilot','air_date':'2026-01-01','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL','file_fingerprint':'legacy-current',
    'release_traits':auto.parse_release('Test.Show.S01E01.2160p.WEB-DL.DV-GRP'),
    'media_info':{'resolution':'2160p','video_codec':'HEVC/x265','hdr':'Unknown','audio_codec':'DD+','dolby_vision':False,'hdr10_plus':False,'hdr_present':False},
}
legacy_info=engine._record_release_info(legacy_rec,'2160p WEB-DL',{})
check(engine._dynamic_range_rank(legacy_info)==1,'Legacy DV provenance was erased by a weak negative probe')
check(legacy_info.get('_dynamic_range_unconfirmed') is True,'Legacy optimistic dynamic-range state is not marked unconfirmed')
incoming_dv=auto.parse_release('Test.Show.S01E01.2160p.WEB-DL.DV-GRP2')
check(engine._is_quality_upgrade(incoming_dv,'2160p WEB-DL',p4,legacy_info)==(True,'dynamic range replacement verifies an unconfirmed current trait'),'Legacy same-rank corrective DV replacement regressed')

# End-to-end Smart Import reproduction. The new release explicitly says DV+HDR,
# while the lightweight probe is forced to return a false-negative triplet. The
# saved record must still become terminal for Wanted after a disk reload.
series=tvroot/'Test Show'/'Season 1'; series.mkdir(parents=True)
old=series/'Test Show - S01E01.mkv'; old.write_bytes(b'OLD-CURRENT-'*4096)
old_fp=engine._media_fingerprint(old)
item={'id':'test-show','kind':'tv','title':'Test Show','year':2026,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','root_folder':str(tvroot),
      'seasons':[{'season_number':1,'monitored':True,'episodes':[dict(legacy_rec,file_path=str(old),file_size=old.stat().st_size,file_fingerprint=old_fp)]}]}
(data/'media-library.json').write_text(json.dumps([item]),encoding='utf-8')
source=root/'Test.Show.S01E01.2160p.WEB-DL.DV.HDR-GRP.mkv'; source.write_bytes(b'NEW-DVHDR-'*8192)
false_probe={'resolution':'2160p','video_codec':'HEVC/x265','hdr':'Unknown','audio_codec':'DD+','dolby_vision':False,'hdr10_plus':False,'hdr_present':False}
engine._probe_media_traits=lambda _path:dict(false_probe)
ctx={'source':'automation_grab','item_id':'test-show','title':'Test Show','kind':'tv','season':1,'episode':1,'episode_title':'Pilot',
     'release_title':'Test.Show.S01E01.2160p.WEB-DL.DV.HDR-GRP','release_quality':'2160p WEB-DL','target_key':'tv:test-show:S01E01'}
result=engine.import_completed_download(ctx,[str(source)])
check(result.get('ok') and result.get('imported_count')==1,f'Synthetic upgrade import failed: {result}')

saved=json.loads((data/'media-library.json').read_text(encoding='utf-8'))
saved_ep=saved[0]['seasons'][0]['episodes'][0]
check(saved_ep.get('dynamic_range_import_trusted') is True,'Successful Smart Import did not stamp trusted post-import dynamic-range provenance')
check(str((saved_ep.get('release_traits') or {}).get('hdr'))=='Dolby Vision + HDR','Imported release traits were not persisted')
check((saved_ep.get('media_info') or {}).get('dolby_vision') is False,'False-negative probe fixture did not survive import')
post_info=engine._record_release_info(saved_ep,'2160p WEB-DL',engine._media_quality_cache())
check(engine._dynamic_range_rank(post_info)==0,'Fresh DV+HDR Smart Import was downgraded by weak negative probe evidence')
check(post_info.get('_dynamic_range_unconfirmed') is False,'Fresh trusted Smart Import was incorrectly marked unconfirmed')
check(engine._quality_upgrade_status('2160p WEB-DL',p4,post_info).get('wanted') is False,'Fresh DV+HDR import does not satisfy 4K Preferred')
check(saved_ep.get('cutoff_met') is True,'Persisted episode cutoff_met was not reconciled from canonical post-import state')

wanted=engine.wanted()
check(not wanted.get('upgrades'),f'Satisfied DV+HDR target still appears in Wanted after disk reload: {wanted.get("upgrades")}')
summary=engine.summary()
check(not (summary.get('wanted') or {}).get('upgrades'),'Automation summary reintroduced satisfied Wanted upgrade')
check(int((summary.get('counts') or {}).get('upgrades') or 0)==0,'Automation upgrade count did not reconcile after import')

# A new trusted DV-only import remains below DV+HDR, but another DV-only release is
# not repeatedly accepted. This prevents automatic replacement loops while keeping
# the next real DV+HDR step eligible.
trusted_dv={'file_quality':'2160p WEB-DL','file_fingerprint':'trusted-dv','quality_source':'newzdeck-import','dynamic_range_import_trusted':True,
            'release_traits':auto.parse_release('Test.Show.S01E01.2160p.WEB-DL.DV-GRP'),
            'media_info':dict(false_probe)}
trusted_dv_info=engine._record_release_info(trusted_dv,'2160p WEB-DL',{})
check(engine._dynamic_range_rank(trusted_dv_info)==1 and not trusted_dv_info.get('_dynamic_range_unconfirmed'),'Fresh DV import trust state is wrong')
check(engine._quality_upgrade_status('2160p WEB-DL',p4,trusted_dv_info).get('wanted') is True,'DV-only import should remain Wanted for DV+HDR')
check(engine._is_quality_upgrade(incoming_dv,'2160p WEB-DL',p4,trusted_dv_info)[0] is False,'Fresh trusted DV import allows repeat same-rank DV loop')
incoming_dvhdr=auto.parse_release('Test.Show.S01E01.2160p.WEB-DL.DV.HDR-GRP2')
check(engine._is_quality_upgrade(incoming_dvhdr,'2160p WEB-DL',p4,trusted_dv_info)==(True,'dynamic range improves'),'Trusted DV -> DV+HDR progression regressed')

# Positive actual-file evidence can still promote an understated release title.
positive={'file_quality':'2160p WEB-DL','release_traits':auto.parse_release('Test.Show.S01E01.2160p.WEB-DL-GRP'),
          'media_info':{'dolby_vision':True,'hdr10_plus':False,'hdr_present':True,'hdr':'Dolby Vision + HDR'}}
pos=engine._record_release_info(positive,'2160p WEB-DL',{})
check(engine._dynamic_range_rank(pos)==0,'Positive media-probe DV+HDR evidence failed to promote understated provenance')

# 1080p Balanced Allow-only semantics and v3.6.86 snapshot architecture remain.
check(engine._dynamic_range_upgrade_target(p1080) is None,'1080p Balanced Allow policies became mandatory again')
check('cache=quality_cache if isinstance(quality_cache,dict) else self._media_quality_cache()' in automation,'caller-owned quality-cache snapshot path changed')
for required in ('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;','state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'):
    check(required in app,'Frozen Newsgroup Browser value changed: '+required)
for required in ('VIDEO_THUMB_SAMPLE_MB = 24','max_segments=12','BROWSE_OVERVIEW_CHUNK_HEADERS = 800','BROWSE_FIRST_PAINT_HEADERS = 800','BROWSE_LARGE_PAGE_THRESHOLD = 1000'):
    check(required in server,'Frozen backend/browser value changed: '+required)

workflow=ROOT/'.github'/'workflows'/'publish-release-trigger.yml'
if workflow.exists():
    w=workflow.read_text(encoding='utf-8')
    for required in ("Where-Object { $_ -like 'Source commit:*' }","-replace '^Source commit:\\s*',''",'python release/windows/validate-v3687-regressions.py','python release/windows/validate-v3688-regressions.py'):
        check(required in w,'Canonical release workflow marker missing: '+required)
print('v3.6.89 Duplicate Fingerprint Reconciliation Fix regression guard: PASS')
