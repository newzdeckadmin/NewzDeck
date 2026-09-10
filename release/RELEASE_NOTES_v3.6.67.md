# NewzDeck v3.6.67 — Video Thumbnail Concurrency Tuning

v3.6.67 is a narrow Newsgroup Browser performance release driven by v3.6.66 schema-6 diagnostics. The v3.6.66 acceptance capture showed that Video localhost transport overhead was negligible while the Video endpoint saturated its four-request ceiling and visible Video thumbnails still accumulated meaningful scheduler queue time.

## Changes

- **High-connection Video ceiling: 4 → 6.** Providers with 48 or more configured connections may now run up to six Video thumbnail tasks when the overall preview budget allows it.
- **Lower tiers unchanged.** Providers below 48 connections retain the existing one/two/three Video task tiers.
- **Download reserve still wins.** The Video limit remains bounded by `state.thumbConcurrency`, so active downloads and adaptive preview throttling can reduce Video work below six automatically.
- **No Video HTTP gate.** v3.6.66 diagnostics showed only single-digit-millisecond localhost transport overhead, so no Image-style browser HTTP admission gate is added to Video.
- **Schema-6 telemetry preserved.** Video queue, HTTP, paired backend, transport-gap, BODY/sample, frame, failure and endpoint-concurrency measurements remain unchanged for acceptance testing.

## Deliberately unchanged

- v3.6.65 five-request Image thumbnail HTTP admission gate
- provider connection allocation and NNTP download behavior
- 24 MB Video sample size and 12-segment cap
- 800-header first paint and OVER/XOVER chunk size
- 1,000-item progressive threshold
- v3.6.63/v3.6.64 All Posts resolver render coalescing/batching
- v3.6.66 preview failure classification
- private SABnzbd 5.1.2 and Downloads/post-processing
- Smart Import and Automation reconciliation
- Metadata Server v0.3.3 and Discover
- terminal download-history schema 3

## Acceptance target

On a 48+ connection provider during browse/idle conditions, diagnostics should show Video endpoint concurrency able to reach up to six, materially lower visible Video scheduler queue time than v3.6.66, and no offsetting deterioration in Video BODY/sample latency, Image responsiveness, header timing, or download-reserve behavior.
