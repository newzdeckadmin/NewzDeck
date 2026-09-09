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


auto = load_module('newzdeck_v3659_automation_guard', APP / 'automation_engine.py')
sab = load_module('newzdeck_v3659_sab_guard', APP / 'sab_engine.py')


class DummyDownloadManager:
    pass


def make_auto(root: Path):
    return auto.MediaAutomationEngine(root, lambda value: value, lambda value: value, DummyDownloadManager(), lambda: [], version='3.6.62')


def check(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def raw_movie(tid: int = 123, title: str = 'Cache Test Movie') -> dict:
    return {
        'tmdb_id': tid, 'media_type': 'movie', 'title': title, 'original_title': title,
        'release_date': '2026-01-02', 'overview': 'Cached detail payload', 'images': {},
        'genres': ['Drama'], 'rating': 7.5, 'popularity': 12.0, 'vote_count': 50,
        'original_language': 'en', 'external_ids': {}, 'cast': [], 'crew': [], 'videos': [],
        'recommendations': [], 'similar': [], 'production_companies': [], 'countries': [],
    }


# 1. metadata-cache.json must parse once, reuse memory, detect peer changes before write,
# and use compact JSON rather than pretty-printing a multi-megabyte hot cache.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3659-metadata-cache-') as td:
    root = Path(td)
    now = time.time()
    seed = {'cloud:test': {'ts': now, 'value': {'ok': True, 'payload': 'x' * 2048}}}
    (root / 'metadata-cache.json').write_text(json.dumps(seed, indent=2), encoding='utf-8')
    engine = make_auto(root)
    check(engine._cache_get('cloud:test') == seed['cloud:test']['value'], 'Initial metadata-cache read failed.')
    check(engine._cache_get('cloud:test') == seed['cloud:test']['value'], 'Repeated metadata-cache read changed the cached value.')
    snap = engine.discover_performance_snapshot()['metadata_cache']
    check(int(snap.get('disk_reads') or 0) == 1, f'Metadata cache reparsed unexpectedly: {snap}')
    check(int(snap.get('memory_hits') or 0) >= 1, f'Metadata cache did not report an in-memory hit: {snap}')

    # Simulate another NewzDeck process changing the shared cache after this process
    # has already parsed it. The next local write must reload/merge that peer state.
    peer = dict(seed)
    peer['cloud:peer'] = {'ts': now + 1, 'value': {'peer': True, 'padding': 'y' * 17}}
    time.sleep(0.01)
    (root / 'metadata-cache.json').write_text(json.dumps(peer, indent=2), encoding='utf-8')
    engine._cache_put('cloud:local', {'local': True})
    check(engine._flush_metadata_cache_now() is True, 'v3.6.62 coalesced cache flush failed while preserving v3.6.59 peer-merge semantics.')
    persisted = json.loads((root / 'metadata-cache.json').read_text(encoding='utf-8'))
    check('cloud:peer' in persisted and 'cloud:local' in persisted, 'Signature-aware cache write overwrote peer-process state.')
    raw = (root / 'metadata-cache.json').read_text(encoding='utf-8')
    check('\n  "' not in raw, 'metadata-cache.json is still being pretty-printed instead of compact-written.')
    snap = engine.discover_performance_snapshot()['metadata_cache']
    check(int(snap.get('disk_reads') or 0) >= 2, f'Peer cache change was not reloaded before write: {snap}')
    check(int(snap.get('writes') or 0) == 1, f'Unexpected metadata-cache write count: {snap}')

# 2. Stale persisted detail must return immediately, schedule refresh, and prefetch must
# never count as a viewed-title personalization event.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3659-detail-stale-') as td:
    root = Path(td)
    engine = make_auto(root)
    movie = raw_movie()
    cloud_key = engine._discover_detail_cloud_cache_key('movie', 123)
    (root / 'metadata-cache.json').write_text(json.dumps({cloud_key: {'ts': time.time() - 7200, 'value': movie}}), encoding='utf-8')
    engine._metadata_cache_memory = None
    engine._metadata_cache_signature = None
    refresh_calls = []
    engine._start_discover_detail_refresh = lambda kind, ident, key: refresh_calls.append((kind, ident, key)) or True
    prefetched = engine.discover_detail({'provider': 'tmdb', 'tmdb_id': 123, 'kind': 'movie', 'interaction': 'prefetch'})
    check(prefetched.get('performance', {}).get('detail_source') == 'persistent', f'Stale persisted detail did not use persistent cache: {prefetched}')
    check(prefetched.get('performance', {}).get('stale') is True, 'Old persistent detail was not identified as stale.')
    check(len(refresh_calls) == 1, 'Stale persisted detail did not schedule one background refresh.')
    state = json.loads((root / 'discover-state.json').read_text(encoding='utf-8')) if (root / 'discover-state.json').exists() else {}
    check(not (state.get('viewed') or {}), 'Hover prefetch incorrectly recorded a viewed title.')

    opened = engine.discover_detail({'provider': 'tmdb', 'tmdb_id': 123, 'kind': 'movie', 'interaction': 'open'})
    state = json.loads((root / 'discover-state.json').read_text(encoding='utf-8'))
    check(len(state.get('viewed') or {}) == 1, 'Explicit Discover open did not record viewed-title feedback.')
    check(opened.get('performance', {}).get('detail_source') == 'memory', 'Explicit open did not reuse the in-memory detail cache after prefetch.')

# 3. A true cold detail miss is bounded to 8 seconds at the metadata API layer.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3659-detail-cold-') as td:
    root = Path(td)
    engine = make_auto(root)
    calls = []
    movie = raw_movie(456, 'Cold Detail Movie')
    def fake_metadata(path, params=None, timeout=12, *, allow_cached_fallback=True):
        calls.append((path, timeout, allow_cached_fallback))
        return movie
    engine._metadata_api = fake_metadata
    cold = engine.discover_detail({'provider': 'tmdb', 'tmdb_id': 456, 'kind': 'movie', 'interaction': 'open'})
    check(calls and calls[0][1] == 8, f'Cold detail metadata budget is not 8 seconds: {calls}')
    check(cold.get('performance', {}).get('detail_source') == 'cloud', f'Cold detail did not report cloud source: {cold}')

# 4. Discover route telemetry must expose bounded percentiles and detail/cache counters.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3659-telemetry-') as td:
    engine = make_auto(Path(td))
    for value in (10, 20, 30, 40, 50):
        engine.note_discover_request('detail', value, ok=value < 50)
    snap = engine.discover_performance_snapshot()
    route = (snap.get('routes') or {}).get('detail') or {}
    check(int(route.get('count') or 0) == 5 and int(route.get('errors') or 0) == 1, f'Discover route counters are wrong: {route}')
    check(float(route.get('p95_ms') or 0) >= 40, f'Discover route p95 was not retained: {route}')
    check(int(snap.get('detail_refresh_limit') or 0) == 2, 'Detail background refresh concurrency cap is not exposed as 2.')

# 5. Static/runtime integration markers: UI prefetch must be delayed/bounded and the
# diagnostics snapshot/report must expose Discover performance without probing endpoints.
app_js = (APP / 'static' / 'app.js').read_text(encoding='utf-8')
server_text = (APP / 'server.py').read_text(encoding='utf-8')
index_html = (APP / 'static' / 'index.html').read_text(encoding='utf-8')
check("const UI_VERSION = '3.6.62'" in app_js, 'UI version marker is not v3.6.62.')
check('discoverDetailPrefetchLimit:2' in app_js and '},650)' in app_js and 'fetchDiscoverDetail(item,{prefetch:true})' in app_js, 'Hover-prefetch dwell/concurrency guard is missing.')
check("interaction='open'" in app_js and "interaction:'open'" not in app_js, 'Discover interaction payload helper changed unexpectedly.')
check('renderDiscoverDetailPreview' in app_js, 'Progressive Discover detail preview is missing.')
check("'discover_performance': MEDIA_AUTOMATION.discover_performance_snapshot()" in server_text, 'Discover performance is missing from diagnostics JSON.')
check('Discover performance:' in server_text and "_discover_response('detail'" in server_text, 'Discover route/report telemetry wiring is missing.')
check('3.6.62-progressive-header-reuse-thumbnail-phase-telemetry' in index_html, 'v3.6.62 static cache identity marker is missing.')

# 6. Release identities stay coherent while SAB behavior/version remains unchanged.
manifest = json.loads((APP / 'build-manifest.json').read_text(encoding='utf-8'))
check((APP / 'version.txt').read_text(encoding='utf-8').strip() == '3.6.62', 'version.txt is not v3.6.62.')
check(manifest.get('version') == '3.6.62' and manifest.get('base_version') == '3.6.61', f'Build manifest version/base mismatch: {manifest}')
check(manifest.get('adapter_version') == '3.6.62' and manifest.get('sab_version') == '5.1.2', f'Build manifest adapter/SAB mismatch: {manifest}')
check(sab.ADAPTER_VERSION == '3.6.62', f'Wrong SAB adapter identity: {sab.ADAPTER_VERSION}')
check(sab.SAB_VERSION == '5.1.2' and sab.TERMINAL_HISTORY_VERSION == 3, 'v3.6.62 changed SAB 5.1.2 or terminal-history schema unexpectedly.')

print('v3.6.62 regression guard: PASS')
