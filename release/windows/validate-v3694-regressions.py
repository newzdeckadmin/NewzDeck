from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'src'/'app'
STATIC=APP/'static'

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
    'static/themes.css':'2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721',
    'build-manifest.json':'36fd81bfb09be9b1ae23225520719010a43601b60f8467d13e89cd07b06223ac',
    'version.txt':'7d1e1967d448824bd388968ce6c1665293b9be823deae8e870a46963874fd903',
}
for rel,expected in EXPECTED.items():
    check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.99 Final UX & Backup/Restore payload')

server=(APP/'server.py').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
sab=(APP/'sab_engine.py').read_text(encoding='utf-8')
app=(STATIC/'app.js').read_text(encoding='utf-8')
index=(STATIC/'index.html').read_text(encoding='utf-8')
styles=(STATIC/'styles.css').read_text(encoding='utf-8')
themes=(STATIC/'themes.css').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
picker=(ROOT/'src'/'windows'/'NewzDeckPicker.go').read_text(encoding='utf-8')
yenc=(ROOT/'src'/'windows'/'NewzDeckYenc.go').read_text(encoding='utf-8')
builder=(ROOT/'release'/'windows'/'build-portable.py').read_text(encoding='utf-8')
workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
installer=(ROOT/'release'/'windows'/'NewzDeck.iss').read_text(encoding='utf-8')

