# NewzDeck v3.6.54 — Downloads History Compaction & Automation Startup Efficiency

v3.6.54 is a scale/efficiency release based on the full-load v3.6.53 diagnostic captured during an active SABnzbd download. The transfer, repair, extraction and Smart Import paths were healthy; this release removes long-term state growth and repeated UI work that would become increasingly expensive as durable history grows.

## Changes

- **Operational ledger compaction.** `sab-engine/newzdeck-jobs.json` now retains operational/actionable state instead of serving as a second permanent Completed-history store. A finalized Completed job is retired only after its NewzDeck terminal-history row is durable. Failed/cancelled jobs, Retry/Retry Import cases, in-progress imports, cleanup-pending work and unfinished browser-flat finalization remain tracked.
- **Bounded history beyond 5,000 rows.** When terminal history is already at its 5,000-row retention cap, finalized Completed jobs older than the retained cutoff are intentionally expired from the operational ledger rather than leaking into an unbounded hidden backlog.
- **Bounded statistics accounting IDs.** The monotonic `statistics_accounted_jobs` deduplication map keeps the newest 20,000 IDs, far beyond the private SAB History window, while preventing a secondary state-growth vector.
- **Page-native terminal history.** Completed/Failed ordered ID indexes and raw terminal status counts are rebuilt only when durable history changes. A 50-row page slices that index directly instead of copying/sorting all retained history.
- **Smaller Completed transport.** Completed responses no longer include the UUID of every matching historical job. Failed continues to provide `matching_ids` because “Remove all failed” requires it.
- **Truly compact page rows.** Full Automation context and SAB stage logs stay out of normal Completed/Failed rows. Human-readable Automation identity is flattened into the compact row; bounded SAB/PAR2 stage evidence remains durable and is returned only by the lazy Details request.
- **No SAB History resurrection.** Recent SAB History entries already represented in NewzDeck terminal history are not re-adopted into the operational ledger after compaction.
- **Automation sidebar-count cache.** TV/Movie/Wanted badge counts are cached against media-library, quality-profile and Automation-config file signatures plus the local date, so unchanged startup probes do not repeatedly walk the same library/Wanted state.
- **Startup probe cancellation.** The sidebar count retry sequence stops after the first populated response. Full Automation warm retries also stop once a coherent summary is loaded.

## Validation

The v3.6.54 regression guard includes a 6,000-Completed-job scale fixture plus failed/importing/live jobs. It requires terminal history to remain capped at 5,000 rows, the operational ledger to retain only actionable/nonterminal state, statistics-accounted IDs to remain bounded, Completed pages to omit all-history IDs/rich fields, Failed batch IDs to remain available, lazy SAB/PAR2 detail to survive ledger retirement, and recent SAB History not to resurrect compacted jobs.

The same guard verifies sidebar-count cache hits/invalidation and the JavaScript startup-probe cancellation markers.

## Preserved behavior

Private SABnzbd 5.1.2 remains authoritative for transfer, verification, PAR2 repair, extraction and retry. v3.6.53’s pre-SAB NZB identity gate, automatic next-candidate recovery, fail-closed Smart Import, durable 5,000-row NewzDeck history, copy-on-write Live Downloads presentation and retained queue-sampler failure evidence remain intact, along with all earlier Library Integrity, Selected Episodes, runtime handoff and installer protections.
