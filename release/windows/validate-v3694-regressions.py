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
    'server.py':'5dd4c5c788c3938696bce02109a81f2780d3ffe6a8d7abbc638e2a42ad9247a5',
    'automation_engine.py':'3cc4416de258bfeb178c33a320d6b2054d725cd1055b5eb7e2f84dcebae55ff4',
    'sab_engine.py':'1fdc35a95eaee66329db62b488cae546c085a4394499d31e6789dfb89b97587e',
    'static/app.js':'e9e6f64523bab10dbf703a7e55585bd492428db1e48ea9e415614d7fc1e219b3',
    'static/index.html':'ca8c2bb83aaaf15c707cb455b0b5ec0cbc6207b0f390274573eeb5bc03b07e58',
    'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'static/themes.css':'799288a3c1abf86637898881d2f88d652977f7d9a1803a69e61b4a6519beae9a',
    'build-manifest.json':'ca372b916ea5c3343a34c5ec3a59da0a9270757d54f839968c4b38b9aac9d845',
    'version.txt':'e08fa63b65c0de91e88bad41a162947e84cc18bf1939e98dde337ea0c2a76dc8',
}
for rel,expected in EXPECTED.items():
    check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.94 Themes & Color Schemes payload')

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

check((APP/'version.txt').read_text().strip()=='3.6.94','version.txt mismatch')
check('APP_VERSION = "3.6.94"' in server,'server version mismatch')
check("version='3.6.94'" in automation,'Automation version mismatch')
check('ADAPTER_VERSION = "3.6.94"' in sab,'SAB adapter version mismatch')
check("const UI_VERSION = '3.6.94';" in app,'UI version mismatch')
check(manifest.get('version')=='3.6.94' and manifest.get('base_version')=='3.6.93' and manifest.get('adapter_version')=='3.6.94','manifest lineage mismatch')
check(manifest.get('release')=='Themes & Color Schemes','release name mismatch')
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
check('/themes.css?v=3.6.94-themes-color-schemes' in index,'themes.css cache-busted link missing')
check('/styles.css?v=3.6.94-themes-color-schemes' in index and '/app.js?v=3.6.94-themes-color-schemes' in index,'theme release cache identity mismatch')
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
check('python release/windows/validate-v3694-regressions.py' in workflow,'canonical workflow does not run v3.6.94 guard')
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
print('v3.6.94 Themes & Color Schemes regression guard: PASS (12 palettes, Night exact fallback, contrast and Defender baseline preserved).')
