NewzDeck v3.6.50
Snapshot Sampler & State-Lock Hardening

New in v3.6.50:
- One background SAB Queue/History sampler now feeds routine Downloads snapshots and completion monitoring, reducing competing localhost control reads; fresh-sample tombstone/duplicate cleanup is centralized there.
- Presentation snapshots no longer block behind either the in-process state lock or cross-process job-ledger writer; they use one 25 ms bounded refresh budget and safely reuse current in-memory ownership state when either lock is busy.
- Snapshot rendering no longer runs statistics reconciliation, SAB cleanup, adoption/import/failure-feedback work or strict ledger saves; small presentation bookkeeping is deferred, while terminal/PAR2 persistence runs in the completion worker.
- Snapshot diagnostics identify shared-state, engine-status, SAB reconciliation and provider-health timing, plus the timestamp and dominant measured phase of the worst build.
- Explicit download controls still use fresh authoritative Queue/History reads; stale sampler data never authorizes destructive recovery decisions.
- Old successful/satisfied Automation targets compact candidate transcripts after seven days while preserving blacklists, selected-release evidence, active/waiting/problem targets and the existing 45-day retention.
- Setup removes only the two known retired NewzDeckBootstrap.exe and NewzDeckCore.exe leftovers discovered by Diagnostic Collector v1.0.5.
- v3.6.49 bounded Downloads data plane/provider-health/Library Integrity/Smart Import protections, v3.6.48 integrity hardening, v3.6.47 Selected Episodes/PAR2 visibility and private SABnzbd 5.1.2 remain preserved.
