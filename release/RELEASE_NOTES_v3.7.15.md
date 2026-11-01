# NewzDeck v3.7.15 — Newsgroup Media Filters & Bulk Queue Reliability

This targeted update addresses two reported Newsgroups problems while preserving the v3.7.14 Completed-history cleanup and v3.7.13 preview-recovery behavior.

## Fixed

- **Images / Video / Images + Video completeness:** use the same smart multipart reconstruction for the same loaded header pages as All Posts instead of the shallower basic scan. Enable bounded yEnc filename-resolution probes in media views, so valid recovered `.jpg`, `.png`, `.mp4`, etc. classify in their corresponding filters.
- **All Posts multi-selection:** ordinary clicks toggle/add selections instead of silently replacing the selected set. Shift-click extends the range, Ctrl-click still toggles.
- **Add selected to queue:** separate loose files are submitted as individual SABnzbd queue jobs, rather than combining unrelated files into one NZB. True explicit browser-set collections still submit as packages for correct PAR2/post-processing.
- **Large and partial batches:** loose files submit in bounded 12-file requests; the UI reports partial failures and keeps unconfirmed items selected for deliberate retry.

## Preserved

The v3.7.13 image integrity and permanent preview suppression rules remain intact: proven broken/undecodable previews remain hidden, not reintroduced as gallery cards. The v3.7.14 history-only Remove all completed feature remains unchanged. No changes to Metadata Server v0.3.3, Diagnostic Collector v1.0.31, native thumbnail decoder, NNTP provider configuration, SABnzbd 5.1.2, SABCTools 9.6.3, Direct Unpack/PAR2, Smart Import, Automation, themes, or managed updates.

## Acceptance on Windows

1. In one newsgroup, compare the same loaded page in All Posts and all three media filters, including multipart and recovered-name examples.
2. In All Posts, click multiple different loose files, verify the selected count, then Add selected to queue. Verify separate queue cards and files.
3. Select a genuine package and verify it stays grouped, and confirm queued downloads still survive application restart.
4. Reconfirm Completed Remove All deletes only history and does not delete any downloaded media.

The canonical Windows publishing workflow builds the installer/Portable ZIP after guarded GitHub publication. Local/source tests are not a substitute for live NNTP and Windows acceptance tests.
