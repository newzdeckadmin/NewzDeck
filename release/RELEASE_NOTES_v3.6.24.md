# NewzDeck v3.6.24 — Durable Download Statistics

NewzDeck v3.6.24 promotes the accepted v3.6.24-r1 Download Statistics reliability fix built on production v3.6.23. The release replaces incomplete legacy/session accounting in the private SABnzbd adapter with a durable cross-process statistics ledger.

## Lifetime download totals

- NewzDeck now reads SABnzbd `server_stats.total` as the exact persistent SAB lifetime byte counter.
- The preserved pre-SAB NewzDeck total remains an additive baseline rather than competing with the SAB counter through `max()` logic.
- Total Downloaded therefore continues across the embedded-SAB migration, restarts, upgrades and History clearing.

## Idempotent completion accounting

- Completed SAB jobs are recorded exactly once by NZO id in the shared cross-process engine ledger.
- Desktop and Windows-service runtimes can observe the same completion without double-counting it.
- Successful completion count and known transfer timing remain preserved after the corresponding SAB History row is cleared.
- Statistics reconciliation runs from the background completion path and does not depend on the Downloads page being open.

## Transfer Time and Average Speed

- New completions accumulate SAB's actual `download_time` value.
- Existing retained SAB History and Archive are scanned once in bounded pages to recover as much historical transfer-time information as remains available.
- Average Speed is calculated as a weighted average using downloaded bytes whose transfer duration is known.
- Diagnostic timing coverage makes partial historical reconstruction explicit instead of combining unrelated byte/time windows.
- If old SAB History was deleted before v3.6.24, its exact historical transfer duration cannot be reconstructed; NewzDeck does not invent it.

## Persistent Peak Speed

- A newly observed peak transfer rate is written to the durable statistics ledger immediately.
- Peak Speed therefore survives desktop/service restart and no longer behaves like a current-session maximum.
- Historical peaks that were never persisted by older releases cannot be reconstructed after the fact.

## Diagnostics and migration safety

- Existing statistics are migrated idempotently to the durable SAB-aware schema while retaining the earliest known tracking date.
- Copy Diagnostics now reports the statistics source, pre-SAB baseline bytes, SAB lifetime bytes, timed bytes, timing coverage, accounted jobs, backfill state, last reconciliation time and persistent peak.
- Shared-state merging treats cumulative statistics as monotonic and preserves the earliest tracking timestamp.

## Preserved production behavior

NewzDeck v3.6.23 accent-insensitive Automation/Newznab matching remains intact, including `90 Day Fiancé` ↔ `90 Day Fiance` compatibility without changing canonical TMDB/library names.

NewzDeck v3.6.22 All Posts binary resolution/recovery remains intact, including actionable unresolved binaries, obfuscated-name classification/retry behavior, long reconstruction polling, loose-binary placement and conservative PAR2/archive recovery. NewzDeck v3.6.21 image browsing and Related Media behavior and v3.6.20 authoritative SAB Queue/History control and fresh-state reconciliation also remain intact.

Downloads queue controls, Automation scheduling, Smart Import, Discover/TMDB, Metadata Server v0.3.3 integration, Windows background service/tray/runtime handoff, installer/updater behavior and normal NZB/package semantics are not intentionally changed by this release.

Normal installed updates preserve NewzDeck settings, provider configuration, Automation data, history, queue state and user data.
