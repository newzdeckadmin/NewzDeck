from __future__ import annotations
import re
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
    'server.py':'cf095fa4af834c60d050e56e90aacbddf3d26b2e7e672e1938766725b97a17db',
    'automation_engine.py':'5880a9747dbe5ef4be2bc17685119d82155c1f688d3d10b04ee5c9b1c0513e39',
    'sab_engine.py':'56e5a089f26cfdd3a2b6e40e1838973194220687c191de14f91e1f6953be42c3',
    'static/app.js':'42f5c835e9435b7ceba0ae4664326813c803718de3c9f2dfe6430a40b87c1845',
    'static/index.html':'7c1f68a8aa7b7e6441d142592f6f198dbe8331c2e6dd5c60d4952d1d236296ad',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'build-manifest.json':'623006d630ae88ec859e371561e69e46daeebc55f7c8417847015799e720e1f8',
    'version.txt':'44a1fcae929eb12521b0218135694ad3d84f616ba88ff4914fa1e8ffb45617ea',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.96 payload')

auto=load('newzdeck_v3686_automation_guard',APP/'automation_engine.py')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
_THEME_COLOR_FALLBACK=re.compile(r'var\(--nz-[a-z0-9-]+,(#[0-9a-fA-F]{3,8}|rgba?\([^()]*\)|white)\)')
styles=_THEME_COLOR_FALLBACK.sub(lambda m:m.group(1),styles)
check(hashlib.sha256(styles.encode('utf-8')).hexdigest()=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','v3.6.96 Night fallback reconstruction does not preserve the exact v3.6.93 stylesheet for this carried-forward guard')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.96','version.txt mismatch')
check('APP_VERSION = "3.6.96"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.96';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.96' and manifest.get('base_version')=='3.6.95' and manifest.get('adapter_version')=='3.6.96','build manifest lineage mismatch')
check(manifest.get('release')=='Library Article-Aware Sorting','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')
check('v=3.6.96-library-article-aware-sorting' in index,'v3.6.87 asset cache identity missing')
check(hashlib.sha256(styles.encode('utf-8')).hexdigest()=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','frozen stylesheet changed')

# The fix must be structural: callers may provide one cache snapshot and one
# already-resolved current-file trait view to every candidate evaluation.
for required in (
    "def _record_release_info(self, rec:dict[str,Any]|None, current_quality:str='Unknown', quality_cache:dict[str,Any]|None=None)",
    "def _current_target_release_info(self, item:dict[str,Any]|None, season=None, episode=None, current_quality:str='Unknown', quality_cache:dict[str,Any]|None=None)",
    "def _auto_release_matches(self, item:dict[str,Any], row:dict[str,Any], release:dict[str,Any], profile:dict[str,Any], *, upgrade:bool=False, current_info:dict[str,Any]|None=None)",
    "def _evaluate_release(self, title:str, size:int, profile:dict[str,Any], *, item:dict[str,Any]|None=None, season=None, episode=None, current_quality:str='Unknown', current_info:dict[str,Any]|None=None)",
    'wanted=self.wanted(quality_cache)',
    'calendar=self.calendar(quality_cache=quality_cache)',
    'self._decorate_live_cutoff_flags(lib,profiles,quality_cache)',
    'current_info=self._current_target_release_info(item,season,episode,current_quality,quality_cache)',
    'current_info=current_info)',
):
    check(required in automation,'v3.6.87 snapshot reuse marker missing: '+required)

class DummyDownloadManager: pass
root=Path(tempfile.mkdtemp(prefix='newzdeck-v3686-guard-'))
engine=auto.MediaAutomationEngine(root,lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.96')
p4=copy.deepcopy(auto.DEFAULT_PROFILES[0]); p1080=copy.deepcopy(auto.DEFAULT_PROFILES[1])

# v3.6.87 evidence authority remains intact before measuring performance behavior.
candidate_title='Dark.Matter.2024.S02E02.A.Perfect.World.2160p.ATVP.WEB-DL.DDP5.1.Atmos.DV.HDR.HEVC-GRP'
candidate=auto.parse_release(candidate_title)
terminal_rec={
    'episode_number':2,'name':'A Perfect World','air_date':'2020-01-01','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL','file_fingerprint':'terminal-fp',
    'media_info':{'quality':'2160p WEB-DL','dolby_vision':True,'hdr10_plus':False,'hdr_present':True,'hdr':'Dolby Vision + HDR'},
}
terminal_item={'id':'terminal','kind':'tv','title':'Dark Matter','year':2024,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':2,'monitored':True,'episodes':[terminal_rec]}]}
qterminal={'terminal-fp':{'quality':'2160p WEB-DL','source':'newzdeck-import','release_title':'Dark.Matter.2024.S02E02.2160p.ATVP.WEB-DL.DV.HEVC-PROVENANCE'}}
terminal_info=engine._record_release_info(terminal_rec,'2160p WEB-DL',qterminal)
check(engine._dynamic_range_rank(terminal_info)==0,'Successful media probe did not preserve terminal DV+HDR state')
check(engine._quality_upgrade_status('2160p WEB-DL',p4,terminal_info).get('wanted') is False,'Already-terminal DV+HDR file remains falsely Wanted')
true_dv_rec={
    'episode_number':2,'name':'A Perfect World','air_date':'2020-01-01','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL',
    'media_info':{'quality':'2160p WEB-DL','dolby_vision':True,'hdr10_plus':False,'hdr_present':False,'hdr':'Dolby Vision'},
}
true_dv_item={'id':'true-dv','kind':'tv','title':'Dark Matter','year':2024,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':2,'monitored':True,'episodes':[true_dv_rec]}]}
true_dv_info=engine._record_release_info(true_dv_rec,'2160p WEB-DL',{})
better,why=engine._is_quality_upgrade(candidate,'2160p WEB-DL',p4,true_dv_info)
check(better and why=='dynamic range improves','DV+HDR no longer upgrades true DV-only current media')
true_eval=engine._evaluate_release(candidate_title,12*1024**3,p4,item=true_dv_item,season=2,episode=2,current_quality='2160p WEB-DL',current_info=true_dv_info)
check(true_eval.get('accepted'),'DV+HDR candidate should remain eligible against true DV-only current media')
check(engine._dynamic_range_upgrade_target(p1080) is None,'1080p Balanced Allow policy regressed')

# Health is a separate UI endpoint and must also own exactly one snapshot rather
# than referencing a summary-local variable or re-reading per Wanted record.
health_engine=auto.MediaAutomationEngine(Path(tempfile.mkdtemp(prefix='newzdeck-v3686-health-')),lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.96')
health_engine._library=lambda:[]
health_engine.public_config=lambda:{'tv_roots':[],'movie_roots':[],'automatic_grab_enabled':False,'automatic_feed_enabled':True}
health_engine.public_indexers=lambda:[]
health_engine._auto_runtime=lambda:{'targets':{},'indexer_health':{}}
health_engine._auto_active_targets=lambda:[]
health_reads={'n':0}
def read_health_cache():
    health_reads['n']+=1
    return {}
health_engine._media_quality_cache=read_health_cache
health_engine.automation_health()
check(health_reads['n']==1,f'Automation Health read media quality cache {health_reads["n"]} times instead of once')

# Production symptom 1: the complete Automation summary used to reread the same
# media-quality-cache.json once per existing episode across several surfaces.
# Hundreds of records must now consume exactly one caller-owned snapshot.
episodes=[]; summary_cache={}
for n in range(1,181):
    fp=f'summary-fp-{n}'
    rec={
        'episode_number':n,'name':f'Episode {n}','air_date':'2020-01-01','monitored':True,
        'has_file':True,'file_quality':'2160p WEB-DL','file_fingerprint':fp,
        'media_info':({'quality':'2160p WEB-DL','dolby_vision':True,'hdr10_plus':False,'hdr_present':True,'hdr':'Dolby Vision + HDR'} if n%2 else {'quality':'2160p WEB-DL','dolby_vision':True,'hdr10_plus':False,'hdr_present':False,'hdr':'Dolby Vision'}),
    }
    episodes.append(rec)
    # Provenance deliberately disagrees with some actual files. v3.6.87 must keep
    # the one-snapshot performance fix while using successful media evidence.
    summary_cache[fp]={'quality':'2160p WEB-DL','release_title':f'Perf.Show.S01E{n:03d}.2160p.WEB-DL.DV.HEVC-PROVENANCE'}
summary_item={'id':'perf','kind':'tv','title':'Perf Show','year':2026,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':1,'monitored':True,'episodes':episodes}]}
engine._library=lambda:[copy.deepcopy(summary_item)]
engine._profiles=lambda:[copy.deepcopy(p4)]
engine.public_config=lambda:{
    'automatic_grab_enabled':False,'automatic_backlog_enabled':False,'automatic_upgrades_enabled':False,
    'automatic_season_packs_enabled':True,'automatic_feed_enabled':True,'automatic_feed_interval_minutes':5,
    'automatic_smart_retry_enabled':True,'automatic_quiet_hours_enabled':False,'automatic_quiet_start':'01:00','automatic_quiet_end':'07:00',
    'automatic_notifications_enabled':False,'automatic_search_interval_minutes':15,'automatic_retry_minutes':60,
    'automatic_release_delay_minutes':5,'automatic_queue_depth':25,'automatic_metadata_refresh_hours':6,
    'automatic_library_scan_minutes':30,'automatic_movie_availability':'digital_physical','tv_roots':[],'movie_roots':[],
}
engine.public_indexers=lambda:[]
engine._activity=lambda:[]
engine.automatic_status=lambda:{'enabled':False,'running':False}
engine.automation_health=lambda:{'roots':[],'blacklists':[]}
engine.storage_health_snapshot=lambda:{'roots':[],'low_roots':[]}
summary_reads={'n':0}
def read_summary_cache():
    summary_reads['n']+=1
    return summary_cache
engine._media_quality_cache=read_summary_cache
summary=engine.summary()
check(summary_reads['n']==1,f'Automation summary reread media quality cache {summary_reads["n"]} times for 180 records')
check(len(summary.get('wanted',{}).get('upgrades') or [])==90,'Summary snapshot changed expected terminal/DV-only classification')

# Production symptom 2: Interactive Search used to call the resolver again for
# every candidate during both score evaluation and automatic-eligibility checks.
# A 220-candidate search must resolve current traits from exactly one cache read.
search_current={
    'episode_number':1,'name':'Pilot','air_date':'2020-01-01','monitored':True,
    'has_file':True,'file_quality':'2160p WEB-DL','file_fingerprint':'search-fp',
    'media_info':{'quality':'2160p WEB-DL','dolby_vision':True,'hdr10_plus':False,'hdr_present':False,'hdr':'Dolby Vision'},
}
search_item={'id':'his-hers','kind':'tv','title':'His and Hers','year':2026,'monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':1,'monitored':True,'episodes':[search_current]}]}
engine._library=lambda:[copy.deepcopy(search_item)]
engine._profiles=lambda:[copy.deepcopy(p4)]
engine._indexers=lambda:[{'id':'synthetic','name':'Synthetic','enabled':True}]
rows=[]
for n in range(220):
    rows.append({
        'title':f'His.and.Hers.S01E01.2160p.WEB-DL.DV.HDR.HEVC-GRP{n:03d}',
        'size':12*1024**3,'guid':f'guid-{n}','download_url':f'https://example.invalid/{n}',
        'published':time.time()-86400,'indexer':'Synthetic',
    })
engine._search_indexer=lambda idx,item,season,episode:copy.deepcopy(rows)
engine._auto_runtime=lambda:{'targets':{}}
engine._save_auto_runtime=lambda value:None
engine._sync_automatic_failures=lambda value:False
search_reads={'n':0}
search_cache={'search-fp':{'quality':'2160p WEB-DL','release_title':'His.and.Hers.S01E01.2160p.WEB-DL.DV.HDR.HEVC-PROVENANCE'}}
def read_search_cache():
    search_reads['n']+=1
    return search_cache
engine._media_quality_cache=read_search_cache
result=engine.search_releases('his-hers',1,1)
check(search_reads['n']==1,f'Interactive Search reread media quality cache {search_reads["n"]} times for 220 candidates')
check(len(result.get('releases') or [])==220,'Synthetic Interactive Search candidate count changed')
eligible=[r for r in result.get('releases') or [] if r.get('accepted')]
check(eligible,'Interactive Search lost all valid DV+HDR candidates')
check(all(any('dynamic range improves' in str(x) for x in r.get('reasons') or []) for r in eligible),'Eligible candidates lost dynamic-range improvement explanation')

# Frozen runtime/release-engineering boundaries remain explicit.
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
print('v3.6.86 Automation Cache Snapshot Performance Hotfix carried-forward guard under v3.6.96: PASS')
