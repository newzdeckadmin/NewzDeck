NewzDeck v3.6.59
Discover Responsiveness & Metadata Cache Efficiency

New in v3.6.59:
- Discover title details use stale-while-revalidate: persisted detail renders immediately while stale metadata refreshes in the background.
- metadata-cache.json is held in a signature-aware process-local parsed cache instead of being reparsed for every lookup.
- Cache writes use compact JSON and revalidate the shared file before writing so desktop/service peers cannot be overwritten by stale process state.
- True cold Discover detail calls use an 8-second cloud budget and background detail refresh is capped at two concurrent requests.
- Hover prefetch waits longer, is concurrency-bounded, and no longer counts as a viewed title for For You personalization.
- Diagnostics expose Discover route latency, detail source/refresh counters, and metadata-cache read/write cost.
- Preserves v3.6.58 Automation reconciliation and private SABnzbd 5.1.2 behavior.
