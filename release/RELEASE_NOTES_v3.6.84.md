# NewzDeck v3.6.84 - Wanted Upgrade Reasoning & Cutoff Policy Fix

v3.6.84 is a narrow Automation correctness release built on the published v3.6.83 baseline. It fixes the Quality Upgrades/Wanted regression visible when existing files were shown with self-contradictory messages such as `Current 2160p WEB-DL has not reached 2160p WEB-DL`.

## Root cause

The v3.6.81 structured profile model introduced independent quality-ladder, release-source and dynamic-range upgrade dimensions. The existing `cutoff_met` path still collapsed those dimensions into one boolean and treated every dynamic-range state that was not `Avoid` as a terminal target. That made `Allow` behave like `Prefer`, especially in the built-in 1080p Balanced profile, and the Wanted renderer then described every non-terminal trait state as `Quality below cutoff` even when the base quality and cutoff labels were identical.

## Corrected profile semantics

- Base quality cutoff is evaluated independently from trait upgrades.
- An explicit WEB-DL cutoff can still upgrade a generic WEB release at the same resolution/rank, but it is described as a release-source upgrade rather than a base-quality cutoff miss.
- Dynamic-range upgrade targets are now formed only from `Prefer` or `Require` policy values.
- `Allow` means acceptable and no longer creates an ongoing upgrade requirement.
- 4K Preferred keeps the intended SDR -> HDR -> Dolby Vision -> Dolby Vision + HDR fallback progression because its dynamic-range states are explicitly preferred.
- 1080p Balanced accepts SDR at 1080p WEB-DL because its HDR/Dolby Vision states are allowed rather than preferred.

## Wanted explanations

Quality Upgrades now carries a reason code, reason label, detail and upgrade path that reflect the actual dimension being improved. Examples include:

- `Quality below cutoff` with `Current: 1080p WEBRip -> 2160p WEB-DL`
- `Release source upgrade` with `Source: 2160p WEB -> 2160p WEB-DL`
- `Preferred dynamic range upgrade` with `Dynamic range: SDR -> Dolby Vision + HDR fallback`

The generic `Current X -> X` presentation is no longer used when the upgrade is actually a source or dynamic-range preference.

## Stale cutoff flags

Library and Calendar responses now recompute derived `cutoff_met` status from the active profile and stored release/media traits. This prevents pre-v3.6.84 persisted booleans from leaving items stuck in an obsolete `upgrade wanted` state until the user manually rescans the library.

## Preserved behavior

- v3.6.83 installed/runtime/UI update-version coherency and same-version protection
- v3.6.81 structured Quality Profile schema, WEB-DL preference and explicit preferred dynamic-range progression
- Newsgroup Browser accepted architecture/tuning
- SABnzbd 5.1.2 integration, download queue, post-processing and Smart Import
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- Defender-clean yEnc source/build/hash identity
- guarded source commit -> annotated immutable tag -> separate trigger commit publication topology
