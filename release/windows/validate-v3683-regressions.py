from __future__ import annotations
import ast, hashlib, json, re, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py':'115b49c5c656e5d9366746d6adba166a0fc8d3770d6b33847aff48c4dc570e4f',
    'automation_engine.py':'67da05374cb70a305ccafd3251ce27a806f9521bfb211ce657596ae7708b0098',
    'sab_engine.py':'7c84060a3316a014bd859d54f46606f1a3b2f94d4df34f5297a22078d4d5f75e',
    'static/app.js':'5d9400336a87c0503ef7a1e15cfdea744c1ea0865be37f0c6a1cf3ed666c9e11',
    'static/index.html':'d77a224e530a4fa8cbfecad88db14321255729adf843feb4fb0e7186e656ea5d',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'build-manifest.json':'36fd81bfb09be9b1ae23225520719010a43601b60f8467d13e89cd07b06223ac',
    'version.txt':'7d1e1967d448824bd388968ce6c1665293b9be823deae8e870a46963874fd903',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.99 carried-forward payload')
server=(APP/'server.py').read_text(encoding='utf-8')
app=(APP/'static'/'app.js').read_text(encoding='utf-8')
index=(APP/'static'/'index.html').read_text(encoding='utf-8')
styles=(APP/'static'/'styles.css').read_text(encoding='utf-8')
_THEME_COLOR_FALLBACK=re.compile(r'var\(--nz-[a-z0-9-]+,(#[0-9a-fA-F]{3,8}|rgba?\([^()]*\)|white)\)')
styles=_THEME_COLOR_FALLBACK.sub(lambda m:m.group(1),styles)
check(hashlib.sha256(styles.encode('utf-8')).hexdigest()=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','v3.6.99 Night fallback reconstruction does not preserve the exact v3.6.93 stylesheet for this carried-forward guard')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
check((APP/'version.txt').read_text().strip()=='3.6.99','version.txt mismatch')
check(manifest.get('version')=='3.6.99' and manifest.get('base_version')=='3.6.96' and manifest.get('adapter_version')=='3.6.99','build manifest lineage mismatch')
check(manifest.get('release')=='Final UX & Backup/Restore','release identity mismatch')
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
ns={'re':re,'Any':object,'APP_VERSION':'3.6.99','installed_version':lambda:'3.6.99'}
exec(compile(mod,'<v3683-version-helpers>','exec'),ns)
check(ns['_update_available_for']('3.6.99','3.6.99') is False,'same-version release was incorrectly treated as an update')
check(ns['_update_available_for']('3.7.0','3.6.99') is True,'newer release was not treated as an update')
check(ns['_update_available_for']('3.6.92','3.6.99') is False,'older release was incorrectly treated as an update')
check(ns['_update_cache_matches_install']({'current_version':'3.6.92'},'3.6.99') is False,'old-version update cache accepted')
check(ns['_update_cache_matches_install']({'installed_version':'3.6.99'},'3.6.99') is True,'current-version update cache rejected')

# v3.6.81 functional behavior remains present and release pipeline remains canonical.
for required in ('MEDIA_AUTOMATION.maybe_refresh_monitored_metadata()','MEDIA_AUTOMATION.maybe_run_automatic()'):
    check(required in server,'Automation service-loop behavior missing: '+required)
check(server.find('MEDIA_AUTOMATION.maybe_refresh_monitored_metadata()') < server.find('MEDIA_AUTOMATION.maybe_run_automatic()'),'metadata refresh no longer precedes automatic grab')
for required in ("Where-Object { $_ -like 'Source commit:*' }","-replace '^Source commit:\\s*',''",'python release/windows/validate-v3683-regressions.py','python release/windows/validate-v3684-regressions.py','python release/windows/validate-v3685-regressions.py','python release/windows/validate-v3686-regressions.py'):
    check(required in workflow,'Canonical release workflow marker missing: '+required)
print('v3.6.83 Quality Profile UI & Update Version Coherency carried-forward guard under v3.6.99: PASS')
