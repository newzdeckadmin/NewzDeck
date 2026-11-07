# NewzDeck v3.7.20 — Image Sets Date-Based Sequence Detection

Adds reliable Image Sets grouping for filenames with a **leading image counter** followed by a shared date label, without weakening the existing protections against unrelated files being grouped together.

## Fixed

- `0001_2026-06-05.png`, `0002_2026-06-05.png`, `0003_2026-06-05.png`, etc. now receive the same Image Sets group identity (`2026-06-05`) and their correct sequence indexes.
- Also understands numbered date labels such as `001-2026-06-05.jpg`, `0004_2026.06.05.webp`, and `0005_2026_06_05.jpeg`, with a valid date and a leading sequence counter.
- The date-stamped pattern is considered **before** legacy trailing number matching; the day (`05`) is no longer mistaken for the image's sequence number.
- A bare date such as `2026-06-05.png`, an impossible date (for example `2026-02-30`), and a four-digit year masquerading as a sequence counter do not accidentally create an Image Set. A genuinely explicit subject index/total may still establish a set.

## Preserved

- Existing filename counters (leading and trailing), image `N of M` patterns, subject-provided album/index/total metadata and all Image Sets ON/OFF controls.
- At least **three recognized items** are required for the grouped Image Sets UI; different posters, newsgroups, or media kinds remain separate.
- The published v3.7.19 media scan disk-I/O optimization, v3.7.18 Windows CI recovery, v3.7.17 original image filename restoration, v3.7.16 hidden FFmpeg/FFprobe, v3.7.15 media views and bulk queue, v3.7.14 Completed history and v3.7.13 preview/image fixes.
- NNTP, SABnzbd 5.1.2, SABCTools 9.6.3, Direct Unpack/PAR2, Smart Import, Metadata Server v0.3.3, Diagnostic Collector v1.0.31 and persisted user settings are unchanged.

## Windows acceptance

1. Browse a newsgroup containing three or more consecutive images named `0001_2026-06-05.png`, `0002_2026-06-05.png`, etc. from the same poster, with Image Sets ON. Expect one dated set.
2. Open the set and confirm individual images appear in the correct order and can be viewed and downloaded.
3. Turn Image Sets OFF and verify individual items appear normally; test a different date, another poster, and another group.
4. Verify established `Vacation_001.jpg` / `[01/25]` groups, ordinary Videos views and Downloads behavior are unchanged.

Source/behavioral tests alone cannot confirm real newsgroup metadata and NNTP runtime behavior.
