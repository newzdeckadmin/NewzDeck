NewzDeck v3.6.74 - Video Cancellation Overlap Diagnostics

This release is a diagnostics-only Newsgroup Browser observability update built on v3.6.73.

Highlights:
- Every Video thumbnail request now carries a local correlation ID and the browser's logical active counts into the backend.
- Browsing telemetry schema 11 measures current-session versus superseded backend Video activity, cancellation-detection delay, and cancellation-drain duration.
- Bounded recent request lifecycle records let diagnostics determine whether backend peaks above the six-request browser ceiling are abandoned older work or another active admission path.
- v3.6.73 stable thumbnail identity behavior remains intact.
- Thumbnail scheduling, Image/Video concurrency, sample limits, provider allocation, SABnzbd 5.1.2, Settings reliability, All Posts behavior, Automation, Smart Import, Discover, and Metadata Server behavior are not retuned.

See release/RELEASE_NOTES_v3.6.74.md for details.
