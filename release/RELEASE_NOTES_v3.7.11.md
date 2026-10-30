# NewzDeck v3.7.11 — Image Integrity & Corrupt Preview Removal

A targeted fix for blank and partially decoded image cards that could survive v3.7.10 visual-quality inspection.

## Improvements

- Detect nearly black previews with tiny decoder artifacts, noisy neutral blank images, and large gray/black/white partial-decode regions on any edge.
- Inspect decoded images at 64×64 sampling, with row/column summaries and an inexpensive early exit for normal images. Keep visual checks paced.
- Protect queued checks and pending removal when Continuous browsing advances the gallery generation but the same article remains visible.
- Validate the article identity again immediately before removing a card, so reordering cannot remove the wrong item.
- Preserve original media/download files. Only damaged preview cards are hidden from Images/Media and excluded from Image Sets within the browsing session.

## Preserved

All v3.7.10 functionality, v3.7.9 bounded fallback recovery, v3.7.8 Image Sets ON/OFF and classifier, and v3.7.7 Newsgroups pane resizing remain intact. There are no intended changes to NNTP, the native decoder, cached data formats, downloads, Automation, SABnzbd 5.1.2, SABCTools 9.6.3, Smart Import, Backup & Restore, themes, or managed updates.

The detector is conservative; subtle photographic corruption without a strong blank or decoder-fill pattern can still be impossible to determine from a thumbnail alone.
