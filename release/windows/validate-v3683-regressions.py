from __future__ import annotations
import ast, hashlib, json, re, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'3d45cec7ab9d836a7ff2cadc5ed8f8caab75e911aece19acd729e79d2c6bf7e5',
    'automation_engine.py':'eba353ca751ec259262918444f7d96e0a04262ffc9c8ca934e438e9ba702478e',
    'sab_engine.py':'262406b082712c73ffcce8b30d0de15247d9e5a93b6fb82c7132ad7db22e3680',
    'static/app.js':'2d41baf1935dc99015d4c401c2bdd610b4486477ee3429abca808af4eb5dfb54',
    'static/index.html':'53259051490170fa79acf0b11454d1b96f5049e79ea7a6a690f1319f05559183',
    'static/styles.css':'ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2',
    'build-manifest.json':'2d06e148b86ee2da4cf98f0e3f0caa099efb5e8294ab66e01b31df4cb07cb519',
    'version.txt':'428801e7d19029d5cacd7d5f906a4c329d88b4b3efa3eaeee183b9cf5aec3d40',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.87 carried-forward payload')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
check((APP/'version.txt').read_text().strip()=='3.6.87','version.txt mismatch')
check(manifest.get('version')=='3.6.87' and manifest.get('base_version')=='3.6.86' and manifest.get('adapter_version')=='3.6.87','build manifest lineage mismatch')
check(manifest.get('release')=='Dynamic Range Evidence Authority Fix','release identity mismatch')
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
ns={'re':re,'Any':object,'APP_VERSION':'3.6.87','installed_version':lambda:'3.6.87'}
exec(compile(mod,'<v3683-version-helpers>','exec'),ns)
check(ns['_update_available_for']('3.6.87','3.6.87') is False,'same-version release was incorrectly treated as an update')
check(ns['_update_available_for']('3.6.88','3.6.87') is True,'newer release was not treated as an update')
check(ns['_update_available_for']('3.6.86','3.6.87') is False,'older release was incorrectly treated as an update')
check(ns['_update_cache_matches_install']({'current_version':'3.6.86'},'3.6.87') is False,'old-version update cache accepted')
check(ns['_update_cache_matches_install']({'installed_version':'3.6.87'},'3.6.87') is True,'current-version update cache rejected')

# v3.6.81 functional behavior remains present and release pipeline remains canonical.
for required in ('MEDIA_AUTOMATION.maybe_refresh_monitored_metadata()','MEDIA_AUTOMATION.maybe_run_automatic()'):
    check(required in server,'Automation service-loop behavior missing: '+required)
check(server.find('MEDIA_AUTOMATION.maybe_refresh_monitored_metadata()') < server.find('MEDIA_AUTOMATION.maybe_run_automatic()'),'metadata refresh no longer precedes automatic grab')
for required in ("Where-Object { $_ -like 'Source commit:*' }","-replace '^Source commit:\\s*',''",'python release/windows/validate-v3683-regressions.py','python release/windows/validate-v3684-regressions.py','python release/windows/validate-v3685-regressions.py','python release/windows/validate-v3686-regressions.py'):
    check(required in workflow,'Canonical release workflow marker missing: '+required)
print('v3.6.83 Quality Profile UI & Update Version Coherency carried-forward guard under v3.6.87: PASS')
