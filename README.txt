NewzDeck v3.6.87 - Dynamic Range Evidence Authority Fix

This is a targeted Automation correctness hotfix built on v3.6.86.

Highlights:
- A successful probe of the actual imported media file now overrides stale or optimistic DV/HDR claims from the original release name for dynamic-range decisions only.
- Release provenance still owns facts the container cannot prove, including WEB-DL/WEBRip source identity and release-group metadata.
- An SDR 2160p WEB-DL current file can now upgrade to Dolby Vision-only at the same base quality tier instead of being rejected as "same quality tier".
- A true Dolby Vision-only current file still upgrades to Dolby Vision + HDR fallback, while an actual DV+HDR current file remains terminal.
- The v3.6.86 one-cache-snapshot Automation and Interactive Search performance fix is preserved.
- Newsgroup Browser tuning, SABnzbd 5.1.2, Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 are unchanged.

See release/RELEASE_NOTES_v3.6.87.md for details.
