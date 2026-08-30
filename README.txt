NewzDeck v3.6.8
Image Browsing Performance & Gallery Quality
Getting Started

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application. v3.6.8 builds on v3.6.7 with
a cumulative image-browsing performance and gallery-quality pass validated
through portable acceptance revisions r1-r6.

WHAT'S NEW IN v3.6.8

- Long Continuous sessions use bounded gallery scanning, RAM-aware caches, and separate NNTP/decode budgets.
- Deep page jumps reset stale scroll/prefetch state and prioritize the destination page.
- WIC-first persistent native thumbnail workers reduce process startup and large-image decode cost.
- Very large visible multipart images can borrow a small number of coordinated BODY lanes.
- Recent header pages and persistent thumbnail/suppression state are reused from RAM.
- Genuinely tiny source images are suppressed from visual gallery/media results.
- Chromium hot-path work uses constant-time thumbnail lookup, native blank validation, geometry snapshots, and normal asynchronous painting.

NewzDeck remains intentionally unsigned. Verify downloads with NewzDeck_v3.6.8_SHA256.txt if desired.
