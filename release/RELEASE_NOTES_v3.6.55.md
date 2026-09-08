# NewzDeck v3.6.55 - Terminal History Index & Diagnostics Efficiency

v3.6.55 is a focused efficiency and diagnostics release based on a sustained v3.6.54 capture taken while private SABnzbd was actively downloading and Automation was continuously Smart Importing completed episodes. The transfer, repair, extraction and Smart Import stack was healthy; the remaining issues were avoidable terminal-history maintenance work and diagnostic ambiguity introduced by the v3.6.54 operational-ledger compaction model.

## Changes

- **No-op terminal-history sync fast path.** The completion monitor still checks tracked operational jobs every two seconds, but when no terminal summary changed and no one-time history maintenance is required, it now returns before copying, sorting or rebuilding the full durable history.
- **Exactly one index rebuild per durable mutation.** A terminal-history write owns the rebuild for that mutation. History removal no longer rebuilds once in memory and then rebuilds again during the write.
- **Observable history maintenance efficiency.** New telemetry reports terminal-history sync runs, no-op syncs, changed rows, index rebuilds and rebuilds avoided. This makes it possible to prove that a 5,000-row history is not being reindexed on unchanged monitor passes.
- **Scope-native diagnostics.** `/api/diagnostics` now consumes the scope-native Live Downloads snapshot rather than the operational/full snapshot. User-facing Completed/Failed counts therefore remain durable after finalized Completed jobs have been retired from `newzdeck-jobs.json`.
- **Operational versus durable state is explicit.** Diagnostics separately report operational tracked jobs, operational presentable/actionable jobs, live collection rows, and durable Completed/Failed/Cancelled terminal counts.
- **Honest provider measurement state.** A provider with zero latency samples and no success/failure measurements reports latency and success as `N/A` instead of implying a measured `0 ms` or rendering `None%`. SAB runtime connection state remains independently authoritative.
- **Clearer multi-active normalization evidence.** Telemetry retains both the current and last overlap signatures and states whether the current condition originates from raw SAB multiple-Active status, visible-card normalization, or both. The product invariant remains one foreground Downloading card.
- **Pages/repository hygiene preserved.** The v3.6.54 post-release UTF-8 documentation repair remains the publishing baseline and is carried forward unchanged except for the normal current-release documentation update.

## Full-load evidence behind this release

The v3.6.54 diagnostic contained 715 durable terminal rows, 710 finalized Completed jobs already retired from the operational ledger, 22 terminal-history writes, but 1,077 terminal-history index rebuilds during roughly 47 minutes of runtime. Downloads snapshot p95 remained only 16 ms, so this was not an emergency performance problem; it was unnecessary work that would scale poorly toward the 5,000-row history cap.

The same capture proved that `/api/downloads?scope=live` correctly reported 710 Completed and 5 Failed while `/api/diagnostics` reported 0 Completed and 5 Failed because it still consumed the old operational/full snapshot semantics. v3.6.55 aligns diagnostics with the durable user-facing state model.

## Preserved behavior

Private SABnzbd 5.1.2 remains authoritative for NNTP transfer, verification, PAR2 repair, extraction and retry. v3.6.54 operational-ledger compaction, page-native terminal history, smaller Completed transport, SAB-history resurrection protection and Automation startup caching remain intact. v3.6.53's NZB identity gate, automatic next-candidate recovery, fail-closed Smart Import and durable history remain intact, along with earlier Library Integrity, Selected Episodes, queue continuity, runtime handoff and installer protections.
