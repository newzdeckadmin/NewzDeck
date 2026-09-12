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
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.85 carried-forward payload')

auto=load('newzdeck_v3684_automation_guard',APP/'automation_engine.py')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))

check((APP/'version.txt').read_text().strip()=='3.6.85','version.txt mismatch')
check('APP_VERSION = "3.6.85"' in server,'server version mismatch')
check("const UI_VERSION = '3.6.85';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.85' and manifest.get('base_version')=='3.6.84' and manifest.get('adapter_version')=='3.6.85','build manifest lineage mismatch')
check(manifest.get('release')=='Wanted & Interactive Search Trait Coherency Fix','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')

class DummyDownloadManager: pass
root=Path(tempfile.mkdtemp(prefix='newzdeck-v3684-guard-'))
engine=auto.MediaAutomationEngine(root,lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.85')
p4=auto.DEFAULT_PROFILES[0]; p1080=auto.DEFAULT_PROFILES[1]
def info(title): return auto.parse_release(title)

# Allow is acceptable, not a hidden terminal upgrade requirement.
sdr1080=info('Show.S01E01.1080p.WEB-DL.x264-GRP')
hdr1080=info('Show.S01E01.1080p.WEB-DL.HDR10.x264-GRP')
check(engine._dynamic_range_upgrade_target(p1080) is None,'1080p Balanced Allow policies incorrectly create a dynamic-range target')
check(engine._quality_cutoff_met(sdr1080['quality'],p1080,sdr1080),'1080p Balanced SDR WEB-DL should meet cutoff')
check(not engine._is_quality_upgrade(hdr1080,sdr1080['quality'],p1080,sdr1080)[0],'Allow-only HDR must not create an automatic upgrade')

# Explicit Prefer policies retain the v3.6.81 dynamic-range progression.
sdr=info('Show.S01E01.2160p.WEB-DL.x265-GRP')
hdr=info('Show.S01E01.2160p.WEB-DL.x265.HDR10-GRP')
dv=info('Show.S01E01.2160p.WEB-DL.x265.DV-GRP')
dvhdr=info('Show.S01E01.2160p.WEB-DL.x265.DV.HDR10-GRP')
check(engine._dynamic_range_upgrade_target(p4)==0,'4K Preferred terminal dynamic-range target changed')
check(engine._is_quality_upgrade(hdr,sdr['quality'],p4,sdr)[0],'HDR must upgrade SDR for 4K Preferred')
check(engine._is_quality_upgrade(dv,hdr['quality'],p4,hdr)[0],'Dolby Vision must upgrade HDR for 4K Preferred')
check(engine._is_quality_upgrade(dvhdr,dv['quality'],p4,dv)[0],'DV+HDR fallback must upgrade DV-only for 4K Preferred')
check(engine._quality_cutoff_met(dvhdr['quality'],p4,dvhdr),'DV+HDR at 4K Preferred cutoff must be terminal')

# Same base label must produce a trait explanation, never X has not reached X.
state=engine._quality_upgrade_status(sdr['quality'],p4,sdr)
check(state.get('wanted') and state.get('reason_code')=='dynamic_range_upgrade','4K SDR should be a preferred dynamic-range upgrade')
check(state.get('reason_label')=='Preferred dynamic range upgrade','dynamic-range Wanted label mismatch')
check(state.get('upgrade_path')=='Dynamic range: SDR → Dolby Vision + HDR fallback','dynamic-range upgrade path mismatch')
check('has not reached 2160p WEB-DL' not in str(state.get('reason_detail') or ''),'same-quality contradiction returned for dynamic-range upgrade')

# Generic WEB remains a source upgrade when cutoff asks for explicit WEB-DL.
generic=info('Show.S01E01.2160p.WEB.x265.DV.HDR10-GRP')
source_state=engine._quality_upgrade_status('2160p WEB-DL',p4,generic)
check(source_state.get('wanted') and source_state.get('reason_code')=='release_source_upgrade','generic WEB should remain upgradeable to explicit WEB-DL')
check(source_state.get('upgrade_path')=='Source: 2160p WEB → 2160p WEB-DL','source upgrade path mismatch')
check('has not reached 2160p WEB-DL' not in str(source_state.get('reason_detail') or ''),'same-quality contradiction returned for source upgrade')

# A genuine base-quality miss still uses the cutoff explanation.
low=info('Show.S01E01.1080p.WEBRip.x264-GRP')
low_state=engine._quality_upgrade_status(low['quality'],p4,low)
check(low_state.get('wanted') and low_state.get('reason_code')=='quality_below_cutoff','base-quality miss no longer classified correctly')
check('has not reached 2160p WEB-DL' in str(low_state.get('reason_detail') or ''),'base-quality cutoff detail missing')

# Reproduce the Watched/Wanted regression with persisted library rows.
library=[
 {'id':'balanced','kind':'tv','title':'Balanced Show','monitored':True,'monitor_mode':'all','quality_profile_id':'quality-1080p','seasons':[{'season_number':1,'monitored':True,'episodes':[{'episode_number':1,'name':'Episode 1','air_date':'2020-01-01','monitored':True,'has_file':True,'file_quality':'1080p WEB-DL','release_traits':sdr1080,'cutoff_met':False}]}]},
 {'id':'preferred','kind':'tv','title':'Preferred Show','monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':1,'monitored':True,'episodes':[{'episode_number':1,'name':'Episode 1','air_date':'2020-01-01','monitored':True,'has_file':True,'file_quality':'2160p WEB-DL','release_traits':sdr,'cutoff_met':False}]}]},
 {'id':'source','kind':'tv','title':'Source Show','monitored':True,'monitor_mode':'all','quality_profile_id':'quality-4k-preferred','seasons':[{'season_number':1,'monitored':True,'episodes':[{'episode_number':1,'name':'Episode 1','air_date':'2020-01-01','monitored':True,'has_file':True,'file_quality':'2160p WEB-DL','release_traits':generic,'cutoff_met':False}]}]},
]
(root/'media-library.json').write_text(json.dumps(library),encoding='utf-8')
wanted=engine.wanted(); upgrades={x.get('item_id'):x for x in wanted.get('upgrades') or []}
check('balanced' not in upgrades,'1080p Balanced false upgrade still appears in Wanted')
check(upgrades.get('preferred',{}).get('reason_code')=='dynamic_range_upgrade','Wanted did not surface dynamic-range reason')
check(upgrades.get('source',{}).get('reason_code')=='release_source_upgrade','Wanted did not surface source reason')
for row in upgrades.values():
    q=str(row.get('current_quality') or ''); cutoff=str(row.get('cutoff') or '')
    if q==cutoff:
        check(f'Current {q} has not reached {cutoff}' not in str(row.get('reason_detail') or ''),'Wanted emitted identical-quality contradiction')

# Live snapshot decoration corrects stale persisted cutoff flags without waiting for scan.
loaded=engine._library(); engine._decorate_live_cutoff_flags(loaded,engine._profiles())
bal_ep=loaded[0]['seasons'][0]['episodes'][0]
check(bal_ep.get('cutoff_met') is True,'live cutoff decoration did not repair stale Balanced flag')

# Frontend must render the backend's explicit upgrade path and use non-misleading copy.
for required in ("x.upgrade_path||`Current:","Quality upgrade wanted","profile-approved upgrade path"):
    check(required in app,'Wanted UI regression marker missing: '+required)
check("const current=type==='upgrade'?`<span class=\"wanted-current\">Current: ${escapeHtml(x.current_quality" not in app,'old unconditional Wanted current/cutoff renderer remains')
check('v=3.6.85-wanted-search-trait-coherency-fix' in index,'carried current asset cache identity missing')

# Frozen areas are intentionally untouched by this release.
check('image_thumb_http_admission' not in manifest.get('release','').casefold(),'unexpected browser tuning scope')
print('v3.6.84 Wanted Upgrade Reasoning & Cutoff Policy Fix carried-forward guard under v3.6.85: PASS')
