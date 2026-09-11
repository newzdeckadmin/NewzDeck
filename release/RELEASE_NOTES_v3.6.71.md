# NewzDeck v3.6.71 — Video Thumbnail Decode Failure Suppression

v3.6.71 is a narrow behavioral follow-up to the v3.6.70 observability release. A representative production Video-browsing capture recorded 81 browser-side post-processing failures and all 81 were `complete-browser-decode-failed`, while partial-sample browser-frame extraction succeeded and the six-slot Video endpoint reached its intended concurrency. The same capture showed healthy localhost transport and negligible backend executor/build-lock wait.

The follow-up source review found a concrete retry-policy mismatch: v3.6.70 correctly preserved `browser-decode-failed` in telemetry, but the UI failure path ignored client `error.code`, converted that result back to generic `preview_failed`, and therefore treated it as retryable.

## Changes

- **Preserve client Video error codes.** `friendlyPreviewError()` now retains client `error.code` when the backend did not provide an `error_code`.
- **Definitive browser decode policy.** `browser-decode-failed` and `ffmpeg-required` are treated as non-retryable unsupported-media outcomes for the current runtime. They remain visible in All Posts/All-content contexts where appropriate but are not repeatedly fetched just because a group is refreshed.
- **No stale requeue path.** Known unsupported media are excluded from Related Media representative selection, remain marked unpreviewable across group refreshes, and are rejected by `queueThumbnail()` if a stale holder attempts to queue them.
- **Accurate Retry UI.** Cached non-retryable thumbnail failures no longer show a Retry button. Transient frame timeout, frame capture, thumbnail-store and unknown failures remain retryable.
- **Schema 9 policy telemetry.** `video_thumbnail_policy` records aggregate visible/prefetch + partial/complete non-retryable policy application. No media bytes, filenames, image contents or codec payloads are added to diagnostics.

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

After representative Video browsing and revisiting/refreshing the same group, Diagnostic Collector v1.0.28 should show schema 9 `video_thumbnail_policy` reason counts for `browser-decode-failed`/`ffmpeg-required` non-retryable policy applications. Browser decode failures should no longer present misleading Retry UI or be re-requested merely by normal group refresh/Related Media representative selection. Concurrency and transport metrics should remain consistent with the accepted v3.6.70 baseline.
