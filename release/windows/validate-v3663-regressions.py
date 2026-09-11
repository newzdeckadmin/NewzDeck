from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'src' / 'app'


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Could not load {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


server_text = (APP / 'server.py').read_text(encoding='utf-8')
app_js = (APP / 'static' / 'app.js').read_text(encoding='utf-8')
index_html = (APP / 'static' / 'index.html').read_text(encoding='utf-8')
auto_text = (APP / 'automation_engine.py').read_text(encoding='utf-8')
manifest = json.loads((APP / 'build-manifest.json').read_text(encoding='utf-8'))
sab = load_module('newzdeck_v3663_sab_guard', APP / 'sab_engine.py')

# 1. Name-resolution activity must not rebuild the full All Posts DOM simply to
# start/retry/finish. Result-driven rendering remains for visible presentation changes.
start = app_js.index('async function resolveObfuscatedNames({manual=false}={}){')
end = app_js.index('\nfunction binaryNameResolutionInfo', start)
resolver = app_js[start:end]
for forbidden in (
    "reason:'name-resolution-state'",
    "reason:'name-resolution-retry'",
    "reason:'name-resolution-finish'",
):
    check(forbidden not in resolver, f'Redundant full render returned to name resolution: {forbidden}')
check('queueNameResolutionResultRender' in resolver and "reason:'name-resolution-batched-result'" in app_js, 'Result-driven name-resolution rendering/batching was removed.')
for marker in (
    'function updateNameResolutionActivityDomInPlace()',
    "querySelector('.binary-resolve-btn')",
    "btn.textContent='Resolving names…'",
    "chip.textContent='RESOLVING…'",
    'updateNameResolutionActivityDomInPlace();scheduleObfuscatedNameResolution()',
):
    check(marker in app_js, f'Missing targeted name-resolution DOM marker: {marker}')

# 2. Browser thumbnail telemetry must separate client scheduling/local HTTP/post
# processing/recovery instead of attributing all latency to the Python endpoint.
for stage in ('thumbnail_queue', 'thumbnail_http', 'thumbnail_post', 'thumbnail_recovery'):
    check(f"perfRecord('{stage}'" in app_js, f'Missing browser thumbnail stage: {stage}')
    check(f'"{stage}"' in server_text, f'Backend does not accept browser thumbnail stage: {stage}')
for marker in (
    'function thumbnailErrorReason(e)',
    'async function thumbnailImageApiTimed(',
    'async function finishImageThumbnailResponseTimed(',
    "reason:'retry-after-full-preview'" if False else "'retry-after-full-preview'",
    "perfRecord('thumbnail',performance.now()-started,thumbnailOK)",
):
    check(marker in app_js, f'Missing thumbnail trace marker: {marker}')
check('stage.startswith("thumbnail_")' in server_text and 'client_{stage}_reason_{reason}' in server_text, 'Thumbnail reason aggregation is missing.')

# 3. Backend image-thumbnail errors must use the existing preview classification and
# expose bounded per-code counters without inventing a second error taxonomy.
for marker in (
    'info = preview_error_info(exc)',
    'thumbnail_failure_code_',
    'info.get("error_code")',
    'thumbnail_retryable_failures',
    'return self._json(422, timed_payload(info))',
):
    check(marker in server_text, f'Missing backend thumbnail failure classification marker: {marker}')
for code in ('browse_cancelled', 'article_missing', 'multipart_incomplete', 'provider_temporary', 'decode_failed', 'preview_failed'):
    check(code in server_text, f'Existing preview error classification disappeared: {code}')

# 4. v3.6.62 progressive-header optimization/tuning remains unchanged.
tree = ast.parse(server_text)
wanted = {'BROWSE_OVERVIEW_CHUNK_HEADERS', 'BROWSE_FIRST_PAINT_HEADERS', 'BROWSE_LARGE_PAGE_THRESHOLD'}
body = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in wanted for name in names): body.append(node)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in wanted:
        body.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in {'_overview_chunk_ranges', '_first_paint_overview_range', '_merge_overview_headers'}:
        body.append(node)
module = ast.Module(body=body, type_ignores=[]); ast.fix_missing_locations(module)
ns: dict[str, object] = {}
exec(compile(module, '<v3663-browse-helpers>', 'exec'), ns)
check(ns['BROWSE_OVERVIEW_CHUNK_HEADERS'] == 800, 'OVER/XOVER chunk limit changed.')
check(ns['BROWSE_FIRST_PAINT_HEADERS'] == 800, 'First-paint header limit changed.')
check(ns['BROWSE_LARGE_PAGE_THRESHOLD'] == 1000, 'Large-page threshold changed.')
seed = [{'article': n} for n in range(1401, 2201)]
older = [{'article': n} for n in range(601, 1402)]
ids = [int(x['article']) for x in ns['_merge_overview_headers'](seed, older)]
check(ids == list(range(601, 2201)) and len(ids) == len(set(ids)), 'Progressive seed reuse merge regressed.')
for marker in ('background_seed_headers_reused', 'background_duplicate_headers_avoided', 'background_network_headers'):
    check(marker in server_text, f'v3.6.62 progressive reuse telemetry disappeared: {marker}')

# 5. Release identity and unrelated architecture stay coherent.
check((APP / 'version.txt').read_text(encoding='utf-8').strip() == '3.6.71', 'version.txt is not v3.6.71.')
check(manifest.get('version') == '3.6.71' and manifest.get('base_version') == '3.6.70', f'Build manifest version/base mismatch: {manifest}')
check(manifest.get('adapter_version') == '3.6.71' and manifest.get('sab_version') == '5.1.2', f'Build manifest adapter/SAB mismatch: {manifest}')
check(sab.ADAPTER_VERSION == '3.6.71', f'Wrong SAB adapter identity: {sab.ADAPTER_VERSION}')
check(sab.SAB_VERSION == '5.1.2' and sab.TERMINAL_HISTORY_VERSION == 3, 'SAB 5.1.2 or terminal-history schema 3 changed.')
check("version='3.6.71'" in auto_text, 'Automation default version identity did not migrate.')
check('_discover_library_index_snapshot' in auto_text and '_flush_metadata_cache_now' in auto_text, 'Discover v3.6.60 optimization stack was not preserved.')
check('"schema_version": 9' in server_text and '"contract": "passive-runtime-browsing-performance"' in server_text, 'Browsing telemetry schema/contract is not v3.6.71.')
check('3.6.71-video-thumbnail-decode-suppression' in index_html, 'Static cache identity is missing.')
check('<div class="version"><b>NewzDeck</b><span>v3.6.71</span></div>' in index_html, 'Visible UI version is not v3.6.71.')

print('v3.6.71 regression guard: PASS')
