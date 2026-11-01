# NewzDeck v3.7.16 — Silent Windows Video Thumbnail Helpers

Fixes repeated terminal/console windows appearing while browsing a newsgroup in the **Videos** view.

## Fixed

- FFmpeg frame extraction for reconstructed newsgroup video samples and cached full previews now uses `CREATE_NO_WINDOW` on Windows. The same 15-second timeout, frame extraction arguments, caching, and browser-fallback paths are retained.
- FFprobe video metadata reads use the same hidden Windows process creation policy, keeping their 12-second timeout and JSON parsing unchanged.
- Non-Windows platforms continue to pass zero creation flags.

## Preserved

All v3.7.15 Images/Video/Images + Video smart reconstruction, multi-selection, individual SABnzbd jobs and package handling. All v3.7.14 Completed Remove All history safeguards, v3.7.13 image preview recovery and image integrity rules, native thumbnail helpers, video preview concurrency, NNTP, SABnzbd 5.1.2, SABCTools 9.6.3, Direct Unpack/PAR2, Automation, Metadata Server v0.3.3 and Diagnostic Collector v1.0.31.

## Windows acceptance

1. Open a newsgroup containing numerous videos in Videos and Images + Video.
2. Scroll as thumbnails load or switch pages. No terminal windows should open, and preview tiles should continue loading normally.
3. Test a cached video, an uncached video, a video requiring browser fallback, and the full-video viewer.
4. Confirm All Posts multi-selection and queueing of separate loose files still work.

The source/behavioral tests are not a substitute for a live Windows/NNTP verification.
