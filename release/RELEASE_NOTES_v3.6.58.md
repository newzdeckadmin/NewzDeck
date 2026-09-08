# NewzDeck v3.6.58 — Automation Runtime Reconciliation & State Efficiency

v3.6.58 is a narrow Automation runtime-state and diagnostics release based on the first full v3.6.57 acceptance capture. It does not change the private SABnzbd 5.1.2 transfer, verification, PAR2 repair, extraction, retry, or provider-failover architecture.

## Changes

- **Conservative orphan runtime pruning.** Old canonical Automation target-runtime records are removed only when `media-library.json` exists, parses successfully, and no longer contains the target item ID. A 24-hour grace window protects recent delete/re-add or handoff state, and opaque/unparseable target keys fail safe and remain untouched.
- **Semantic target-state precedence.** Library-proven `imported`/`satisfied` state wins over stale `searching`, `queueing`, `queued`, `grabbed`, or `waiting` writes even when a stale cycle writes later on the wall clock. A real grab whose `last_grab_ts` occurs after the final state remains allowed.
- **Runtime efficiency telemetry.** Diagnostics expose runtime target count, valid/orphan counts, orphan ratio, `automation-runtime.json` bytes, prune counts, reclaimed bytes, last-prune time, and stale-state demotions blocked.
- **Historical Integrity Hold normalization.** Unmistakable v3.6.56 terminal-history evidence containing the legacy Smart Import held-for-review/byte-identical message is classified as `failure_class=import_integrity_hold`. This is historical normalization only; it does not reconstruct an active target hold, blacklist, fingerprint, or retry policy.
- **Diagnostics report timing.** NewzDeck now measures `diagnostics_report_build_ms` separately from the existing 1.5-second diagnostics snapshot cache. This release measures first and does not add formatted-report caching without evidence.

## Validation

The v3.6.58 regression guard reproduces the real stale-state race, verifies a genuinely newer grab remains permitted, proves old orphans are pruned only with a valid authoritative library while recent/opaque targets are preserved, verifies malformed library JSON cannot trigger deletion, migrates a legacy byte-identical Smart Import hold without creating current Automation policy state, and confirms the v3.6.55 terminal-history no-op/index fast path remains intact.

## Preserved behavior

v3.6.57 presentation/raw transfer count integrity, explicit Integrity Holds and exact bad-release blacklisting remain unchanged. v3.6.56 duplicate-content protection and recovered-warning handling, v3.6.55 terminal-history efficiency, v3.6.53 identity/history safeguards, Smart Import ownership, Library Integrity, Windows service/tray handoff, installer behavior, and private SABnzbd 5.1.2 authority remain in place.
