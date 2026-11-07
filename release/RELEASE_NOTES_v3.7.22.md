# NewzDeck v3.7.22 — Loose Video Filename Restoration

Fixes a Newsgroups download issue in which an individually selected video could be saved to disk as `NewzDeck Loose <12-character-token>.mkv` or `.mp4` instead of the filename shown in the browser.

## Fixed

- NewzDeck already stores the selected video's original filename with its SABnzbd job. When SAB uses the internal unique staging title as its output basename, finalization now restores the known video filename.
- Includes recognized video formats such as MKV, MP4, M4V, AVI, MOV, WMV, TS, M2TS, WEBM, MPG and MPEG.
- Applies only to one-file browser-loose jobs, only when the on-disk filename exactly matches *that job's* internal `NewzDeck Loose <token>` name, and only when the real and target extensions match.
- Uses existing numbered collision-safe names instead of overwriting any existing media, and records the final filename in NewzDeck's Completed history.
- Refuses opaque or missing target names, other staging tokens, extension changes and arbitrary archive/executable types. Never guesses a filename for unrelated downloads.

## Preserved

- The original loose-image filename restoration, SABnzbd 5.1.2, SABCTools 9.6.3, NNTP and file contents.
- v3.7.21 Image Sets visibility, v3.7.20 dated-sequence classification, v3.7.19 disk-I/O cache, v3.7.16 hidden FFmpeg windows, v3.7.15 loose-file queueing, v3.7.14 Completed history cleanup and v3.7.13 gallery recovery.
- Multi-file packages, downloaded/imported media, active and queued jobs, Automation, Metadata Server v0.3.3 and Diagnostic Collector v1.0.31.

## Windows acceptance

1. Select a loose MKV or MP4 video in a newsgroup with a descriptive filename, then download it.
2. Confirm the saved file has that filename (or a numbered collision-safe variant) and Completed shows the exact saved filename.
3. Test two separate loose videos, an already existing filename, a single loose image, and a multi-file package.
4. Verify that no unrelated files have been renamed, deleted or overwritten.

Previously downloaded files are not renamed retroactively. Source/behavioral tests are not a substitute for live Windows/NNTP testing.
