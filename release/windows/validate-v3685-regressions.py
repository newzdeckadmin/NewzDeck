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
    'server.py':'9b147f4d400796daba60d921121f061fda47c8ae2656606ffee23ec955a91c9c',
    'automation_engine.py':'7e06f1631e14bc218d87eebfc9c8e11b3adc8b7eabbcc83470971c30e604f496',
    'sab_engine.py':'db10d1f2682b309a3948001c85a76dfba1a8b0f382c03825348e1f8bf0da0b87',
    'static/app.js':'d906aa6380b7e6dd496fda79fa4eed8eaa0273f74917210ffc759346d8b358e1',
    'static/index.html':'de9f3a7e66cda904b850cb6e8367ef20dd08d0c57d844a59f9a642f49b0430ce',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'cb1e5e252f672c77d31639933db8a7a73bc0b064c55abcdb7848a5002bbfe827',
    'version.txt':'c2774a94bba26baaca42593431e7ab43aabf67e087beb5d5aaa6ef45858a4891',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.85 payload')

auto=load('newzdeck_v3685_automation_guard',APP/'automation_engine.py')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.85','version.txt mismatch')
check('APP_VERSION = "3.6.85"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.85';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.85' and manifest.get('base_version')=='3.6.84' and manifest.get('adapter_version')=='3.6.85','build manifest lineage mismatch')
check(manifest.get('release')=='Wanted & Interactive Search Trait Coherency Fix','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')
check('v=3.6.85-wanted-search-trait-coherency-fix' in index,'v3.6.85 asset cache identity missing')
check(sha(APP/'static'/'styles.css')=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','frozen stylesheet changed')

# One canonical helper must own all current-file trait evidence precedence.
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
for required in (
    'def _record_release_info(self, rec:',
    'return self._record_release_info(rec,current_quality)',
    "self._record_release_info(item['movie_file'],current_quality)",
    'self._record_release_info(ep,current_quality)',
    "self._record_release_info(rec,str(rec.get('quality') or 'Unknown'))",
    "self._record_release_info(mf,str((mf or {}).get('quality') or 'Unknown'))",
):
    check(required in automation,'Canonical current-file trait resolver marker missing: '+required)
check("rec.get('release_traits') or rec.get('media_info')" not in automation,'Library cutoff still bypasses canonical trait resolver')
check("ep.get('release_traits') or ep.get('media_info')" not in automation,'TV Wanted/Calendar still bypasses canonical trait resolver')

class DummyDownloadManager: pass
root=Path(tempfile.mkdtemp(prefix='newzdeck-v3685-guard-'))
engine=auto.MediaAutomationEngine(root,lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.85')
p4=auto.DEFAULT_PROFILES[0]; p1080=auto.DEFAULT_PROFILES[1]
candidate_title='Dark.Matter.2024.S02E02.A.Perfect.World.2160p.ATVP.WEB-DL.DDP5.1.Atmos.DV.HDR.HEVC-GRP'
candidate=auto.parse_release(candidate_title)
check(engine._dynamic_range_rank(candidate)==0,'DV+HDR candidate is not terminal dynamic range')

# Reproduce the exact v3.6.84 split-brain condition. Conservative media_info says
# DV-only, while the fingerprint-bound original release title proves DV+HDR.
terminal_rec={
    'episode_number':2,'name':'A Perfect World','air_date':'2026-09-03','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL','file_fingerprint':'terminal-fp',
    'media_info':{'quality':'2160p WEB-DL','dolby_vision':True,'hdr_present':False,'hdr':'Dolby Vision'},
}
terminal_item={'id':'terminal','kind':'tv','title':'Dark Matter','year':2024,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':2,'monitored':True,'episodes':[terminal_rec]}]}
(root/'media-quality-cache.json').write_text(json.dumps({'terminal-fp':{'quality':'2160p WEB-DL','source':'newzdeck-import','release_title':candidate_title}}),encoding='utf-8')
terminal_info=engine._record_release_info(terminal_rec,'2160p WEB-DL')
check(engine._dynamic_range_rank(terminal_info)==0,'Fingerprint-bound DV+HDR release title was not used by canonical resolver')
check(engine._quality_upgrade_status('2160p WEB-DL',p4,terminal_info).get('wanted') is False,'Already-terminal DV+HDR file remains falsely Wanted')
check(engine._current_target_release_info(terminal_item,2,2,'2160p WEB-DL')==terminal_info,'Interactive Search current traits disagree with canonical record resolver')
terminal_eval=engine._evaluate_release(candidate_title,12*1024**3,p4,item=terminal_item,season=2,episode=2,current_quality='2160p WEB-DL')
check(not terminal_eval.get('accepted'),'Same terminal candidate should not replace an already-terminal current file')
check(any('same quality tier' in str(x) for x in terminal_eval.get('rejections') or []),'Already-terminal candidate rejection changed unexpectedly')

# If the current file is genuinely DV-only (no stronger stored/cached evidence),
# Wanted must keep the upgrade and the exact DV+HDR candidate must be ELIGIBLE.
true_dv_rec={
    'episode_number':2,'name':'A Perfect World','air_date':'2026-09-03','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL',
    'media_info':{'quality':'2160p WEB-DL','dolby_vision':True,'hdr_present':False,'hdr':'Dolby Vision'},
}
true_dv_item={'id':'true-dv','kind':'tv','title':'Dark Matter','year':2024,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':2,'monitored':True,'episodes':[true_dv_rec]}]}
true_dv_info=engine._record_release_info(true_dv_rec,'2160p WEB-DL')
check(engine._dynamic_range_rank(true_dv_info)==1,'True DV-only current file no longer resolves as Dolby Vision')
true_status=engine._quality_upgrade_status('2160p WEB-DL',p4,true_dv_info)
check(true_status.get('wanted') and true_status.get('reason_code')=='dynamic_range_upgrade','True DV-only current file is not Wanted for DV+HDR fallback')
check(true_status.get('upgrade_path')=='Dynamic range: Dolby Vision → Dolby Vision + HDR fallback','True DV-only Wanted path mismatch')
better,why=engine._is_quality_upgrade(candidate,'2160p WEB-DL',p4,true_dv_info)
check(better and why=='dynamic range improves','DV+HDR candidate is still rejected against true DV-only current file')
true_eval=engine._evaluate_release(candidate_title,12*1024**3,p4,item=true_dv_item,season=2,episode=2,current_quality='2160p WEB-DL')
check(true_eval.get('accepted'),f'DV+HDR candidate should be eligible against true DV-only current file: {true_eval.get("rejections")}')
check(any('dynamic range improves' in str(x) for x in true_eval.get('reasons') or []),'Interactive Search does not explain accepted dynamic-range improvement')

# Wanted itself must consume the same resolver: terminal item disappears, true-DV remains.
(root/'media-library.json').write_text(json.dumps([terminal_item,true_dv_item]),encoding='utf-8')
wanted=engine.wanted(); upgrades={str(x.get('item_id')):x for x in wanted.get('upgrades') or []}
check('terminal' not in upgrades,'Wanted still uses weaker media_info instead of canonical fingerprint evidence')
check(upgrades.get('true-dv',{}).get('reason_code')=='dynamic_range_upgrade','Wanted lost the true DV-only dynamic-range upgrade')

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
):
    check(required in workflow,'Canonical release workflow marker missing: '+required)
for required in ('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;','state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'):
    check(required in app,'Frozen Newsgroup Browser value changed: '+required)
for required in ('VIDEO_THUMB_SAMPLE_MB = 24','max_segments=12','BROWSE_OVERVIEW_CHUNK_HEADERS = 800','BROWSE_FIRST_PAINT_HEADERS = 800','BROWSE_LARGE_PAGE_THRESHOLD = 1000'):
    check(required in server,'Frozen backend/browser value changed: '+required)
print('v3.6.85 Wanted & Interactive Search Trait Coherency Fix regression guard: PASS')
