# NewzDeck v3.6.51 — Heavy-Load Snapshot & Handoff Hardening

NewzDeck v3.6.51 is a focused production hardening release based on diagnostics captured while v3.6.50 was actively downloading at roughly 48 MB/s with all 52 SAB connections in use.

## Changes

- **Memory-only Downloads state refresh.** The v3.6.50 25 ms presentation budget bounded lock acquisition but still decoded and merged the multi-megabyte `newzdeck-jobs.json` after acquiring the lock. v3.6.51 removes all ledger file I/O and JSON merging from snapshot rendering. Strict background workers remain authoritative for cross-process reconciliation.
- **Background-cached engine health.** Live SAB heartbeat/identity work is refreshed by the engine coordinator. Downloads snapshots consume the cache and never initiate an engine heartbeat or read `engine.json` on the foreground HTTP path.
- **Clearer heavy-load timing.** Card/collection/statistics projection has its own `snapshot_projection_*` telemetry and participates in worst-phase attribution instead of being hidden inside `other`.
- **New SAB-job ownership grace.** A newly submitted SAB job is still shown immediately, but NewzDeck waits four seconds before treating a missing ledger record as an ownership inconsistency. Persistent or explicitly tombstoned jobs still surface the warning, at most once per orphan episode.
- **Episode-based multi-active telemetry.** Repeated snapshots of the same SAB download/post-processing overlap count as samples of one correction episode instead of inflating `multiple_active_slot_corrections` every poll.
- **Correct legacy compaction byte telemetry.** An already-compacted `downloads.json` now reports its real unchanged size as `bytes_after` instead of zero.

## Preserved behavior

The v3.6.50 Queue/History sampler, deferred state persistence, targeted installer cleanup and Automation evidence aging remain intact. v3.6.49 bounded Downloads payload/history behavior, background provider health, Library Integrity caching, strict Smart Import output ownership, v3.6.48 identity/integrity protections, v3.6.47 Selected Episodes/PAR2 repair visibility and private SABnzbd 5.1.2 are preserved.

## Release guards

The Windows release remains blocked unless all historical identity/quality/Selected Episodes/PAR2 tests, v3.6.49 data-plane tests, v3.6.50 sampler/state-lock tests and the new v3.6.51 heavy-load guards pass.
