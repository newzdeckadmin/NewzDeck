# NewzDeck v3.6.13 - Download Continuity & Automation Clarity

NewzDeck v3.6.13 is a focused download-state and Automation clarity release built on v3.6.12.

## Download continuity

- **Stable Active cards:** once SAB positively proves a package is transferring, NewzDeck keeps bounded presentation ownership across transient SAB queue-slot gaps while byte progress or foreground activity proves the transfer is continuing.
- **Real state still wins:** explicit pause, propagation retry, terminal SAB history, or a different foreground package ends the continuity bridge immediately.
- **Verified Remove/Cancel:** NewzDeck no longer hides a card or records an explicit removal tombstone until SAB confirms the NZO ID is absent from the live queue.
- **Hidden-transfer recovery:** older explicit removal tombstones that still point to a live SAB job are reconciled by reissuing the user's stop/delete intent.
- **Diagnostics:** Active-card continuity bridges and hidden-transfer cleanup activity are reported for troubleshooting.

## Automation clarity and season-pack policy

- **Wanted explains policy pauses:** items excluded because existing-backlog search is disabled now show `BACKLOG PAUSED`, with a direct path to Automation settings.
- **Upgrade policy is visible:** Wanted can show `UPGRADES OFF` instead of leaving an apparently actionable item unexplained.
- **Clearer monitoring copy:** All Episodes / Missing Episodes descriptions distinguish monitoring from automatic backlog searching.
- **Season packs are fallback-only:** individual episodes are searched first. A pack is considered only when the whole monitored, fully aired season is still missing and every individual episode search has returned no acceptable release.
- **No pack/episode overlap:** an active member episode suppresses a pack, and a queued pack reserves all member episode targets for the rest of the Automation cycle.
- **No redundant full-season grabs:** a partially complete season will not automatically fetch an entire season pack.

## Preserved

- v3.6.12 installer-owned Update Center runtime restore.
- v3.6.11 SAB ownership/completion continuity and Smart Import reconciliation.
- v3.6.10 Python source-freshness protections.
- Accepted v3.6.8 image-browsing performance and gallery-quality work.

Normal installed updates preserve settings, provider configuration, queue state, Automation data, history, and other user data under the version-independent NewzDeck user-data directory.
