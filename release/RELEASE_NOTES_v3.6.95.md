# NewzDeck v3.6.95 - Light Theme Readability Hotfix

NewzDeck v3.6.95 is a presentation-only follow-up to v3.6.94. It fixes the three light palettes without changing application layout, behavior, backend settings, Automation, downloading, updater ownership, or native helper behavior.

## Fixed

- **Light, Arctic, and Sandstone controls are readable throughout the app.** Search fields, selectors, toolbars, tabs, cards, panels, and other UI surfaces that inherited the old Night-style overlay role now derive from each light theme's coordinated light surfaces.
- **True overlays stay intentionally dark.** Modal backdrops, the fullscreen media viewer, image/poster badges, media action buttons, play overlays, and poster gradients use a separate dark scrim role with high-contrast foreground colors.
- Placeholder text in the three light themes now follows the readable muted-text role.

## Preserved

- Night, Midnight, Ocean, Emerald, Amethyst, Rosewood, Sunset, Graphite, and Aurora palettes are unchanged from v3.6.94.
- Night still reconstructs the exact v3.6.93 production stylesheet colors.
- The 12-theme Settings selector, immediate preview, Save/Cancel behavior, local-only persistence, and pre-paint restore remain unchanged.
- No layout, font, sizing, spacing, Automation, Wanted, Smart Import, Discover, Newsgroup Browser, Downloads, post-processing, or SABnzbd behavior changes are included.
- The Defender-clean folder-only Picker, accepted yEnc helper, direct checksum-verified Setup updater, installer-owned runtime handoff, Metadata Server v0.3.3, and Diagnostic Collector v1.0.31 are preserved.

## Release-gate additions

- The nine dark theme palette blocks are frozen to their v3.6.94 identities.
- Light, Arctic, and Sandstone must use light surface semantics for generic overlay-derived UI and separate scrim semantics for true overlays.
- Light-theme text/control and scrim contrast is validated before publication.
