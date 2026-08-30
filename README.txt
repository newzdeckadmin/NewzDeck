NewzDeck v3.6.15
Wanted State Reconciliation & Responsive Automation

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.15

- Wanted now reconciles QUEUED/GRABBED-style badges against the live download
  engine instead of trusting stale persisted Automation runtime state.
- A missing live job is allowed a short handoff grace, then the target changes to
  RETRYING rather than continuing to claim it is queued.
- Cross-runtime grab reservations display QUEUEING until a real live job appears.
- Continuous Automation shows useful phase/target progress and Next Cycle reports
  In progress while the current cycle is actually running.
- Metadata refresh and library reconciliation no longer block release searching.
- Automatic NZB retrieval is bounded so one problematic result cannot hold the
  entire cycle indefinitely.
- Long-running cycles merge newer concurrent failure/blacklist and maintenance
  runtime state before writing their final snapshot.

v3.6.14 Windows-safe Automation JSON persistence and responsive Save feedback,
v3.6.13 download continuity/verified removal/season-pack policy, and the v3.6.12
installer-owned update lifecycle remain preserved.
