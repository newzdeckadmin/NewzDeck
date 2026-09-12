from __future__ import annotations
import hashlib, importlib.util, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def digest_text(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
server=(APP/'server.py').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
sab_text=(APP/'sab_engine.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')

# v3.6.82's pipeline recovery remains protected while v3.6.86 carries the
# v3.6.84/v3.6.85 Automation correctness work forward and fixes cache-read scaling.
check((APP/'version.txt').read_text().strip()=='3.6.86','current version mismatch')
check(automation.count("version='3.6.86'")==1,'Automation version identity mismatch')
check(sab_text.count('ADAPTER_VERSION = "3.6.86"')==1,'SAB adapter version identity mismatch')
check("Where-Object { $_ -like 'Source commit:*' }" in workflow and "-replace '^Source commit:\\s*',''" in workflow,'canonical Source commit parser regressed')
check('python release/windows/validate-v3682-regressions.py' in workflow and 'python release/windows/validate-v3683-regressions.py' in workflow and 'python release/windows/validate-v3684-regressions.py' in workflow and 'python release/windows/validate-v3685-regressions.py' in workflow and 'python release/windows/validate-v3686-regressions.py' in workflow,'current guard chain incomplete')

# The full v3.6.82 stylesheet is an immutable prefix; v3.6.83 may only append its reviewed suffix.
marker='/* v3.6.83 Quality Profile UI & Update Version Coherency */'
check(styles.count(marker)==1,'v3.6.83 stylesheet marker mismatch')
prefix,_=styles.split(marker,1)
check(hashlib.sha256((prefix.rstrip('\n')+'\n').encode()).hexdigest()=='8a8d8f0c28678a7e32aace4ec7bdac620c3a6ac8882e3c0bb8d076d48678d6ba','v3.6.82 stylesheet baseline changed')

# Re-prove v3.6.81 functionality that v3.6.82 intentionally carried forward.
auto=load('newzdeck_v3682_guard_current',APP/'automation_engine.py')
class DummyDownloadManager: pass
engine=auto.MediaAutomationEngine(Path(tempfile.mkdtemp(prefix='newzdeck-v3682-guard-')),lambda x:x,lambda x:x,DummyDownloadManager(),lambda:[],version='3.6.86')
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
print('v3.6.82 release-pipeline recovery / carried Automation behavior guard: PASS')
