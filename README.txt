NewzDeck v3.6.54
Downloads History Compaction & Automation Startup Efficiency

New in v3.6.54:
- Finalized Completed jobs are retired from the cross-runtime operational ledger after their durable terminal-history row is safely committed. Failed, cancelled, retryable, importing, cleanup-pending, and other actionable jobs remain operational.
- Durable terminal history now owns cached Completed/Failed indexes and status counts, so a 50-row page no longer copies and sorts the full 5,000-row history.
- Completed pages no longer transport every matching UUID, and compact terminal rows carry flattened Automation identity while rich SAB/PAR2 stage history stays lazy behind Details.
- SAB recent History cannot re-adopt a finalized job already owned by NewzDeck terminal history.
- Automation sidebar counts are cached against library/profile/config file signatures and local date. Startup count probes stop after the first populated response; full-summary warm retries stop after success.
- Preserves the v3.6.53 NZB identity gate, next-candidate recovery, Smart Import protections, copy-on-write Live Downloads presentation, sampler evidence, and private SABnzbd 5.1.2.
