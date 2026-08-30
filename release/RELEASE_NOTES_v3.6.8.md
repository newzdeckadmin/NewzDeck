# NewzDeck v3.6.8 — Image Browsing Performance & Gallery Quality

NewzDeck v3.6.8 is a cumulative newsgroup image-browsing performance and gallery-quality release built on v3.6.7. It promotes the accepted v3.6.8-r1 through r6 work after real-world testing confirmed substantial improvements in long Continuous sessions, deep page jumps, large-image thumbnail generation, cached revisits, and burst rendering.

## Image browsing performance

- **Long-session pressure controls** — bounded demand scans, far-offscreen decoded-image release, RAM-aware hot caches, and a separately bounded native decode pool.
- **Deep page-jump isolation** — explicit navigation cancels stale work, resets scroll velocity, starts at the top, and temporarily disarms Continuous append/predictive prefetch.
- **Persistent WIC-first native thumbnails** — NewzDeckThumb.exe uses Windows Imaging Component first, falls back safely, and keeps a small worker pool alive.
- **Size-aware scheduling and multipart lanes** — quick visible thumbnails are favored without starving large images; very large visible multipart images may borrow 2-3 coordinated BODY lanes.
- **RAM and persistent cache acceleration** — recent header pages, thumbnail URLs, tiny-image suppression state, and thumbnail identities are reused.
- **Conservative next-page warming** — the first few images of a predictively fetched next Continuous page may be prepared at the lowest priority.

## Gallery quality and browser hot path

- **Tiny-source suppression** — genuinely thumbnail-sized originals are omitted from visual galleries and negative-cached; Raw/All Posts access remains available.
- **O(1) thumbnail element registry** — queue/completion/recovery use a generation-aware map instead of repeatedly searching the accumulated Continuous DOM.
- **Native blank validation** — visually blank generated thumbnails are rejected before caching/display and use the existing full-preview fallback.
- **Normal asynchronous paint** — healthy thumbnails no longer perform routine canvas pixel readback or forced offsetHeight repaint cycles.
- **Expanded Diagnostics** — native decoder, WIC/fallback, BODY lanes, RAM catalog, worker reuse, prewarm, DOM registry, blank rejects, and token-cache telemetry.

## Preserved

- v3.6.7 Browsing Pipeline & Long-Scroll Performance.
- v3.6.6 Adaptive Preview Connection Scaling and download priority.
- v3.6.5 Windows Taskbar Identity Reliability.
- v3.6.4 Newsgroup Package Browser & Binary Reconstruction.
- Private SAB high-throughput downloads, Smart Import, Automation, Discover/TMDB, provider behavior, and Metadata Server v0.3.3 compatibility.

## Upgrade notes

You may install v3.6.8 directly over an existing NewzDeck installation. Manual tray or background-service shutdown should not normally be required.

NewzDeck remains intentionally unsigned. Verify downloads with `NewzDeck_v3.6.8_SHA256.txt` if desired.
