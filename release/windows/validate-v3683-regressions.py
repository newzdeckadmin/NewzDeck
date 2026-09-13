from __future__ import annotations
import ast, hashlib, json, re, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
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
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.90 carried-forward payload')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
check((APP/'version.txt').read_text().strip()=='3.6.90','version.txt mismatch')
check(manifest.get('version')=='3.6.90' and manifest.get('base_version')=='3.6.89' and manifest.get('adapter_version')=='3.6.90','build manifest lineage mismatch')
check(manifest.get('release')=='Windows Defender Picker Compatibility & Release Gate Hardening','release identity mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')

# Preserve the accepted v3.6.82 stylesheet exactly, then own only the reviewed v3.6.83 suffix.
marker='/* v3.6.83 Quality Profile UI & Update Version Coherency */'
check(styles.count(marker)==1,'v3.6.83 stylesheet marker count mismatch')
prefix,suffix=styles.split(marker,1)
base=(prefix.rstrip('\n')+'\n').encode('utf-8')
check(hashlib.sha256(base).hexdigest()=='8a8d8f0c28678a7e32aace4ec7bdac620c3a6ac8882e3c0bb8d076d48678d6ba','pre-v3.6.83 stylesheet baseline changed')
for required in ('quality-profile-scroll','quality-profile-actions','grid-template-rows:auto minmax(0,1fr) auto','scrollbar-gutter:stable','quality-profile-footer-note'):
    check(required in suffix,'Quality Profile layout marker missing: '+required)

# About must be dynamic; the stale historical label must never return.
check('NewzDeck v3.6.62' not in index,'About still contains stale v3.6.62 identity')
for required in ('id="aboutVersion"','id="aboutRuntimeVersion"','id="qualityProfileModal"','class="quality-profile-scroll"','quality-profile-actions'):
    check(required in index,'About/Profile DOM marker missing: '+required)
for required in ('qualityProfileTemplate','qualityProfileQualityList','qualityPolicyDolbyVision','qualityPolicyDvHdr','qualityPolicyHevc','qualityPolicyAtmos','qualityProfileProperRepack'):
    check(required in index or required in app,'Structured Quality Profile control missing: '+required)

# Browser update safety must independently reject same-version offers.
for required in ('function compareUpdateVersions','effectiveCurrent=compareUpdateVersions(installed,UI_VERSION)>=0?installed:UI_VERSION','const available=compareUpdateVersions(latest,effectiveCurrent)>0','Runtime restart required','state.onlineUpdate={...d'):
    check(required in app,'Frontend update coherency marker missing: '+required)

# Backend update authority must come from version.txt and caches must be install-version coherent.
for required in ('def installed_version() -> str:','(APP_DIR / "version.txt").read_text','def _update_available_for(','def _update_cache_matches_install(','cache_coherent = _update_cache_matches_install(cached, installed)','"installed_version": installed','"runtime_version": APP_VERSION','"runtime_mismatch": runtime_mismatch'):
    check(required in server,'Backend update coherency marker missing: '+required)

# Execute only the pure version helpers from server.py to prove same-version and cache semantics.
tree=ast.parse(server)
selected=[]
for node in tree.body:
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in {'_version_tuple','_update_available_for','_update_cache_matches_install'}:
        selected.append(node)
mod=ast.Module(body=selected,type_ignores=[]); ast.fix_missing_locations(mod)
ns={'re':re,'Any':object,'APP_VERSION':'3.6.90','installed_version':lambda:'3.6.90'}
exec(compile(mod,'<v3683-version-helpers>','exec'),ns)
check(ns['_update_available_for']('3.6.90','3.6.90') is False,'same-version release was incorrectly treated as an update')
check(ns['_update_available_for']('3.6.91','3.6.90') is True,'newer release was not treated as an update')
check(ns['_update_available_for']('3.6.89','3.6.90') is False,'older release was incorrectly treated as an update')
check(ns['_update_cache_matches_install']({'current_version':'3.6.89'},'3.6.90') is False,'old-version update cache accepted')
check(ns['_update_cache_matches_install']({'installed_version':'3.6.90'},'3.6.90') is True,'current-version update cache rejected')

# v3.6.81 functional behavior remains present and release pipeline remains canonical.
for required in ('MEDIA_AUTOMATION.maybe_refresh_monitored_metadata()','MEDIA_AUTOMATION.maybe_run_automatic()'):
    check(required in server,'Automation service-loop behavior missing: '+required)
check(server.find('MEDIA_AUTOMATION.maybe_refresh_monitored_metadata()') < server.find('MEDIA_AUTOMATION.maybe_run_automatic()'),'metadata refresh no longer precedes automatic grab')
for required in ("Where-Object { $_ -like 'Source commit:*' }","-replace '^Source commit:\\s*',''",'python release/windows/validate-v3683-regressions.py','python release/windows/validate-v3684-regressions.py','python release/windows/validate-v3685-regressions.py','python release/windows/validate-v3686-regressions.py'):
    check(required in workflow,'Canonical release workflow marker missing: '+required)
print('v3.6.83 Quality Profile UI & Update Version Coherency carried-forward guard under v3.6.90: PASS')
