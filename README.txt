NewzDeck v3.6.71
Video Thumbnail Decode Failure Suppression

New in v3.6.71:
- Fixes the client-side retry-policy gap exposed by v3.6.70 diagnostics: browser-decode-failed and ffmpeg-required Video thumbnail errors keep their real error codes instead of becoming generic retryable preview_failed errors.
- Confirmed browser codec/decoder limitations are retained as non-retryable for the current runtime, are not requeued by group refresh/Related Media paths, and no longer show a misleading Retry button.
- Transient browser frame timeout, capture, thumbnail-store, and unknown failures remain retryable.
- Advances browsing-performance telemetry to schema 9 with passive video_thumbnail_policy reason counters for acceptance testing.
- Preserves the accepted six-slot Video ceiling, five-request Image gate, 24 MB/12-segment Video sample bounds, 800/800/1000 headers, All Posts accumulator, Metadata Server v0.3.3, private SABnzbd 5.1.2, Discover, Smart Import and Automation.

NewzDeck remains free and open source under GPL-3.0-only.
