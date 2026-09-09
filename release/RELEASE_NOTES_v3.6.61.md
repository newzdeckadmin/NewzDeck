# NewzDeck v3.6.61 — Newsgroup Browser Progressive Headers & Telemetry

v3.6.61 is a narrow newsgroup-browsing performance release based on a real v3.6.60 production diagnostic captured on a second Windows computer with Diagnostic Collector v1.0.16. The capture showed one current-runtime `/api/articles` overview timeout while native thumbnail decode remained fast, so this release targets the interactive header path rather than changing the proven image decoder, SAB transfer stack, Discover, or Automation architecture.

## Changes

- **Bounded All Posts first paint.** Qualifying 1,000–2,000 item progressive All Posts pages render from the newest 800 headers inside the requested logical page instead of waiting for the full page plus overlap before showing useful content.
- **Existing background completion retained.** The established progressive Smart Binary worker completes the full logical page after first paint, then estimates and fetches any deeper opaque multipart headers needed for package reconstruction.
- **Bounded OVER/XOVER ranges.** Large header ranges are split newest-first into adjacent chunks of at most 800 headers, reducing the chance that one large multiline NNTP response consumes the full 15-second interactive browsing socket budget.
- **No overlap spill on older pages.** The first-paint window is clamped inside the requested logical page, so page 2+ cannot spend its bounded window on the newer overlap region.
- **Passive backend browsing telemetry.** Diagnostics now retain bounded per-mode timing for header-pool wait, GROUP selection, OVER/XOVER, article processing, total page time, background reconstruction, group-list latency, header counts, cache hits, and timeout/failure counters.
- **Passive Chromium browsing telemetry.** The browser periodically ships the bounded timing samples NewzDeck already measures—Headers, Render, Set index, DOM window, Local search, Thumbnail, Full preview, and Viewer preload—into in-memory backend diagnostics, tagged by Images, Videos, Media, or All Posts.
- **Collector-compatible diagnostics contract.** The new `newsgroup_browsing_performance` field is exposed by `/api/diagnostics`; Diagnostic Collector v1.0.16 can capture it without adding `/api/groups`, `/api/articles`, preview, thumbnail, or other workload requests.

## Production evidence addressed

The second-computer v3.6.60 diagnostic exercised All Posts browsing with a 2,000 article limit and Continuous Browse enabled. It recorded a real `Unable to load article overview: The read operation timed out` event. During the same browsing session, native thumbnail decoding averaged roughly 21 ms with essentially zero decode queue wait, while BODY retrieval/reconstruction averaged hundreds of milliseconds. That evidence points to header/BODY network work—not WIC/native image decoding—as the more valuable optimization target.

v3.6.61 therefore does **not** simply raise thumbnail concurrency or decoder worker counts. It reduces synchronous header first-paint work and improves observability so later diagnostics can separate provider/network latency from local grouping/render/thumbnail/preview work.

## Validation

The v3.6.61 regression guard proves that a 2,200-header range partitions as 800/800/600 newest-first chunks, page-1 first paint is capped at the newest 800 logical-page headers, page-2+ overlap cannot expand or displace that first-paint window, and non-progressive semantics remain unchanged. It also requires the progressive background completion path, the passive diagnostics contract, client telemetry batching, v3.6.60 Discover library/cache optimizations, SABnzbd 5.1.2, and terminal-history schema 3 to remain intact.

## Preserved behavior

Metadata Server v0.3.3, private SABnzbd 5.1.2, download throughput/repair/extraction/retry behavior, terminal-history schema 3, v3.6.60 Discover library indexing/cache-write coalescing, v3.6.59 Detail/prefetch semantics, v3.6.58 Automation reconciliation, Smart Import ownership, Integrity Hold behavior, Library Integrity, Windows service/tray handoff, and Setup/Portable behavior remain unchanged.
