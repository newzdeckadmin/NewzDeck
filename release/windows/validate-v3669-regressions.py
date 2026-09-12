from __future__ import annotations
import ast, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'src'/'app'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def check(c,m):
 if not c: raise AssertionError(m)
server=(APP/'server.py').read_text(encoding='utf-8'); app=(APP/'static'/'app.js').read_text(encoding='utf-8'); manifest=json.loads((APP/'build-manifest.json').read_text(encoding='utf-8')); sab=load('newzdeck_v3669_sab_guard',APP/'sab_engine.py')
for marker in (
 'SETTINGS_SAVE_RETRY_SECONDS = 3.0',
 'SETTINGS_SAVE_RETRYABLE_WINERRORS = frozenset({5, 32, 33})',
 '_SETTINGS_SAVE_WRITE_LOCK = threading.Lock()',
 'def settings_save_reliability_snapshot()',
 'def _settings_json_write(value: Any)',
 'replace_retry_seconds=SETTINGS_SAVE_RETRY_SECONDS',
 'retryable_winerrors=SETTINGS_SAVE_RETRYABLE_WINERRORS',
 'Recovered settings file replacement after transient Windows contention',
 "'settings_save_reliability': settings_save_reliability_snapshot()",
 '        _settings_json_write(settings)',
): check(marker in server,'v3.6.75 settings reliability marker missing: '+marker)
check('def _atomic_text_write(path: Path, text: str, *, replace_retry_seconds: float = 0.0' in server,'Atomic writer default is no longer single-attempt')
check('winerror not in retryable_winerrors' in server,'Settings retry no longer filters WinError classes')
check('newzdeck_replace_retries' in server and '_SETTINGS_SAVE_STATS["retry_attempts"] += retries' in server,'Settings terminal failures no longer preserve retry-attempt telemetry')
check('deadline = time.monotonic() + retry_window' in server and 'remaining = deadline - time.monotonic()' in server,'Settings retry window is not hard-bounded')
check('def json_write(path: Path, value: Any) -> None:\n    _atomic_text_write(path, json.dumps(value, indent=2, ensure_ascii=False))' in server,'General json_write unexpectedly opted into retry behavior')
for marker in ('const NAME_RESOLUTION_RENDER_AUTO_SOFT_MS=1400;','const NAME_RESOLUTION_RENDER_AUTO_MAX_MS=3000;','const NAME_RESOLUTION_RENDER_MANUAL_SOFT_MS=1800;','const NAME_RESOLUTION_RENDER_MANUAL_MAX_MS=4200;',"perfRecord('name_resolution_batch'","perfRecord('name_resolution_render_wait'"):
 check(marker in app,'Accepted v3.6.68 resolver behavior regressed: '+marker)
check('"schema_version": 11' in server and '"contract": "passive-runtime-browsing-performance"' in server,'Browsing telemetry schema 7/contract changed')
check('const THUMBNAIL_HTTP_ADMISSION_LIMIT=5;' in app,'Image HTTP admission changed')
formula='state.videoThumbConcurrency=Math.max(1,Math.min(6,connections>=48?6:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));'
check(formula in app,'Accepted six-slot Video ceiling changed')
tree=ast.parse(server); wanted={'BROWSE_OVERVIEW_CHUNK_HEADERS','BROWSE_FIRST_PAINT_HEADERS','BROWSE_LARGE_PAGE_THRESHOLD'}; body=[]
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id in wanted for x in node.targets): body.append(node)
 elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in wanted: body.append(node)
mod=ast.Module(body=body,type_ignores=[]); ast.fix_missing_locations(mod); ns={}; exec(compile(mod,'<v3669>','exec'),ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS']==800 and ns['BROWSE_FIRST_PAINT_HEADERS']==800 and ns['BROWSE_LARGE_PAGE_THRESHOLD']==1000,'Header strategy changed')
check((APP/'version.txt').read_text().strip()=='3.6.75','version.txt mismatch')
check(manifest.get('version')=='3.6.75' and manifest.get('base_version')=='3.6.74' and manifest.get('adapter_version')=='3.6.75','build manifest identity mismatch')
check(sab.ADAPTER_VERSION=='3.6.75' and sab.SAB_VERSION=='5.1.2','SAB identity changed')
check(getattr(sab,'TERMINAL_HISTORY_SCHEMA_VERSION',3)==3,'terminal-history schema changed')
print('v3.6.75 regression guard: PASS')
