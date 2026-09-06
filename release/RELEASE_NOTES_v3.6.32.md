# NewzDeck v3.6.32 — Automation Target Integrity & Downgrade Protection

NewzDeck v3.6.32 is a targeted Automation safety release based on a production-state audit of v3.6.31. The audit confirmed two related failures: unattended Automation could continue acting on a stale **missing** target after that target had already been satisfied, and a long-running library scan could later overwrite newer Smart Import state. In the worst case, that stale state let Smart Import treat an existing file with temporarily unknown quality as an upgrade candidate and replace a higher-quality library file with a lower-quality fallback release.

The SAB/download control path accepted in v3.6.31 is not redesigned in this release.

## Authoritative automatic-target revalidation

Immediately before an **automatic** Automation grab fetches its NZB, NewzDeck now re-reads the current library state and verifies the physical target:

- a stale `missing` grab is suppressed if the episode/movie is already present;
- a stale season-pack grab is suppressed if any intended member episode is already present;
- an `upgrade` grab is suppressed if the prior file disappeared or the incoming quality is not provably better than the current physical file;
- the check is performed after candidate selection but before indexer NZB retrieval and SAB submission.

Manual Interactive Search and one-time Discover grabs remain user-controlled.

## Fail-closed downgrade protection

Smart Import now recovers the existing physical file's quality from the strongest available evidence: matching live library state, NewzDeck's fingerprint-quality cache, filename metadata, or conservative media probing.

An empty/Unknown previous quality no longer means that an incoming file may overwrite the library. Before commit, NewzDeck revalidates every actionable import:

- identical fingerprints become `DUPLICATE`;
- only a provably better incoming quality may remain `UPGRADE`;
- equal, worse, or indeterminate incoming quality becomes `KEEP_EXISTING`;
- a stale `IMPORT` whose destination appeared while planning is reclassified before any replacement occurs.

This preserves allowed fallback qualities for truly missing media while making existing media fail closed against downgrades.

## Library-scan optimistic concurrency

Library scanning intentionally performs filesystem traversal outside the global Automation lock. v3.6.32 records each target's file state when the scan starts and compares that baseline with the live record at commit time.

If Smart Import or another newer operation changed the target during the scan, the live state wins and that stale scan result is skipped. Unchanged targets continue to reconcile normally on the same pass.

## Diagnostics

Copy Diagnostics now includes:

`Automation target integrity: stale_grabs_suppressed=...; scan_merge_conflicts=...; downgrades_blocked=...; existing_quality_recovered=...; last_event_ts=...`

These counters make production verification direct instead of inferring protection from job history.

## Preserved behavior

v3.6.32 does not redesign Queue/History polling, persistent SAB HTTP transport, historical-SAB quarantine behavior, download ownership, Direct Unpack, Smart Import naming, Discover/TMDB, provider settings, or installer/updater behavior. `sab_engine.py` receives only the required adapter-version identity bump to v3.6.32.

v3.6.31 historical SAB probe quieting, v3.6.30 identity-probe stabilization, v3.6.29 persistent SAB control transport, and v3.6.28 durable Downloads continuity remain preserved.
