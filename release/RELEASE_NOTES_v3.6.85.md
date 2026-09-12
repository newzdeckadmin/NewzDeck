# NewzDeck v3.6.85 - Wanted & Interactive Search Trait Coherency Fix

v3.6.85 is a narrow Automation correctness release built on the published v3.6.84 baseline. It fixes the remaining disagreement exposed when Wanted requested a Dolby Vision -> Dolby Vision + HDR fallback upgrade while Interactive Search rejected an actual DV+HDR candidate as `same quality tier`.

## Root cause

NewzDeck had two paths for describing the traits of an existing library file. Interactive Search and automatic release evaluation used `_current_target_release_info()`, which prefers persisted `release_traits`, then a fingerprint-bound cached original release title, and only then conservative `media_info`. Wanted, Library cutoff decoration and Calendar bypassed that resolver and passed `release_traits or media_info` directly.

That distinction matters because best-effort media probing can omit HDR fallback metadata that is still known from the original release. The same file could therefore be interpreted as Dolby Vision-only by Wanted but as Dolby Vision + HDR fallback by Interactive Search.

## One canonical current-file trait resolver

v3.6.85 centralizes the existing evidence precedence in `_record_release_info()` and routes all relevant surfaces through it:

- stored `release_traits`;
- fingerprint-bound cached original `release_title`;
- conservative `media_info`;
- stored base quality as the final fallback.

`_current_target_release_info()` now delegates to that same helper instead of implementing a separate copy of the logic. Wanted, live Library cutoff decoration and Calendar also use it.

## Result

- If an existing file is already **Dolby Vision + HDR fallback**, it satisfies that preferred terminal dynamic-range state everywhere and does not remain in Wanted merely because media probing omitted the HDR fallback flag.
- If an existing file is genuinely **Dolby Vision-only**, Wanted still requests **Dolby Vision + HDR fallback**, and a DV+HDR candidate at the same 2160p WEB-DL tier is accepted as `dynamic range improves`.
- The v3.6.84 1080p Balanced correction remains: Allow-only HDR/Dolby Vision states do not create false upgrade requirements.
- Generic WEB -> explicit WEB-DL and true base-quality upgrades keep their existing semantics.

## Preserved behavior

- v3.6.84 Wanted reason/cutoff-policy fix and 4K preferred dynamic-range progression
- v3.6.83 installed/runtime/UI update-version coherency and same-version update protection
- Newsgroup Browser accepted architecture/tuning
- SABnzbd 5.1.2 integration, download queue, post-processing and Smart Import
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- Defender-clean yEnc source/build/hash identity
- guarded source commit -> annotated immutable tag -> separate trigger commit publication topology
