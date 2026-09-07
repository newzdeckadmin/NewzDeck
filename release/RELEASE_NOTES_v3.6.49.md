# NewzDeck v3.6.49 — Downloads Data-Plane & Runtime Efficiency

NewzDeck v3.6.49 is a production hardening release built directly on v3.6.48. It addresses the remaining application-side findings from the September 7 diagnostics audit without changing the private SABnzbd version or weakening the continuity and Automation safeguards established in v3.6.47–v3.6.48.

## Downloads data-plane

- The desktop now requests a bounded Downloads view instead of serializing the entire terminal history on every routine poll.
- Active, Queued, and Post-processing views use the live scope; Completed and Failed use deterministic 50-item terminal chunks with **Load More** up to the existing bounded client maximum.
- Global queue/count statistics remain authoritative even when the returned job list is scoped.
- Failed bulk removal retains the complete set of matching failed IDs, so paging does not turn **Remove all failed** into a partial operation.
- The original full `/api/downloads` contract remains available for compatibility and diagnostics callers that do not request a scope.

## Runtime performance and observability

- Expensive SAB provider configuration/status/warning reads are refreshed by the existing background engine worker instead of being synchronously performed on the foreground Downloads snapshot path.
- Real no-progress recovery still forces fresh provider checks at the established 20/35/90-second recovery boundaries; this change removes routine polling cost without weakening stall handling.
- Provider-health cache entries older than 15 seconds no longer retain a positive socket count as authoritative.
- Snapshot telemetry now records a bounded rolling sample and reports p50, p90, p95, and p99 build latency.
- Downloads responses expose preparation time and JSON serialization size/time headers for future diagnostics attribution.

## Provider and engine status clarity

- Diagnostics now overlays provider rows with the authoritative SAB runtime server/socket state. An Easynews server actively carrying 52 SAB connections no longer appears as an idle native-provider `standby` row.
- SAB's normal “Direct Unpack was automatically enabled” message is classified as an informational engine notice rather than a warning.
- Metadata/TMDB status distinguishes `not_probed_this_runtime` from an actual degraded/offline upstream state and reports the age of the last successful TMDB request when known.

## Persistent-state efficiency

- When SAB is authoritative, terminal jobs in the retired native `downloads.json` ledger have only their obsolete per-article segment/error/recovery arrays compacted. Job identity, status, paths, timing, statistics, and every non-terminal legacy record are preserved.
- `automation-runtime.json` is now written as compact JSON while retaining the existing 45-day target retention and exact data model. This reduces repeated multi-megabyte write amplification without a database migration.

## Library Integrity

- Library Integrity audit results are cached until either `media-library.json` or `media-quality-cache.json` changes.
- A post-audit signature check prevents a concurrent Smart Import or scan from publishing a cache entry against stale inputs.
- Cache hit/miss information is exposed in the audit result for diagnostics.
- All v3.6.48 same-series cross-episode duplicate detection and review behavior remains intact.

## Smart Import output ownership

- Explicit SAB `history.storage`/output paths are no longer trusted solely because they exist and contain media.
- The normalized completed-output identity must agree with the tracked Automation job/release before Smart Import can consume it.
- SAB's bounded `_UNPACK_`, `_FAILED_`, and `_ADMIN_` staging prefixes remain supported.
- This permanently guards the historical failure where a **Big Brother Canada S07E29** Automation context was pointed at a **Love Island S05E11/S05E10** `_UNPACK_` folder.

## Regression coverage

The production supplemental validator retains the exact 29 historical TV false-positive identities recovered from v3.6.47 diagnostics and adds synthetic release blockers for:

- Library Integrity cache hit and mutation invalidation.
- Safe same-series duplicate handling from v3.6.48.
- Terminal-only legacy segment compaction.
- Non-terminal legacy resume-state preservation.
- Valid matching SAB `_UNPACK_` output resolution.
- Rejection of a cross-job Love Island output for a Big Brother Canada context.
- Scoped live/Completed/Failed Downloads views and terminal paging.
- Informational Direct Unpack classification.
- v3.6.49 server/UI/runtime identity and data-plane markers.

## Preserved behavior

This release intentionally preserves:

- NewzDeck's authoritative single-package Downloads presentation and continuity bridges.
- Selected Episodes monitoring and Continuous Automation eligibility from v3.6.47.
- PAR2 Verify/Repair visibility and terminal failure classification from v3.6.47.
- Private SABnzbd **5.1.2** and its official pinned Windows x64 SHA-256.
- v3.6.46 quality-aware release selection.
- v3.6.45 observable Library Scan progress.
- Strict TV series-prefix identity and the real-world v3.6.48 regression corpus.
- Smart Import ownership/recovery, installer-owned runtime handoff, background service/tray behavior, and GPLv3 source-release workflow.

## Diagnostic-based acceptance evidence

Using the September 7, 12:28 PM production diagnostic snapshot as a read-only fixture:

- The prior full Downloads JSON shape is about **1.58 MB** when compact-serialized.
- The new live-scope shape for the captured 24 active/queued jobs is about **144 KB**, roughly a **91% payload reduction** for routine live polling.
- A 50-item Completed page from the same history is about **362 KB** instead of retransmitting all 209 Completed jobs.
- Compact Automation runtime serialization reduces the captured **7.40 MB** pretty JSON to about **5.16 MB** with identical parsed data.
- Terminal-only legacy segment compaction reduces the captured retired native `downloads.json` from about **3.23 MB** to about **134 KB**, removing 22,259 terminal segment records while leaving the statistics/job summary ledger present.

These figures are acceptance evidence from that captured production state, not fixed limits or promises for every library/queue size.
