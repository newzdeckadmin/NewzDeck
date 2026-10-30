# NewzDeck v3.7.10 — Broken Image Suppression

v3.7.10 improves removal of unusable images from the Newsgroups gallery and Image Sets.

## Fixed

- **Blank image cards:** the browser now validates decoded image pixels on a paced queue instead of assuming that an `img` load event means the pixels are usable.
- **Strong partial-decode artifacts:** full-size neutral decoder-fill regions at the lower or right edge, with detailed image content elsewhere, are treated as evidence of a broken image. Ordinary colored designs and letterbox borders are excluded.
- **Cached and recovered images:** the same check applies to cached thumbnails and to v3.7.9 full-image preview fallbacks.
- **Gallery removal:** a confirmed unusable preview follows the existing unavailable-media path, removes the card in Images/Media modes, clears the thumbnail/full-image caches, invalidates the thumbnail token, and excludes the member from Image Sets for the current browsing session.
- **Repeated decode failures:** a full-image browser recovery that fails now follows the existing thumbnail-error suppression path rather than leaving a permanent Retry card.
- **Responsive browsing:** visual checks are paced one at a time, reducing the risk of main-thread stalls during heavy gallery loading.

## Preserved

- v3.7.9 bounded thumbnail fallback, queue concurrency and Image Sets indexing optimization.
- v3.7.8 Image Sets detection and ON/OFF controls.
- v3.7.7 Newsgroups splitter, all 12 color themes and existing browser layout.
- NNTP, download engine, native thumbnail decoder, SABnzbd 5.1.2, SABCTools 9.6.3, PAR2, Automation, Smart Import, Backup & Restore, and managed About & Updates lifecycle.

Conservative browser-pixel screening cannot prove that every superficially decodable but damaged photograph is corrupt; it removes unmistakably blank or partially filled renders without treating every low-detail photograph as a failure. Raw All Posts remains available.
