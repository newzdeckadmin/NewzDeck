# NewzDeck v3.6.88 - Smart Import Wanted Reconciliation Fix

v3.6.88 is a narrow Automation correctness hotfix built on v3.6.87. It fixes a post-import state problem where a successfully downloaded and imported upgrade could continue to appear in Wanted with the old dynamic-range state even when the newly imported release satisfied the profile target.

## Production symptom

After a Wanted upgrade completed and Smart Import replaced the library file, Wanted could continue showing the previous state, including cases where the new release was explicitly Dolby Vision + HDR fallback and therefore should have satisfied the 4K Preferred target.

Switching between Wanted, TV and back to Wanted did not correct the row because the backend continued resolving the saved file through the same stale/overly-negative dynamic-range evidence path.

## Root cause

v3.6.87 correctly separated release provenance from intrinsic file evidence, but it still treated the lightweight built-in media probe's *absence* of Dolby Vision/HDR signatures as authoritative negative evidence.

The probe intentionally inspects bounded container data and is not a complete HEVC/Matroska/MP4 media analyzer. A valid DV/HDR file can therefore produce no positive signature in that bounded sample. Immediately after Smart Import, that false-negative probe could overwrite the explicit traits of the release NewzDeck had just selected and imported. Wanted then recalculated against the downgraded trait view and retained the old upgrade row.

## Confidence-aware dynamic-range evidence

v3.6.88 changes the evidence model:

- Positive media-probe DV/HDR signatures remain authoritative evidence and can promote or correct the current file; only an all-negative bounded probe is treated as inconclusive.
- A negative result from the lightweight probe no longer erases explicit release traits merely because no signature was found.
- Successful Smart Import stamps the imported release's dynamic-range provenance as the authoritative post-import Automation state.
- Pre-v3.6.88 records whose release title claims DV/HDR but whose lightweight probe cannot positively confirm it are marked as unconfirmed rather than forcibly downgraded.
- Interactive Search may accept one same-rank preferred dynamic-range replacement for that legacy unconfirmed state while it is still below the profile target.
- Once that replacement is imported by v3.6.88, the new import is trusted for Automation state, preventing a repeat-download loop.

## Expected progression

For the 4K Preferred profile at 2160p WEB-DL:

- legacy/unconfirmed DV claim -> real DV candidate: eligible corrective replacement
- SDR/HDR -> DV: upgrade
- SDR/HDR/DV -> DV + HDR fallback: upgrade
- newly imported DV-only -> DV-only: not an upgrade
- newly imported DV-only -> DV + HDR fallback: upgrade
- newly imported DV + HDR fallback: target satisfied and removed from Wanted

## Persistence and refresh

Smart Import now calculates the saved episode/movie cutoff state from the same canonical post-import record that Wanted uses. No library rescan, cache clear or application restart is required. The normal Automation summary refresh will see the persisted satisfied target and remove it from Wanted.

## Preserved behavior

- v3.6.87 same-tier correction for legacy optimistic dynamic-range provenance
- v3.6.86 one-quality-cache-snapshot-per-operation performance fix
- v3.6.84 cutoff reason/policy semantics
- SABnzbd 5.1.2 integration and transactional Smart Import
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- frozen Newsgroup Browser architecture/tuning
- guarded source commit -> annotated tag -> separate trigger commit publication topology
