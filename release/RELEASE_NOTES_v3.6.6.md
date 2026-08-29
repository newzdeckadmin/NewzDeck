# NewzDeck v3.6.6 — Adaptive Preview Connection Scaling

NewzDeck v3.6.6 is a focused browsing-performance release built on v3.6.5. It promotes the accepted v3.6.6-r1 adaptive preview scheduler so image-heavy newsgroups can use substantially more of a high-connection NNTP account while the app is idle, without sacrificing download throughput when real transfers begin.

## Faster image browsing

- **Adaptive connection ramping** — gallery browsing starts at the proven v3.6.5 preview concurrency, then increases in bounded steps only while enough thumbnail work is queued and measured throughput remains healthy.
- **Higher preview ceiling** — the backend preview worker pool increases from 24 to 80 workers.
- **Connection budget awareness** — roughly 12% of configured provider connections remain reserved for headers, name resolution, and interaction. A 55-connection provider can ramp from 16 toward 48 concurrent preview requests.
- **Throughput/error feedback** — NewzDeck measures completed-thumbnail rate and failure rate, holding or stepping concurrency back down when additional parallelism stops helping.
- **Download priority remains intact** — as soon as an active download, retry, or cancellation transfer appears, preview scheduling immediately returns to the small download-reserve budget.
- **Fast idle socket release** — warm preview NNTP sessions close about three seconds after a browsing burst becomes idle so the download engine can reclaim provider connection slots quickly.
- **Scaled media helpers** — automatic video-thumbnail concurrency can reach 4 and grouped-set cover work can reach 6 when the overall preview budget supports it.

## Preserved

- v3.6.5 Windows Taskbar Identity Reliability remains intact.
- v3.6.4 Newsgroup Package Browser & Binary Reconstruction remains intact, including package-first All Posts, multipart reconstruction, deobfuscation, sorting, queueing, and the persistent Min size cutoff.
- v3.6.3 Automation Sidebar Startup & Cache Reliability, v3.6.2 Tray Upgrade Lock Reliability, v3.6.1 Installer Upgrade Reliability, the v3.6.0 UI/UX Overhaul, and v3.5.52 Authoritative Service Runtime Handoff remain preserved.
- Private SAB high-throughput downloads, Smart Import, Automation, Discover/TMDB, provider behavior, and Metadata Server v0.3.3 compatibility remain unchanged.

## Upgrade notes

You may install v3.6.6 directly over an existing NewzDeck installation. Manual tray or background-service shutdown should not normally be required.

NewzDeck remains intentionally unsigned, so Windows SmartScreen may show an **Unknown Publisher** warning. Verify downloads with `NewzDeck_v3.6.6_SHA256.txt` if desired.
