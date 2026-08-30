NewzDeck v3.6.18
Idle-Aware Engine Pause Recovery

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.18

- Engine-pause recovery now runs only when transfer work actually exists.
- An empty private SAB engine can idle as aggregate Paused without causing a
  repeating Resume/recovery cycle.
- The Active continuity bridge also requires evidence of transfer work, so a
  genuinely drained queue cannot retain stale Active cards.
- Diagnostics distinguishes benign "SAB paused, no work" idle state from a real
  pause mismatch with transfers waiting.
- v3.6.17's canonical Downloads-state model remains intact: visible cards, counts,
  Remaining, speed and ETA come from the same job set.
- v3.6.17 Smart Import dead-runtime recovery and stall detection remain intact.
- v3.6.16 verified Remove/Cancel and Active continuity remain preserved.
