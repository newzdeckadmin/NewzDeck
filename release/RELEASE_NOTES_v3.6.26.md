# NewzDeck v3.6.26 — Verified Remove & Bulk Failed Cleanup

NewzDeck v3.6.26 is a focused follow-up to v3.6.25. It fixes a Remove-control regression exposed while the private SAB engine was actively downloading under load: NewzDeck could report that the engine was reconnecting even though transfers were healthy, because Remove was gated by a separate short localhost identity ping.

## Verified Remove without the false reconnect gate

- Individual **Remove** no longer requires a separate strict SAB ping before checking the requested job.
- NewzDeck now reads the target job directly from SAB Queue/History with bounded retries and bases removal safety on that job-specific evidence.
- A transient localhost control reset therefore no longer implies that SAB's download/NNTP transfer plane is offline.
- If SAB proves the job is still live, NewzDeck keeps it visible and does not hide it locally.
- If SAB proves the transfer is terminal/absent, NewzDeck can complete the local cleanup even if the later History-delete mutation experiences a transient reset; the durable tombstone prevents stale History from resurrecting the card.

## Truly bulk Remove all failed

- **Remove all failed** now performs one targeted multi-ID Queue/History verification pass rather than running a complete verification cycle for every Failed card.
- Terminal History entries are deleted through one bulk SAB History mutation when possible.
- This sharply reduces localhost control traffic when dozens of failed downloads are being cleaned at once.
- A failed bulk verification leaves unproven jobs visible rather than guessing or hiding active work.

## Preserved v3.6.25 reliability work

The v3.6.25 Automation backlog and Smart Import safeguards remain unchanged: exhausted imports stay terminal until explicit Retry Import, output resolution is job-owned and fail-closed, Love Island/Big Brother franchise and edition mismatches are rejected, high-frequency import persistence is throttled, SAB read/recovery pressure is reduced, stale ownership does not churn indefinitely, and the library integrity audit remains read-only.

NewzDeck v3.6.24 durable Download Statistics, v3.6.23 accent-insensitive Automation search, v3.6.22 All Posts binary resolution/recovery, v3.6.21 Related Media/image browsing, and v3.6.20 authoritative SAB Queue/History reconciliation also remain intact.

Discover/TMDB, Metadata Server v0.3.3 integration, Windows background service/tray/runtime handoff, installer/updater behavior, provider settings, normal NZB/package semantics, and user-data preservation are not intentionally changed by this release.
