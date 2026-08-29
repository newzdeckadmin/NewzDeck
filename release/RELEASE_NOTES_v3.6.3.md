# NewzDeck v3.6.3 — Automation Sidebar Startup & Cache Reliability

NewzDeck v3.6.3 is a focused startup and UI reliability release built on v3.6.2. It promotes the accepted Automation sidebar startup fix, restores Automation editor actions that were preventing the browser initializer from completing, and adds a dedicated full-preview cache control. The accepted v3.6.0 UI/UX Overhaul and the v3.6.1/v3.6.2 installed-upgrade reliability fixes remain intact.

## Fixed

- **Automation navigation counts populate at startup** — TV, Movies, and Wanted sidebar badges no longer wait for the user to open an Automation page before showing the current library state.
- **Lightweight sidebar count path** — navigation badges use a small Automation count endpoint that is independent of the full Automation summary and provider/newsgroup startup.
- **Startup count race protection** — a transient empty Automation snapshot cannot erase valid positive sidebar counts while startup is settling.
- **Automation browser initialization restored** — missing Quality Profile and Newznab Indexer editor handlers could throw a top-level JavaScript `ReferenceError` before `initializeApp()` ran. The complete editor wiring is restored.
- **Sidebar placeholder state corrected** — zero placeholders stay hidden until real Automation count data is available.

## Added

- **Clear Preview Cache** — Settings → Storage & Cache now has a dedicated action for clearing full-preview cache files and browser preview memory without clearing thumbnails.
- **Thumbnail cache memory reset** — clearing the thumbnail cache now also clears the browser's in-memory thumbnail caches/promises so the action is immediately reflected in the current session.

## Preserved

- v3.6.2 process-authoritative `NewzDeckTray.exe` shutdown during installed upgrades remains unchanged.
- v3.6.1 confirmed background-service shutdown before replacing `NewzDeckService.exe` remains unchanged.
- The complete v3.6.0 UI/UX Overhaul remains intact.
- Private SAB high-throughput downloads, Smart Import, Automation scoring/execution, Discover/TMDB integration, authoritative service-runtime handoff, provider behavior, and Metadata Server v0.3.3 compatibility remain unchanged.

## Upgrade notes

You may install v3.6.3 directly over an existing NewzDeck installation. The v3.6.1 and v3.6.2 installer shutdown protections are preserved, so manual tray or service shutdown should not be required.

NewzDeck remains intentionally unsigned, so Windows SmartScreen may show an **Unknown Publisher** warning. Verify downloads with `NewzDeck_v3.6.3_SHA256.txt` if desired.
