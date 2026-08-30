# NewzDeck v3.6.18 - Idle-Aware Engine Pause Recovery

NewzDeck v3.6.18 is a focused Downloads-engine state hotfix built on v3.6.17.

## Idle-aware SAB engine pause recovery

- **Recovery requires work:** a raw SAB aggregate `Paused` state is treated as an engine mismatch only when SAB has a live Queue slot or reports non-zero transfer bytes.
- **Idle is not an error:** an empty private SAB engine may settle into `Paused` internally without NewzDeck repeatedly sending Resume or showing `Engine paused unexpectedly - recovering`.
- **No recovery loop:** the previous idle -> recovery -> idle cycling is eliminated.
- **Workload-aware Active bridge:** the bounded coherent Active-snapshot bridge also requires transfer-work evidence, preventing a drained queue from preserving stale Active cards.
- **Diagnostics clarity:** benign empty-queue SAB pause state is distinguished from a real pause mismatch where transfer work is waiting.
- **User Pause remains authoritative:** an intentional NewzDeck Pause is immediate and is never overridden by recovery logic.

## Preserved from v3.6.17

- One canonical Downloads state for cards, counts, Remaining, speed, and ETA.
- SAB aggregate Remaining retained for diagnostics only.
- Every live SAB Queue slot represented by a visible NewzDeck card.
- User Pause state separated from private-SAB engine state.
- PID-aware Smart Import claim recovery.
- Smart Import progress heartbeat and `IMPORT STALLED` detection.

## Preserved from earlier releases

- v3.6.16 verified Failed/Completed Remove/Cancel and Active continuity protections.
- v3.6.15 Wanted-state reconciliation and bounded Continuous Automation release retrieval.
- v3.6.14 Windows-safe Automation JSON persistence and responsive Save acknowledgements.
- v3.6.12 installer-owned Update Center runtime restoration.

Normal installed updates preserve settings, provider configuration, queue state, Automation data, history, and other user data under NewzDeck's version-independent user-data directory.
