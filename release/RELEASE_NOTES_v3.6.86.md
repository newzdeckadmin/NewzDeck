# NewzDeck v3.6.86 - Automation Cache Snapshot Performance Hotfix

v3.6.86 is a targeted performance hotfix built on the published v3.6.85 baseline. It keeps the v3.6.85 DV/DV+HDR correctness fix and removes the repeated disk I/O that made Automation and Interactive Search much slower on real libraries.

## Root cause

v3.6.85 centralized current-file trait resolution in `_record_release_info()`. That was the correct decision model, but the helper called `_media_quality_cache()` whenever a file had a fingerprint and the caller did not supply already-resolved traits.

`_media_quality_cache()` reads and parses `media-quality-cache.json`. Library cutoff decoration, Wanted, Calendar, Interactive Search candidate scoring, and automatic safety checks can call the current-file resolver many times in one logical operation. On a library with many imported episodes or a search returning many candidates, v3.6.85 therefore reread and reparsed the same JSON file repeatedly.

The result matched the production symptoms: Automation eventually loaded but took substantially longer than normal, and **Search releases** could remain on the searching/evaluating screen while candidate-count-dependent cache reads accumulated.

## One snapshot per logical operation

v3.6.86 keeps the v3.6.85 evidence precedence unchanged but lets the canonical resolver consume a caller-owned, read-only quality-cache snapshot.

- The Automation `summary()` response reads `media-quality-cache.json` once and shares that same snapshot with live Library cutoff decoration, Wanted, and Calendar.
- `wanted()`, `calendar()`, and live cutoff decoration still work independently; when called outside the summary response they each take one snapshot for the whole pass rather than one per file record.
- Interactive Search resolves the current library file once before candidate scoring. Every release candidate and automatic-eligibility check reuses that same current-file trait dictionary.
- Automatic feed matching and the scheduler's post-search safety pass similarly resolve one current-file trait view per upgrade target rather than per candidate.

This also makes each response internally coherent: every record/candidate in one operation is evaluated against the same quality-cache snapshot even if another NewzDeck process updates the persisted cache concurrently.

## Preserved correctness

- A true **Dolby Vision-only** current 2160p WEB-DL remains upgradeable to **Dolby Vision + HDR fallback**.
- A DV+HDR candidate is still accepted as `dynamic range improves` against a true DV-only current file.
- A file already proven to contain DV+HDR fallback remains terminal and does not stay falsely Wanted.
- 1080p Balanced Allow-only HDR/Dolby Vision policies remain acceptable rather than mandatory targets.
- Generic WEB -> explicit WEB-DL and true base-quality upgrades retain their existing semantics.

## Preserved behavior

- v3.6.85 canonical current-file trait precedence and Wanted/Interactive Search coherency
- v3.6.84 Wanted reason/cutoff-policy fix and 4K preferred dynamic-range progression
- v3.6.83 installed/runtime/UI update-version coherency and same-version update protection
- Newsgroup Browser accepted architecture/tuning
- SABnzbd 5.1.2 integration, download queue, post-processing and Smart Import
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- Defender-clean yEnc source/build/hash identity
- guarded source commit -> annotated immutable tag -> separate trigger commit publication topology
