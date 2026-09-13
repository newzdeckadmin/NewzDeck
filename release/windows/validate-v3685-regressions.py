from __future__ import annotations
import hashlib, importlib.util, json, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'

def check(c,m):
    if not c: raise AssertionError(m)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

EXPECTED={
    'server.py':'ac9e7bd7358db1730f65734273d7522e8d355072f94c1f496f55bd49bc1f5fa6',
    'automation_engine.py':'99c3be38f1391cb69ed080e25590adfa0686a2f825e08855a2ace418cedc4482',
    'sab_engine.py':'730251293a10456b507755f0c5b2fc5ed7058991dcd8c8c219e69165eece6645',
    'static/app.js':'14b20eeb8ff607aa54ab5f33bacd225def4908fd179f0178439cf310a42a3b1c',
    'static/index.html':'c64cc5580d5367216e6415402bc5b5e59fa503c81be3fb9b68c0d515e3030301',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'92e12f63a1d2229802c3b16933d137e58c7ce7d681f8de1e6eec0ed2580f4fcc',
    'version.txt':'8b61b18dd869a8daa094d28bd3e92a380c14d8d457f299d3f00486300a2bc287',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.88 payload')

auto=load('newzdeck_v3685_automation_guard',APP/'automation_engine.py')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.88','version.txt mismatch')
check('APP_VERSION = "3.6.88"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.88';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.88' and manifest.get('base_version')=='3.6.87' and manifest.get('adapter_version')=='3.6.88','build manifest lineage mismatch')
check(manifest.get('release')=='Smart Import Wanted Reconciliation Fix','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')
check('v=3.6.88-smart-import-wanted-reconciliation-fix' in index,'v3.6.87 asset cache identity missing')
check(sha(APP/'static'/'styles.css')=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','frozen stylesheet changed')

# One canonical helper must own all current-file trait evidence precedence.
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
for required in (
    'def _record_release_info(self, rec:',
    'quality_cache:dict[str,Any]|None=None',
    'return self._record_release_info(rec,current_quality,quality_cache)',
    "self._record_release_info(item['movie_file'],current_quality,cache)",
    'self._record_release_info(ep,current_quality,cache)',
    "self._record_release_info(rec,str(rec.get('quality') or 'Unknown'),cache)",
    "self._record_release_info(mf,str((mf or {}).get('quality') or 'Unknown'),cache)",
):
    check(required in automation,'Canonical current-file trait resolver marker missing: '+required)
check("rec.get('release_traits') or rec.get('media_info')" not in automation,'Library cutoff still bypasses canonical trait resolver')
check("ep.get('release_traits') or ep.get('media_info')" not in automation,'TV Wanted/Calendar still bypasses canonical trait resolver')

class DummyDownloadManager: pass
root=Path(tempfile.mkdtemp(prefix='newzdeck-v3685-guard-'))
engine=auto.MediaAutomationEngine(root,lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.88')
p4=auto.DEFAULT_PROFILES[0]; p1080=auto.DEFAULT_PROFILES[1]
candidate_title='Dark.Matter.2024.S02E02.A.Perfect.World.2160p.ATVP.WEB-DL.DDP5.1.Atmos.DV.HDR.HEVC-GRP'
candidate=auto.parse_release(candidate_title)
check(engine._dynamic_range_rank(candidate)==0,'DV+HDR candidate is not terminal dynamic range')

# v3.6.87 refines the canonical resolver without reintroducing split-brain behavior:
# release provenance can claim DV+HDR, but a successful media probe is authoritative
# for intrinsic dynamic-range state.  Every surface must see the same corrected view.
overclaim_rec={
    'episode_number':2,'name':'A Perfect World','air_date':'2026-09-03','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL','file_fingerprint':'overclaim-fp',
    'media_info':{'quality':'2160p WEB-DL','dolby_vision':True,'hdr10_plus':False,'hdr_present':False,'hdr':'Dolby Vision'},
}
overclaim_item={'id':'overclaim','kind':'tv','title':'Dark Matter','year':2024,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':2,'monitored':True,'episodes':[overclaim_rec]}]}
cache={'overclaim-fp':{'quality':'2160p WEB-DL','source':'newzdeck-import','release_title':candidate_title}}
(root/'media-quality-cache.json').write_text(json.dumps(cache),encoding='utf-8')
overclaim_info=engine._record_release_info(overclaim_rec,'2160p WEB-DL',cache)
check(engine._dynamic_range_rank(overclaim_info)==1,'Successful media probe did not correct provenance-only DV+HDR overclaim to true DV-only')
check(engine._current_target_release_info(overclaim_item,2,2,'2160p WEB-DL',cache)==overclaim_info,'Interactive Search current traits disagree with canonical record resolver')
overclaim_status=engine._quality_upgrade_status('2160p WEB-DL',p4,overclaim_info)
check(overclaim_status.get('wanted') and overclaim_status.get('reason_code')=='dynamic_range_upgrade','Corrected DV-only current file is not Wanted for DV+HDR fallback')
better,why=engine._is_quality_upgrade(candidate,'2160p WEB-DL',p4,overclaim_info)
check(better and why=='dynamic range improves','DV+HDR candidate is rejected after correcting provenance overclaim')
overclaim_eval=engine._evaluate_release(candidate_title,12*1024**3,p4,item=overclaim_item,season=2,episode=2,current_quality='2160p WEB-DL',current_info=overclaim_info)
check(overclaim_eval.get('accepted'),'DV+HDR candidate should be eligible against probe-proven DV-only current media')

# Conversely, actual media evidence can prove the terminal state even when release
# provenance is weaker. This prevents the authority change from creating false upgrades.
terminal_rec={
    'episode_number':3,'name':'Terminal','air_date':'2026-09-03','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL','file_fingerprint':'terminal-fp',
    'release_traits':auto.parse_release('Dark.Matter.2024.S02E03.2160p.WEB-DL.HEVC-GRP'),
    'media_info':{'quality':'2160p WEB-DL','dolby_vision':True,'hdr10_plus':False,'hdr_present':True,'hdr':'Dolby Vision + HDR'},
}
terminal_item={'id':'terminal','kind':'tv','title':'Dark Matter','year':2024,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':2,'monitored':True,'episodes':[terminal_rec]}]}
terminal_info=engine._record_release_info(terminal_rec,'2160p WEB-DL',cache)
check(engine._dynamic_range_rank(terminal_info)==0,'Actual DV+HDR media probe was not authoritative over weaker provenance')
check(engine._quality_upgrade_status('2160p WEB-DL',p4,terminal_info).get('wanted') is False,'Actual DV+HDR current file remains falsely Wanted')
terminal_eval=engine._evaluate_release(candidate_title,12*1024**3,p4,item=terminal_item,season=2,episode=3,current_quality='2160p WEB-DL',current_info=terminal_info)
check(not terminal_eval.get('accepted'),'Same terminal candidate should not replace an actual DV+HDR current file')

# Wanted itself must consume the same resolver: corrected DV-only stays upgradeable,
# while the actual terminal DV+HDR item disappears.
(root/'media-library.json').write_text(json.dumps([overclaim_item,terminal_item]),encoding='utf-8')
wanted=engine.wanted(cache); upgrades={str(x.get('item_id')):x for x in wanted.get('upgrades') or []}
check(upgrades.get('overclaim',{}).get('reason_code')=='dynamic_range_upgrade','Wanted lost corrected DV-only dynamic-range upgrade')
check('terminal' not in upgrades,'Wanted ignored actual DV+HDR media evidence')

# v3.6.84 policy behavior must remain fixed while trait-source coherency changes.
sdr1080=auto.parse_release('Show.S01E01.1080p.WEB-DL.x264-GRP')
check(engine._dynamic_range_upgrade_target(p1080) is None,'1080p Balanced Allow policies regressed into a mandatory target')
check(engine._quality_cutoff_met(sdr1080['quality'],p1080,sdr1080),'1080p Balanced SDR WEB-DL no longer satisfies cutoff')
generic=auto.parse_release('Show.S01E01.2160p.WEB.x265.DV.HDR10-GRP')
source_state=engine._quality_upgrade_status('2160p WEB-DL',p4,generic)
check(source_state.get('reason_code')=='release_source_upgrade','WEB -> WEB-DL source upgrade semantics regressed')

# Release-engineering and frozen runtime boundaries remain explicit.
for required in (
    "Where-Object { $_ -like 'Source commit:*' }",
    "-replace '^Source commit:\\s*',''",
    'python release/windows/validate-v3684-regressions.py',
    'python release/windows/validate-v3685-regressions.py',
    'python release/windows/validate-v3686-regressions.py',
    'python release/windows/validate-v3687-regressions.py',
):
    check(required in workflow,'Canonical release workflow marker missing: '+required)
for required in ('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;','state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'):
    check(required in app,'Frozen Newsgroup Browser value changed: '+required)
for required in ('VIDEO_THUMB_SAMPLE_MB = 24','max_segments=12','BROWSE_OVERVIEW_CHUNK_HEADERS = 800','BROWSE_FIRST_PAINT_HEADERS = 800','BROWSE_LARGE_PAGE_THRESHOLD = 1000'):
    check(required in server,'Frozen backend/browser value changed: '+required)
print('v3.6.85 Wanted & Interactive Search Trait Coherency Fix carried-forward guard under v3.6.88: PASS')
