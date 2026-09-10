NewzDeck v3.6.66
Preview Failure Classification & Video Thumbnail Telemetry

New in v3.6.66:
- Splits known immediate/permanent preview failures out of the generic retryable preview_failed bucket.
- Adds paired client/server timing, backend phase timing, failure counters and endpoint concurrency telemetry for video thumbnails.
- Keeps unknown/transient failures retryable until diagnostics establish otherwise.
- Preserves the v3.6.65 five-request Image HTTP admission gate, provider/NNTP concurrency, 800-header strategy, Metadata Server v0.3.3, private SABnzbd 5.1.2, Discover, Smart Import and Automation behavior.

NewzDeck remains free and open source under GPL-3.0-only.
