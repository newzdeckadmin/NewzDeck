NewzDeck v3.6.38
Crash Recovery & Automation Queue Reconciliation

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.38

- Prevents Continuous Automation from treating an incompletely recovered post-restart
  SAB queue as free capacity and downloading duplicate episode targets.
- Rechecks authoritative queue occupancy immediately before every unattended Grab.
- Uses recent persisted target state only during the short new-runtime recovery window
  so queue/history reconstruction cannot overfill the configured Automation depth.
- Defers unattended grabbing while the private download engine is not probe-ready.
- Retries the expected service-before-tray SAB startup race after 8 seconds instead of
  the generic 90-second genuine-launch-failure cooldown.
- Does not cancel, remove, reorder, or rewrite existing/recovered downloads.

Normal installed updates preserve settings, provider configuration, Automation data,
history, queue state, and user data.

Additional crash-recovery scope: reconcile already-imported recovered SAB History jobs from authoritative library truth and recover a sole unintended per-job pause without overriding explicit user pause intent.
