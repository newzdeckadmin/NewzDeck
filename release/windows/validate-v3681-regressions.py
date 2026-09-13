from __future__ import annotations
import importlib.util, json, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
auto=load('newzdeck_v3681_automation_guard',APP/'automation_engine.py')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))

class DummyDownloadManager: pass
engine=auto.MediaAutomationEngine(Path(tempfile.mkdtemp(prefix='newzdeck-v3681-guard-')),lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.88')
profile=auto.DEFAULT_PROFILES[0]

def info(title): return auto.parse_release(title)
# Explicit WEB-DL is better than ambiguous WEB at equal resolution.
current=info('Show.S01E01.2160p.WEB.x265-GRP')
better,why=engine._is_quality_upgrade(info('Show.S01E01.2160p.WEB-DL.x265-GRP'),current['quality'],profile,current)
check(better and why=='release source improves','WEB-DL must upgrade generic WEB')
# Dynamic-range progression at identical base quality/source.
sdr=info('Show.S01E01.2160p.WEB-DL.x265-GRP')
hdr=info('Show.S01E01.2160p.WEB-DL.x265.HDR10-GRP')
dv=info('Show.S01E01.2160p.WEB-DL.x265.DV-GRP')
dvhdr=info('Show.S01E01.2160p.WEB-DL.x265.DV.HDR10-GRP')
check(engine._is_quality_upgrade(hdr,sdr['quality'],profile,sdr)[0],'HDR must upgrade SDR')
check(engine._is_quality_upgrade(dv,hdr['quality'],profile,hdr)[0],'Dolby Vision must upgrade HDR')
check(engine._is_quality_upgrade(dvhdr,dv['quality'],profile,dv)[0],'Dolby Vision + HDR fallback must upgrade DV-only')
check(engine._dynamic_range_rank(dvhdr)==0,'DV + HDR fallback must be terminal dynamic-range rank')
check(engine._quality_cutoff_met(dvhdr['quality'],profile,dvhdr),'DV + HDR at base cutoff should satisfy terminal 4K Preferred cutoff')
# HDR/DV can never override a worse base tier.
check(not engine._is_quality_upgrade(info('Show.S01E01.1080p.WEB-DL.DV.HDR10-GRP'),'2160p WEB-DL',profile,sdr)[0],'1080p DV must not replace 2160p SDR')
# Structured hard policy gates are enforced.
avoid_dv={**profile,'trait_policies':{'dynamic_range':{'dolby_vision':'avoid'},'video_codec':{},'audio':{}},'upgrade_dynamic_range':True}
ev=engine._evaluate_release('Show.S01E01.2160p.WEB-DL.DV.HDR10-GRP',8*1024**3,avoid_dv,item={'kind':'tv','title':'Show','seasons':[]},season=1,episode=1,current_quality='Unknown')
check(any('avoids dolby vision' in x for x in ev['rejections']),'Structured Avoid policy not enforced')
# Metadata maintenance must be independent of automatic grabbing in service loop.
metadata_call='MEDIA_AUTOMATION.maybe_refresh_monitored_metadata()'; auto_call='MEDIA_AUTOMATION.maybe_run_automatic()'
check(metadata_call in server and auto_call in server,'Service loop metadata/automation calls missing')
loop=server[server.find('if time.time()-self.last_media_auto_check'):server.find('# Download Engine v2.')]
check(loop.find(metadata_call)>=0 and loop.find(metadata_call)<loop.find(auto_call),'Metadata refresh must run independently before automatic-grab worker')
# Structured profile builder surface is present and old raw default is gone.
for required in ('QUALITY_CATALOG=[','qualityProfileTemplate','qualityProfileQualityList','qualityPolicyDolbyVision','qualityPolicyDvHdr','qualityPolicyHevc','qualityPolicyAtmos','upgrade_dynamic_range','prefer_proper_repack'):
    check(required in app or required in index,'Quality Profile Builder marker missing: '+required)
check("['2160p','1080p','720p','WEB']" not in app,'Primitive raw quality defaults returned')
for required in ('quality-profile-modal-card','quality-ladder-row','quality-policy-grid','quality-profile-summary'):
    check(required in styles,'Quality Profile Builder stylesheet marker missing: '+required)
check(manifest.get('release')=='Smart Import Wanted Reconciliation Fix','Release manifest name mismatch')
print('v3.6.88 Automation Intelligence & Quality Profiles regression guard: PASS')
