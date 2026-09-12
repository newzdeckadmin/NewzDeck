# NewzDeck v3.6.87 - Dynamic Range Evidence Authority Fix

v3.6.87 is a narrow Automation correctness hotfix built on the published v3.6.86 baseline. It fixes the remaining same-tier upgrade rejection exposed when an existing 2160p WEB-DL file is actually SDR/non-Dolby-Vision, but release-name provenance made NewzDeck believe the current file already contained Dolby Vision.

## Production symptom

Wanted could correctly show that a 2160p WEB-DL still had a preferred dynamic-range upgrade path, yet Interactive Search could reject a real Dolby Vision candidate at the same 2160p WEB-DL tier with:

`Not an upgrade over current quality 2160p WEB-DL (same quality tier)`

That is wrong when the media file currently on disk does not actually contain Dolby Vision.

## Root cause

v3.6.85 centralized current-file trait resolution and v3.6.86 made that resolver efficient by sharing one quality-cache snapshot per logical operation. The evidence order, however, still treated the stored/original release name as authoritative for every trait.

A release name can claim `DV`, `HDR`, or both even when the imported media file does not actually contain those signals. Because the provenance record was returned before `media_info`, a stale or optimistic release title could make an SDR file rank as Dolby Vision. A DV-only candidate would then compare as DV -> DV and be rejected as the same tier.

## Provenance and intrinsic media evidence are now separated

v3.6.87 keeps release provenance for facts that the container cannot reliably prove, including source identity such as WEB-DL vs WEBRip and release-group information.

For dynamic-range state, a **successful current-file media probe** is authoritative:

- `dolby_vision`
- `hdr10_plus`
- `hdr_present`

The media probe writes those boolean keys only after it successfully reads the file. Their presence therefore distinguishes a real probe result from an inaccessible/failed probe. A `False` value is meaningful and can correct a stale release-name claim.

## Result

For a 4K Preferred profile at the same 2160p WEB-DL base tier:

- actual SDR current file -> Dolby Vision candidate: **upgrade accepted**
- actual SDR current file -> Dolby Vision + HDR fallback candidate: **upgrade accepted**
- actual HDR current file -> Dolby Vision candidate: **upgrade accepted**
- actual Dolby Vision current file -> Dolby Vision candidate: **not an upgrade**
- actual Dolby Vision current file -> Dolby Vision + HDR fallback candidate: **upgrade accepted**
- actual Dolby Vision + HDR fallback current file -> lower/equal dynamic-range candidate: **not an upgrade**

The original release title can still supply WEB-DL/WEBRip/source and release-group provenance; only intrinsic dynamic-range truth is corrected by a successful media probe.

## Performance fix preserved

v3.6.87 does not undo v3.6.86. Automation summary, Wanted, Calendar, Health and Interactive Search continue to reuse one media-quality-cache snapshot/current-file trait view per logical operation. No per-record or per-candidate quality-cache reread has been reintroduced.

## Preserved behavior

- v3.6.86 Automation/Interactive Search cache-snapshot performance hotfix
- v3.6.85 canonical current-file trait resolver architecture
- v3.6.84 cutoff reason/policy correction and 4K preferred progression
- v3.6.83 installed/runtime/UI update-version coherency and same-version update protection
- Newsgroup Browser accepted architecture/tuning
- SABnzbd 5.1.2 integration, download queue, post-processing and Smart Import
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- Defender-clean yEnc source/build/hash identity
- guarded source commit -> annotated immutable tag -> separate trigger commit publication topology
