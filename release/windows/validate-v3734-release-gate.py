#!/usr/bin/env python3
"""Source/manifest v3.7.34 gate; inherits v3.7.32 feature regressions."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]
read=lambda rel:(R/rel).read_text('utf8')
def check(test,msg):
    if not test:raise AssertionError('v3.7.34 current-release gate: '+msg)
manifest=json.loads(read('src/app/build-manifest.json'))
check(read('src/app/version.txt').strip()=='3.7.34','version.txt')
check(tuple(manifest.get(k) for k in ('version','base_version','adapter_version','sab_version','sabctools_version'))==
    ('3.7.34','3.7.33','3.7.34','5.1.3','9.6.3'),'build-manifest identity and SAB pin')
for path,marker in [('src/app/server.py','APP_VERSION = "3.7.34"'),
 ('src/app/sab_engine.py','ADAPTER_VERSION = "3.7.34"'),
 ('src/app/automation_engine.py',"version='3.7.34'"),
 ('src/app/static/app.js',"const UI_VERSION = '3.7.34'")]:
    check(marker in read(path),path+' version')
check('3.7.34' in read('src/app/static/index.html'),'UI cache identity')
srv=read('src/app/server.py');sab=read('src/app/sab_engine.py')
for marker in ('class ManualGrabOperations:',"if data.get('async_grab') is True:",
               'GRAB_OPERATIONS.start(data)','GRAB_OPERATIONS.get(identifier)',
               'def _finalize_flat_native_output(', '"flat_output_requested":',
               'flatten_completed_folder = _flat_output_module.flatten_completed_folder'):
    check(marker in srv,'native Grab/flat behavior '+marker)
for marker in ('def _finalize_flat_completed_nzb(', '"flat_output_requested":',
               '"flat_output_plan": {}','flatten_completed_folder = _load_flat_output_from_installed_source()',
               'if bool(meta.get("flat_output_requested")) and not bool(meta.get("flat_output_done")): return False',
               'def _flatten_completed_browser_images(', 'SAB_VERSION = "5.1.3"'):
    check(marker in sab,'SAB preservation and flat-output state '+marker)
for path in ('src/app/flat_output.py', 'release/windows/validate-v3733-flat-output.py',
             'release/windows/validate-v3733-grab-identity.py',
             'release/windows/validate-v3734-sab-preservation.py',
             'release/RELEASE_NOTES_v3.7.34.md'):
    check((R/path).is_file(),path+' exists')
workflow=R/'.github/workflows/publish-release-trigger.yml'
if workflow.is_file():
    text=workflow.read_text('utf8')
    for marker in ("$env:VERSION -cne '3.7.34'",'validate-v3734-release-gate.py',
        'validate-v3734-sab-preservation.py','validate-v3733-flat-output.py',
        'validate-v3733-grab-identity.py','validate-v3732-async-grab.py',
        'validate-v3732-history.py','validate-v3731-video-discovery.py','validate-v3729-metadata-refresh.py'):
        check(marker in text,'Windows workflow current gate '+marker)
    check('python release/windows/validate-v3732-release-gate.py\n' not in text,'obsolete release gate invoked')
    check('python release/windows/validate-v3733-release-gate.py\n' not in text,'obsolete v3.7.33 release gate invoked')
    check('python release/windows/validate-v3733-sab-preservation.py\n' not in text,'obsolete v3.7.33 SAB version test invoked')
    check('python release/windows/validate-v3732-sab-preservation.py\n' not in text,'obsolete version pin test invoked')
    build=read('release/windows/build-portable.py');installer=read('release/windows/build-release.ps1')
    check('"flat_output.py"' in build and 'src/app/flat_output.py' in build,'Portable source packaging')
    check("'flat_output.py'" in installer,'installer source required')
    check('a.version = argValue("--version", "3.7.34")' in read('src/windows/NewzDeckTray.go'),'tray version')
    check('VersionInfoVersion={#AppVersion}.0' in read('release/windows/NewzDeck.iss'),'Inno three-part version')
test_source=read('release/windows/validate-v3733-flat-output.py')
check("Path(slot['storage']).samefile(root)" in test_source,'Windows alias safe identity test')
check("slot['storage']==str(root)" not in test_source,'old path spelling assertion persists')
print('PASS: source/manifest v3.7.34, flat checkbox, manual Grab identity, historic regressions and conditional canonical Windows build/publish gates')
