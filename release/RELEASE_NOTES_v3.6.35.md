# NewzDeck v3.6.35 — Manual Import Live Progress

NewzDeck v3.6.35 is a focused production follow-up to v3.6.34. The Manual Media Import workflow is unchanged in purpose and safety, but **Import & Organize now exposes real transaction progress** while an external TV season or episode is being organized.

## Real progress instead of an indeterminate wait

After a Manual Import preview is accepted and **Import & Organize** starts, the Import Media modal remains open and displays a live progress bar. Progress comes from the existing Smart Import transaction itself rather than a timer.

The progress state reports:

- overall percentage;
- current import phase;
- the current source/media filename where applicable;
- byte-based advancement while a file is copied across drives or volumes;
- final completion details including files organized and Wanted targets satisfied.

Same-volume moves do not require a full byte copy, so they advance through preparation, staging, commit, library-state update, and reconciliation phases.

## Completion means fully accounted for

The progress bar reserves its final range for NewzDeck's authoritative library update and Wanted reconciliation. It reaches **100% only after** the imported media has been committed, the resulting quality/cutoff state has been written, and Wanted has been recalculated.

This prevents the UI from reporting completion while NewzDeck is still reconciling the reason the media was imported in the first place.

## Modal and preview safety

While the import is active, source/season/episode controls and close actions are locked so the visible job cannot be accidentally detached from the selections that produced it. Changing the source folder or target selection before starting an import invalidates the prior preview and requires Preview Import again.

The backend still rebuilds the plan at start time. If final revalidation finds unresolved `NEEDS_ATTENTION` media, the job is rejected before import transaction work begins instead of partially importing around an unsafe item.

## Preserved behavior

- v3.6.34 Manual Media Import season/episode mapping, canonical renaming/moving, existing-file decisions, and immediate Wanted reconciliation remain intact.
- v3.6.32 last-second target revalidation, existing-quality recovery, no-downgrade Smart Import protection, and scan/import concurrency safeguards remain intact.
- v3.6.33 country-edition search aliases and local release identity compatibility remain unchanged.
- v3.6.31 historical SAB probe quieting, v3.6.30 identity-probe stabilization, v3.6.29 persistent SAB control transport, and v3.6.28 Downloads continuity remain unchanged except for required v3.6.35 identity markers.
- Automatic retry timing, Wanted policy, queue depth, release-feed behavior, and Continuous Automation scheduling are not redesigned by this release.
