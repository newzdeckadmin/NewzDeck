# NewzDeck v3.6.68 — Name Resolution Render Accumulator & Wait Telemetry

v3.6.68 is a narrow Newsgroup Browser All Posts performance release driven by the first production workload that meaningfully exercised v3.6.64 filename-resolution result rendering. In that v3.6.67 diagnostic, 46 resolver result batches produced 46 expensive full article renders, every `name_resolution_batch` sample was exactly 1, and those renders averaged roughly 487 ms. The existing 1.4-second one-shot timer was functioning correctly but was not coalescing the real sequential workload.

## Changes

- **Bounded automatic render accumulator.** The existing 1.4-second point becomes a soft wait rather than an unconditional single-result flush. If a second resolver result batch arrives before the hard deadline, NewzDeck renders immediately with both batches accumulated.
- **Three-second automatic hard cap.** A lone automatic result is never held longer than 3.0 seconds, preventing indefinite or long visible filename delay. The deadline is anchored to the first pending result and is not restarted by later batches.
- **Manual three-batch target.** Manual `Resolve more names` work targets three accumulated result batches with a 4.2-second hard cap, while the existing end-of-pass flush still displays any pending changes immediately when the manual pass finishes.
- **Resolver wait telemetry.** New `name_resolution_render_wait` client timing records the visible accumulation delay alongside the existing `name_resolution_batch` value, allowing diagnostics to measure render reduction against user-visible latency.
- **Browsing telemetry schema 7.** All schema-6 Image/Video admission, paired transport, BODY/sample, failure, endpoint-concurrency and render telemetry is retained.

## Deliberately unchanged

- v3.6.67 six-slot Video thumbnail ceiling for 48+ connection providers
- v3.6.65 five-request Image thumbnail HTTP admission gate
- provider connection allocation and NNTP download behavior
- 24 MB Video sample size and 12-segment cap
- 800-header first paint and OVER/XOVER chunk size
- 1,000-item progressive threshold
- v3.6.66 preview failure classification
- private SABnzbd 5.1.2 and Downloads/post-processing
- Smart Import and Automation reconciliation
- Metadata Server v0.3.3 and Discover
- terminal download-history schema 3

## Acceptance target

A deliberate All Posts workload with unresolved/obfuscated names should show fewer `name-resolution-batched-result` renders than resolver result batches, `name_resolution_batch` values above 1 for at least part of the workload, and `name_resolution_render_wait` bounded near 3 seconds for automatic activity. Image and Video performance should remain consistent with their accepted v3.6.67 behavior.
