NewzDeck v3.6.20
Authoritative SAB & Fresh-State Reconciliation

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.20

- One authoritative private SAB identity; historical NewzDeck SAB generations are
  quarantined/retired instead of adopted as the active engine.
- Proven stale duplicate queue entries are cleaned without deleting legitimate
  tracked re-downloads.
- SAB 5.x provider/bootstrap configuration is reconciled correctly.
- NewzDeck-to-SAB localhost control traffic is serialized through one transport.
- Downloads and Automation completion monitoring share one coherent Queue/History
  reader with bounded retries and stale-data leases.
- Stale Queue state cannot trigger Pause/Resume recovery, drive destructive queue
  reconciliation, or renew an old Downloads snapshot indefinitely.
- A temporarily unreadable SAB control channel is shown as refreshing; speed and
  Remaining are treated as unknown until fresh state returns.
- Ambiguous addlocalfile resets reconcile accepted jobs without duplicate submission.
- Copy Diagnostics includes the Queue/History transport counters.
- Handoff diagnostics now say "Reconciled SAB job after submission/runtime handoff."

The accepted validation demonstrated:
Automation -> Queue -> SAB -> NNTP -> Completed -> Smart Import.
