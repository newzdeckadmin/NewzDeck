# NewzDeck v3.6.7 — Browsing Pipeline & Long-Scroll Performance

NewzDeck v3.6.7 is a focused newsgroup-browsing responsiveness release built on v3.6.6. It promotes the accepted v3.6.7-r1 browsing-pipeline work so fast image browsing is paired with lower page latency, less wasted stale work, better continuous scrolling, and bounded long-session UI pressure.

## Faster, smoother browsing

- **Stale preview cancellation** — switching groups, pages, Gallery/List, media filters, or leaving Browse invalidates obsolete thumbnail/preview work. yEnc BODY reconstruction checks the browsing-session cancellation token while segments are streamed so stale transfers can stop early instead of consuming NNTP connections until completion.
- **Warm header connections** — up to two short-lived NNTP header clients are reused for interactive group paging, eliminating repeated connect/authentication overhead. They retire after roughly ten seconds idle.
- **Predictive older-page prefetch** — continuous browsing begins loading the next older header page several viewport-heights before the bottom so the page can often append immediately.
- **Velocity-aware thumbnail demand** — thumbnail look-ahead grows in the direction of fast scrolling and contracts again when movement slows, keeping the v3.6.6 adaptive preview scheduler fed without fixed-distance overfetch.
- **Progressive All Posts reconstruction** — All Posts > Packages can return a useful initial package view before a deep multipart header expansion is finished, then complete the same page in a bounded background worker.
- **Long-scroll memory relief** — very long gallery sessions release far-offscreen decoded thumbnail images in bounded batches while preserving cached thumbnail URLs for fast return scrolling without another NNTP BODY download.

## Preserved

- v3.6.6 Adaptive Preview Connection Scaling remains intact, including the 80-worker preview ceiling, connection-budget awareness, failure/throughput backoff, download priority, and fast idle socket release.
- v3.6.5 Windows Taskbar Identity Reliability remains intact.
- v3.6.4 Newsgroup Package Browser & Binary Reconstruction remains intact, including package-first All Posts, multipart reconstruction, provider-independent name recovery, sorting, queueing, and the persistent Min size cutoff.
- v3.6.3 Automation Sidebar Startup & Cache Reliability, v3.6.2 Tray Upgrade Lock Reliability, v3.6.1 Installer Upgrade Reliability, the v3.6.0 UI/UX Overhaul, and v3.5.52 Authoritative Service Runtime Handoff remain preserved.
- Private SAB high-throughput downloads, Smart Import, Automation, Discover/TMDB, provider behavior, and Metadata Server v0.3.3 compatibility remain unchanged.

## Upgrade notes

You may install v3.6.7 directly over an existing NewzDeck installation. Manual tray or background-service shutdown should not normally be required.

NewzDeck remains intentionally unsigned, so Windows SmartScreen may show an **Unknown Publisher** warning. Verify downloads with `NewzDeck_v3.6.7_SHA256.txt` if desired.
