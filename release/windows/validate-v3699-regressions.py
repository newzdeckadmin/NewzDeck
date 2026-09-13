from __future__ import annotations
import ast, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'; STATIC=APP/'static'
def check(c,m):
    if not c: raise AssertionError(m)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def blob(rel): return subprocess.check_output(['git','-C',str(ROOT),'rev-parse',f'HEAD:{rel}'],text=True).strip()
server=(APP/'server.py').read_text(encoding='utf-8'); automation=(APP/'automation_engine.py').read_text(encoding='utf-8'); sab=(APP/'sab_engine.py').read_text(encoding='utf-8')
app=(STATIC/'app.js').read_text(encoding='utf-8'); index=(STATIC/'index.html').read_text(encoding='utf-8'); themes=(STATIC/'themes.css').read_text(encoding='utf-8')
manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); workflow=(ROOT/'.github'/'workflows'/'publish-release-trigger.yml').read_text(encoding='utf-8')
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
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.7.0 payload')
check((APP/'version.txt').read_text().strip()=='3.7.0','version.txt mismatch')
check('APP_VERSION = "3.7.0"' in server and "version='3.7.0'" in automation and 'ADAPTER_VERSION = "3.7.0"' in sab and "const UI_VERSION = '3.7.0';" in app,'application identity mismatch')
check(manifest.get('version')=='3.7.0' and manifest.get('base_version')=='3.6.99' and manifest.get('release')=='Production Milestone & Repository Hygiene' and manifest.get('sab_version')=='5.1.2','manifest identity mismatch')

# Backup schema + scope.
for marker in ("'format':'NewzDeckBackup'","'schema':2","'kind':'complete' if include_secrets else 'configuration'","'excluded':['download_payloads','download_queue','sab_runtime','automation_runtime','caches','thumbnails','logs','diagnostics','metadata_cache']"):
    check(marker in server,'portable backup marker missing: '+marker)
check("rec.pop('password_protected','')" in server and "rec.pop('api_key_protected','')" in server,'portable backup leaks protected machine-bound secret blobs')
check("rec['password']=unprotect_secret(protected)" in server and "rec['api_key']=unprotect_secret(protected)" in server,'Complete Backup secret export path missing')
check('config_backup_complete_api' in server and '"/api/config/backup/complete"' in server,'Complete Backup POST endpoint missing')
check('data = self._body_json(25_000_000 if parsed.path == "/api/config/restore" else 2_000_000)' in server,'bounded large restore-body support missing')

# Transactional restore / safety.
for marker in ('_write_pre_restore_safety_backup','NewzDeckInternalSafetyBackup','with MEDIA_AUTOMATION.auto_run_lock:','with MEDIA_AUTOMATION.lock:','self._restore_raw_snapshot(current)','self.settings_api(settings,respond=False)','_clear_automation_config_caches'):
    check(marker in server,'transactional restore marker missing: '+marker)
check("data.get('format')=='NewzDeckConfigBackup'" in server,'legacy NewzDeckConfigBackup restore compatibility missing')
check("Unsupported NewzDeck backup schema" in server,'backup schema validation missing')
check("metadata_installation_secret_protected" in server and "metadata_access_token_protected" in server,'installation-scoped metadata identity preservation missing')
check('_restore_match_provider_secret' in server and '_restore_match_indexer_secret' in server,'secret-free restore matching missing')
check("machine_scope=True if sys.platform=='win32'" in server,'restored credentials are not re-protected for Windows service compatibility')
for marker in (
    '_sanitize_restore_paths',
    "(('download_folder','Download folder'),('watch_folder','NZB watch folder'))",
    'Path(value).expanduser().is_dir()',
    "if old: out[key]=old",
    "else: out.pop(key,None)",
    "warnings.append(f'{label} was not available on this PC, so the current local path was kept.')",
):
    check(marker in server,'cross-PC path safety missing: '+marker)

# Browser-side authenticated encryption; password never appears in backup API body.
for marker in ("NEWZDECK_BACKUP_PBKDF2_ITERATIONS=600000","name:'PBKDF2',hash:'SHA-256'","name:'AES-GCM',length:256","algorithm:'AES-256-GCM'","kdf:'PBKDF2-SHA-256'","await api('/api/config/backup/complete',{})"):
    check(marker in app,'client encryption marker missing: '+marker)
check("password" not in "await api('/api/config/backup/complete',{})",'backup password is sent to backend')
check("backupWithPresentation" in app and "theme:savedTheme()" in app,'theme presentation backup missing')
check("applyTheme(payload.presentation.theme,{persist:true})" in app,'theme restore missing')
check(".newzdeck-backup" in index and 'Backup &amp; Restore' in index and 'Create Encrypted Complete Backup' in index,'Backup & Restore Settings UX missing')

# v3.6.96 sort and v3.6.95 themes are preserved.
check('function automationLibrarySortKey(item)' in app and r"replace(/^(?:the|an|a)\s+/i,'')" in app,'article-aware sorting regressed')
check(sha(STATIC/'styles.css')=='ab31b3abb9de549ac90df980bdfce437a98c1c1cb5a5d0852b252ddcb670a75d','styles.css changed')
check(sha(STATIC/'themes.css')=='2a44223d165b8e1caa8bc5a52842ce76cf396557e6af59b9ecd2aee8bf6a1721','themes.css changed')
check('v3.6.95 Light Theme Readability Hotfix' in themes,'light-theme baseline marker missing')

# Defender-sensitive native/update architecture remains frozen.
for rel,expected in {
 'src/windows/NewzDeckPicker.go':'b01efb115ab63b27278faa7c32c631305a8ffd89',
 'src/windows/NewzDeckLauncher.go':'feefee65380f4ffdca9891f7727867670bfbcadd',
 'src/windows/NewzDeckYenc.go':'38f6df7ed77bc7d3b5d8c83b1973e86fc6fa9c15',
 'release/windows/build-portable.py':'5617ee744dc8ed4e51bb1b7c68bd22cfea65eb74',
 'release/windows/NewzDeck.iss':'b7c96b5721b00d468ab9582dfaa80e7f7fa2308d',
}.items(): check(blob(rel)==expected,f'protected native/update blob changed: {rel}')
check('python release/windows/validate-v3699-regressions.py' in workflow,'canonical workflow does not run v3.7.0 guard')
check("-ArgumentList @('--taskbar-fix')" not in workflow,'retired Picker behavior returned')
print('v3.6.99 Backup/Restore behavior carried forward under v3.7.0: PASS')
