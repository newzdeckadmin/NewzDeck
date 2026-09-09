# NewzDeck v3.6.62 — Progressive Header Reuse & Thumbnail Phase Telemetry

v3.6.62 is a narrow Newsgroup Browser efficiency and observability release based on the first real v3.6.61 production capture collected with Diagnostic Collector v1.0.17. v3.6.61 removed the current-runtime `/api/articles` timeout seen in v3.6.60 and proved the 800-header first-paint/chunk strategy, while the new telemetry exposed two next-order costs: the first 800 progressive headers were downloaded again by background completion, and image-thumbnail client latency remained much higher than BODY/decode time.

## Changes

- **Progressive header reuse.** The bounded first-paint OVER/XOVER rows are now passed into background Smart Binary completion instead of being discarded. The worker fetches only the missing portions of the full logical/overlap range.
- **No duplicate first-paint transfer.** Seed and newly fetched OVER rows are merged by article number before grouping. In the observed two-page v3.6.61 workload, this removes the 1,600-header duplicate network work while preserving the same complete logical-page result.
- **Smart Binary expansion remains bounded.** After the logical range is complete, only genuinely older headers estimated as necessary for opaque multipart reconstruction are fetched, still through the existing 800-header newest-first chunking path.
- **Thumbnail endpoint phase telemetry.** Passive diagnostics now separate persistent-cache lookup, preview-executor queue wait, per-thumbnail build-lock wait, BODY transfer, native decode, worker time, and total image-thumbnail endpoint latency by browsing mode.
- **Thumbnail lifecycle counters.** Diagnostics retain requests, cache hits, cache-after-wait hits, failures, timeouts, fallbacks, and BODY bytes so slow thumbnails can be attributed without increasing concurrency or decode workers first.
- **Render-reason telemetry.** The existing aggregate Render metric is preserved and augmented with bounded reason-specific samples/counters for initial page loads, Continuous Browse, progressive completion, name-resolution state/retry/result/finish, thumbnail hiding, and other UI causes.
- **Existing safety preserved.** The 800-header first-paint/chunk limits, 1,000-item progressive threshold, preview scheduler/concurrency, native thumbnail worker sizing, Metadata Server v0.3.3, Discover, Automation/Smart Import, private SABnzbd 5.1.2, and terminal-history schema 3 remain unchanged.

## Production evidence addressed

The first v3.6.61 production diagnostic had zero current-runtime browsing errors/timeouts, confirming the header-timeout fix. Images header processing and rendering were fast, while OVER/XOVER remained the dominant uncached header cost. Two progressive All Posts loads showed 1,600 foreground first-paint headers followed by 4,400 background headers even though the two complete ranges themselves required 4,400 headers, proving the first-paint rows were redundantly fetched again.

The same capture showed image-thumbnail client latency around seconds while BODY assembly averaged hundreds of milliseconds and native decode remained around tens of milliseconds with essentially no decode queue wait. v3.6.62 therefore instruments the endpoint phases rather than guessing by increasing decoder or provider concurrency. It also records render reasons because All Posts produced many more render samples than header-load samples.

## Regression protections

- Seed first-paint rows plus missing-range rows must merge into one unique article-number sequence with no gaps or duplicates.
- Background completion may fetch only missing logical/overlap ranges plus genuinely older Smart Binary expansion.
- The 800-header chunk/first-paint settings and 1,000-item large-page threshold remain unchanged.
- Thumbnail telemetry is passive and does not alter preview connection budgets or native decode worker sizing.
- Aggregate Render telemetry remains available while reason-specific telemetry is additive.
- All carried v3.6.61 and earlier regression guards remain mandatory.
- SAB remains 5.1.2 and terminal-history schema remains 3.
