from __future__ import annotations
import hashlib, importlib.util, json, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def digest_text(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()
def digest_bytes(data): return hashlib.sha256(data).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
server=(APP/'server.py').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
sab_text=(APP/'sab_engine.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_bytes()
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))

# v3.6.82 is a release-pipeline recovery hotfix. Runtime files must normalize
# exactly to the accepted v3.6.81 payload after removing release identity only.
def normalize_one(text,new,old,label):
    check(text.count(new)==1,f'{label}: expected exactly one {new!r}')
    return text.replace(new,old,1)
check(digest_text(normalize_one(server,'APP_VERSION = "3.6.82"','APP_VERSION = "3.6.81"','server'))=='e7cad7e4f55a52da93c8c0f6e8c50d52bd42069ccf969e86a3890077650d08d0','server.py changed beyond release identity')
check(digest_text(normalize_one(automation,"version='3.6.82'","version='3.6.81'",'automation'))=='5aba35f3de668a29713b65d8a6ce82357290b70b0653dd11519f865c01d3f237','automation_engine.py changed beyond release identity')
check(digest_text(normalize_one(sab_text,'ADAPTER_VERSION = "3.6.82"','ADAPTER_VERSION = "3.6.81"','sab'))=='43426a921519db9e0cba3c148fbcf855da6eecf4d6354969bf3cf6b7850c1ce1','sab_engine.py changed beyond release identity')
check(digest_text(normalize_one(app,"const UI_VERSION = '3.6.82';","const UI_VERSION = '3.6.81';",'app.js'))=='2bedea16c03f17914a7cd80db656d64d2a4b9ed69fd40f36f580268e76aa1d3e','app.js changed beyond release identity')
normalized_index=index.replace('3.6.82-release-pipeline-recovery','3.6.81-automation-intelligence-quality-profiles').replace('v3.6.82','v3.6.81')
check(digest_text(normalized_index)=='13fa4ced6e23cdfc94d524de60ba03f48a3eff3682e3585c512c4ff63a386e5e','index.html changed beyond release/cache identity')
check(digest_bytes(styles)=='8a8d8f0c28678a7e32aace4ec7bdac620c3a6ac8882e3c0bb8d076d48678d6ba','Quality Profile Builder stylesheet changed in pipeline-only hotfix')
check((APP/'version.txt').read_text(encoding='utf-8').strip()=='3.6.82','version.txt mismatch')
check(manifest.get('version')=='3.6.82' and manifest.get('base_version')=='3.6.81' and manifest.get('adapter_version')=='3.6.82','build-manifest version lineage mismatch')
check(manifest.get('release')=='Automation Intelligence & Quality Profiles','functional release identity changed')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')

# Re-prove the key v3.6.81 behaviors rather than trusting identity-only checks.
auto=load('newzdeck_v3682_automation_guard',APP/'automation_engine.py')
class DummyDownloadManager: pass
engine=auto.MediaAutomationEngine(Path(tempfile.mkdtemp(prefix='newzdeck-v3682-guard-')),lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.82')
profile=auto.DEFAULT_PROFILES[0]
def info(title): return auto.parse_release(title)
current=info('Show.S01E01.2160p.WEB.x265-GRP')
check(engine._is_quality_upgrade(info('Show.S01E01.2160p.WEB-DL.x265-GRP'),current['quality'],profile,current)[0],'WEB-DL must still upgrade generic WEB')
sdr=info('Show.S01E01.2160p.WEB-DL.x265-GRP'); hdr=info('Show.S01E01.2160p.WEB-DL.x265.HDR10-GRP'); dv=info('Show.S01E01.2160p.WEB-DL.x265.DV-GRP'); dvhdr=info('Show.S01E01.2160p.WEB-DL.x265.DV.HDR10-GRP')
check(engine._is_quality_upgrade(hdr,sdr['quality'],profile,sdr)[0],'HDR must still upgrade SDR')
check(engine._is_quality_upgrade(dv,hdr['quality'],profile,hdr)[0],'DV must still upgrade HDR')
check(engine._is_quality_upgrade(dvhdr,dv['quality'],profile,dv)[0],'DV+HDR must still upgrade DV-only')
check(not engine._is_quality_upgrade(info('Show.S01E01.1080p.WEB-DL.DV.HDR10-GRP'),'2160p WEB-DL',profile,sdr)[0],'dynamic range must not override lower base resolution')
for required in ('qualityProfileTemplate','qualityProfileQualityList','qualityPolicyDolbyVision','qualityPolicyDvHdr','qualityPolicyHevc','qualityPolicyAtmos'):
    check(required in app or required in index,'Structured Quality Profile Builder marker missing: '+required)
check('MEDIA_AUTOMATION.maybe_refresh_monitored_metadata()' in server,'Independent monitored metadata refresh call missing')
print('v3.6.82 release-pipeline recovery / v3.6.81 behavior regression guard: PASS')
