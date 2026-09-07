# NewzDeck v3.6.38 — Crash Recovery & Automation Queue Reconciliation

NewzDeck v3.6.38 is a focused crash-recovery release based on two diagnostic snapshots captured immediately after an unexpected Windows restart.

## What the diagnostics proved

Before the restart, Continuous Automation was correctly maintaining its configured **25/25** queue. During post-boot recovery, SABnzbd and NewzDeck reconstructed the existing queue/history asynchronously. An Automation cycle began while that live snapshot was still incomplete, calculated room for new grabs, and kept using that initial allowance even as old jobs reappeared. The recovered runtime later reported far more active Automation targets than the configured queue depth.

The later stuck-state snapshot exposed a second recovery defect:

- **140** completed SAB History jobs were shown as **Import Failed**.
- Every one of those 140 jobs had completed **before the Windows crash**.
- Every one had been **adopted from SAB after restart** with recovered Automation context.
- Every target was already present in NewzDeck's authoritative media library on disk at the **same or better quality** as the recovered release.
- NewzDeck had therefore successfully imported/organized those episodes before the crash, but the final per-SAB-job import marker was not durable when the system stopped.
- Because Smart Import had correctly cleaned each old SAB source folder after success, v3.6.37's restart adoption path later saw no Completed Download Folder and retried output discovery 24 times before falsely declaring **Import Failed**.

The same snapshot also showed the sole remaining live SAB queue job individually **Paused** while NewzDeck's global queue state was unpaused, leaving 0 active downloads.

## Recovered completed-import reconciliation

v3.6.38 adds a fail-closed reconciliation path for this exact crash boundary.

A recovered SAB History job is marked already imported only when all of the following are true:

- the job was adopted from SAB with recovered Automation context;
- it is an exact missing-media target, not a season pack or upgrade;
- the authoritative Automation library already records that exact movie/episode as having a file;
- the recorded library path exists on disk;
- the authoritative library quality is equal to or better than the recovered release quality.

When those proofs pass, NewzDeck restores the per-job Smart Import completion state and releases the false Post-processing/Import Failed reservation. **No media is moved, deleted, copied, or redownloaded.**

If any proof is missing, normal Smart Import/Retry Import behavior remains unchanged.

## Authoritative queue admission

v3.6.38 also prevents the original post-restart overfill:

- Continuous Automation defers a cycle if the private SAB engine is not currently probe-ready.
- The cycle re-reads authoritative Automation occupancy immediately before every automatic Grab.
- Jobs that are recovered while a cycle is already running consume queue capacity immediately.
- Once effective occupancy reaches the configured queue depth, the cycle stops adding releases even if its initial snapshot showed free capacity.
- During the first ten minutes of a newly started Automation runtime, recent persisted queued/grabbed/processing target state is conservatively merged with live state.

## Recovered sole paused job

If NewzDeck's global queue is unpaused but the **only** live SAB Queue item is individually Paused after being adopted from recovered Automation state, v3.6.38 makes one bounded automatic Resume attempt.

Future per-job Pause/Resume actions now persist explicit user pause intent. An explicitly user-paused job is never auto-resumed by this recovery path.

## Faster normal boot recovery

The Windows background service can start before the signed-in tray helper is ready. v3.6.37 correctly avoided rotating SAB identity for that environmental failure but still applied the generic 90-second launch cooldown. v3.6.38 gives only this known service/tray ordering race a short 8-second retry delay. Genuine SAB launch failures retain the existing 90-second protection.

## Preserved behavior

- Manual Interactive Search/Grab behavior is unchanged.
- Newznab querying, scoring, blacklisting, TV-edition matching, and release identity checks are unchanged.
- Normal Smart Import, existing-media handling, no-downgrade protection, and final target-integrity validation are unchanged.
- v3.6.37 operation progress/activity indicators remain intact.
- v3.6.36 Automation Search/action wiring remains intact.
- v3.6.35 Manual Import live progress and v3.6.34 external media import remain intact.
- Persistent SAB transport, identity isolation, historical-engine quarantine, and Downloads continuity remain intact except for the explicitly bounded recovery behavior above.
