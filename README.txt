NewzDeck v3.6.58
Automation Runtime Reconciliation & State Efficiency

New in v3.6.58:
- Old Automation runtime target records are conservatively pruned when their canonical item IDs no longer exist in a valid media-library.json, with a 24-hour grace window.
- Library-proven imported/satisfied targets cannot be demoted by stale searching/queueing/queued/grabbed/waiting scheduler writes; a genuinely newer grab remains allowed.
- Diagnostics expose runtime target/orphan counts, runtime bytes, prune/reclaimed-byte metrics and stale-state demotions blocked.
- Unmistakable legacy v3.6.56 byte-identical Smart Import holds are normalized historically to import_integrity_hold without reactivating current target holds.
- Diagnostics now measure server-side report construction time before any formatted-report caching decision.
- Preserves v3.6.57 Integrity Hold/count semantics, v3.6.55 terminal-history efficiency and private SABnzbd 5.1.2.
