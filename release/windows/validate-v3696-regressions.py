from __future__ import annotations
import hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'; STATIC=APP/'static'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def blob(rel): return subprocess.check_output(['git','-C',str(ROOT),'rev-parse',f'HEAD:{rel}'],text=True).strip()
server=(APP/'server.py').read_text(encoding='utf-8'); automation=(APP/'automation_engine.py').read_text(encoding='utf-8'); sab=(APP/'sab_engine.py').read_text(encoding='utf-8')
app=(STATIC/'app.js').read_text(encoding='utf-8'); index=(STATIC/'index.html').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
check((APP/'version.txt').read_text().strip()=='3.6.99','current version mismatch')
check('APP_VERSION = "3.6.99"' in server and "version='3.6.99'" in automation and 'ADAPTER_VERSION = "3.6.99"' in sab and "const UI_VERSION = '3.6.99';" in app,'release identity mismatch')
check(manifest.get('version')=='3.6.99' and manifest.get('base_version')=='3.6.96' and manifest.get('adapter_version')=='3.6.99','manifest lineage mismatch')

# v3.6.96 article-aware Automation ordering remains active while the original
# visible title is preserved.
check('function automationLibrarySortKey(item)' in app,'article-aware sort helper missing')
check(r"replace(/^(?:the|an|a)\s+/i,'')" in app,'A/An/The sort-key rule changed')
check('function renderAutomationLibrary(kind){const items=(state.automation?.library||[]).filter(x=>x.kind===kind).slice().sort(compareAutomationLibraryItems);' in app,'TV/Movie library no longer uses shared comparator')
check('<h3>${escapeHtml(item.title)}</h3>' in app,'visible title rendering changed')
def sort_key(title):
    label=str(title or '').strip(); stripped=re.sub(r'^(?:the|an|a)\s+','',label,flags=re.I).strip(); return stripped or label
for title,expected in (
    ('A Knight of the Seven Kingdoms','Knight of the Seven Kingdoms'),('The Legend of Vox Machina','Legend of Vox Machina'),
    ('An American Story','American Story'),('Theodore','Theodore'),('Annihilation','Annihilation'),('A-Team','A-Team'),('The','The'),
): check(sort_key(title)==expected,f'article sort-key regression: {title!r}')

# Themes/readability remain frozen.
check(sha(STATIC/'styles.css')=='ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d','styles.css changed')
check(sha(STATIC/'themes.css')=='2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721','themes.css changed')
for marker in ('v3.6.95 Light Theme Readability Hotfix','--nz-overlay:var(--nz-surface-2);','--nz-scrim:'):
    check(marker in (STATIC/'themes.css').read_text(encoding='utf-8'),'theme fix regressed: '+marker)

# Defender-sensitive native/update architecture remains frozen.
for rel,expected in {
 'src/windows/NewzDeckPicker.go':'b01efb115ab63b27278faa7c32c631305a8ffd89',
 'src/windows/NewzDeckLauncher.go':'feefee65380f4ffdca9891f7727867670bfbcadd',
 'src/windows/NewzDeckYenc.go':'38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15',
 'release/windows/build-portable.py':'5617ee744dc8ed4e51bb1b7c68bd22cfea65eb74',
 'release/windows/NewzDeck.iss':'b7c96b5721b00d468ab9582dfaa80e7f7fa2308d',
}.items(): check(blob(rel)==expected,f'protected native/update blob changed: {rel}')
check('python release/windows/validate-v3696-regressions.py' in workflow,'canonical workflow no longer runs v3.6.96 guard')
check("$pickerLockSource = Join-Path $env:RUNNER_TEMP 'NewzDeckPickerLockSmoke.go'" in workflow,'inert Picker-lock upgrade smoke changed')
check("-ArgumentList @('--taskbar-fix')" not in workflow,'retired Picker taskbar-fix smoke returned')
print('v3.6.96 Library Article-Aware Sorting carried-forward guard under v3.6.99: PASS')
