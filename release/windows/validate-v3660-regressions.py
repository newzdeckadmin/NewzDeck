from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import time
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


auto = load_module('newzdeck_v3660_automation_guard', APP / 'automation_engine.py')
sab = load_module('newzdeck_v3660_sab_guard', APP / 'sab_engine.py')


class DummyDownloadManager:
    pass


def make_auto(root: Path):
    engine = auto.MediaAutomationEngine(root, lambda value: value, lambda value: value, DummyDownloadManager(), lambda: [], version='3.6.72')
    # Keep timer-driven persistence out of deterministic fixture timing. Tests call
    # the same production flush method explicitly after verifying in-memory state.
    engine._metadata_cache_flush_delay_seconds = 60
    return engine


def check(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def movie_record(item_id: str, tmdb_id: int, title: str, *, year: int = 2026, has_file: bool = True) -> dict:
    return {
        'id': item_id, 'kind': 'movie', 'title': title, 'year': year,
        'metadata_provider': 'tmdb', 'metadata_id': str(tmdb_id), 'tmdb_id': tmdb_id,
        'monitored': True, 'movie_file': f'{title}.mkv' if has_file else '', 'genres': ['Drama'],
    }


# 1. Discover library status must parse/build one index, reuse it for subsequent cards,
# preserve metadata/TMDB/title matching, and rebuild only after the library signature changes.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3660-library-index-') as td:
    root = Path(td)
    library = [movie_record('m1', 101, 'Indexed Movie')]
    library.append({
        'id': 't1', 'kind': 'tv', 'title': 'Indexed Show', 'year': 2025,
        'metadata_provider': 'tmdb', 'metadata_id': '202', 'tmdb_id': 202,
        'monitored': True, 'genres': ['Comedy'], 'seasons': [],
    })
    (root / 'media-library.json').write_text(json.dumps(library), encoding='utf-8')
    engine = make_auto(root)
    one = engine._discover_library_status({'provider': 'tmdb', 'metadata_id': '101', 'tmdb_id': 101, 'title': 'Indexed Movie', 'year': 2026})
    two = engine._discover_library_status({'provider': 'tmdb', 'metadata_id': '202', 'tmdb_id': 202, 'title': 'Indexed Show', 'year': 2025})
    title_fallback = engine._discover_library_status({'provider': 'other', 'metadata_id': '', 'title': 'Indexed Movie', 'year': 2026})
    check(one.get('in_library') and one.get('library_id') == 'm1', f'Metadata-ID index lookup failed: {one}')
    check(two.get('in_library') and two.get('library_id') == 't1', f'TMDB index lookup failed: {two}')
    check(title_fallback.get('in_library') and title_fallback.get('library_id') == 'm1', f'Title/year fallback changed semantics: {title_fallback}')
    snap = engine.discover_performance_snapshot()['library_index']
    check(int(snap.get('builds') or 0) == 1 and int(snap.get('misses') or 0) == 1, f'Library index rebuilt during unchanged card decoration: {snap}')
    check(int(snap.get('hits') or 0) >= 2 and int(snap.get('records') or 0) == 2, f'Library index reuse telemetry is wrong: {snap}')

    library.append(movie_record('m2', 303, 'Peer Library Change', year=2024, has_file=False))
    time.sleep(0.01)
    (root / 'media-library.json').write_text(json.dumps(library), encoding='utf-8')
    changed = engine._discover_library_status({'provider': 'tmdb', 'metadata_id': '303', 'tmdb_id': 303, 'title': 'Peer Library Change', 'year': 2024})
    snap = engine.discover_performance_snapshot()['library_index']
    check(changed.get('in_library') and changed.get('library_id') == 'm2', f'Changed library was not reindexed: {changed}')
    check(int(snap.get('builds') or 0) == 2 and int(snap.get('records') or 0) == 3, f'Library signature change did not cause exactly one rebuild: {snap}')

# 2. Bursty metadata-cache puts must be instantly readable from memory but result in one
# physical compact write when flushed, while merging a peer-process disk update first.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3660-cache-coalesce-') as td:
    root = Path(td)
    now = time.time()
    seed = {'cloud:seed': {'ts': now, 'value': {'seed': True}}}
    (root / 'metadata-cache.json').write_text(json.dumps(seed), encoding='utf-8')
    engine = make_auto(root)
    check(engine._cache_get('cloud:seed') == {'seed': True}, 'Initial metadata cache read failed.')
    for index in range(6):
        engine._cache_put(f'cloud:local:{index}', {'index': index})
    check(engine._cache_get('cloud:local:5') == {'index': 5}, 'Dirty cache put was not immediately readable from memory.')
    before = engine.discover_performance_snapshot()['metadata_cache']
    check(int(before.get('write_requests') or 0) == 6 and int(before.get('writes') or 0) == 0, f'Cache puts still performed synchronous disk writes: {before}')
    check(int(before.get('coalesced_write_requests') or 0) == 5 and int(before.get('dirty_keys') or 0) == 6, f'Cache coalescing telemetry is wrong before flush: {before}')

    peer = dict(seed)
    peer['cloud:peer'] = {'ts': now + 1, 'value': {'peer': True}}
    time.sleep(0.01)
    (root / 'metadata-cache.json').write_text(json.dumps(peer), encoding='utf-8')
    check(engine._flush_metadata_cache_now() is True, 'Coalesced metadata cache flush did not succeed.')
    persisted = json.loads((root / 'metadata-cache.json').read_text(encoding='utf-8'))
    check('cloud:peer' in persisted and all(f'cloud:local:{i}' in persisted for i in range(6)), 'Coalesced flush lost peer or local cache entries.')
    raw = (root / 'metadata-cache.json').read_text(encoding='utf-8')
    check('\n  "' not in raw, 'Coalesced metadata cache flush stopped using compact JSON.')
    after = engine.discover_performance_snapshot()['metadata_cache']
    check(int(after.get('writes') or 0) == 1 and int(after.get('write_requests') or 0) == 6, f'Burst did not collapse to one physical write: {after}')
    check(int(after.get('dirty_keys') or 0) == 0 and int(after.get('pending_write_requests') or 0) == 0, f'Dirty cache state survived a successful flush: {after}')
    check(int(after.get('disk_reads') or 0) >= 2, f'Peer disk change was not reloaded before coalesced write: {after}')

# 3. Tiny-sample route statistics must be mathematically honest and include average/sample count.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3660-percentiles-') as td:
    engine = make_auto(Path(td))
    engine.note_discover_request('detail', 100, ok=True)
    engine.note_discover_request('detail', 300, ok=True)
    route = engine.discover_performance_snapshot()['routes']['detail']
    check(float(route.get('p50_ms') or 0) == 200.0, f'Two-sample p50 should interpolate to 200ms: {route}')
    check(float(route.get('p95_ms') or 0) == 290.0, f'Two-sample p95 should interpolate to 290ms: {route}')
    check(float(route.get('avg_ms') or 0) == 200.0 and int(route.get('sample_count') or 0) == 2, f'Route average/sample telemetry is missing: {route}')

# 4. Static diagnostics/runtime contract: new library-index and write-coalescing fields
# must be exposed without changing the v3.6.59 Detail/prefetch behavior or cloud budgets.
auto_text = (APP / 'automation_engine.py').read_text(encoding='utf-8')
server_text = (APP / 'server.py').read_text(encoding='utf-8')
app_js = (APP / 'static' / 'app.js').read_text(encoding='utf-8')
index_html = (APP / 'static' / 'index.html').read_text(encoding='utf-8')
check('_discover_library_index_snapshot' in auto_text and "'library_index':library_stats" in auto_text, 'Discover library-index implementation/telemetry is missing.')
check('_flush_metadata_cache_now' in auto_text and '_metadata_cache_coalesced_write_requests' in auto_text, 'Metadata-cache write coalescing implementation is missing.')
check('cache_write_requests=' in server_text and 'library_index_builds=' in server_text, 'Diagnostics report does not expose v3.6.72 local-data-path telemetry.')
check("const UI_VERSION = '3.6.72'" in app_js, 'UI version marker is not v3.6.72.')
check('discoverDetailPrefetchLimit:2' in app_js and '},650)' in app_js, 'v3.6.59 conservative hover prefetch was not preserved.')
check('3.6.72-browse-timeout-error-attribution' in index_html, 'v3.6.72 static cache identity marker is missing.')
check('<div class="version"><b>NewzDeck</b><span>v3.6.72</span></div>' in index_html, 'Visible sidebar footer version is not v3.6.72.')

# 5. Release identities stay coherent while Metadata Server/SAB/terminal history stay unchanged.
manifest = json.loads((APP / 'build-manifest.json').read_text(encoding='utf-8'))
check((APP / 'version.txt').read_text(encoding='utf-8').strip() == '3.6.72', 'version.txt is not v3.6.72.')
check(manifest.get('version') == '3.6.72' and manifest.get('base_version') == '3.6.71', f'Build manifest version/base mismatch: {manifest}')
check(manifest.get('adapter_version') == '3.6.72' and manifest.get('sab_version') == '5.1.2', f'Build manifest adapter/SAB mismatch: {manifest}')
check(sab.ADAPTER_VERSION == '3.6.72', f'Wrong SAB adapter identity: {sab.ADAPTER_VERSION}')
check(sab.SAB_VERSION == '5.1.2' and sab.TERMINAL_HISTORY_VERSION == 3, 'v3.6.72 changed SAB 5.1.2 or terminal-history schema unexpectedly.')
check("timeout=8" in auto_text and "interaction=='prefetch'" in auto_text, 'v3.6.59 bounded Detail/prefetch semantics were not preserved.')

print('v3.6.72 regression guard: PASS')
