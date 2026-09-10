# NewzDeck v3.6.65 — Thumbnail HTTP Admission Control & Demand Telemetry

v3.6.65 is a narrow Newsgroup Browser performance release based on v3.6.64 production telemetry. The v3.6.64 request-paired measurements showed that normal Image thumbnail latency was no longer dominated by Python thumbnail processing: Chromium-observed localhost HTTP time substantially exceeded the exact paired backend time, while the image-thumbnail endpoint peaked at six concurrent requests. NewzDeck's provider-derived thumbnail scheduler can submit substantially more work than that, so v3.6.65 separates browser HTTP admission from NNTP/provider concurrency.

## Changes

- **Five-request image-thumbnail HTTP admission gate.** At most five browser `/api/thumbnail/image` requests are admitted at once. This is a localhost/Chromium transport limit only; it does not reduce the user's configured NNTP connections, preview ramp ceilings, backend preview workers, native decoder workers, or video limits.
- **Priority preserved across the new gate.** Visible thumbnail tasks outrank prefetch/offscreen tasks while waiting for HTTP admission. Existing scheduler priorities and Related Media cover reservations remain in control of which work is started.
- **Speculative warming cannot bypass admission.** Next-page image warming now uses the same centralized `/api/thumbnail/image` wrapper and the same five-request gate.
- **Admission timing telemetry.** Browser diagnostics record `thumbnail_admission` wait time separately from the existing scheduler `thumbnail_queue`, Chromium `thumbnail_http`, paired backend `thumbnail_server_pair`, and `thumbnail_transport_gap` measurements.
- **Visible-versus-prefetch demand telemetry.** Scheduler and HTTP reason breakdowns identify visible, prefetch/offscreen, Related Media cover, and speculative-page image demand so acceptance testing can distinguish user-visible latency from background work.
- **Browsing telemetry schema 5.** Adds `thumbnail_admission` while retaining all v3.6.64 request-paired transport, endpoint-concurrency, resolver-batch, and failure-classification telemetry.
- **Expected browse cancellation normalized.** Initial `BrowseSessionCancelled` checks in preview, image-thumbnail, and video-thumbnail endpoints return the existing non-retryable `browse_cancelled` contract. Thumbnail task handling ignores this expected supersession instead of painting it as a failed preview.

## Deliberately unchanged

- 800-header first paint and OVER/XOVER chunk size
- 1,000-item progressive threshold
- provider connection allocation and NNTP throughput behavior
- adaptive preview/thumbnail scheduler ceilings
- native thumbnail decoder worker architecture
- v3.6.63/v3.6.64 All Posts name-resolution render coalescing/batching
- private SABnzbd 5.1.2 and Downloads/post-processing behavior
- Smart Import and Automation reconciliation
- Metadata Server v0.3.3
- Discover behavior
- terminal download-history schema 3

## Acceptance target

A production diagnostic run should show the Image thumbnail endpoint peak at or below five for NewzDeck browser-generated image-thumbnail requests, materially lower `thumbnail_transport_gap`/`thumbnail_http` latency, and separate `thumbnail_admission` plus scheduler queue distributions for visible versus prefetch demand. The same run should intentionally exercise All Posts/name resolution so v3.6.64 result-batching can finally be accepted independently of this transport change.
