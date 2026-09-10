NewzDeck v3.6.67
Video Thumbnail Concurrency Tuning

New in v3.6.67:
- Raises only the Video thumbnail ceiling for providers with 48+ configured connections from 4 to 6.
- Keeps the existing overall adaptive preview budget and download-reserve behavior authoritative.
- Preserves schema-6 Video queue/HTTP/server/transport/BODY telemetry for acceptance testing.
- Preserves the five-request Image HTTP gate, provider allocation, 24 MB Video sample limit, 800-header strategy, Metadata Server v0.3.3, private SABnzbd 5.1.2, Discover, Smart Import and Automation.

NewzDeck remains free and open source under GPL-3.0-only.
