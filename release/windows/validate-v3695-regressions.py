from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'src'/'app'; STATIC=APP/'static'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
EXPECTED={
    'server.py': '115b49c5c656e5d9366746d6adba166a0fc8d3770d6b33847aff48c4dc570e4f',
    'automation_engine.py': '67da05374cb70a305ccafd3251ce27a806f9521bfb211ce657596ae7708b0098',
    'sab_engine.py': '7c84060a3316a014bd859d54f46606f1a3b2f94d4df34f5297a22078d4d5f75e',
    'static/app.js': '5d9400336a87c0503ef7a1e15cfdea744c1ea0865be37f0c6a1cf3ed666c9e11',
    'static/index.html': 'd77a224e530a4fa8cbfecad88db14321255729adf843feb4fb0e7186e656ea5d',
    'static/styles.css': 'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
    'static/themes.css': '2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721',
    'build-manifest.json': '36fd81bfb09be9b1ae23225520719010a43601b60f8467d13e89cd07b06223ac',
    'version.txt': '7d1e1967d448824bd388968ce6c1665293b9be823deae8e870a46963874fd903'
}
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.99 Final UX & Backup/Restore payload')
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

# v3.6.95 was deliberately presentation-only. The underlying tokenized stylesheet
# remains byte-for-byte v3.6.94; only themes.css semantics for the three light
# palettes plus identity/cache metadata may change.
check(hashlib.sha256(styles.encode()).hexdigest()=='ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d','styles.css changed in light-theme-only hotfix')
wrap=re.compile(r'var\(--nz-[a-z0-9-]+,(#[0-9a-fA-F]{3,8}|rgba?\([^()]*\)|white)\)')
rebuilt=wrap.sub(lambda m:m.group(1),styles)
check(hashlib.sha256(rebuilt.encode()).hexdigest()=='ad20bff9927560c8b877a932c0f42ec6fe7b104a606812f61c47b6c0013e7bd2','Night fallback reconstruction no longer matches exact v3.6.93 stylesheet')

# All dark theme palette blocks are frozen exactly to v3.6.94.
DARK_HASHES={
    'midnight': 'edaab39fc2a9ba7e2c45aba41e2b3d185272feb6670ba2aa91cb25651a3d2328',
    'ocean': '9a949ff3f966d12209adbac702c92a240d130f424f81384811054c71d5f99b64',
    'emerald': '8e68c6d2fe95f20cb6e96cb750aca8927278117fd0eacd7d55bfc4294dda4dfb',
    'amethyst': 'e150de89a18a411d3d88a2aac5f5d5c982872a4edee96d1ca3e8235f368923d6',
    'rosewood': '187e901985c1212f71c91e33130c12f5313fa31abd23a95c0e81bdf7af7a2127',
    'sunset': '1b936ac2f73275eef9b48d8889c1b11bb5d19f30576b22792e73f4dfc33cfb51',
    'graphite': 'c26f8c6cc9e12a18e1bb2d0474b06856de2bffb67eb65810f3d743689c14912b',
    'aurora': '835fede72b21e1324a38a60f84a16c462aa911a97aaa0ae29674c650a768ffe7'
}
for theme,expected in DARK_HASHES.items():
    m=re.search(r'html\[data-theme="'+re.escape(theme)+r'"\]\{[^}]*\}',themes)
    check(m is not None,f'dark palette missing: {theme}')
    check(hashlib.sha256(m.group(0).encode()).hexdigest()==expected,f'v3.6.95 unexpectedly changed dark theme {theme}')
check('html[data-theme="night"]{color-scheme:dark}' in themes,'Night rule changed')

# Light palettes must no longer route generic overlay-derived controls through a
# dark color. They use their coordinated light surface and retain a separate
# dark scrim role for true modal/media/image overlays.
LIGHT={'light':'#172431','arctic':'#152a38','sandstone':'#2d2823'}
for theme,scrim in LIGHT.items():
    m=re.search(r'html\[data-theme="'+theme+r'"\]\{[^}]*\}',themes)
    check(m is not None,f'light palette missing: {theme}')
    b=m.group(0)
    check('--nz-overlay:var(--nz-surface-2);' in b,f'{theme} still uses a dark generic overlay surface')
    check(f'--nz-scrim:{scrim};' in b,f'{theme} dark scrim role missing')
    check('--nz-scrim-text:' in b and '--nz-scrim-muted:' in b,f'{theme} scrim foreground roles missing')
    check('color-scheme:light;' in b,f'{theme} lost light color-scheme')
for marker in (
    '/* v3.6.95 Light Theme Readability Hotfix',
    '.modal{background:color-mix(in srgb,var(--nz-scrim) 72%,transparent)!important}',
    '.media-viewer{background:color-mix(in srgb,var(--nz-scrim) 97.5%,transparent)!important;color:var(--nz-scrim-text)!important}',
    '.video-play-overlay span', '.select-media-btn', '.card-download-btn', '.set-badge', '.discover-card-hover',
    'input::placeholder', 'textarea::placeholder',
): check(marker in themes,'light-theme semantic fix marker missing: '+marker)

# Verify the exact user-facing failure class: generic search/form surfaces now
# derive from a light palette while their text remains dark enough to read.
def rgb(h):
    h=h.lstrip('#'); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
def lum(h):
    def f(v): return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    r,g,b=rgb(h); return .2126*f(r)+.7152*f(g)+.0722*f(b)
def contrast(a,b):
    x,y=lum(a),lum(b); hi,lo=max(x,y),min(x,y); return (hi+.05)/(lo+.05)
for theme in LIGHT:
    m=re.search(r'html\[data-theme="'+theme+r'"\]\{[^}]*\}',themes); vals=dict(re.findall(r'--nz-([a-z0-9-]+):(#[0-9a-fA-F]{6})',m.group(0)))
    for fg in ('text','text-2','accent-2'):
        got=contrast(vals[fg],vals['surface-2'])
        check(got>=4.5,f'{theme} {fg}/surface-2 contrast {got:.2f} is below 4.5')
    check(contrast(vals['scrim-text'],vals['scrim'])>=7.0,f'{theme} scrim text contrast is below 7.0')

# Theme registry/persistence behavior and backend isolation remain v3.6.94.
for required in ("const THEME_STORAGE_KEY = 'newzdeckTheme';","const LIGHT_THEME_IDS = new Set(['light','arctic','sandstone']);",'function applyTheme(value,{persist=false}={})',"localStorage.setItem(THEME_STORAGE_KEY,theme)"):
    check(required in app,'theme behavior changed: '+required)
check('/themes.css?v=3.6.99-final-ux-backup-restore' in index and '/styles.css?v=3.6.99-final-ux-backup-restore' in index and '/app.js?v=3.6.99-final-ux-backup-restore' in index,'hotfix cache identity mismatch')
check('newzdeckTheme' not in server and 'newzdeckTheme' not in automation and 'newzdeckTheme' not in sab,'theme preference leaked into backend')

# Defender-clean/update architecture stays frozen.
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
check('python release/windows/validate-v3695-regressions.py' in workflow,'canonical workflow does not run v3.6.99 guard')
print('v3.6.99 Library Article-Aware Sorting regression guard: PASS (three light palettes corrected; nine dark palettes and Defender baseline frozen).')
