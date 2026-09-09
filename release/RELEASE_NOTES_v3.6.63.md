# NewzDeck v3.6.63 — Name Resolution Render Coalescing & Thumbnail Trace Telemetry

v3.6.63 is a narrow Newsgroup Browser responsiveness and observability release based on the first v3.6.62 production acceptance capture collected with Diagnostic Collector v1.0.18. v3.6.62 successfully eliminated duplicate progressive first-paint header retrieval and remained free of browsing timeouts, while its new telemetry showed that almost half of All Posts full renders came from filename-resolution state/finish transitions and that browser-observed thumbnail latency remained substantially higher than backend endpoint time.

## Changes

- **Name-resolution activity updates in place.** Starting, retrying, and finishing an All Posts filename-resolution pass no longer rebuilds the complete article/package DOM merely to change resolver activity state.
- **Result-driven package rendering retained.** A full All Posts render still occurs when a name-resolution response changes resolved filenames, classification/deferred state, or request-failure presentation, preserving package regrouping and filename visibility.
- **Resolver UI remains live.** The Resolve names control is disabled/labeled in place while work is active, and visible unresolved rows receive/remove the `RESOLVING…` activity chip without forcing an otherwise unnecessary list rebuild.
- **Client thumbnail queue timing.** Browser telemetry now measures the time a thumbnail task spends in NewzDeck's thumbnail scheduler before execution begins.
- **Local thumbnail HTTP timing.** Browser telemetry separately measures each `/api/thumbnail/image` round trip, including success/failure reason tags, so local request/response time can be compared directly with Python endpoint timing.
- **Browser thumbnail post-processing timing.** Persistent thumbnail response handling/capture/storage is timed separately from the local HTTP request.
- **Full-preview recovery timing.** When an item thumbnail falls back through the existing full-preview recovery path, diagnostics now record recovery duration and whether recovery succeeded.
- **Backend thumbnail failure classification.** Existing preview errors are counted by their established classification (`article_missing`, `multipart_incomplete`, `provider_temporary`, `decode_failed`, `preview_failed`, or `browse_cancelled`) and retryable failures are counted separately.
- **Browsing telemetry schema 3.** The passive runtime telemetry contract adds the new client thumbnail stages and reason counters without creating synthetic browsing workload.
- **Existing tuning preserved.** The v3.6.62 first-paint seed reuse, 800-header first-paint/chunk limits, 1,000-item progressive threshold, provider/preview concurrency, native decoder worker sizing, Metadata Server v0.3.3, Discover, Automation/Smart Import, private SABnzbd 5.1.2, and terminal-history schema 3 remain unchanged.

## Production evidence addressed

The v3.6.62 capture recorded 130 All Posts renders. Sixty-one were Continuous Browse renders and 63 were name-resolution state/finish renders; only four were initial/progressive paint. Name-resolution state and finish renders averaged roughly 280 ms and reached about 600 ms p95, making redundant resolver-state rebuilds a measurable UI cost.

The same capture showed that the Python thumbnail endpoint itself averaged roughly 567 ms for Images while browser-observed thumbnail tasks averaged roughly 1.61 seconds. Server-side cache lookup, executor wait, build-lock wait, and decode were all small; NNTP BODY retrieval dominated backend work. v3.6.63 therefore adds client-side queue/HTTP/post/recovery timing instead of blindly increasing concurrency or decoder workers.

Media browsing also showed a much higher image-thumbnail failure rate than Images browsing, without corresponding timeout failures. v3.6.63 classifies those failures using the already-established preview error taxonomy before any recovery/concurrency policy is changed.

## Regression safety

- v3.6.62 progressive seed reuse remains release-blocked by its pure merge fixture and header telemetry markers.
- The 800/800/1,000 browsing thresholds remain fixed.
- Name resolution must keep result-driven full renders while state/retry/finish activity stays targeted/in-place.
- The new thumbnail telemetry is passive and bounded.
- All carried guards through v3.6.62 remain mandatory.
- SABnzbd remains pinned to 5.1.2 and terminal-history schema remains 3.
