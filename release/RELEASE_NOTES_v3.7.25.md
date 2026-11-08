# NewzDeck v3.7.25 — Image Sets UI Refinement

## Fixed

- In **Newsgroups > Images**, **Videos**, and **Images + Video**, turning **Image Sets OFF** now removes the entire **Grouped Sets / Related Media** side panel rather than leaving an unused third column.
- The main gallery/list expands into the free space using NewzDeck's existing full-width browser layout.
- Turning **Image Sets ON** restores the original Related Media panel without needing to restart or reload the app.
- **All Posts** retains its existing two-column layout independent of Image Sets, and its package/raw-post controls remain unchanged.
- The hidden panel is marked `aria-hidden` for accessibility, and any transient preview-pane `open` state is cleared when the panel is hidden.

## Preserved

- Existing Image Sets grouping, date-based sequences, set covers, lazy thumbnails, and original image/video browsing behavior.
- Persistent Image Sets setting and all user preferences.
- v3.7.24 yEnc multipart inspection reliability and v3.7.23 unknown-binary discovery/recovery.
- Download management, private SABnzbd 5.1.2, SABCTools 9.6.3, Windows service and tray, Automation, Smart Import, settings and media library data.
- Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 unchanged.

## Verification

- Source tests exercise all eight combinations of media tab and Image Sets state, plus an OFF → ON → OFF toggle sequence against the actual `updateBrowseModeControls()` function.
- Existing release regression gates remain enabled, including gallery, Image Sets date classification, failed-cover visibility, filename restoration and yEnc parsing.

## Windows acceptance

1. Open a newsgroup and set filter to Images or Videos. Set **Image Sets OFF** and verify the entire side panel disappears, while the main results pane expands.
2. Turn **Image Sets ON** and confirm Related Media returns.
3. Change to Images + Video, then back to Images; confirm the correct layout in both states.
4. Switch to All Posts, confirming its full-width layout and package/raw-post controls.
5. Restart NewzDeck and confirm the saved Image Sets setting and pane layout are restored.
6. Confirm gallery previews, thumbnails and downloads still function.

No user-data or schema migration is required. This is a focused UI change; Windows visual acceptance remains necessary.
