NewzDeck v3.6.60
Discover Library Index & Cache Write Coalescing

New in v3.6.60:
- Discover library status now uses a signature-aware lookup index instead of reparsing and scanning media-library.json for every card.
- metadata-cache.json updates remain immediately available in memory while bursty metadata responses are coalesced into one compact atomic disk flush.
- Coalesced cache flushes use a cross-process lock and signature reload so service/desktop peer entries are merged before persistence.
- Diagnostics expose library-index build/hit timing plus cache write requests, actual writes, coalesced requests, dirty keys and flush outcomes.
- Discover percentile reporting now interpolates tiny samples and includes average/sample counts.
- Preserves v3.6.59 stale detail rendering, hover-prefetch/view semantics, Metadata Server v0.3.3, v3.6.58 Automation reconciliation and private SABnzbd 5.1.2.
