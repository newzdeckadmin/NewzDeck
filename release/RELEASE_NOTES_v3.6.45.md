# NewzDeck v3.6.45 — Library Scan Progress & Visibility

## What changed

Automation library scans can take meaningful time on large TV/movie collections. v3.6.45 makes that work observable without changing what NewzDeck considers a valid library file.

- **Real scan progress:** Scan library and per-title Scan files now start a background scan job and poll a lightweight read-only progress endpoint.
- **Measured phases:** the UI reports Waiting, Preparing, Discovering files, Scanning files, Reading media metadata, Reconciling library, Saving library state, and Complete.
- **Useful counts:** live title/file counts, discovered media files, matched files, detected changes, offline roots, and current title/root are surfaced while the scan runs.
- **ETA:** once enough determinate work has completed, NewzDeck estimates time remaining from measured progress instead of displaying a fake timer.
- **Honest discovery state:** directory enumeration remains indeterminate until the current file set is known; NewzDeck does not invent a percentage during that phase.
- **Persistent visibility:** progress survives normal Automation redraws and reopening a media item while the scan is still active.
- **No overlapping expensive scans:** manual and scheduled reconciliation share one execution lock so the same library is never walked twice concurrently. A user scan waits visibly if scheduled reconciliation is just finishing.
- **Compatibility preserved:** the original synchronous scan API remains available; only the browser UI moves to the new start/progress contract.

## Safety and regression protection

The underlying reconciliation rules remain unchanged: TV identity filtering, quality recovery, reviewed-fingerprint exclusions, root-offline handling, `_merge_scan_state` conflict protection, and non-destructive Library Integrity behavior are retained. v3.6.44's read-only Integrity Audit GET route and all v3.6.43 strict TV identity compatibility tests remain mandatory.
