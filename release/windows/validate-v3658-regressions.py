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

auto = load_module('newzdeck_v3658_automation_guard', APP / 'automation_engine.py')
sab = load_module('newzdeck_v3658_sab_guard', APP / 'sab_engine.py')

class DummyDownloadManager:
    pass

def make_auto(root: Path):
    return auto.MediaAutomationEngine(root, lambda value: value, lambda value: value, DummyDownloadManager(), lambda: [], version='3.6.66')

def check(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)

# 1. Orphan target pruning must be authoritative, age-gated, and fail-safe.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3658-runtime-prune-') as td:
    root = Path(td)
    now = time.time()
    library = [{
        'id': 'show-current', 'kind': 'tv', 'title': 'Current Show',
        'seasons': [{'season_number': 1, 'episodes': [{'episode_number': 1, 'has_file': True, 'file_path': r'X:\TV\Current Show\Season 1\Current Show - S01E01.mkv'}]}],
    }]
    (root / 'media-library.json').write_text(json.dumps(library), encoding='utf-8')
    seeded = {'targets': {
        'tv:show-current:s01e001': {'status': 'imported', 'updated_ts': now - 100},
        'tv:deleted-old:s01e001': {'status': 'waiting', 'updated_ts': now - 2 * 86400},
        'tv:deleted-recent:s01e001': {'status': 'waiting', 'updated_ts': now - 900},
        'manual:opaque-target': {'status': 'waiting', 'updated_ts': now - 2 * 86400},
    }}
    (root / 'automation-runtime.json').write_text(json.dumps(seeded), encoding='utf-8')
    engine = make_auto(root)
    persisted = json.loads((root / 'automation-runtime.json').read_text(encoding='utf-8'))
    targets = persisted['targets']
    check('tv:deleted-old:s01e001' not in targets, 'Old canonical orphan target was not pruned.')
    check('tv:deleted-recent:s01e001' in targets, 'Recent orphan target ignored the grace window.')
    check('manual:opaque-target' in targets, 'Unparseable/opaque target was pruned instead of failing safe.')
    prune = persisted.get('runtime_prune') or {}
    check(int(prune.get('orphan_targets_pruned') or 0) == 1, f'Unexpected prune count: {prune}')
    check(int(prune.get('orphan_target_bytes_reclaimed') or 0) > 0, 'Prune telemetry did not report reclaimed bytes.')

    # A malformed authoritative library must disable destructive cleanup.
    persisted['targets']['tv:deleted-old-2:s01e001'] = {'status': 'waiting', 'updated_ts': now - 3 * 86400}
    (root / 'automation-runtime.json').write_text(json.dumps(persisted), encoding='utf-8')
    (root / 'media-library.json').write_text('{malformed', encoding='utf-8')
    engine._runtime_orphan_prune_last_attempt_ts = 0
    engine._prune_orphan_runtime_targets(force=True)
    malformed_result = json.loads((root / 'automation-runtime.json').read_text(encoding='utf-8'))
    check('tv:deleted-old-2:s01e001' in malformed_result['targets'], 'Malformed library caused fail-open deletion.')

# 2. Library-proven final state must beat a stale later scheduler write, but not a real newer grab.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3658-semantic-merge-') as td:
    root = Path(td)
    now = time.time()
    library = [{
        'id': 'love-island-games', 'kind': 'tv', 'title': 'Love Island Games',
        'seasons': [{'season_number': 1, 'episodes': [{'episode_number': 1, 'has_file': True, 'file_path': r'X:\TV\Love Island Games\Season 1\Love Island Games - S01E01.mkv'}]}],
    }]
    (root / 'media-library.json').write_text(json.dumps(library), encoding='utf-8')
    key = 'tv:love-island-games:s01e001'
    final = {'targets': {key: {'status': 'imported', 'message': 'Imported S01E01', 'updated_ts': now, 'imported_path': r'X:\TV\Love Island Games\Season 1\Love Island Games - S01E01.mkv'}}}
    (root / 'automation-runtime.json').write_text(json.dumps(final), encoding='utf-8')
    engine = make_auto(root)

    stale_cycle = {'targets': {key: {
        'status': 'grabbed', 'message': 'Queued stale candidate',
        'updated_ts': now + 20, 'last_search_ts': now + 20,
        'last_grab_ts': now - 60, 'last_grab_title': 'stale.release',
    }}}
    merged = engine._merge_auto_runtime_concurrent(stale_cycle)
    check(merged['targets'][key]['status'] == 'imported', f"Stale scheduler demoted imported state: {merged['targets'][key]}")
    check(int(engine.target_integrity_telemetry().get('stale_state_demotions_blocked') or 0) >= 1, 'Blocked stale-state demotion was not counted.')

    genuine_new_grab = {'targets': {key: {
        'status': 'grabbed', 'message': 'Explicit newer grab',
        'updated_ts': now + 40, 'last_grab_ts': now + 30,
        'last_grab_title': 'newer.release',
    }}}
    merged_new = engine._merge_auto_runtime_concurrent(genuine_new_grab)
    check(merged_new['targets'][key]['status'] == 'grabbed', 'A genuinely newer grab was incorrectly suppressed by final-state precedence.')

