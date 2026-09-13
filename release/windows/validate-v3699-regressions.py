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
for rel,expected in EXPECTED.items(): check(sha(APP/rel)==expected,f'{rel} differs from reviewed v3.6.99 payload')
check((APP/'version.txt').read_text().strip()=='3.6.99','version.txt mismatch')
check('APP_VERSION = "3.6.99"' in server and "version='3.6.99'" in automation and 'ADAPTER_VERSION = "3.6.99"' in sab and "const UI_VERSION = '3.6.99';" in app,'application identity mismatch')
check(manifest.get('version')=='3.6.99' and manifest.get('base_version')=='3.6.96' and manifest.get('release')=='Final UX & Backup/Restore' and manifest.get('sab_version')=='5.1.2','manifest identity mismatch')

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
check('python release/windows/validate-v3699-regressions.py' in workflow,'canonical workflow does not run v3.6.99 guard')
check("-ArgumentList @('--taskbar-fix')" not in workflow,'retired Picker behavior returned')
print('v3.6.99 Final UX & Backup/Restore regression guard: PASS')
