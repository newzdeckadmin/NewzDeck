# NewzDeck v3.6.50 — Snapshot Sampler & State-Lock Hardening

NewzDeck v3.6.50 targets the remaining snapshot latency/contention seen in the real v3.6.49 diagnostics while preserving the v3.6.49 Downloads data-plane changes.

## Highlights

- **Single routine SAB sampler.** A background worker maintains the Queue/History pair and publishes fresh samples before optional housekeeping. Downloads snapshots and completion monitoring consume that pair instead of each initiating competing routine SAB reads. Removed-tombstone/stale-duplicate cleanup is driven only from a freshly fetched sampler pair; explicit controls remain fresh/authoritative.
- **Bounded presentation ledger refresh.** Downloads no longer waits indefinitely for either NewzDeck's in-process state lock or the cross-process tracking ledger if Smart Import or another writer owns it. The presentation path uses one 25 ms non-blocking budget across both locks, then uses the already-coherent in-memory state. Mutation/import/control paths remain strict and blocking.
- **Presentation is no longer a background-work executor.** Snapshot rendering no longer performs statistics reconciliation, queue cleanup, cross-runtime adoption, Automation import kicking/failure feedback, browser-image flattening, or strict state saves. The small ownership bookkeeping it can discover is deferred to the engine worker, while terminal/PAR2 evidence persistence is owned by the completion worker.
- **Better latency attribution.** Diagnostics now includes shared-state and engine-status timing, sampler health, and worst-build timestamp/phase in addition to the v3.6.49 percentile and SAB/provider timings.
- **Automation runtime aging.** Imported/satisfied targets older than seven days keep the selected/top candidate and durable blacklist while redundant candidate transcripts and expired attempt memory are compacted. Waiting/error/active targets are not compacted.
- **Installer hygiene.** Setup explicitly removes only `NewzDeckBootstrap.exe` and `NewzDeckCore.exe`, the two retired binaries identified by Diagnostic Collector v1.0.5.

## Regression safety

The established strict TV identity, Library Integrity, scan progress, quality selection, Selected Episodes, PAR2/repair visibility, Smart Import ownership, Downloads continuity, bounded history API and provider-health regressions remain required. A new v3.6.50 release guard tests bounded ledger-lock behavior, forbids blocking state saves inside snapshot rendering, validates sampler/deferred-persistence markers, checks stable Automation evidence compaction, and verifies retired-binary installer cleanup before release assets can build.
