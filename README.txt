NewzDeck v3.6.17
Downloads State Integrity & Smart Import Recovery

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.17

- Downloads now has one canonical state model: cards, counts, Remaining, speed and
  ETA are all derived from the same visible job set.
- SAB's aggregate remaining-byte counter is diagnostic only and cannot create an
  impossible "0 Active / 0 Queued / many GB remaining" view.
- Every live SAB Queue slot must be represented by a visible NewzDeck card.
- User-facing Queue paused state comes from NewzDeck's own durable Pause intent,
  while internal SAB pause mismatches are shown as engine recovery.
- Smart Import claims validate the owner PID so an import orphaned by an update or
  service restart is reclaimed immediately.
- Smart Import now has a progress heartbeat and displays IMPORT STALLED after
  90 seconds without progress from a still-live owner.
- Diagnostics exposes state-consistency, engine-pause and import-recovery counters.

v3.6.16 verified Remove/Cancel and Active-continuity work, v3.6.15 Wanted-state
reconciliation, v3.6.14 Automation persistence hardening, and the v3.6.12
installer-owned update lifecycle remain preserved.
