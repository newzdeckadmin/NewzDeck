# NewzDeck v3.6.17 - Downloads State Integrity & Smart Import Recovery

NewzDeck v3.6.17 is a structural Downloads-state reliability release built on v3.6.16.

## One canonical Downloads state model

- **One source for cards and KPIs:** Active/Queued counts, transfer speed, Remaining and ETA are finalized from the same visible job set used to render Downloads cards.
- **Raw SAB remaining is diagnostic only:** SAB's aggregate remaining-byte value can no longer create a contradictory view where the UI shows no transfer jobs but still reports a large Remaining value.
- **No hidden live SAB jobs:** every live SAB Queue slot must have a visible NewzDeck card. If normal ownership adoption fails, NewzDeck surfaces a recovery/stopping card instead of hiding the transfer.
- **Consistency telemetry:** Diagnostics records raw-vs-visible remaining bytes and every snapshot consistency correction.

## Pause intent is separated from engine state

- **User pause is authoritative:** `Queue paused` now means NewzDeck's durable user Pause state, not merely one raw SAB aggregate `Paused` sample.
- **Engine mismatch is explicit:** an unexpected private-SAB pause while NewzDeck intends Running is shown as `Engine paused unexpectedly - recovering`.
- **Background recovery remains isolated:** the background SAB coordinator reasserts Resume; the UI snapshot path does not mutate SAB.
- **Real Pause remains immediate:** user-requested Pause is never overridden by mismatch recovery.

## Smart Import ownership recovery

- **PID-aware claims:** persisted Smart Import ownership now verifies that the owning NewzDeck process is still alive.
- **Dead-runtime reclaim:** an import orphaned by an update/service restart is reclaimed immediately instead of waiting for the historical ten-minute lease.
- **Progress heartbeat:** Smart Import updates a heartbeat alongside import progress.
- **Visible stalls:** a still-live import with no progress heartbeat for 90 seconds is marked `IMPORT STALLED` and reports its no-progress age.
- **No duplicate import:** a live owner process keeps its claim and is not automatically duplicated.

## Preserved

- v3.6.16 verified Failed/Completed Remove/Cancel and Active continuity through transient SAB pause conditions.
- v3.6.15 Wanted-state reconciliation, QUEUEING handoff state, cycle progress and bounded automatic NZB retrieval.
- v3.6.14 Windows-safe Automation JSON persistence and responsive monitoring Save acknowledgements.
- v3.6.12 installer-owned Update Center runtime restoration.

Normal installed updates preserve settings, provider configuration, queue state, Automation data, history, and other user data under NewzDeck's version-independent user-data directory.
