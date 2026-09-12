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
sab = load_module('newzdeck_v3662_sab_guard', APP / 'sab_engine.py')

# 1. Progressive completion must reuse the first-paint rows and merge any missing
# ranges without duplicate/missing article numbers. Extract the pure merge helper only.
tree = ast.parse(server_text)
body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_merge_overview_headers']
check(len(body) == 1, 'Could not locate the v3.6.77 overview merge helper.')
module = ast.Module(body=body, type_ignores=[]); ast.fix_missing_locations(module)
ns: dict[str, object] = {}
exec(compile(module, '<v3662-overview-merge>', 'exec'), ns)
merge = ns['_merge_overview_headers']
seed = [{'article': n, 'subject': f'seed-{n}'} for n in range(1401, 2201)]
older = [{'article': n, 'subject': f'older-{n}'} for n in range(601, 1402)]
rows = merge(seed, older)
ids = [int(row['article']) for row in rows]
check(ids == list(range(601, 2201)), f'Seed/missing-range merge lost or duplicated article numbers: {ids[:3]}..{ids[-3:]} len={len(ids)}')
check(len(ids) == len(set(ids)) == 1600, 'Progressive merge contains duplicate article numbers.')

# 2. The background worker must fetch only missing ranges around the reused seed,
# then reserve deeper retrieval for genuine Smart Binary expansion.
for marker in (
    'seed_articles: list[dict[str, Any]] | None = None',
    'missing_ranges: list[tuple[int, int]] = []',
    'missing_ranges.append((fetch_start, min(fetch_end, seed_start - 1)))',
    'missing_ranges.append((max(fetch_start, seed_end + 1), fetch_end))',
    'raw_articles = _merge_overview_headers(raw_articles)',
    'background_seed_headers_reused',
    'background_duplicate_headers_avoided',
    'background_network_headers',
    'list(raw_articles) if first_paint_deferred else None',
):
    check(marker in server_text, f'Missing progressive reuse marker: {marker}')
check('BROWSE_OVERVIEW_CHUNK_HEADERS = 800' in server_text, '800-header OVER/XOVER chunk limit changed unexpectedly.')
check('BROWSE_FIRST_PAINT_HEADERS = 800' in server_text, '800-header first-paint limit changed unexpectedly.')
check('BROWSE_LARGE_PAGE_THRESHOLD = 1000' in server_text, 'Large-page threshold changed unexpectedly.')

# 3. Thumbnail diagnostics must describe queue/cache/lock/BODY/decode/worker/endpoint
# phases without changing the proven native decoder or preview concurrency architecture.
for marker in (
    '"thumbnail_cache_lookup"',
    '"thumbnail_build_lock_wait"',
    '"thumbnail_body"',
    '"thumbnail_decode"',
    '"thumbnail_endpoint_total"',
    '"thumbnail_requests"',
    '"thumbnail_cache_hits"',
    '"thumbnail_cache_after_wait_hits"',
    '"thumbnail_failures"',
    '"thumbnail_timeouts"',
    '"thumbnail_fallbacks"',
    '"thumbnail_body_bytes"',
    'perf_stage_prefix="thumbnail"',
):
    check(marker in server_text, f'Missing thumbnail phase telemetry marker: {marker}')
check('f"{perf_stage_prefix}_executor_wait"' in server_text and 'f"{perf_stage_prefix}_worker"' in server_text, 'Preview executor/worker timing instrumentation is missing.')
check('THUMB_DECODE_WORKER_COUNT' in server_text and 'THUMB_HELPER_POOL' in server_text, 'Native thumbnail worker/helper architecture was unexpectedly removed.')

# 4. Render reasons must augment—not replace—the existing aggregate Render metric.
for marker in (
    'f"render_reason_{reason}"',
    "perfRecord('render',performance.now()-renderStarted,true,{reason})",
    "reason:append?'continuous-page':'page-load'",
    "reason:'progressive-completion'",
    "reason:'name-resolution-batched-result'",
):
    check(marker in server_text or marker in app_js, f'Missing carried render-reason telemetry marker: {marker}')
check('updateNameResolutionActivityDomInPlace' in app_js, 'v3.6.77 removed the targeted name-resolution activity updater.')
check("const UI_VERSION = '3.6.77'" in app_js, 'UI version marker is not v3.6.77.')
check('"schema_version": 11' in server_text and '"contract": "passive-runtime-browsing-performance"' in server_text, 'Browsing telemetry schema/contract is not v3.6.77.')

# 5. Release/runtime identities remain coherent and unrelated subsystems are preserved.
check((APP / 'version.txt').read_text(encoding='utf-8').strip() == '3.6.77', 'version.txt is not v3.6.77.')
check(manifest.get('version') == '3.6.77' and manifest.get('base_version') == '3.6.76', f'Build manifest version/base mismatch: {manifest}')
check(manifest.get('adapter_version') == '3.6.77' and manifest.get('sab_version') == '5.1.2', f'Build manifest adapter/SAB mismatch: {manifest}')
check(sab.ADAPTER_VERSION == '3.6.77', f'Wrong SAB adapter identity: {sab.ADAPTER_VERSION}')
check(sab.SAB_VERSION == '5.1.2' and sab.TERMINAL_HISTORY_VERSION == 3, 'v3.6.77 changed SAB 5.1.2 or terminal-history schema 3.')
check("version='3.6.77'" in auto_text, 'Automation default version identity did not migrate to v3.6.77.')
check('_discover_library_index_snapshot' in auto_text and '_flush_metadata_cache_now' in auto_text, 'v3.6.60 Discover optimization stack was not preserved.')
check('3.6.77-ux-layout-control-consistency' in index_html, 'v3.6.77 static cache identity is missing.')
check('<div class="version"><b>NewzDeck</b><span>v3.6.77</span></div>' in index_html, 'Visible sidebar version is not v3.6.77.')

print('v3.6.77 regression guard: PASS')
