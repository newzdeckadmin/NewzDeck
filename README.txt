NewzDeck v3.6.16
Verified Download Control & Active Continuity

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.16

- Failed/Completed Remove is more resilient to transient SAB Queue/History API reads.
- Terminal SAB Failed/Completed/Cancelled history can safely prove a transfer is
  already stopped when Queue itself is briefly unreadable.
- Verified Remove/Cancel now reports its real failure reason instead of a generic
  unexpected application error.
- Successful Remove/Cancel cannot fall back to the stale pre-removal snapshot.
- Package Remove/Cancel buttons show Removing... / Cancelling... while verification runs.
- NewzDeck's own Pause/Resume intent is authoritative for immediate presentation.
- A transient unexpected SAB global Paused sample cannot immediately wipe a proven
  Active queue; NewzDeck holds the coherent view briefly and reasserts Resume.
- Genuine user Pause remains immediate, and persistent SAB pauses are shown after
  the bounded recovery grace.
- SAB adapter identity now matches the application version.

v3.6.15 Wanted-state reconciliation, v3.6.14 Automation state reliability,
v3.6.13 verified queue ownership/removal protections, and the v3.6.12
installer-owned update lifecycle remain preserved.
