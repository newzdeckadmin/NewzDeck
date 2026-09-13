# NewzDeck v3.6.89 - Duplicate Fingerprint Reconciliation Fix

v3.6.89 is a narrow Automation/Smart Import correctness hotfix built on v3.6.88. It fixes the remaining loop where NewzDeck could download an upgrade, prove that its media bytes were already present in the library, classify the completed job as `DUPLICATE`, and then immediately keep the same episode in Wanted and select the same release again.

## Production symptom

A Wanted episode could download a release such as a 2160p WEB-DL Dolby Vision + HDR release. Import Inspector then reported `DUPLICATE - Existing episode has the same fingerprint`, proving that the downloaded media and the library media were byte-identical. Despite that proof, Wanted could continue to show the old unconfirmed dynamic-range state and Automation could queue the same release again.

## Root cause

v3.6.88 correctly stamped normal `IMPORT` and `UPGRADE` results with trusted release traits so Wanted could use the release NewzDeck had just selected and imported. The `DUPLICATE` / `KEEP_EXISTING` reconciliation branch still rebuilt the existing file record from its base quality and lightweight media probe, however.

For a fingerprint-identical `DUPLICATE`, this discarded the strongest new fact NewzDeck had learned: **the existing library file is the exact payload of the selected release**. The record could therefore fall back to legacy/unconfirmed DV/HDR state and become eligible for the same corrective replacement again. `KEEP_EXISTING` could also erase trusted traits from an equal-or-better file by reconstructing it from probe data alone.

## Fingerprint-proven duplicate reconciliation

v3.6.89 carries byte-identity proof from import planning through staging cleanup and uses it during final reconciliation:

- `DUPLICATE` is trusted only when Smart Import has explicitly proven matching source and existing-file fingerprints.
- For an Automation grab with that proof, the selected release's parsed traits are attached to the existing library file.
- The existing fingerprint is rebound to the original release title in `media-quality-cache.json`.
- The record is stamped `dynamic_range_import_trusted` just like a normal successful import.
- Cutoff/Wanted state is recalculated from the same canonical record used by the decision engine.
- The redundant staging copy can still be removed safely; the proof survives that cleanup boundary.

## KEEP_EXISTING preservation

When NewzDeck keeps an equal or better library file rather than replacing it, v3.6.89 preserves that file's existing release traits and trusted dynamic-range metadata. An inconclusive lightweight probe can no longer erase provenance that was already established by a previous successful import.

## Expected behavior

For a 4K Preferred target:

- Existing file and downloaded DV+HDR release have the same fingerprint -> existing record becomes trusted DV+HDR -> cutoff satisfied -> target leaves Wanted.
- Existing file and downloaded DV-only release have the same fingerprint -> existing record becomes trusted DV-only -> target can remain Wanted for DV+HDR, but another same-rank DV-only release is no longer accepted as a corrective replacement.
- `KEEP_EXISTING` on a previously trusted DV/HDR file -> the trusted traits remain intact.

No library rescan, cache clear, or manual file replacement is required.

## Preserved behavior

- v3.6.88 confidence-aware dynamic-range evidence and post-import Wanted reconciliation
- v3.6.87 same-tier correction for legacy optimistic dynamic-range provenance
- v3.6.86 one-quality-cache-snapshot-per-operation performance fix
- SABnzbd 5.1.2 integration and transactional Smart Import
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- frozen Newsgroup Browser architecture/tuning
- guarded source commit -> annotated tag -> separate trigger commit publication topology
