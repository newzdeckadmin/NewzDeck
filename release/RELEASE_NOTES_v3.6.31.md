# NewzDeck v3.6.31 — Historical SAB Probe Quieting

NewzDeck v3.6.31 is a deliberately narrow cleanup after v3.6.30 production acceptance. Under about 38.5 minutes of normal download load, v3.6.30 reported **0 Queue/History resets**, **0 degraded snapshots**, **0 stale snapshots suppressed**, 52/52 live NNTP connections, successful Smart Imports, and 18/18 successful runtime-auth probes. The remaining low-level control noise was isolated to **76 failed `mode=version` probes**.

A source audit showed those version requests were not coming from the normal current-SAB runtime path. They came from the once-per-minute stale/private-SAB quarantine sweep, which iterated historical NewzDeck SAB ports and attempted a full HTTP version fingerprint even when those old ports were already closed. With two historical ports, that produces almost exactly two failed version probes per minute.

## Closed historical ports are now skipped before HTTP

- The historical SAB sweep now performs a cheap localhost TCP listener preflight before any SAB HTTP identity request.
- If a historical port is closed/free, NewzDeck skips it immediately. No `mode=version` request is sent, the main persistent SAB HTTP connection is not redirected to that dead port, and no transport reset is recorded for that closed port.
- The authoritative current SAB port is excluded from the historical sweep exactly as before.

## Occupied historical ports retain strong proof

The safety behavior is intentionally unchanged when a historical port is actually occupied:

- NewzDeck still performs a real key-free SAB version fingerprint.
- It still authenticates using only historical NewzDeck-owned credentials associated with that port.
- A proven stale SAB with queue work may be paused/quarantined so hidden duplicate transfers cannot continue.
- A proven empty stale SAB may be shut down to release its port.
- An unknown process is never adopted or mutated.

This preserves stale-engine recovery while removing pointless network traffic against known-dead ports.

## Historical SAB sweep diagnostics

Diagnostics now includes a dedicated **Historical SAB sweep** line with:

- sweep count;
- historical ports considered;
- closed/free ports skipped before HTTP;
- occupied ports that required strong identity probing;
- authenticated stale NewzDeck SAB instances;
- timestamp of the last sweep.

The existing **SAB HTTP transport**, **SAB Queue/History transport**, and **SAB identity probes** lines remain unchanged for direct before/after comparison with v3.6.30.

## Preserved behavior

v3.6.31 does not alter Queue/History polling, persistent HTTP/1.1 serialization, retry/reconciliation, Smart Import, Downloads visibility continuity, transfer-state presentation, provider behavior, or download ownership. The accepted v3.6.30 runtime-auth and configuration no-op optimization remain intact.

NewzDeck v3.6.29 persistent SAB control transport, v3.6.28 durable Downloads continuity, v3.6.27 runtime-adapter identity validation, v3.6.26 verified individual Remove and bulk **Remove all failed**, v3.6.25 Automation backlog/Smart Import safeguards, v3.6.24 durable Download Statistics, v3.6.23 accent-insensitive Automation matching, v3.6.22 All Posts binary recovery, and v3.6.21 Related Media/image browsing remain preserved.

Discover/TMDB, Metadata Server v0.3.3 integration, provider settings, Windows installer/updater behavior, and user-data preservation are otherwise unchanged.
