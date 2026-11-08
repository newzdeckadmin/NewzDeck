#!/usr/bin/env python3
"""v3.7.27 regression gate: lightweight live progress and no destructive changes."""
from pathlib import Path
import ast,re,json
root=Path(__file__).resolve().parents[2]
s=(root/'src/app/server.py').read_text(encoding='utf-8')
a=(root/'src/app/sab_engine.py').read_text(encoding='utf-8')
j=(root/'src/app/static/app.js').read_text(encoding='utf-8')
assert 'def presentation_pulse(self, limit: int = 500)' in a
pulse=a.split('    def presentation_pulse(',1)[1].split('    def _queue_and_history(',1)[0]
for forbidden in ('self._api(', 'self._save_state(', 'self._queue_and_history_fetch(', 'self.snapshot('):
    assert forbidden not in pulse,('pulse contains blocking or state-changing operation',forbidden)
assert '_queue_sample_lock' in pulse and 'age <= 3.0' in pulse
for route in ['/api/downloads/pulse','/api/diagnostics/ping','/api/diagnostics']:
    assert route in s
assert 'return self._json(200, diagnostics_snapshot())' in s
assert 'return self._json(200, DOWNLOAD_MANAGER.add(provider_id, group, items))' in s
assert 'source-delta' not in s
assert 'def _parse_yenc_part(' in s and '_parse_yenc_part(control, meta)' in s
assert 'class GroupSearchManager:' in s
for marker in ('downloadBulkQueueActive++','downloadBulkQueueActive=Math.max(0,downloadBulkQueueActive-1)',
               "api('/api/downloads/pulse'", "api('/api/diagnostics/ping'",
               'downloadLastFullAttemptAt', 'downloadLastFullAppliedAt', 'downloadPulseFailures',
               'UI event-loop lag: last=', 'if(submittedBatches%3===0)await new Promise(resolve=>setTimeout(resolve,0))'):
    assert marker in j,marker
assert "const limit=terminalView?Math.max(1,Math.min(500,Number(state.downloadHistoryLimit||50))):200;" in j
assert 'if(submittedKeys.has(key)&&!failedKeys.has(key))state.selectedItems.delete(key)' in j
assert 'if(failedKeys.size)toast(' in j
assert "showContextMenu(e.clientX,e.clientY" in j
manifest=json.loads((root/'src/app/build-manifest.json').read_text(encoding='utf-8'))
assert manifest['version']=='3.7.27' and manifest['base_version']=='3.7.26' and manifest['adapter_version']=='3.7.27'
print('PASS: v3.7.27 nonblocking queue pulse, bounded UI refresh, diagnostics liveness, retained queue safeguards')
