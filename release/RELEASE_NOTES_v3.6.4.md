# NewzDeck v3.6.4 — Newsgroup Package Browser & Binary Reconstruction

NewzDeck v3.6.4 is a major Newsgroup browsing release built on v3.6.3. It replaces the raw, fragment-heavy All Posts experience with a package-oriented binary browser, reconstructs heavily obfuscated multipart streams before they reach the UI, adds low-bandwidth local/provider-side name recovery without indexer API usage, and makes general binaries practical to sort, filter, select, and download.

## Newsgroup browsing overhaul

- **Package-first All Posts view** — All Posts now uses a wide metadata-first Packages view while Images, Video, and Images + Video retain Gallery/List thumbnails and the media Preview pane.
- **Packages / Raw posts switch** — Packages is the normal binary-browsing experience; Raw posts remains available as an advanced fallback.
- **Connected binary packages** — multipart RAR/legacy RAR, split ZIP/7-Zip/numeric sets, PAR2 files, and matching sidecars can collapse into one package with expandable original filenames and subjects.
- **General binaries are downloadable** — complete non-image/video binaries are first-class selectable queue items, and healthy grouped releases queue under one collection identity.
- **Package health** — NewzDeck reports likely-complete sets, incomplete articles, internal archive-volume gaps, and PAR2 presence. Incomplete/non-downloadable fragments are hidden from the normal Downloadable view and remain available through All or Incomplete-only troubleshooting filters.
- **Package sorting** — Newest, Oldest, Largest, Smallest, Name A-Z, Most files, and Best health are available directly in the package browser.
- **Browse-level minimum size** — an always-visible Min size control in All Posts > Packages supports MB/GB values, including decimals. `0` disables the cutoff. Filtering uses reconstructed binary/package size rather than individual yEnc segment size.

## Multipart reconstruction and obfuscation recovery

- **Opaque yEnc reconstruction** — subjects such as `yEnc (2614/2932)` are recognized as segments of a multipart binary instead of leaking hundreds or thousands of standalone POST rows into the browser.
- **Anonymous multipart fallback** — heavily obfuscated streams can be reconstructed conservatively even when both the visible subject token and From identity change per segment, using shared yEnc totals, part counters, posting sequence, segment-size consistency, and bounded posting windows.
- **Header-only smart expansion** — All Posts can scan additional XOVER headers to assemble very large multipart binaries without downloading BODY payloads merely to browse them. Load Older skips header ranges already consumed by that reconstruction.
- **yEnc name recovery** — suspicious items can read only the beginning of an NNTP BODY response to recover the yEnc `name=` field instead of downloading a full segment just to identify it.
- **PAR2/SFV metadata recovery** — small bounded metadata files may provide protected/original filenames and stronger package-title hints.
- **Archive-header inspection** — bounded RAR4/RAR5, ZIP, and best-effort plain 7-Zip header inspection can recover meaningful internal filenames when the outer transport name remains randomized.
- **Structural package reconstruction** — randomized binaries can be connected using recovered title hints, counters, posting proximity/sequence, and conservative size patterns. Confidence is surfaced and speculative groups are not blindly treated as safe complete packages.
- **Persistent name cache** — successful resolutions are retained and applied before multipart grouping on later loads.

## Browsing reliability

- **Fresh page 1 on open** — opening or reopening a newsgroup now starts with a fresh page-1 header load instead of restoring a stale saved page/session snapshot. Useful per-group display preferences remain saved.
- **Responsive control layout** — the active-newsgroup controls are organized into stable responsive rows so wrapping does not collide with paging, summaries, or selection controls.
- **Read-state badge containment** — UNSEEN/NEW badges remain within their rows and no longer paint over sticky package controls while scrolling.
- **Provider-agnostic design** — Newsgroup deobfuscation makes no Easynews web-scraping calls and performs no Newznab/indexer reconciliation, so browsing does not consume indexer API quotas and works the same way with other NNTP providers.

## Preserved

- v3.6.3 Automation Sidebar Startup & Cache Reliability remains intact.
- v3.6.2 Tray Upgrade Lock Reliability and v3.6.1 Installer Upgrade Reliability remain intact.
- The complete v3.6.0 UI/UX Overhaul remains intact.
- Private SAB high-throughput downloads, Smart Import, Automation scoring/execution, Discover/TMDB integration, authoritative service-runtime handoff, provider behavior, and Metadata Server v0.3.3 compatibility remain preserved.

## Upgrade notes

You may install v3.6.4 directly over an existing NewzDeck installation. Manual tray or background-service shutdown should not normally be required.

NewzDeck remains intentionally unsigned, so Windows SmartScreen may show an **Unknown Publisher** warning. Verify downloads with `NewzDeck_v3.6.4_SHA256.txt` if desired.
