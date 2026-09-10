# NewzDeck v3.6.66 — Preview Failure Classification & Video Thumbnail Telemetry

v3.6.66 is a narrow Newsgroup Browser diagnostics and correctness release based on two v3.6.65 acceptance captures. Those captures validated the five-request Image HTTP admission gate: the Chromium/local transport gap fell sharply and visible scheduling remained healthy under heavier browsing. The remaining evidence showed two gaps instead: hundreds of extremely fast generic `preview_failed` results were still treated as retryable, and Video thumbnail latency lacked request-paired backend/transport evidence.

## Changes

- **Specific preview failure classes.** Known permanent conditions now report dedicated non-retryable codes for missing segments/references, segment-count limits, preview safety limits, non-previewable media, empty video samples, and corrupt/unsupported encoding. Unknown failures remain `preview_failed` and retryable; temporary provider/segment-fetch failures remain retryable.
- **Video request-paired transport telemetry.** `/api/thumbnail/video` now returns the exact request's backend elapsed time, allowing Chromium HTTP time to be split into paired server work and client-minus-server transport/dispatch gap just like Images.
- **Video backend phase telemetry.** Diagnostics record video thumbnail executor wait/worker time, cache lookup, build-lock wait, BODY/sample retrieval, sample bytes, frame extraction, endpoint total, failure codes, retries/timeouts and cache-hit counters.
- **Video endpoint concurrency telemetry.** Current/peak `/api/thumbnail/video` endpoint concurrency is exposed separately without changing the existing video concurrency ceiling.
- **Browser post-processing timing.** Video browser-frame extraction/persistence is timed separately from local HTTP so client decode work can be distinguished from provider/backend work.
- **Browsing telemetry schema 6.** Retains all schema-5 Image admission/demand, paired transport, resolver batching and endpoint-concurrency data while adding Video endpoint concurrency/phase coverage.

## Deliberately unchanged

- v3.6.65 five-request Image thumbnail HTTP admission gate
- 800-header first paint and OVER/XOVER chunk size
- 1,000-item progressive threshold
- provider connection allocation and NNTP throughput behavior
- adaptive preview/Image/Video scheduler ceilings
- native thumbnail decoder worker architecture
- Video sample size and segment cap
- v3.6.63/v3.6.64 All Posts name-resolution render coalescing/batching
- private SABnzbd 5.1.2 and Downloads/post-processing behavior
- Smart Import and Automation reconciliation
- Metadata Server v0.3.3
- Discover behavior
- terminal download-history schema 3

## Acceptance target

A production diagnostic should show which specific failure codes replace the former fast generic `preview_failed` population and whether those permanent classes stop generating pointless Retry actions. Video browsing should provide enough paired HTTP/server/transport-gap and backend phase samples to determine whether future Video work belongs in scheduling, localhost transport, provider BODY/sample retrieval, ffmpeg/browser frame extraction, or no tuning at all. All Posts/name-resolution should still be exercised separately to accept v3.6.64 resolver result batching.
