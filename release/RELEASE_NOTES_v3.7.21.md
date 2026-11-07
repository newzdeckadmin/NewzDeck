# NewzDeck v3.7.21 — Image Sets Visibility & Cover Recovery

Fixes a browsing regression exposed by the v3.7.20 date-based Image Set classifier. Recognized image sequences could disappear from both the main gallery and the Related Media pane after a failed set-cover sample.

## Fixed

- Keeps complete three-or-more-member Image Sets visible in the Related Media pane even if their cover thumbnail cannot be retrieved.
- Shows a bounded, non-spinning **Cover unavailable** placeholder instead of removing the entire set. Set identity, image count, **Open set**, and **Queue all** remain accessible.
- A failure to retrieve a *sampled set cover* no longer marks each sampled article as independently unpreviewable. Individual image preview checks still protect the gallery from confirmed broken media.
- Preserves Image Sets OFF so eligible individual images continue to appear in their normal browser view, rather than being hidden by failures in the grouped-cover path.
- Does not launch repeated failed cover probes or unbounded background work.

## Preserved

- v3.7.20 `0001_2026-06-05.png` date-sequence recognition, malformed-date safeguards, and existing filename/subject Image Set formats.
- v3.7.19 media-library disk-I/O caching, v3.7.17 restored image filenames, v3.7.16 hidden FFmpeg/FFprobe, v3.7.15 media views and multi-file queues, v3.7.14 Completed history, and v3.7.13 gallery recovery.
- All existing NNTP/SABnzbd transfer, Smart Import, Automation, user settings, Metadata Server v0.3.3, and Diagnostic Collector v1.0.31 behavior.

## Acceptance on Windows with live NNTP

1. Open the affected newsgroup in Images with Image Sets ON and at least three `0001_2026-06-05.png`-style posts from the same poster; a **2026-06-05** set should remain visible in Related Media.
2. If a cover cannot be generated, verify the set still shows **Cover unavailable**, **Open set**, and **Queue all** rather than disappearing.
3. Turn Image Sets OFF and verify the eligible items are individually visible. Check All Posts separately if they do not appear.
4. Verify the same behavior after scrolling, refresh, and switching newsgroups. Confirm that definitive failures of *individual* image previews remain suppressed.
5. Confirm bulk queueing, downloaded filenames, and v3.7.19 idle disk-I/O improvements remain unaffected.

Unit tests validate the known source regression but do not prove that a specific provider's missing articles are complete and downloadable.
