NewzDeck v3.6.64
Name Resolution Result Batching & Thumbnail Transport Telemetry

New in v3.6.64:
- Batches rapid All Posts filename-resolution result updates before rebuilding the full article/package DOM.
- Adds request-paired thumbnail HTTP/server/transport-gap telemetry so client-side delay is measured on the exact same request.
- Tracks current and peak image-thumbnail endpoint concurrency by Images, Videos, Media, and All Posts mode.
- Preserves v3.6.62 progressive header reuse, v3.6.63 resolver status-render coalescing, 800-header limits, Discover/Automation behavior, Metadata Server v0.3.3, private SABnzbd 5.1.2 and terminal-history schema 3.

NewzDeck remains free and open source under GPL-3.0-only.
