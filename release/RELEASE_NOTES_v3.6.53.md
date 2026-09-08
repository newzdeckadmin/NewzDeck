# NewzDeck v3.6.53 — NZB Identity Gate & Durable Downloads History

v3.6.53 closes the disguised-season-pack correctness gap found in the v3.6.52 full-load diagnostic and completes the Downloads data-plane work that had previously been deferred.

## Changes

- **Pre-SAB NZB identity gate.** Automatic TV grabs inspect actual NZB `<file subject>` identities after retrieval and before queue submission. A single-episode target is rejected when the NZB positively contains other episode identities or complete-season/season-pack markers. Obfuscated subjects without contradictory evidence remain allowed.
- **Automatic next-candidate recovery.** Content-invalid releases are blacklisted for the target and Continuous Automation immediately attempts the next ranked candidate rather than failing the entire cycle.
- **Smart Import remains fail-closed.** Existing strict output ownership/episode identity checks remain authoritative after download; pre-SAB validation adds an earlier line of defense.
- **Copy-on-write Live presentation index.** Background state reconciliation publishes only active/non-terminal durable jobs, terminal counts, tombstones and pause state. Routine Live projection consumes that memory view instead of scanning the complete ledger or waiting for state locks.
- **Durable NewzDeck terminal history.** `sab-engine/terminal-history.json` is bootstrapped from existing terminal ledger records, stores compact summaries independently of SAB's bounded History window, and retains the newest 5,000 terminal rows. Removing a terminal job removes its row; Retry supersedes the old row.
- **Lazy terminal details.** Completed/Failed paging returns compact history rows. Rich transfer/PAR2 diagnostics are fetched only when the user expands Details.
- **Sampler failure evidence.** Diagnostics retain the last sampler failure text/timestamp and bounded failure-reason counts even after later successful cycles.

## Real regression fixture

The release guard models the production `Big.Brother.Canada.S07E29.1080p.WEB.h264-DiRT` case: an advertised single episode whose NZB contains 998 files, explicit S07E01–S07E29 identities and `S07.Complete` PAR2 evidence. It must be rejected before the download manager receives the NZB. A valid multi-part S07E29 NZB and an obfuscated/no-evidence NZB must still pass.

## Preserved behavior

Private SABnzbd 5.1.2 remains the transfer/repair/extraction authority. v3.6.52 sparse version probing/zero-wait state gate, v3.6.51 cached engine status/handoff grace, v3.6.50 Queue/History sampler, v3.6.49 bounded API transport, Library Integrity, Selected Episodes and PAR2 visibility are preserved.
