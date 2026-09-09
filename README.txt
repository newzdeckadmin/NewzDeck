NewzDeck v3.6.63
Name Resolution Render Coalescing & Thumbnail Trace Telemetry

New in v3.6.63:
- All Posts filename resolution updates activity state in place instead of rebuilding the full article/package DOM merely to start, retry, or finish a pass.
- Result-driven full renders remain when resolved filenames, classifications, deferred state, or request failures actually change visible package presentation.
- Browser diagnostics separate thumbnail task queue wait, local thumbnail HTTP round-trip, browser post-processing, and full-preview recovery timing.
- Backend diagnostics classify image-thumbnail failures by the existing preview error code and track retryable failures.
- Preserves v3.6.62 progressive first-paint header reuse, 800-header limits, Discover/Automation behavior, Metadata Server v0.3.3, private SABnzbd 5.1.2 and terminal-history schema 3.
