#!/usr/bin/env python3
"""v3.7.22 video filename-restoration behavior: single-job identity and collision safety."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import tempfile
import threading

SRC = Path(__file__).resolve().parents[2] / 'src/app/sab_engine.py'
spec = importlib.util.spec_from_file_location('newzdeck_sab_video_name_test', SRC)
sab = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sab
spec.loader.exec_module(sab)

TOKEN = 'NewzDeck Loose 9f90e233b029'
VIDEO = 'Family Vacation 2026 - Part 01.mkv'


def check(condition, message):
    if not condition:
        raise AssertionError('v3.7.22 loose video: ' + message)


def case(label, names, expected, *, direct=False, stage_name=TOKEN, exists=(), result_names=None, should_succeed=True):
    with tempfile.TemporaryDirectory(prefix='newzdeck-video-name-') as temporary:
        root = Path(temporary)
        stage = root if direct else root / stage_name
        if not direct:
            stage.mkdir()
        for name in names:
            (stage / name).write_bytes(b'video-payload-' + name.encode('utf-8'))
        for name in exists:
            (root / name).write_bytes(b'preexisting-user-file')
        obj = object.__new__(sab.SabDownloadManager)
        obj.download_dir_getter = lambda: root
        obj.lock = threading.RLock()
        events = []
        obj._event = lambda *a, **kw: events.append((a, kw))
        meta = {'name': expected[0] if expected else 'Fallback', 'browser_flat_images': True,
                'browser_flattened': False, 'browser_flat_filenames': expected,
                'browser_flat_staging_name': stage_name, 'browser_group': 'alt.binaries.videos'}
        tracked = {'job-001': meta}
        obj._tracked = lambda: tracked
        obj._touch_job_locked = lambda _: None
        obj._save_state = lambda: None
        obj._browser_name_recovery_after_flatten = lambda *args: args[-1]
        slot = {'storage': str(root / names[0] if direct else stage), 'status': 'Completed',
                'filename': stage_name}
        worked = obj._flatten_completed_browser_images('job-001', meta, slot)
        check(worked is should_succeed, label + ': result')
        actual = sorted(x.name for x in root.iterdir() if x.is_file())
        if result_names is not None:
            check(actual == sorted(result_names), label + f': files {actual} != {result_names}')
        for name in exists:
            check((root / name).read_bytes() == b'preexisting-user-file', label + ': overwrote an existing file')
        if should_succeed:
            check(Path(slot['storage']).samefile(root), label + ': SAB history storage not root')
            check(meta['browser_flattened_files'] == (result_names or names)[:len(names)] or
                  sorted(meta['browser_flattened_files']) == sorted(x for x in actual if x not in exists),
                  label + ': persisted completed filenames disagree with disk')
            if len(meta['browser_flattened_files']) == 1:
                shown = obj._job_from_slot('job-001', meta, slot, history=True)
                check(shown['filename'] == meta['browser_flattened_files'][0], label + ': Completed filename incorrect')
                check(shown['display_name'] == meta['browser_flattened_files'][0], label + ': Completed display name incorrect')
        return events


f = sab.SabDownloadManager._browser_final_loose_name
for ext in ('.mp4', '.mkv', '.m4v', '.avi', '.mov', '.wmv', '.ts', '.m2ts', '.webm', '.mpg', '.mpeg'):
    expected = 'Real Video' + ext
    check(f(TOKEN + ext, [expected], TOKEN) == expected, 'failed to restore ' + ext)
    check(f(TOKEN + ' (2)' + ext, [expected], TOKEN) == expected, 'SAB numbered suffix ' + ext)
    check(f(TOKEN + ext.upper(), [expected], TOKEN) == expected, 'case-insensitive video extension ' + ext)
check(f(TOKEN + '.jpg', ['Real Image.jpg'], TOKEN) == 'Real Image.jpg', 'regressed image fix')
check(f(TOKEN + '.mp4', ['Wrong Extension.mkv'], TOKEN) == TOKEN + '.mp4', 'changed extension')
check(f(TOKEN + '.mp4', ['file.bin'], TOKEN) == TOKEN + '.mp4', 'opaque expected')
check(f(TOKEN + '.mp4', [], TOKEN) == TOKEN + '.mp4', 'missing expected')
check(f(TOKEN + '.mp4', ['one.mp4','two.mp4'], TOKEN) == TOKEN + '.mp4', 'multiple expected')
check(f(TOKEN + '.mp4', ['Legit.mp4'], 'NewzDeck Loose abcdef123456') == TOKEN + '.mp4', 'different job token')
check(f('Original Title.mp4', ['Different Title.mp4'], TOKEN) == 'Original Title.mp4', 'real decoded name changed')
check(f(TOKEN + '.zip', ['Original Title.zip'], TOKEN) == TOKEN + '.zip', 'archive renamed')
check(f(TOKEN + '.exe', ['Original Title.exe'], TOKEN) == TOKEN + '.exe', 'executable renamed')
check(f(TOKEN + '.mp4', ['NewzDeck Loose 000000000000.mp4'], TOKEN) == TOKEN + '.mp4', 'opaque saved name')
case('stage video', [TOKEN + '.mkv'], [VIDEO], result_names=[VIDEO])
case('stage mp4', [TOKEN + '.mp4'], ['Short Film.mp4'], result_names=['Short Film.mp4'])
case('direct root', [TOKEN + '.mkv'], [VIDEO], direct=True, result_names=[VIDEO])
case('numbered title', [TOKEN + ' (2).mkv'], [VIDEO], result_names=[VIDEO])
case('collision', [TOKEN + '.mkv'], [VIDEO], exists=[VIDEO], result_names=[VIDEO, 'Family Vacation 2026 - Part 01 (2).mkv'])
case('leave real decoded name', ['Authentic Title.mkv'], [VIDEO], result_names=['Authentic Title.mkv'])
case('different token', [TOKEN + '.mkv'], [VIDEO], stage_name='NewzDeck Loose abcdef123456', result_names=[TOKEN + '.mkv'])
case('keep other formats', [TOKEN + '.zip'], ['Archive.zip'], result_names=[TOKEN + '.zip'])
case('leave 2-file job intact', ['One.mkv','Two.mkv'], ['One.mkv','Two.mkv'], result_names=['One.mkv','Two.mkv'])
print('validate-v3722-loose-video.py: PASS (video/image, staged/root, collision, Completed, mismatch, packages)')
