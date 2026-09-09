NewzDeck v3.6.61
Newsgroup Browser Progressive Headers & Telemetry

New in v3.6.61:
- Large All Posts pages paint from a bounded newest 800-header window instead of waiting on the full 2,000+ header overlap range.
- Full-page and opaque multipart reconstruction continues through the existing background completion path.
- Large OVER/XOVER requests are split into bounded newest-first chunks to reduce interactive header timeout risk.
- Diagnostics now retain passive newsgroup browsing performance telemetry by Images, Videos, Media and All Posts mode, including backend header stages and Chromium render/thumbnail/preview timings.
- Preserves Discover v3.6.60 behavior, Metadata Server v0.3.3, Automation/Smart Import integrity, private SABnzbd 5.1.2 and terminal-history schema 3.
