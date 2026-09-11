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


auto = load_module('newzdeck_v3661_automation_guard', APP / 'automation_engine.py')
sab = load_module('newzdeck_v3661_sab_guard', APP / 'sab_engine.py')
server_text = (APP / 'server.py').read_text(encoding='utf-8')
app_js = (APP / 'static' / 'app.js').read_text(encoding='utf-8')
index_html = (APP / 'static' / 'index.html').read_text(encoding='utf-8')
manifest = json.loads((APP / 'build-manifest.json').read_text(encoding='utf-8'))

# 1. Pure header-window helpers must keep every large interactive range bounded and
# newest-first. Extract only the constants/helpers so the guard never starts NewzDeck.
tree = ast.parse(server_text)
wanted_constants = {'BROWSE_OVERVIEW_CHUNK_HEADERS', 'BROWSE_FIRST_PAINT_HEADERS', 'BROWSE_LARGE_PAGE_THRESHOLD'}
body = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in wanted_constants for name in names):
            body.append(node)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in wanted_constants:
        body.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in {'_overview_chunk_ranges', '_first_paint_overview_range'}:
        body.append(node)
helper_module = ast.Module(body=body, type_ignores=[])
ast.fix_missing_locations(helper_module)
ns: dict[str, object] = {}
exec(compile(helper_module, '<v3661-browse-helpers>', 'exec'), ns)
chunk = ns['_overview_chunk_ranges']
first = ns['_first_paint_overview_range']
check(chunk(1, 2200) == [(1401, 2200), (601, 1400), (1, 600)], f'Large overview is not split newest-first into <=800-header chunks: {chunk(1, 2200)}')
check(first(1, 2200, 201, 2200, 2000, True, True) == (1401, 2200, True), 'Page-1 progressive first paint is not exactly the newest 800 logical-page headers.')
check(first(4801, 7200, 5001, 7000, 2000, True, True) == (6201, 7000, True), 'Older-page overlap leaked into the progressive first-paint window.')
check(first(4801, 7200, 5001, 7000, 2000, False, True) == (4801, 7200, False), 'Non-progressive header range semantics changed unexpectedly.')

# 2. Backend integration: first paint must hand the complete original logical range
# to the existing background reconstruction path, which then performs bounded chunks
# and deeper opaque multipart expansion without refetching the initial page wholesale.
for marker in (
    'def overview_chunked(',
    'background_smart = (full_fetch_start, full_fetch_end)',
    'raw_articles = client.overview(first_start, first_end); overview_calls = 1',
    'def _merge_overview_headers(',
    'missing_ranges: list[tuple[int, int]] = []',
    'background_seed_headers_reused',
    'SMART_BROWSE_EXECUTOR.submit(_finish_progressive_smart_page',
):
    check(marker in server_text, f'Missing carried progressive-header marker: {marker}')
check('BROWSE_OVERVIEW_CHUNK_HEADERS = 800' in server_text and 'BROWSE_FIRST_PAINT_HEADERS = 800' in server_text, 'Carried 800-header bounds changed unexpectedly.')

# 3. Passive telemetry must be bounded, mode-attributed, and exposed only through
# diagnostics plus the normal UI sample-post endpoint. The Diagnostic Collector does
# not need to generate /api/articles, preview, or thumbnail workload.
for marker in (
    "'newsgroup_browsing_performance': newsgroup_browsing_performance_snapshot()",
    '"contract": "passive-runtime-browsing-performance"',
    'if parsed.path == "/api/browse/performance":',
    'note_browser_performance_samples(data.get("samples"))',
    '_BROWSER_PERF_SAMPLE_LIMIT = 240',
    '_BROWSER_PERF_ALLOWED_MODES = {"images", "videos", "media", "all"}',
):
    check(marker in server_text, f'Missing passive browsing telemetry marker: {marker}')
for marker in (
    'perfTelemetryPending:[]',
    'schedulePerfTelemetryFlush',
    "api('/api/browse/performance',{samples},{timeoutMs:2500})",
    'content_filter:browserPerfMode()',
    "perfRecord('preview',performance.now()-started,false)",
):
    check(marker in app_js, f'Missing browser-side passive telemetry marker: {marker}')

# 4. Preserve the v3.6.60 Discover optimization stack and all established runtime
# architecture while only migrating current version markers.
check("const UI_VERSION = '3.6.72'" in app_js, 'UI version marker is not v3.6.72.')
check('3.6.72-browse-timeout-error-attribution' in index_html, 'v3.6.72 static cache identity is missing.')
check('<div class="version"><b>NewzDeck</b><span>v3.6.72</span></div>' in index_html, 'Visible sidebar version is not v3.6.72.')
check((APP / 'version.txt').read_text(encoding='utf-8').strip() == '3.6.72', 'version.txt is not v3.6.72.')
check(manifest.get('version') == '3.6.72' and manifest.get('base_version') == '3.6.71', f'Build manifest version/base mismatch: {manifest}')
check(manifest.get('adapter_version') == '3.6.72' and manifest.get('sab_version') == '5.1.2', f'Build manifest adapter/SAB mismatch: {manifest}')
check(sab.ADAPTER_VERSION == '3.6.72', f'Wrong SAB adapter identity: {sab.ADAPTER_VERSION}')
check(sab.SAB_VERSION == '5.1.2' and sab.TERMINAL_HISTORY_VERSION == 3, 'v3.6.72 changed SAB 5.1.2 or terminal-history schema 3.')
check("version='3.6.72'" in (APP / 'automation_engine.py').read_text(encoding='utf-8'), 'Automation default version identity did not migrate to v3.6.72.')
check('_discover_library_index_snapshot' in (APP / 'automation_engine.py').read_text(encoding='utf-8'), 'v3.6.60 Discover library index was not preserved.')
check('_flush_metadata_cache_now' in (APP / 'automation_engine.py').read_text(encoding='utf-8'), 'v3.6.60 metadata-cache coalescing was not preserved.')

print('v3.6.72 regression guard: PASS')
