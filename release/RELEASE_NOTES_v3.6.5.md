# NewzDeck v3.6.5 — Windows Taskbar Identity Reliability

NewzDeck v3.6.5 is a focused Windows desktop-integration release built on v3.6.4. It promotes the accepted v3.6.5-r1 taskbar identity fix so the running NewzDeck application uses NewzDeck branding in the Windows taskbar instead of inheriting the Microsoft Edge/Chrome icon from the browser-hosted application window.

## Fixed

- **Correct running-app taskbar icon** — the NewzDeck desktop launcher now assigns the hosted Chromium application window the explicit `NewzDeck.Desktop` AppUserModelID and NewzDeck relaunch/icon metadata after launch.
- **Fresh-install taskbar identity** — Windows Explorer can identify the running NewzDeck window as NewzDeck even on a computer where no prior taskbar/icon cache exists.
- **Window icon branding** — NewzDeck also applies its icon to the hosted window for taskbar/Alt-Tab/title surfaces instead of leaving the browser host's icon in place.
- **Chromium startup race protection** — the launcher reapplies the identity briefly after the window appears because Edge/Chrome can populate or replace window properties during initial application-window startup.
- **Safe browser-host isolation** — only newly created visible Edge/Chrome application windows whose title identifies them as NewzDeck are modified; unrelated browser windows are left untouched.

## Preserved

- v3.6.4 Newsgroup Package Browser & Binary Reconstruction remains unchanged, including package-first All Posts, opaque/anonymous multipart reconstruction, provider-independent name recovery, general-binary queueing, sorting, and the persistent Min size cutoff.
- v3.6.3 Automation Sidebar Startup & Cache Reliability remains preserved.
- v3.6.2 Tray Upgrade Lock Reliability and v3.6.1 Installer Upgrade Reliability remain preserved.
- The v3.6.0 UI/UX Overhaul remains preserved.
- v3.5.52 Authoritative Service Runtime Handoff remains preserved.
- Private SAB high-throughput downloads, Smart Import, Automation, Discover/TMDB, provider behavior, and Metadata Server v0.3.3 compatibility remain unchanged.

## Upgrade notes

You may install v3.6.5 directly over an existing NewzDeck installation. Manual tray or background-service shutdown should not normally be required.

NewzDeck remains intentionally unsigned, so Windows SmartScreen may show an **Unknown Publisher** warning. Verify downloads with `NewzDeck_v3.6.5_SHA256.txt` if desired.
