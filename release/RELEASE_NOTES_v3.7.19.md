# NewzDeck v3.7.19 — Media Library Scan & Disk I/O Optimization

Reduces repeated file reads during Automation library reconciliation when NewzDeck is not downloading.

## Changes
- Adds `media-scan-cache.json`, a **rebuildable** cache containing only the media path, file identity/signature, fingerprint, quality and codec/HDR metadata (never video content).
- On subsequent scans, unchanged files reuse the known metadata without reopening or hashing the video file.
- Cache entries are invalidated when file path, size, nanosecond modification time, volume/file identity changes. A missing or corrupted cache is safely rebuilt.
- TV and movie library scans analyze codec/HDR metadata **once per changed file** instead of twice and share an existing resolution probe with quality analysis.
- Cache writes occur only when new/changed analysis exists, with an upper bound on stored records.
- Filesystem enumeration remains intact so new/moved/missing episodes are detected, and the original quality/cutoff/Smart Import behavior is retained.
- The initial cache-warming scan can still perform meaningful disk reads. This update targets unnecessary *repeat* I/O, not legitimate first-time video analysis.

## Preserved
The published v3.7.18 Windows CI path-identity recovery, v3.7.17 original Image Set filename restoration, v3.7.16 silent FFmpeg/FFprobe helpers, v3.7.15 media filter/bulk queue fixes, v3.7.14 Completed Remove All and v3.7.13 gallery recovery. NNTP, SABnzbd 5.1.2, SABCTools 9.6.3, Direct Unpack/PAR2, Smart Import, Metadata Server v0.3.3, Diagnostic Collector v1.0.31 and user settings remain unchanged.

## Windows acceptance checks
1. After updating, allow one Automation library scan to finish, then observe disk reads from `python.exe` on a **second** scan without media changes.
2. Confirm existing TV/movie quality, episode matching and Smart Import are unchanged.
3. Add, remove or replace a video (including same-size replacement with a changed modification time) and verify library reconciliation reflects it.
4. Verify Video thumbnails, newsgroup filtering, downloads and background service continue normally.
5. For residual continuous disk load, inspect Resource Monitor and Diagnostics to distinguish another process or background operation.

CI tests verify code paths and synthetic file-change behavior, not real-world large-library throughput on the user's Windows host.
