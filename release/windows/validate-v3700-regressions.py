from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/'src'/'app'
STATIC=APP/'static'

def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def blob(rel):
    return subprocess.check_output(['git','-C',str(ROOT),'rev-parse',f'HEAD:{rel}'],text=True).strip()

server=(APP/'server.py').read_text(encoding='utf-8')
automation=(APP/'automation_engine.py').read_text(encoding='utf-8')
sab=(APP/'sab_engine.py').read_text(encoding='utf-8')
app=(STATIC/'app.js').read_text(encoding='utf-8')
index=(STATIC/'index.html').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8'))
workflow=(ROOT/'.github/workflows/publish-release-trigger.yml').read_text(encoding='utf-8')
root_readme=(ROOT/'README.md').read_text(encoding='utf-8')
source_history=(ROOT/'docs/SOURCE_RELEASES.md').read_text(encoding='utf-8')
src_readme=(ROOT/'src/README.md').read_text(encoding='utf-8')
build_readme=(ROOT/'release/windows/README.md').read_text(encoding='utf-8')
third_party=(ROOT/'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')
site=(ROOT/'index.html').read_text(encoding='utf-8')

EXPECTED={
 'server.py':'c6a77e46e4abeafe8c460944828d69efc9c49c3e33aafeb7819e04a9fc697990',
 'automation_engine.py':'ee3cf8243a593e4fd1c45f040f3a4056a7a8507e27015107401354482c782c78',
 'sab_engine.py':'1b80fe99a1dc42dce9f464095ef14b2227bc100a5c2a83d1b7059b97ae1152ef',
 'static/app.js':'3df087fa5aca176db8c84e6f3a9e962600114b1bb9e83470131365ae1d64fc94',
 'static/index.html':'018ce4260c885c0cf0360c163c5ef76ca7cbfdf5c83b4034f73c2b6255178e61',
 'static/styles.css':'ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d',
 'static/themes.css':'2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721',
 'build-manifest.json':'b717797975a554d068a3527626d9207aa56ec2e6f107147abdb9ef312898d724',
 'version.txt':'84746b20a3a72f6ff85a629706e50507c1bd200907456b76dd808a2a5ca0efba',
}
for rel,expected in EXPECTED.items():
    check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.7.0 payload')

check((APP/'version.txt').read_text().strip()=='3.7.0','version.txt mismatch')
check('APP_VERSION = "3.7.0"' in server and "version='3.7.0'" in automation and 'ADAPTER_VERSION = "3.7.0"' in sab and "const UI_VERSION = '3.7.0';" in app,'application version identity mismatch')
check(manifest.get('version')=='3.7.0' and manifest.get('base_version')=='3.6.99' and manifest.get('release')=='Production Milestone & Repository Hygiene' and manifest.get('sab_version')=='5.1.2','manifest identity mismatch')

for marker in ("'format':'NewzDeckBackup'","'schema':2",'_write_pre_restore_safety_backup','self._restore_raw_snapshot(current)','_sanitize_restore_paths'):
    check(marker in server,'v3.6.99 Backup/Restore backend behavior missing: '+marker)
for marker in ('NEWZDECK_BACKUP_PBKDF2_ITERATIONS=600000',"name:'AES-GCM',length:256","await api('/api/config/backup/complete',{})",'function automationLibrarySortKey(item)',r"replace(/^(?:the|an|a)\s+/i,'')"):
    check(marker in app,'preserved UI/backup/sorting behavior missing: '+marker)
check('Backup &amp; Restore' in index and '.newzdeck-backup' in index,'Backup & Restore Settings UI missing')
check('/styles.css?v=3.7.0-production-milestone-repository-hygiene' in index and '/themes.css?v=3.7.0-production-milestone-repository-hygiene' in index and '/app.js?v=3.7.0-production-milestone-repository-hygiene' in index,'v3.7.0 static cache identity missing')
check(sha(STATIC/'styles.css')=='ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d','styles.css changed')
check(sha(STATIC/'themes.css')=='2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721','themes.css changed')

for rel,expected in {
 'src/windows/NewzDeckPicker.go':'b01efb115ab63b27278faa7c32c631305a8ffd89',
 'src/windows/NewzDeckLauncher.go':'feefee65380f4ffdca9891f7727867670bfbcadd',
 'src/windows/NewzDeckYenc.go':'38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15',
 'release/windows/build-portable.py':'5617ee744dc8ed4e51bb1b7c68bd22cfea65eb74',
 'release/windows/NewzDeck.iss':'b7c96b5721b00d468ab9582dfaa80e7f7fa2308d',
}.items():
    check(blob(rel)==expected,f'protected native/update blob changed: {rel}')

check(not (ROOT/'.github/workflows/windows-release.yml').exists(),'obsolete duplicate windows-release.yml still exists')
workflow_files=sorted(p.name for p in (ROOT/'.github/workflows').glob('*.yml'))
check(workflow_files==['publish-release-trigger.yml'],f'unexpected workflow set: {workflow_files}')
check('python release/windows/validate-v3700-regressions.py' in workflow,'canonical workflow does not run v3.7.0 guard')
check("-ArgumentList @('--taskbar-fix')" not in workflow,'retired production Picker behavior returned to canonical workflow')

check('For v3.5.33:' not in src_readme,'src/README.md still presents the current source tree as v3.5.33')
check('RELEASE_COMPLIANCE.md' not in src_readme,'src/README.md still links nonexistent RELEASE_COMPLIANCE.md')
check('publish-release-trigger.yml' in src_readme and 'SOURCE_RELEASES.md' in src_readme,'src/README.md current topology links missing')

check('windows-release.yml' in build_readme and 'retired in v3.7.0' in build_readme,'release/windows/README.md does not document duplicate workflow retirement')
check('publish-release-trigger.yml' in build_readme and 'one authoritative production Windows publication path' in build_readme,'release/windows/README.md canonical workflow guidance missing')
check('Actions → Build Windows release artifacts' not in build_readme,'release/windows/README.md still directs users to retired manual workflow')

check('v3.6.93' not in third_party,'THIRD_PARTY_NOTICES.md retains stale v3.6.93 wording')
for marker in ('Go 1.23.2','CPython 3.12.10','SABnzbd 5.1.2','UnRAR 7.23','par2cmdline-turbo 1.5.0','Inno Setup 7.1.0'):
    check(marker in third_party,'third-party version/license marker missing: '+marker)

check('NewzDeck v3.7.0' in root_readme and '## v3.7.0 milestone' in root_readme,'root README current release not rolled to v3.7.0')
check('## Current release: v3.7.0' in source_history and '**v3.7.0 is the current stable production release.**' in source_history,'source release history current identity missing')
check('- **v3.7.0 - Production Milestone & Repository Hygiene.**' in source_history,'v3.7.0 source-history entry missing')
check('v3.7.0' in site and 'v3.6.99' not in site,'website release identity is stale')

print('v3.7.0 Production Milestone & Repository Hygiene regression guard: PASS')
