NewzDeck v3.6.84 - Wanted Upgrade Reasoning & Cutoff Policy Fix

This is a targeted Automation correctness release built on the verified v3.6.83 production baseline.

Highlights:
- Wanted now distinguishes a true base-quality cutoff miss from a WEB -> WEB-DL source upgrade or a preferred dynamic-range upgrade.
- Allow-only HDR/Dolby Vision policy values no longer act like mandatory terminal targets.
- 1080p Balanced 1080p WEB-DL SDR files correctly satisfy cutoff instead of flooding Quality Upgrades.
- 4K Preferred keeps its explicit SDR -> HDR -> Dolby Vision -> Dolby Vision + HDR fallback progression, but Wanted now explains that progression accurately.
- Live Library/Calendar cutoff flags are recalculated from the active profile so stale pre-v3.6.84 booleans do not keep old false upgrade states visible.
- v3.6.83 update-version coherency, frozen browsing/download behavior, SABnzbd 5.1.2, Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 are unchanged.

See release/RELEASE_NOTES_v3.6.84.md for details.
