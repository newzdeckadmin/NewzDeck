# NewzDeck v3.6.56 - Smart Import Duplicate Protection & Diagnostics Refinement

v3.6.56 is a focused correctness and diagnostics release based on the first sustained v3.6.55 acceptance capture while private SABnzbd was actively downloading and Automation was continuously Smart Importing completed episodes. v3.6.55's terminal-history optimization passed under real load; this release addresses the remaining library-integrity and diagnostic clarity opportunities without changing SAB transfer, repair, extraction or retry behavior.

## Changes

- **Pre-import same-title cross-episode fingerprint protection.** Before a TV Smart Import transaction commits media, NewzDeck fingerprints each actionable incoming file and compares it with other physical episodes already owned by the same Automation title. If the incoming bytes are identical to a different episode, Smart Import fails closed before moving anything, preserves the completed SAB output, and returns Needs Review with the conflicting episode/path.
- **Incoming season-pack duplicate protection.** The same guard compares actionable episode files inside one incoming transaction. Two differently targeted episode files with identical bytes hold the transaction for review before either file reaches the library.
- **Observable integrity protection.** Automation target-integrity telemetry adds `cross_episode_fingerprint_imports_blocked`, and activity history records an `import-integrity-hold` event with bounded conflict evidence. Existing Library Integrity remains the read-only post-import audit.
- **Recovered SAB warning suppression.** Durable Completed history builds exact release identifiers alongside the existing terminal indexes. SAB warnings whose path names an exact durably completed release are removed from current `engine_warnings` and retained separately as bounded `resolved_engine_warnings`; raw SAB logs and raw warning evidence remain unchanged.
- **Raw SAB overlap is no longer called a correction.** Per-slot statuses reporting multiple Active/Fetching jobs are counted separately as raw SAB overlap. Actual visible-card normalization keeps its own correction counter. Diagnostics expose active-slot count, foreground transfer ID and at most three example IDs instead of long all-queue UUID signatures.
- **Short-lived coherent diagnostics cache.** `/api/diagnostics` and `/api/diagnostics/report` reuse one diagnostics generation for 1.5 seconds, avoiding duplicate Downloads projection, Automation state and storage aggregation when Collector/UI request both endpoints back-to-back. Cache hit/miss/age telemetry is included.

## Evidence behind the release

The v3.6.55 acceptance capture proved the history fix: 52 history synchronization passes contained 48 no-op passes, 4 durable history writes and only 5 total index rebuilds (including initial startup construction). Downloads snapshot p95 remained 31 ms with zero slow builds, Queue sampling completed 414/414 cycles without failure, and persistent SAB HTTP reuse was 99.76%.

The same capture found two different Big Brother Canada episode files (S11E24 and S11E25) with the exact same 3,477,771,605-byte fingerprint. SAB had downloaded and unpacked two distinct episode-labeled releases into distinct output folders and NewzDeck imported each from the correct job, pointing to bad/mislabeled release contents rather than cross-job path ownership. v3.6.56 therefore adds a conservative pre-import fingerprint hold so this class of bad release cannot silently enter the library again.

## Preserved behavior

Private SABnzbd 5.1.2 remains authoritative for NNTP transfer, verification, PAR2 repair, extraction and retry. v3.6.55's no-op terminal-history fast path and durable diagnostics counts remain unchanged. v3.6.54 operational-ledger compaction/page-native history/startup caching, v3.6.53 NZB identity gate/next-candidate recovery/fail-closed Smart Import ownership, and all earlier Library Integrity, Selected Episodes, queue continuity, runtime handoff and installer protections remain intact.
