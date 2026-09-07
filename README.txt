NewzDeck v3.6.49
Downloads Data-Plane & Runtime Efficiency

New in v3.6.49:
- Routine Downloads polling uses bounded live/terminal API views instead of serializing the entire Completed/Failed history on every refresh; terminal tabs load 50 records at a time with Load More.
- Expensive SAB provider-health reads run on the background engine worker instead of the foreground Downloads snapshot path, while real stall recovery still forces fresh checks at its existing thresholds.
- Snapshot diagnostics now include rolling p50/p90/p95/p99 latency plus Downloads response preparation/serialization observability.
- Provider diagnostics reflect authoritative SAB runtime sockets so an actively transferring provider no longer appears as standby.
- Normal SAB Direct Unpack auto-enable information is no longer presented as an engine warning.
- Terminal per-article details in the retired native downloads.json ledger are compacted safely; non-terminal resume state and historical statistics are preserved.
- Hot automation-runtime.json writes use compact JSON without changing the Automation state model or retention policy.
- Library Integrity caches an unchanged audit and invalidates automatically when the library or media-quality provenance changes.
- Smart Import rejects stale SAB completed-output paths whose release identity belongs to another Automation job, including the historical Big Brother Canada / Love Island cross-job pattern.
- TMDB diagnostics distinguish “not probed this runtime” from an actual upstream failure.
- v3.6.48 Library Integrity hardening, v3.6.47 Selected Episodes/PAR2 repair visibility, private SABnzbd 5.1.2, quality-aware selection, scan progress, Smart Import, and strict TV identity remain preserved.
