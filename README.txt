NewzDeck v3.6.85 - Wanted & Interactive Search Trait Coherency Fix

This is a narrow Automation correctness release built on v3.6.84.

What changed:
- Wanted, Library/Calendar cutoff state, Interactive Search and automatic upgrade evaluation now use one canonical view of the traits already present in the current library file.
- Stored release traits remain authoritative; otherwise NewzDeck uses the fingerprint-bound original release title before falling back to conservative media probing.
- A current DV+HDR file can no longer appear in Wanted just because media probing reported only Dolby Vision while Interactive Search simultaneously rejects DV+HDR candidates as same-tier.
- A genuinely Dolby Vision-only current file still requests Dolby Vision + HDR fallback, and matching DV+HDR candidates are accepted as dynamic-range improvements.
- v3.6.84's 1080p Balanced Allow semantics and accurate Wanted reason labels remain intact.

Frozen Newsgroup Browser tuning, SABnzbd 5.1.2, Smart Import/post-processing, Metadata Server v0.3.3, Diagnostic Collector v1.0.31 and Defender-clean yEnc behavior are unchanged.

See release/RELEASE_NOTES_v3.6.85.md for details.
