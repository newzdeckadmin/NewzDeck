NewzDeck v3.6.86 - Automation Cache Snapshot Performance Hotfix

This is a targeted performance hotfix built on v3.6.85.

What changed:
- Automation no longer rereads and reparses media-quality-cache.json for every existing episode/movie while building the Library, Wanted, and Calendar response.
- One cache snapshot is shared across the complete Automation summary request, restoring normal Library/TV/Movies/Wanted load behavior for larger libraries.
- Interactive Search resolves the current library file traits once and reuses them for every candidate, eliminating the v3.6.85 Search Releases slowdown/stall.
- Automatic feed and scheduler upgrade evaluation use the same per-target snapshot so unattended searches do not repeat cache I/O per candidate.
- v3.6.85's canonical DV/DV+HDR trait-coherency fix remains intact.

Frozen Newsgroup Browser tuning, SABnzbd 5.1.2, Smart Import/post-processing, Metadata Server v0.3.3, Diagnostic Collector v1.0.31 and Defender-clean yEnc behavior are unchanged.

See release/RELEASE_NOTES_v3.6.86.md for details.