check((APP/'version.txt').read_text().strip()=='3.6.99','version.txt mismatch')
check('APP_VERSION = "3.6.99"' in server,'server version mismatch')
check("version='3.6.99'" in automation,'Automation version mismatch')
check('ADAPTER_VERSION = "3.6.99"' in sab,'SAB adapter version mismatch')
check("const UI_VERSION = '3.6.99';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.99' and manifest.get('base_version')=='3.6.96' and manifest.get('adapter_version')=='3.6.99','manifest lineage mismatch')
check(manifest.get('release')=='Final UX & Backup/Restore','release name mismatch')
check(manifest.get('sab_version')=='5.1.2','SAB version changed')

# Night must reconstruct the exact v3.6.93 stylesheet byte-for-byte. The only
# allowed change to the old stylesheet is wrapping literal colors in semantic
# theme variables whose fallback is the original color.
wrap=re.compile(r'var\(--nz-[a-z0-9-]+,(#[0-9a-fA-F]{3,8}|rgba?\([^()]*\)|white)\)')
rebuilt=wrap.sub(lambda m:m.group(1),styles)
check(hashlib.sha256(rebuilt.encode('utf-8')).hexdigest()=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','Night fallback reconstruction does not match exact v3.6.93 styles.css')
check(len(wrap.findall(styles))>=2900,'theme tokenization coverage unexpectedly low')
check('html[data-theme="night"]{color-scheme:dark}' in themes,'Night color-scheme rule missing')

THEMES=['night','light','midnight','ocean','emerald','amethyst','rosewood','sunset','arctic','graphite','sandstone','aurora']
LIGHT={'light','arctic','sandstone'}
# Theme identity must agree in all three presentation layers.
check("const THEME_IDS = Object.freeze(['night','light','midnight','ocean','emerald','amethyst','rosewood','sunset','arctic','graphite','sandstone','aurora']);" in app,'app theme registry mismatch')
check("const LIGHT_THEME_IDS = new Set(['light','arctic','sandstone']);" in app,'app light-theme registry mismatch')
for theme in THEMES:
    check(f'<option value="{theme}">' in index,f'Settings selector missing theme {theme}')
    check(f"'{theme}'" in index.split('</script>',1)[0],f'pre-paint bootstrap missing theme {theme}')
    check(f'html[data-theme="{theme}"]' in themes,f'themes.css missing selector for {theme}')
for theme in LIGHT:
    check(f'html[data-theme="{theme}"]{{color-scheme:light;' in themes,f'{theme} is not a light color-scheme')
for theme in set(THEMES)-LIGHT-{'night'}:
    check(f'html[data-theme="{theme}"]{{color-scheme:dark;' in themes,f'{theme} is not a dark color-scheme')

# Presentation-only persistence: pre-paint restore, instant preview, Cancel/close
# rollback, and save-only commit. Theme is deliberately absent from backend payload.
for required in (
    "const THEME_STORAGE_KEY = 'newzdeckTheme';",
    'function normalizeTheme(value)',
    'function savedTheme()',
    'function applyTheme(value,{persist=false}={})',
    "localStorage.setItem(THEME_STORAGE_KEY,theme)",
    "set('settingsTheme',savedTheme());",
    "function closeSettingsModal(){applyTheme(savedTheme());els.settingsModal.classList.add('hidden')}",
    "applyTheme($('settingsTheme')?.value||savedTheme(),{persist:true});",
    "$('settingsTheme').onchange=()=>applyTheme($('settingsTheme').value)",
): check(required in app,'theme behavior marker missing: '+required)
check('id="settingsTheme"' in index,'Settings theme selector missing')
check('/themes.css?v=3.6.99-final-ux-backup-restore' in index,'themes.css cache-busted link missing')
check('/styles.css?v=3.6.99-final-ux-backup-restore' in index and '/app.js?v=3.6.99-final-ux-backup-restore' in index,'theme release cache identity mismatch')
head=index.split('</head>',1)[0]
check(head.index('newzdeckTheme') < head.index('/styles.css?'),'saved theme is not restored before render-blocking CSS')
# saveSettingsModal backend payload starts after the theme helpers; a theme property must never be posted.
save=app[app.index('async function saveSettingsModal()'):app.index('async function settingsChooseDownloadFolder()')]
check('theme:' not in save and 'newzdeckTheme' not in save,'theme leaked into backend settings payload')
check('newzdeckTheme' not in server and 'newzdeckTheme' not in automation and 'newzdeckTheme' not in sab,'backend application logic was coupled to presentation theme state')

# Parse core palette values and enforce readable color contrast. This is stricter
# than the minimum for primary/secondary text and meets WCAG AA for normal muted text.
def rgb(h):
    h=h.lstrip('#'); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
def luminance(h):
    def f(v): return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    r,g,b=rgb(h); return .2126*f(r)+.7152*f(g)+.0722*f(b)
def contrast(a,b):
    x,y=luminance(a),luminance(b); hi,lo=max(x,y),min(x,y); return (hi+.05)/(lo+.05)
required_roles={'bg','surface','text','text-2','muted','accent','accent-2','accent-contrast','success','warning','danger'}
for theme in THEMES:
    if theme=='night': continue
    m=re.search(r'html\[data-theme="'+re.escape(theme)+r'"\]\{[^}]*\}',themes)
    check(m is not None,f'palette block missing: {theme}')
    vals=dict(re.findall(r'--nz-([a-z0-9-]+):(#[0-9a-fA-F]{6})',m.group(0)))
    check(required_roles<=vals.keys(),f'{theme} palette missing roles: {sorted(required_roles-vals.keys())}')
    floors=[('text','bg',7.0),('text','surface',7.0),('text-2','bg',4.5),('muted','bg',4.5),('muted','surface',4.5),('accent-contrast','accent',4.5),('accent','surface',3.0),('accent-2','surface',3.0),('success','surface',3.0),('warning','surface',3.0),('danger','surface',3.0)]
    for fg,bg,floor in floors:
        got=contrast(vals[fg],vals[bg])
        check(got+1e-9>=floor,f'{theme}: contrast {fg}/{bg}={got:.2f} below {floor:.1f}')

# Packaging must carry the new stylesheet and provenance entry, while all native
# Defender-sensitive build behavior remains exactly the v3.6.93 design.
check('{"path":"src/app/static/themes.css","sha256":sha(APP/\'static\'/\'themes.css\')}' in builder,'themes.css missing from SOURCE_MANIFEST application_source')
check("'static/themes.css'" in workflow,'canonical Portable validation does not require themes.css')
check('python release/windows/validate-v3694-regressions.py' in workflow,'canonical workflow does not run v3.6.99 guard')
check(hashlib.sha256(picker.encode()).hexdigest()=='df8b23aea5b8dfc18f43276759f3ef7d69dbd767e35eb191c133f6d8ffd97f46','folder-only Picker source changed')
check(hashlib.sha256(yenc.encode()).hexdigest()=='ba11eea2f880a934ff24f73be1cb12f0341456d5972c71f9c860efe9b3673edd','accepted yEnc source changed')
for required in ('PICKER_GO_LDFLAGS = "-H windowsgui"','YENC_GO_LDFLAGS = "-H windowsgui"','YENC_ACCEPTED_BINARY_SHA256 = "4bb07f7b6d38ff99313f74cb4b45555e134af7106e32d55b106a79d603204fad"'):
    check(required in builder,'Defender-clean build marker changed: '+required)
for forbidden in ('--update-handoff','--close-app-windows','--taskbar-fix','os/exec','ShellExecuteExW','EnumWindows'):
    check(forbidden not in picker,'Picker regained retired behavior: '+forbidden)
for required in ('def _launch_verified_setup_update(', 'def _schedule_verified_setup_update('): check(required in server,'direct verified-Setup updater marker missing: '+required)
for forbidden in ('def _launch_update_handoff(', 'NewzDeckUpdateHandoff-', 'shutil.copy2(PICKER_HELPER_EXE'):
    check(forbidden not in server,'legacy copied update handoff returned: '+forbidden)
check("Exec(AppExe, '--close-app-windows'" in installer and "Exec(Helper, '--close-app-windows'" not in installer,'installer update ownership changed')
check("$pickerLockSource = Join-Path $env:RUNNER_TEMP 'NewzDeckPickerLockSmoke.go'" in workflow,'v3.6.93 inert Picker-lock smoke was lost')
check("-ArgumentList @('--taskbar-fix')" not in workflow,'retired Picker taskbar-fix smoke returned')
print('v3.6.99 Library Article-Aware Sorting regression guard: PASS (12 palettes, Night exact fallback, contrast and Defender baseline preserved).')
