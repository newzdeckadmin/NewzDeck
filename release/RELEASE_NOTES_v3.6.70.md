# NewzDeck v3.6.70 — Video Thumbnail Post-Processing Diagnostics

v3.6.70 is a narrow observability release based on a v3.6.69 production capture where all 15 recorded Video thumbnail post-processing samples failed after successful HTTP/sample retrieval. The existing telemetry counted those failures but discarded the browser-side failure reason, so changing concurrency, sample size, or decoding behavior would have been speculative.

## Changes

- **Reason-specific Video post telemetry.** `video_thumbnail_post` now retains aggregate reason timing and counters in the passive browsing-performance contract.
- **Actionable browser classifications.** Browser frame failures distinguish `browser-decode-failed`, `sample-no-frame`, `browser-frame-timeout`, `frame-capture-failed`, `frame-unavailable`, `ffmpeg-required`, and thumbnail-store failures.
- **Context without media content.** Reasons retain visible/prefetch demand and partial/complete sample context. No video bytes, filenames, or thumbnail image contents are added to telemetry.
- **Schema 8.** Browsing-performance schema advances from 7 to 8 for the additive Video post-processing reason contract.

## Deliberately unchanged

- high-connection Video thumbnail ceiling of 6
- adaptive preview/download budget
- Image thumbnail HTTP admission limit of 5
- 24 MB Video sample size and 12-segment cap
- provider connection allocation / NNTP download behavior
- 800-header first paint and OVER/XOVER chunk size
- 1,000-item progressive threshold
- v3.6.68 All Posts bounded resolver accumulator
- v3.6.66 preview failure classification
- v3.6.69 settings-save retry/reliability behavior
- private SABnzbd 5.1.2, Smart Import, Automation reconciliation and Discover
- Metadata Server v0.3.3
- terminal download-history schema 3

## Acceptance target

After representative Video browsing, Diagnostic Collector v1.0.27 should show reason-specific `video_thumbnail_post` timing/counts. The first behavioral follow-up, if any, should be chosen from those observed reasons rather than from aggregate failure counts alone. Image and Video concurrency/performance should remain consistent with the accepted v3.6.69 baseline.
