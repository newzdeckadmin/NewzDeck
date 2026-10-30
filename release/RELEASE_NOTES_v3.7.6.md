# NewzDeck v3.7.6 - Resizable Newsgroups Pane

v3.7.6 is a focused Newsgroups usability release built on the stable v3.7.5 runtime.

## New

- **Resizable Newsgroups column:** drag the divider between Newsgroups and Articles to make the newsgroup-name column wider or narrower.
- **Persistent width:** NewzDeck remembers the chosen width locally and restores it on later launches.
- **Responsive bounds:** the splitter automatically respects the space needed by Articles and Related Media instead of allowing the list to crush the rest of the browser.
- **Keyboard accessible:** focus the divider and use Left/Right Arrow to resize; hold Shift for larger steps.
- **Quick reset:** double-click the divider to restore the default width.
- **Full-name hover:** truncated newsgroup names expose the complete name in a tooltip.

## Preserved

- Newsgroup loading, searching, sorting, bookmarks, Recent history, tabs, and selection behavior are unchanged.
- v3.7.5 Related Media grouping and its regression tests remain intact.
- NNTP connections, thumbnail scheduling, gallery virtualization, SABnzbd 5.1.2, SABCTools 9.6.3, Direct Unpack, PAR2/repair, Automation, Smart Import, Backup & Restore, themes, and the managed updater are unchanged.
- Metadata Server remains v0.3.3 and Diagnostic Collector remains v1.0.31.

The saved width is presentation-only local UI state and does not modify provider or application configuration.
