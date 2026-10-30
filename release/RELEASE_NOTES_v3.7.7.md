# NewzDeck v3.7.7 - Newsgroups Splitter Cascade Hotfix

v3.7.7 fixes the v3.7.6 Newsgroups-column splitter placement and resizing bug.

## Fixed

- A later generic `.panel>*` production style was overriding the splitter's `position:absolute`, causing the handle to become a normal flex child at the bottom-right of the Newsgroups pane.
- Later production `.workspace` rules were replacing the variable-width grid track with fixed `minmax(...)` tracks, so JavaScript changed `--groups-pane-width` but the visible layout ignored it.
- The authoritative splitter and responsive grid-track rules now live at the final CSS layer, after legacy visual overrides.
- The splitter regression gate now checks CSS order, not just the presence of the intended selectors.

## Preserved

The v3.7.6 drag, keyboard resize, persistence, double-click reset, width bounds, and full-name hover behavior are unchanged. v3.7.5 Related Media grouping remains unchanged.

NNTP, thumbnails, gallery virtualization, SABnzbd 5.1.2, SABCTools 9.6.3, Direct Unpack, PAR2/repair, Automation, Smart Import, Backup & Restore, themes, and the managed update lifecycle are unchanged.

Metadata Server remains v0.3.3 and Diagnostic Collector remains v1.0.31.
