NewzDeck v3.6.65
Thumbnail HTTP Admission Control & Demand Telemetry

New in v3.6.65:
- Caps browser-side image-thumbnail HTTP admission at five in-flight /api/thumbnail/image requests while preserving the provider/NNTP preview concurrency model.
- Adds thumbnail_admission timing and visible-versus-prefetch reasons to separate user-visible demand from speculative/offscreen work.
- Routes next-page speculative thumbnail warming through the same HTTP admission gate.
- Treats superseded browsing-session preview/thumbnail requests as expected browse_cancelled control flow instead of generic application errors.
- Preserves v3.6.62 progressive header reuse, v3.6.63/v3.6.64 resolver behavior, 800-header limits, Metadata Server v0.3.3, private SABnzbd 5.1.2, Discover and Automation/Smart Import.

NewzDeck remains free and open source under GPL-3.0-only.
