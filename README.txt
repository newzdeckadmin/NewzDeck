NewzDeck v3.6.73 - Thumbnail Task Identity & Visibility Telemetry

This release is a narrow Newsgroup Browser reliability and observability update built on v3.6.72.

Highlights:
- Queued Image and Video thumbnail work now re-validates its stable source article identity before execution instead of trusting an array index that may have changed during continuous browsing.
- Stale missing or incompatible thumbnail work is discarded locally rather than sending mismatched media/segment data to the thumbnail endpoint.
- Browsing telemetry schema 10 keeps total queue age and adds separate offscreen/prefetch dwell and actual visible-wait measurements, plus passive stable-identity relocation/drop counters.
- Thumbnail scheduling, Image/Video concurrency, sample limits, provider allocation, SABnzbd 5.1.2, Settings reliability, All Posts behavior, Automation, Smart Import, Discover, and Metadata Server behavior are not retuned.

See release/RELEASE_NOTES_v3.6.73.md for details.
