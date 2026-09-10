# NewzDeck v3.6.64 — Name Resolution Result Batching & Thumbnail Transport Telemetry

v3.6.64 is a narrow Newsgroup Browser responsiveness and observability release based on the first v3.6.63 production acceptance capture collected with Diagnostic Collector v1.0.19. v3.6.63 eliminated status-only name-resolution renders, while the new trace telemetry showed that result-driven resolver renders remained expensive and that browser-observed thumbnail HTTP latency substantially exceeded Python endpoint time.

## Changes

- **Name-resolution result batching.** Rapid filename-resolution result batches no longer each force an immediate full All Posts rebuild. Manual passes flush after bounded groups of result batches and at completion; automatic passes coalesce adjacent result updates with a bounded timer and batch threshold.
- **Correct final presentation preserved.** Pending resolver changes are always flushed before a manual pass finishes, and stale group/provider contexts are discarded rather than rendering into the wrong tab.
- **Request-paired thumbnail timing.** `/api/thumbnail/image` responses now carry that exact request's Python elapsed time. Chromium records the paired server duration and `client HTTP - server` transport gap for the same request.
- **Thumbnail endpoint concurrency telemetry.** Diagnostics expose current and peak image-thumbnail endpoint concurrency by Images/Videos/Media/All Posts mode without changing the scheduler, provider connection budget, preview pool, or decoder workers.
- **Browsing telemetry schema 4.** Adds `thumbnail_server_pair`, `thumbnail_transport_gap`, `name_resolution_batch`, and endpoint concurrency gauges while preserving all prior passive telemetry.
- **Existing safety preserved.** v3.6.62 progressive seed reuse, v3.6.63 resolver activity DOM updates, 800-header first-paint/chunk limits, 1,000-item threshold, Metadata Server v0.3.3, Discover, Automation/Smart Import, private SABnzbd 5.1.2, and terminal-history schema 3 remain unchanged.

## Production evidence addressed

The v3.6.63 acceptance capture proved that state/start/finish name-resolution full renders fell to zero, but 55 result-driven renders remained and averaged roughly half a second. The same capture showed Image thumbnail client HTTP around 2.4 seconds average while backend endpoint time was roughly 0.6 seconds, plus long client scheduler queues. v3.6.64 therefore batches only rapid result-driven resolver changes and measures the exact request-paired local transport gap before any concurrency tuning.

## Deliberately unchanged

- 800-header first paint and OVER/XOVER chunk size
- 1,000-item progressive threshold
- provider/preview connection allocation
- thumbnail/video concurrency and native decoder workers
- private SABnzbd 5.1.2 and Downloads/post-processing behavior
- Metadata Server v0.3.3
- Discover and Automation/Smart Import semantics
