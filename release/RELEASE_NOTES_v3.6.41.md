# NewzDeck v3.6.41 — Downloads Snapshot Responsiveness

NewzDeck v3.6.41 is a focused production reliability release based on a completed v3.6.40 Diagnostic Collector capture from a live installed system.

The diagnostic run showed that the authoritative NewzDeck backend, Windows service, and private SABnzbd process all remained healthy while three snapshot-dependent endpoints — `/api/diagnostics`, `/api/diagnostics/report`, and `/api/downloads` — timed out. Lightweight endpoints continued to respond. Source-level correlation isolated the shared dependency to `DOWNLOAD_MANAGER.snapshot()` and its serialized Queue/History/SAB control path.

v3.6.41 keeps the proven serialized private-SAB transport that eliminated overlapping-control WinError 10054 churn, but makes the live Downloads presentation path fail-soft instead of waiting behind legitimate long-running control work.

## What changed

### Bounded live SAB transport access

Live Queue/History presentation reads now wait only briefly for NewzDeck's serialized SAB transport lock. If Automation, configuration, submission, or another legitimate control operation already owns the transport, the live presentation path falls back instead of waiting for that entire operation to finish.

This budget applies only to live presentation reads. Authoritative non-live recovery, reconciliation, and mutation paths retain their existing stronger retry behavior.

### Bounded Queue/History reader contention

The shared Queue/History reader remains serialized, preserving the protection introduced after earlier concurrent SAB-control failures. However, live UI/API callers no longer wait indefinitely if Automation's completion/reconciliation path currently owns that reader.

When a recent coherent Queue snapshot is available, NewzDeck returns that recent data explicitly marked stale for presentation purposes. If sufficiently recent state is not available, the existing control-degraded snapshot path is used.

### Concurrent snapshot callers no longer line up

Once NewzDeck has a coherent Downloads snapshot, a second caller will not wait behind another in-flight snapshot build. It can immediately receive the last coherent presentation snapshot with explicit stale markers.

This prevents `/api/downloads`, Diagnostics, the Diagnostic Collector, and other snapshot consumers from forming a queue behind the same slow build.

The fallback is presentation-only. It does not become authoritative engine truth and does not drive destructive reconciliation.

### Live polling has a tighter request budget

Live Queue and History polling now uses a single short attempt rather than the stronger six-attempt retry policy used by authoritative non-live reads. The next normal UI poll can retry shortly afterward, while the previous coherent snapshot remains visible.

This keeps the UI responsive without weakening recovery behavior that actually changes or reconciles queue state.

### New contention telemetry

v3.6.41 adds diagnostics for future root-cause analysis, including:

- snapshot build duration and maximum observed build duration;
- snapshot-lock busy fallback count and last occurrence;
- serialized SAB transport wait time and maximum wait time;
- serialized SAB transport busy-timeout count;
- current/last SAB control mode observed by transport telemetry;
- Queue/History reader busy fallback count and last occurrence.

SAB transport telemetry itself is now observational and no longer acquires the same SAB control lock merely to report diagnostic counters.

### Installed-runtime identification fix

The health/update status endpoints now recognize Inno Setup's normal `unins000.exe` uninstall marker in addition to the retired legacy `Uninstall.exe` marker.

This fixes installed v3.6.40-era systems being reported as portable even though the Windows service, registry installation, and installed runtime were present.

## Safety and regression guards

The following behavior is intentionally preserved:

- NewzDeck → SAB control traffic remains serialized; v3.6.41 does **not** reintroduce overlapping localhost SAB requests.
- Stale presentation snapshots never drive tombstone cleanup, stale-duplicate cleanup, Pause recovery, terminal-state decisions, queue ownership, Automation admission, or Smart Import reconciliation.
- Authoritative non-live Queue/History reads keep their existing retry budgets.
- Existing queue mutation and recovery behavior is unchanged.
- v3.6.40 runtime-storage cleanup and admin-generation safety remain unchanged.
- v3.6.39 Automation startup-reservation refinement remains unchanged.
- v3.6.38 crash-recovery and authoritative queue-admission protections remain unchanged.
- Manual Search/Grab, Newznab scoring/blacklisting, no-downgrade behavior, Smart Import transaction safety, and user-data locations are unchanged.
- Installer service/tray upgrade handoff behavior is unchanged.

## Validation

Before preparing the production publish package:

- the uploaded v3.6.40 application source was normalized to LF and its Git blob identities were matched against the live `newzdeckadmin/NewzDeck` `main` source for `server.py`, `sab_engine.py`, `automation_engine.py`, `build-manifest.json`, `version.txt`, `app.js`, `index.html`, `styles.css`, and `tmdb-logo.svg`;
- Python syntax compilation passed for `server.py`, `sab_engine.py`, and `automation_engine.py`;
- JavaScript syntax validation passed for `static/app.js`;
- a concurrency harness verified that a second snapshot caller receives the coherent stale presentation instead of blocking behind an in-flight snapshot build;
- the same harness verified bounded live Queue/History reader contention and bounded SAB transport-lock contention.

The canonical GitHub release workflow performs the final Windows builds, source/version guards, deterministic Portable build, Inno Setup build, installer upgrade smoke tests, checksum verification, release tag creation, and artifact publication.
