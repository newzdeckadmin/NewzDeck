# NewzDeck v3.6.0 — UI/UX Overhaul

NewzDeck v3.6.0 is a major application-wide interface and navigation release built on the accepted v3.5.52 production architecture. The download engine, Smart Import, Automation, Discover metadata service integration, Windows background service, tray companion, provider handling, and authoritative-runtime behavior remain on the proven v3.5.52 code path while the desktop experience receives a comprehensive visual overhaul.

## Highlights

- **Clearer application navigation** — the sidebar is organized into Browse, Library, and System sections with stronger active states and improved orientation throughout the app.
- **Higher readability** — typography, spacing, contrast, borders, status colors, focus treatment, and control sizing are standardized across NewzDeck.
- **Readable library counters** — TV, Movies, Wanted, and Downloads counters use high-contrast badges that remain clear against the dark sidebar.
- **Newsgroups mode tabs** — All newsgroups, Bookmarks, and Recent use dedicated label/count layout so text remains fully visible without overlap or truncation.
- **Discover detail polish** — title details use a deliberate full-width backdrop with a seamless transition into the information header.
- **Automation alignment** — poster-card content is organized into stable rows so titles, metadata, availability, monitoring, quality profiles, and Manage actions line up across the library.
- **Automation item settings** — Monitoring, Quality Profile, Root Folder, and Library Name use an explicit responsive grid rather than drifting or narrowing inconsistently.
- **Top utility controls** — Providers, Settings, and About now use real aligned icon-and-label content with responsive compact behavior.
- **Consistent components** — panels, dialogs, provider management, Settings, Downloads, Diagnostics, Discover, Automation, buttons, fields, and headers now share one coherent visual language.

## Preserved reliability work

v3.6.0 deliberately preserves the accepted behavior from the v3.5.x reliability cycle, including authoritative service-runtime handoff, BOM-safe provider loading, stable live Downloads cards, smooth live post-processing, Session 0-safe private SAB launching, durable Grab queueing, Smart Import finalization/cleanup, Discover performance work, and resilient tray behavior.

Metadata Server compatibility remains **v0.3.3**.

## Upgrade notes

Normal installed upgrades preserve NewzDeck data under `%LOCALAPPDATA%\NewzDeck`. You do not need to uninstall v3.5.52 first.

NewzDeck remains intentionally unsigned, so Windows SmartScreen may show an **Unknown Publisher** warning. Verify downloads with `NewzDeck_v3.6.0_SHA256.txt` if desired.

Usenet service is not included; NewzDeck requires your own NNTP provider credentials.
