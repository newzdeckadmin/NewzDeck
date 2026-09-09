NewzDeck v3.6.62
Progressive Header Reuse & Thumbnail Phase Telemetry

New in v3.6.62:
- Progressive All Posts completion reuses the first-paint header window instead of downloading those same headers again.
- Background completion fetches only missing logical-page/overlap headers plus genuinely required older Smart Binary expansion.
- Diagnostics add image-thumbnail endpoint phase timing for cache lookup, executor wait, build-lock wait, BODY transfer, native decode, worker and endpoint total latency by browsing mode.
- Chromium render telemetry now records bounded render reasons while preserving the aggregate Render timing metric.
- Preserves v3.6.61 800-header limits, Discover/Automation behavior, Metadata Server v0.3.3, private SABnzbd 5.1.2 and terminal-history schema 3.
