from __future__ import annotations
import hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'; STATIC=APP/'static'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def blob(rel): return subprocess.check_output(['git','-C',str(ROOT),'rev-parse',f'HEAD:{rel}'],text=True).strip()
EXPECTED={
    'server.py':'cf095fa4af834c60d050e56e90aacbddf3d26b2e7e672e1938766725b97a17db',
    'automation_engine.py':'5880a9747dbe5ef4be2bc17685119d82155c1f688d3d10b04ee5c9b1c0513e39',
    'sab_engine.py':'56e5a089f26cfdd3a2b6e40e1838973194220687c191de14f91e1f6953be42c3',
    'static/app.js':'42f5c835e9435b7ceba0ae4664326813c803718de3c9f2dfe6430a40b87c1845',
    'static/index.html':'7c1f68a8aa7b7e6441d142592f6f198dbe8331c2e6dd5c60d4952d1d236296ad',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'static/themes.css':'2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721',
    'build-manifest.json':'623006d630ae88ec859e371561e69e46daeebc55f7c8417847015799e720e1f8',
    'version.txt':'44a1fcae929eb12521b0218135694ad3d84f616ba88ff4914fa1e8ffb45617ea',
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.96 payload')
server=(APP/'server.py').read_text(encoding='utf-8'); automation=(APP/'automation_engine.py').read_text(encoding='utf-8'); sab=(APP/'sab_engine.py').read_text(encoding='utf-8')
app=(STATIC/'app.js').read_text(encoding='utf-8'); index=(STATIC/'index.html').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
check((APP/'version.txt').read_text().strip()=='3.6.96','version.txt mismatch')
check('APP_VERSION = "3.6.96"' in server and "version='3.6.96'" in automation and 'ADAPTER_VERSION = "3.6.96"' in sab and "const UI_VERSION = '3.6.96';" in app,'release identity mismatch')
check(manifest.get('version')=='3.6.96' and manifest.get('base_version')=='3.6.95' and manifest.get('adapter_version')=='3.6.96','manifest lineage mismatch')
check(manifest.get('release')=='Library Article-Aware Sorting' and manifest.get('sab_version')=='5.1.2','manifest release/SAB identity mismatch')

# This release changes exactly one application behavior: the Automation TV/Movie
# library comparator ignores a complete leading A, An, or The for alphabetical
# placement. The title itself is never rewritten.
old_block="""function automationLibrarySortLabel(item){return String(item?.title||item?.library_title||'').trim()}\nfunction compareAutomationLibraryItems(a,b){const titleOrder=automationLibrarySortLabel(a).localeCompare(automationLibrarySortLabel(b),undefined,{sensitivity:'base',numeric:true});if(titleOrder)return titleOrder;const yearOrder=Number(a?.year||0)-Number(b?.year||0);if(yearOrder)return yearOrder;return String(a?.id||'').localeCompare(String(b?.id||''),undefined,{sensitivity:'base',numeric:true})}\n"""
new_block="""function automationLibrarySortLabel(item){return String(item?.title||item?.library_title||'').trim()}\nfunction automationLibrarySortKey(item){const label=automationLibrarySortLabel(item),withoutArticle=label.replace(/^(?:the|an|a)\\s+/i,'').trim();return withoutArticle||label}\nfunction compareAutomationLibraryItems(a,b){const options={sensitivity:'base',numeric:true},keyOrder=automationLibrarySortKey(a).localeCompare(automationLibrarySortKey(b),undefined,options);if(keyOrder)return keyOrder;const titleOrder=automationLibrarySortLabel(a).localeCompare(automationLibrarySortLabel(b),undefined,options);if(titleOrder)return titleOrder;const yearOrder=Number(a?.year||0)-Number(b?.year||0);if(yearOrder)return yearOrder;return String(a?.id||'').localeCompare(String(b?.id||''),undefined,options)}\n"""
check(app.count(new_block)==1,'article-aware Automation library comparator is missing or duplicated')
check('function renderAutomationLibrary(kind){const items=(state.automation?.library||[]).filter(x=>x.kind===kind).slice().sort(compareAutomationLibraryItems);' in app,'TV/Movie library no longer uses the shared comparator')
check('<h3>${escapeHtml(item.title)}</h3>' in app,'visible Automation library title no longer uses the original item.title')
# Replacing only the new comparator plus current UI version must reconstruct the
# exact v3.6.95 app.js, proving there is no unrelated JavaScript behavior change.
normalized=app.replace(new_block,old_block,1).replace("const UI_VERSION = '3.6.96';","const UI_VERSION = '3.6.95';",1)
check(hashlib.sha256(normalized.encode()).hexdigest()=='e43926f79258a9159b8db2cd35dea475e5ae5a4d2489762c0188f52a706551f7','app.js changed outside version identity and reviewed library comparator')

def sort_key(title):
    label=str(title or '').strip(); stripped=re.sub(r'^(?:the|an|a)\s+','',label,flags=re.I).strip(); return stripped or label
for title,expected in (
    ('A Knight of the Seven Kingdoms','Knight of the Seven Kingdoms'),
    ('The Legend of Vox Machina','Legend of Vox Machina'),
    ('An American Story','American Story'),
    ('the Last of Us','Last of Us'),
    ('Theodore','Theodore'),('Annihilation','Annihilation'),('A-Team','A-Team'),('The','The'),
): check(sort_key(title)==expected,f'article sort-key regression for {title!r}: {sort_key(title)!r}')
# Representative ordering proves both article stripping and ordinary titles mix correctly.
titles=['The Legend of Vox Machina','Severance','A Knight of the Seven Kingdoms','Barry','An American Story']
ordered=sorted(titles,key=lambda x:(sort_key(x).casefold(),x.casefold()))
check(ordered==['An American Story','Barry','A Knight of the Seven Kingdoms','The Legend of Vox Machina','Severance'],f'article-aware order mismatch: {ordered}')

# v3.6.95 theme/readability payload remains byte-for-byte frozen.
check(sha(STATIC/'styles.css')=='ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d','styles.css changed')
check(sha(STATIC/'themes.css')=='2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721','themes.css changed')
for marker in ('v3.6.95 Light Theme Readability Hotfix','--nz-overlay:var(--nz-surface-2);','--nz-scrim:'):
    check(marker in (STATIC/'themes.css').read_text(encoding='utf-8'),'v3.6.95 theme fix regressed: '+marker)
check('/themes.css?v=3.6.96-library-article-aware-sorting' in index and '/styles.css?v=3.6.96-library-article-aware-sorting' in index and '/app.js?v=3.6.96-library-article-aware-sorting' in index,'cache identity mismatch')

# Defender-sensitive native/update build architecture remains frozen to v3.6.95.
for rel,expected in {
 'src/windows/NewzDeckPicker.go':'b01efb115ab63b27278faa7c32c631305a8ffd89',
 'src/windows/NewzDeckLauncher.go':'feefee65380f4ffdca9891f7727867670bfbcadd',
 'src/windows/NewzDeckYenc.go':'38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15',
 'release/windows/build-portable.py':'5617ee744dc8ed4e51bb1b7c68bd22cfea65eb74',
 'release/windows/NewzDeck.iss':'b7c96b5721b00d468ab9582dfaa80e7f7fa2308d',
}.items(): check(blob(rel)==expected,f'protected native/update blob changed: {rel}')
check('python release/windows/validate-v3696-regressions.py' in workflow,'canonical workflow does not run v3.6.96 guard')
check("$pickerLockSource = Join-Path $env:RUNNER_TEMP 'NewzDeckPickerLockSmoke.go'" in workflow,'inert Picker-lock upgrade smoke changed')
check("-ArgumentList @('--taskbar-fix')" not in workflow,'retired Picker taskbar-fix smoke returned')
print('v3.6.96 Library Article-Aware Sorting regression guard: PASS (A/An/The ignored for TV/Movie placement; visible titles and v3.6.95 production baseline preserved).')