# 3. Legacy v3.6.56 duplicate-content hold evidence is historical normalization only.
with tempfile.TemporaryDirectory(prefix='newzdeck-v3658-history-normalize-') as td:
    root = Path(td)
    user = root / 'user'; app = root / 'app'; completed = root / 'completed'
    app.mkdir(); completed.mkdir(); (user / 'sab-engine').mkdir(parents=True)
    legacy = {'version': 2, 'rows': {'legacy-hold': {
        'id': 'legacy-hold', 'status': 'completed', 'created_ts': 50.0, 'completed_ts': 100.0,
        'post_status': 'failed', 'failure_class': '',
        'post_message': 'Smart Import was held for review because incoming media is byte-identical to another episode already in this library title.',
    }}}
    (user / 'sab-engine' / 'terminal-history.json').write_text(json.dumps(legacy), encoding='utf-8')
    manager = sab.SabDownloadManager(
        user_root=user, app_dir=app, download_dir_getter=lambda: completed,
        settings_getter=lambda: {}, providers_getter=lambda: [], secret_unprotect=lambda value: value,
        parse_nzb=lambda payload, name: {'files': []}, diagnostics=None, start_threads=False,
    )
    history = json.loads((user / 'sab-engine' / 'terminal-history.json').read_text(encoding='utf-8'))
    row = history['rows']['legacy-hold']
    check(int(history.get('version') or 0) == 3, 'Terminal history schema was not upgraded to v3.')
    check(row.get('failure_class') == 'import_integrity_hold', f'Legacy hold was not normalized: {row}')
    check(row.get('historical_integrity_hold_normalized') is True, 'Historical normalization marker is missing.')
    # No Automation runtime is created by this historical-only SAB migration.
    check(not (user / 'automation-runtime.json').exists(), 'Historical normalization unexpectedly created active Automation policy state.')
    rebuilds = manager._terminal_history_index_rebuilds
    noops = manager._terminal_history_sync_noops
    changed = manager._sync_terminal_history_from_state(persist=True)
    check(changed == 0, 'Post-migration no-op terminal sync unexpectedly mutated history.')
    check(manager._terminal_history_sync_noops == noops + 1, 'v3.6.55 no-op history fast path regressed.')
    check(manager._terminal_history_index_rebuilds == rebuilds, 'No-op history sync rebuilt the terminal index.')

# 4. Diagnostics must measure report construction rather than optimize blindly.
server_text = (APP / 'server.py').read_text(encoding='utf-8')
for marker in (
    'diagnostics_report_build_ms',
    '_record_diagnostics_report_build',
    'report_started=time.perf_counter()',
    "'automation_runtime_efficiency': MEDIA_AUTOMATION.automation_runtime_efficiency()",
    'stale_state_demotions_blocked',
):
    check(marker in server_text, f'Missing diagnostics/runtime marker: {marker}')

check(sab.ADAPTER_VERSION == '3.6.66', f'Wrong SAB adapter version: {sab.ADAPTER_VERSION}')
check(sab.SAB_VERSION == '5.1.2', f'Private SAB version changed unexpectedly: {sab.SAB_VERSION}')
check(int(sab.TERMINAL_HISTORY_VERSION) == 3, 'Expected terminal history schema v3.')
print('v3.6.66 regression guard: PASS')
