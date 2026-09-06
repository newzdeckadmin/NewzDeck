# NewzDeck v3.6.30 — SAB Identity Probe Stabilization

NewzDeck v3.6.30 is a deliberately narrow follow-up to v3.6.29. Production acceptance of v3.6.29 showed that the persistent serialized SAB HTTP transport solved the serious Queue/History reset problem: over roughly 2.5 hours, NewzDeck handled 22,652 SAB API requests with 97%+ connection reuse, only one Queue/History retry, zero degraded snapshots, and no user-visible download-card instability. Of 294 remaining low-level transport resets, 293 were isolated to the periodic key-free SAB `mode=version` fingerprint.

## Routine liveness no longer fingerprints version

- Normal runtime health checks now validate the authoritative current-generation API key through SAB's key-free `auth` endpoint.
- A successful `auth=apikey` response proves that the saved private key belongs to the listener on the authoritative localhost port, which is sufficient for routine runtime liveness.
- Routine health no longer sends a full SAB `mode=version` fingerprint every engine-loop/configuration cycle.
- If runtime authentication fails, NewzDeck falls back to the existing authoritative reconciliation path, which deliberately restores the stronger full version + credential proof before repairing identity.

## Strong version proof remains at identity boundaries

A real key-free SAB version request is still used where it is materially required:

- startup and startup wait loops;
- authoritative identity reconciliation;
- historical/stale-engine port verification;
- occupied-port recovery;
- explicit SAB restart/recovery confirmation.

This keeps strong process identity checks at lifecycle boundaries while removing them from the high-frequency healthy runtime path.

## Configuration synchronization no-op optimization

- NewzDeck now computes the local provider/settings signature before contacting SAB for configuration synchronization.
- If the desired signature is unchanged, the synchronization pass returns immediately and records a no-op skip.
- Changed or forced configuration still performs an authenticated runtime liveness check before applying SAB configuration.
- The engine loop already calls `ensure_running()` before synchronization, so the new ordering removes duplicate control traffic without weakening engine recovery.

## Identity-probe diagnostics

Diagnostics now includes a dedicated **SAB identity probes** line with:

- full version probe count and failures;
- timestamp of the last full version probe;
- routine runtime-auth probe count and failures;
- timestamp of the last runtime-auth probe;
- unchanged configuration synchronization no-op skips.

The existing **SAB HTTP transport** and **SAB Queue/History transport** diagnostics remain unchanged, so v3.6.30 can be compared directly with the accepted v3.6.29 production run.

## Preserved behavior

The v3.6.29 persistent serialized HTTP/1.1 connection, reconnect/error semantics, per-mode transport counters, and authentication-reconciliation behavior are otherwise unchanged. The v3.6.28 durable Downloads visibility-continuity bridge also remains unchanged as an independent safety layer.

NewzDeck v3.6.27 runtime-adapter identity validation, v3.6.26 verified individual Remove and bulk **Remove all failed**, v3.6.25 Automation backlog/Smart Import safeguards, v3.6.24 durable Download Statistics, v3.6.23 accent-insensitive Automation matching, v3.6.22 All Posts binary recovery, and v3.6.21 Related Media/image browsing remain preserved.

Discover/TMDB, Metadata Server v0.3.3 integration, provider settings, Windows installer/updater behavior, and user-data preservation are otherwise unchanged.
