# NewzDeck v3.6.39 — Automation Startup Reservation Refinement

v3.6.39 is a focused follow-up to v3.6.38 based on a live diagnostic snapshot taken immediately after upgrading to v3.6.38.

## What the diagnostic snapshot proved

v3.6.38 successfully fixed the dangerous post-crash queue overfill. Its authoritative pre-Grab capacity checks prevented Continuous Automation from adding work beyond the configured queue depth.

The same snapshot exposed a narrower startup usability problem:

- SAB was healthy and had **0 live queued/downloading jobs**.
- Continuous Automation nevertheless reported **16/25 active targets** during the first ten minutes after the update.
- Those 16 reservations were old persisted **`pending-*`** handoff records, not durable SAB collection identities.
- Because v3.6.38 conservatively merged recent persisted targets for the entire ten-minute startup recovery window, those unproven handoff records temporarily consumed queue capacity.
- When the ten-minute window expired, the phantom reservations disappeared and downloads began automatically again. This behavior was confirmed live.

## Short grace for unproven pending reservations

v3.6.39 distinguishes a short-lived queue handoff marker from a durable recovered SAB job.

A persisted target whose `last_collection_id` is empty or begins with `pending-` now participates in restart capacity protection for at most **120 seconds**.

This still covers the brief handoff between release selection and SAB queue visibility, including a crash immediately after submission, but prevents old pending records from making a normal update/restart appear idle for ten minutes.

Persisted targets that have a real non-pending collection identity retain the stronger v3.6.38 startup recovery behavior.

## Dynamic Automation capacity during a running cycle

v3.6.38 already re-read authoritative occupancy immediately before every unattended Grab. v3.6.39 keeps that invariant and removes the remaining static allowance calculated from the first queue snapshot.

- The cycle no longer stops because it reached a `max_grabs` value derived from stale initial occupancy.
- Search budget is based on the configured queue depth rather than the number of slots that appeared free at cycle start.
- If recovered/stale reservations disappear while the cycle is still running, the cycle can continue searching and use the newly available capacity.
- Every actual Grab still performs the authoritative live occupancy recheck first, so this does not weaken the overfill protection.

## Preserved behavior

- v3.6.38 crash-recovered completed-import reconciliation is unchanged.
- v3.6.38 sole recovered paused-job repair is unchanged.
- The private SAB engine-ready admission gate and startup recovery protections are unchanged except for the narrower pending-reservation grace period.
- Existing/recovered jobs are not cancelled, removed, reordered, or redownloaded by this refinement.
- Manual Search/Grab, Newznab querying/scoring/blacklisting, TV-edition matching, Smart Import, no-downgrade protection, and target-integrity validation are unchanged.
- v3.6.37 operation feedback, v3.6.36 Automation action wiring, and v3.6.35 Manual Import progress remain intact.
