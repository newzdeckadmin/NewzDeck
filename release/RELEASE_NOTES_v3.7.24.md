# NewzDeck v3.7.24 — Binary Inspection Reliability Fix

## Fixed

- Restores **Identify** for multipart yEnc NNTP articles that contain a `=ypart` control line. The bounded prefix reader previously called nonexistent `_parse_ypart()` instead of the existing `_parse_yenc_part()` helper, causing `NameError` and an HTTP error.
- The fix is exactly one functional callsite in `src/app/server.py`. No unrelated NNTP, queue, Windows service, download engine, or metadata logic is changed.
- Adds a **real-parser** offline regression: synthetic NNTP BODY responses test multipart part numbering and byte ranges, complete single-file yEnc, encoded escape bytes, partial responses, and non-success BODY statuses. Unlike the v3.7.23 mock, it runs the actual parser method.

## Preserved

- All v3.7.23 obfuscated binary Identify, safe complete-file queueing, 4 MB opt-in `.part` export, signature recognition and bounded inspection.
- Safe loose-image/video names, Complete history, filter recovery, Image Sets, cached media-library scans, silent FFmpeg, SABnzbd 5.1.2/SABCTools 9.6.3, native service and tray, Automation, settings, and user data.
- Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 remain unchanged.

## Windows acceptance

1. In All Posts select **Show: All**, **Min size: 0 MB**, then **Raw Posts**.
2. Select **Identify** for an extensionless ~775 KB yEnc article containing a multipart `=ypart` header.
3. Confirm identification returns multipart information (part number, total parts and byte range where available), not `name '_parse_ypart' is not defined`.
4. Confirm single-file articles can still be queued when safe, incomplete fragments remain non-queueable, and opt-in `.part` export stays bounded and collision-safe.
5. Retest Image Sets, Completed history and service/tray. Record new SAB transport diagnostics separately if instability persists.

This release fixes the identified parser failure; it does not claim that every obfuscated NNTP post is a complete or recoverable image. Source/offline testing does not substitute for Windows/Easynews acceptance.
