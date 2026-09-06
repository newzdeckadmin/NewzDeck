# NewzDeck v3.6.29 — Persistent SAB Control Transport

NewzDeck v3.6.29 targets the remaining localhost control-channel instability observed after v3.6.28. v3.6.28 successfully bridged transient SAB Queue/History omissions so Downloads cards stayed visible, but production diagnostics still showed frequent WinError 10054 resets while SAB itself remained alive, connected, downloading, repairing and unpacking normally.

## Persistent private SAB HTTP connection

- NewzDeck no longer sends `Connection: close` on every normal SAB API request.
- Queue, History, statistics, completion monitoring and other built-in SAB control calls now share one persistent HTTP/1.1 connection to `127.0.0.1`.
- The existing re-entrant SAB transport lock remains authoritative, so there is still at most one NewzDeck-to-SAB control request in flight at a time.
- Each response body is fully consumed before the transport lock is released, making the connection safe for the next serialized request.

## Bounded reconnect behavior

- A genuine localhost transport exception immediately invalidates the current persistent connection; the existing read retry, handoff reconciliation and configuration recovery paths then reopen a clean connection as needed.
- A SAB port change or listener replacement cannot accidentally reuse a socket from the previous endpoint.
- Long-idle connections are proactively reopened rather than treating a normal server keep-alive timeout as a failed download.
- If SAB explicitly returns a response that requires connection close, NewzDeck honors it and opens a fresh connection for the next request.
- HTTP authentication failures remain authentication failures: they continue through authoritative API-key reconciliation and are not mislabeled as transport resets.

## Transport diagnostics

Diagnostics now reports a dedicated **SAB HTTP transport** line with:

- total control requests;
- connections opened and reused;
- connection reuse percentage;
- reconnect count;
- transport-reset count;
- server-requested closes;
- proactive idle reopens;
- whether a persistent connection is currently active;
- current connection age;
- last reset timestamp and API mode;
- reset counts grouped by SAB API mode.

This makes it possible to distinguish a healthy high-reuse persistent session from repeated connection churn, and to identify which SAB operation is responsible for any residual reset.

## v3.6.28 safety layer remains intact

The v3.6.28 durable Downloads visibility-continuity logic is intentionally unchanged. If SAB still omits a durably owned non-terminal job from a transient Queue/History observation, NewzDeck retains the card until terminal state, explicit removal, or the existing fresh-absence retention rules authorize release.

## Preserved behavior

NewzDeck v3.6.28 Downloads continuity and clean-generation recovery, v3.6.27 runtime-adapter identity validation, v3.6.26 verified individual Remove and truly bulk **Remove all failed**, v3.6.25 Automation backlog/Smart Import safeguards, v3.6.24 durable Download Statistics, v3.6.23 accent-insensitive Automation matching, v3.6.22 All Posts binary recovery, and v3.6.21 Related Media/image browsing remain preserved.

Discover/TMDB, Metadata Server v0.3.3 integration, provider settings, Windows installer/updater behavior, and user-data preservation are otherwise unchanged.
