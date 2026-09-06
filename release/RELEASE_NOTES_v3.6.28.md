# NewzDeck v3.6.28 — Downloads Continuity & SAB Recovery Hardening

NewzDeck v3.6.28 fixes an intermittent Downloads presentation failure observed under a busy built-in SABnzbd control channel. In the affected sessions, SAB kept downloading normally, but a transient Queue/History omission could cause one or more NewzDeck download cards to disappear briefly and then return on a later poll.

## Durable Downloads visibility

- Once NewzDeck durably owns a non-terminal SAB job, a transient Queue/History slot omission no longer removes that card from the Downloads response.
- A job whose Active continuity lease is no longer provable remains visible as **Queued • refreshing SAB status** instead of falsely remaining Active or disappearing.
- Retry-wait and cancelling jobs remain visible with conservative refresh/confirmation status while SAB state is temporarily incomplete.
- Explicit user Remove/Cancel tombstones and terminal SAB History remain authoritative and are never overridden by the visibility bridge.

## Stale ownership stays bounded

- Normal stale ownership still uses the existing 120-second retention window; Smart Import-owned work retains its existing longer recovery window.
- The retention clock now requires consecutive **fresh Queue + fresh History absence**. A stale/cached read resets that proof window rather than contributing to a false stale-ownership release.
- This prevents the continuity fix from recreating the old ghost-download behavior.

## SAB control and recovery hardening

- Live Queue observations are shared for up to 1.0 second, and History observations are shared for up to 0.75 seconds during post-processing or 1.5 seconds otherwise. The browser may still refresh the Downloads view every 250 ms; these changes reduce redundant localhost SAB API traffic behind that UI cadence.
- Temporary tray/user-session launcher failures are treated as environmental failures and no longer allocate a new SAB `admin-vN` generation. Clean generations remain available for genuine configuration/runtime recovery.
- SAB HTTP User-Agent and `sab-startup.log` labels now use the current `ADAPTER_VERSION`, eliminating the stale 3.6.20 diagnostic labels that remained in v3.6.27.

## Diagnostics

Diagnostics now reports:

- total Downloads visibility bridges;
- queued visibility bridges;
- currently open visibility bridges;
- longest observed visibility gap;
- SAB job-omission event count and last event time.

These counters make future Queue/History observation gaps directly measurable without relying on a screen recording.

## Preserved behavior

NewzDeck v3.6.27 runtime-adapter identity validation remains intact. v3.6.26 verified individual Remove and truly bulk **Remove all failed**, v3.6.25 Automation backlog/Smart Import safeguards, v3.6.24 durable Download Statistics, v3.6.23 accent-insensitive Automation matching, v3.6.22 All Posts binary recovery, and v3.6.21 Related Media/image browsing remain preserved.

Discover/TMDB, Metadata Server v0.3.3 integration, provider settings, Windows installer/updater behavior, and user-data preservation are otherwise unchanged.
