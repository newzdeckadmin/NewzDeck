# NewzDeck v3.6.59 — Discover Responsiveness & Metadata Cache Efficiency

v3.6.59 is a focused Discover responsiveness release based on the v3.6.58 production diagnostics. It leaves Metadata Server v0.3.3 and the private SABnzbd 5.1.2 transfer/repair/extraction architecture unchanged.

## Changes

- **Detail stale-while-revalidate.** A persisted TMDB title-detail record can render immediately even when it is older than the normal freshness window. NewzDeck refreshes that stale detail in the background instead of making the Discover modal wait on the metadata cloud first.
- **Bounded cold-detail latency.** A true detail cache miss now gives the metadata request an 8-second backend budget instead of the previous 18-second detail wait. The UI paints the title/card information immediately while richer metadata is being obtained.
- **Metadata cache parse reuse.** `metadata-cache.json` now has a signature-aware process-local parsed snapshot. Repeated cache reads pay a file-stat check rather than reparsing the entire multi-megabyte JSON document.
- **Peer-safe compact cache writes.** Before a cache write, NewzDeck rechecks the on-disk signature and reloads if another desktop/service process changed the file. The hot cache is written as compact JSON rather than pretty-printed JSON, while preserving the existing 500-entry trim threshold / 400-entry retained set.
- **Conservative hover prefetch.** Discover waits 650 ms before starting a hover detail prefetch and caps browser-side prefetch activity at two concurrent requests. Backend stale-detail refresh is separately capped at two concurrent workers.
- **Prefetch no longer means “viewed.”** Hover prefetch uses an explicit `prefetch` interaction and does not write Discover viewed-history. An explicit Details open records the view, including when it attaches to a prefetch that was already in flight.
- **Progressive detail presentation.** On a cold browser-side detail load, the modal immediately paints the card’s existing poster/backdrop/title/overview while cast, recommendations, release metadata, and links are enriched.
- **Discover performance telemetry.** Diagnostics now expose Home/Browse/Detail route count/error/p50/p95/max timings, metadata-cache bytes/read/write timing and hit counts, detail memory/persistent/cloud source counts, and background-refresh activity.

## Validation

The v3.6.59 regression guard verifies process-local metadata-cache reuse, peer-process file-change merging before writes, compact hot-cache serialization, stale persistent detail fallback, prefetch-vs-open viewed-history semantics, the 8-second cold-detail budget, bounded Discover performance telemetry, UI prefetch limits, static identity coherence, and unchanged SABnzbd 5.1.2 / terminal-history schema 3 behavior.

A synthetic ~15.5 MB metadata-cache test reduced a repeated lookup from about 27 ms for the first parse to about 0.04 ms for the subsequent in-memory lookup on the validation host. This is a synthetic measurement, not a promise of identical production timings.

## Preserved behavior

v3.6.58 Automation runtime reconciliation, 24-hour orphan grace/pruning, semantic imported/satisfied precedence, historical Integrity Hold normalization, Smart Import ownership, Library Integrity, Windows service/tray handoff, Setup behavior, and private SABnzbd 5.1.2 authority remain unchanged.
