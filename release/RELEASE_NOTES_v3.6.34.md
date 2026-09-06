# NewzDeck v3.6.34 — Manual Media Import & Wanted Reconciliation

NewzDeck v3.6.34 adds a production Manual Media Import path for TV media that was obtained outside NewzDeck. A monitored show can now import an external season or individual episode through the same Smart Import organization and safety logic used by completed Automation downloads.

## Import Media from a TV library item

TV Automation items now include **Import Media**. The import flow supports:

- **Entire season** — recursively inspect supported video files in a selected external folder and map exact episode tokens to the chosen season.
- **Single episode** — choose one season/episode target and import the matching file from the selected folder.

The source folder is selected with NewzDeck's existing native Windows folder picker. Selecting an import source does not add it as a TV Root Folder or otherwise change Automation configuration.

## Preview before commit

**Preview Import** is non-destructive. It shows, per source file:

- identified season/episode and episode title;
- incoming quality and current library quality when applicable;
- planned action (`IMPORT`, `UPGRADE`, `KEEP_EXISTING`, `DUPLICATE`, `IGNORE`, or `NEEDS_ATTENTION`);
- the canonical NewzDeck destination path and filename;
- whether the resulting library quality meets the selected quality-profile cutoff.

A preview containing unresolved `NEEDS_ATTENTION` media cannot be committed from the UI. The final commit always rebuilds the plan from current disk/library state rather than trusting a stale preview.

## Smart Import transaction and no-downgrade protection

Manual imports do not use a second organizer. The commit is routed through NewzDeck's existing transactional Smart Import path:

1. identify and plan the selected TV target;
2. re-check the physical destination and recover existing quality immediately before commit;
3. replace an existing file only when the incoming quality is provably better;
4. stage/copy or move the source file and verify size/fingerprint before final placement;
5. update the authoritative Automation library file record only after the media transaction succeeds.

Equal, worse, duplicate, and indeterminate-quality replacements keep the existing library file. Manual source media is not deleted merely because NewzDeck chose `KEEP_EXISTING` or `DUPLICATE`.

## Immediate Wanted reconciliation

After a successful import, NewzDeck writes the resulting file path, detected quality, fingerprint, media information, and cutoff status into the monitored episode record. Wanted is then recalculated immediately.

If the imported media satisfies a previously missing or below-cutoff target, that episode is removed from Wanted without requiring another Newznab search, SAB job, application restart, or library scan. The import result reports how many Wanted targets were satisfied and how many remain for that TV item.

## Preserved behavior

- v3.6.33 country-edition Newznab search aliases and local release identity compatibility remain unchanged.
- v3.6.32 last-second target revalidation, existing-quality recovery, no-downgrade Smart Import guard, and scan/import optimistic concurrency remain intact.
- v3.6.31 historical SAB probe quieting, v3.6.30 identity-probe stabilization, v3.6.29 persistent SAB control transport, and v3.6.28 Downloads continuity remain unchanged except for required v3.6.34 version identity markers.
- Automatic retry timing, Wanted policy, queue depth, release-feed behavior, and Continuous Automation scheduling are not redesigned by this release.
