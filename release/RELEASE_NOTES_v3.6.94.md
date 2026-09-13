# NewzDeck v3.6.94 - Themes & Color Schemes

NewzDeck v3.6.94 adds a presentation-only theme system built on the Defender-clean v3.6.93 production baseline. No application layout, sizing, spacing, download behavior, Automation logic, updater architecture, or native-helper behavior is intentionally changed.

## Added

- Adds twelve selectable color themes: **Night, Light, Midnight, Ocean, Emerald, Amethyst, Rosewood, Sunset, Arctic, Graphite, Sandstone, and Aurora**.
- Adds **Settings > General > Theme** with immediate preview.
- Theme choice is persisted locally only after Settings is saved. Closing or cancelling Settings restores the previously saved theme.
- Restores the saved theme in the document head before render-blocking stylesheets load so light themes do not flash the Night palette at startup.
- Light, Arctic, and Sandstone use native light `color-scheme`; the remaining themes use dark `color-scheme`.

## Color-system safeguards

- **Night is the exact v3.6.93 appearance.** Existing v3.6.93 stylesheet colors are wrapped in semantic theme variables with the original literal as the fallback. The v3.6.94 regression guard reconstructs the prior stylesheet from those fallbacks and requires an exact SHA-256 match.
- Hard-coded stylesheet colors are routed through semantic background, surface, border, text, accent, status, overlay, and shadow roles so alternate themes recolor the whole application rather than only buttons or highlights.
- Alternate palettes are release-gated for readable contrast. Primary and secondary text, muted text, accent contrast, and success/warning/danger colors must meet the defined contrast floors before publication.
- The theme preference is intentionally presentation-only `localStorage` state and is not added to `/api/settings` or backend configuration.

## Preserved

- v3.6.93 Defender-clean `NewzDeckPicker.exe` folder-only scope and normal-Go-metadata build profile.
- The accepted yEnc helper source/build pipeline and pinned binary identity.
- Direct checksum-verified Setup updates and installer-owned runtime shutdown/restore.
- The corrected inert Picker-lock installed-upgrade smoke test from v3.6.93.
- Automation, Wanted, Smart Import, Discover, Newsgroup Browser, Downloads, post-processing, SABnzbd 5.1.2, Metadata Server v0.3.3, and Diagnostic Collector v1.0.31.
