# NewzDeck v3.7.31 — High-Performance Video Discovery & Browsing

## Changes

- **Faster first paint in Videos:** the existing 300-position (or user-configured) header page displays immediately, then a bounded background header-only discovery scans older NNTP positions to find up to 18 complete recognized videos. The scan is limited to the lesser of eight logical pages or 3,600 positions, and it stops at the provider's retained low water mark. This avoids making the initial gallery wait for the deeper scan.
- **More video formats:** subject recognition and recovered yEnc filenames now recognize MPG, MPEG, WMV, TS, M2TS, MTS, FLV, 3GP and VOB, in addition to existing MP4/M4V/MOV/AVI/MKV/WebM. Recognizing a filename is not verification of a valid playable file.
- **Multipart across scan windows:** group the complete bounded header collection together rather than classifying each small page independently. Named multipart groups with different declared part totals are kept separate so an unrelated upload using the same filename cannot make a valid video appear incomplete.
- **Thumbnail failures no longer hide video cards:** failed video frame extraction leaves a visible placeholder and preserves the video's download selection. Image preview suppression remains unchanged; incomplete multipart videos still cannot be downloaded.
- **Videos-only lightweight search:** Videos mode no longer requests All Posts' expensive deep opaque-binary expansion. All Posts, Images and Images + Video retain their existing scan behavior.
- **Progress and lifecycle:** show that older headers are being scanned, account for only fully covered logical pages (no skipped partially-overlapped page), merge asynchronous completion on continuously appended pages, and prevent older worker generations from overwriting a newer forced refresh.

## Preserved

- The existing SABnzbd 5.1.3 managed engine, SABCTools 9.6.3, provider reservations, queue, completed history, transfer speeds, NNTP lane controls and background Windows service/tray.
- v3.7.29 monitored metadata refresh and Wanted protections, v3.7.27 live download pulse, v3.7.26 Entire Group Search, prior Image Sets, filename restoration, and conservative obfuscated binary inspection.
- No persistent header index, background search-history database, new cloud service or changes to user data. Metadata Server 0.3.3 and Diagnostic Collector 1.0.31 unchanged.

## Known limits / Windows acceptance

- The adaptive scan is **bounded**. It does not promise to discover every video in an entire huge newsgroup; users can continue into older pages. Unknown or heavily obfuscated filenames still need existing on-demand identification and may not appear in Videos until resolved.
- The scanner retrieves headers, not video bodies. Decoding video thumbnails remains an independent operation that may be slow for large files or unreliable streams; failed thumbnails are shown as placeholders rather than deleting results.
- Offline simulated NNTP and JavaScript regressions do **not** prove throughput on a user's provider, Windows decoder compatibility, or a successfully published installer. Live testing with mixed-format newsgroups, multipart boundaries, busy downloads and provider errors remains an acceptance step.
- Official Windows Setup and Portable binaries are built **only** by the repository's canonical `publish-release-trigger.yml` Actions workflow, following separate explicit publication authorization. This package is not a locally built Windows executable and does not publish automatically.

## Regression tests

- `python release/windows/validate-v3731-video-discovery.py`
- `node release/windows/validate-v3731-video-ui.js`
- `python release/windows/validate-v3731-sab-preservation.py`
- `python release/windows/validate-v3729-metadata-refresh.py`
- Existing named Image Sets, live search, Downloads, yEnc, filename, image integrity and Windows console-suppression tests remain part of the guarded release validation.
