NewzDeck v3.6.70
Video Thumbnail Post-Processing Diagnostics

New in v3.6.70:
- Adds passive reason-specific telemetry for Video thumbnail post-processing failures.
- Distinguishes browser decode failure, no-frame samples, frame timeout, frame capture failure, FFmpeg-required formats, and thumbnail-store failures while retaining visible/prefetch and partial/complete sample context.
- Advances browsing-performance telemetry to schema 8 only for this additive observability improvement.
- Preserves the accepted six-slot Video ceiling, five-request Image gate, 24 MB/12-segment Video sample bounds, 800/800/1000 headers, All Posts accumulator, Metadata Server v0.3.3, private SABnzbd 5.1.2, Discover, Smart Import and Automation.

NewzDeck remains free and open source under GPL-3.0-only.
