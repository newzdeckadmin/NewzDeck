NewzDeck v3.6.11
SAB Ownership Continuity & Managed Update Handoff

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

v3.6.11 fixes a SAB ownership/completion continuity failure where a real
download could continue at full speed while its individual SAB queue slot was
temporarily absent, causing NewzDeck to drop the card and lose the completion
event required for Post-processing and Smart Import.

It also upgrades the in-app Update Center to a managed lifecycle. A short-lived
native coordinator closes the NewzDeck desktop window and tray, allows Setup to
stop/upgrade the installed background service and application files, then
restores the service, tray, and NewzDeck desktop application after Setup exits.

Highlights:
- Stable Active ownership across temporary SAB queue-slot omissions.
- No automatic removal tombstones from transient SAB presentation gaps.
- Durable queue-to-history completion reconciliation for Automation/Smart Import.
- Recovery of recent legacy automatic-prune tombstones while preserving explicit
  user Remove/Cancel intent.
- Managed Update Center close -> Setup -> restore -> relaunch handoff.
- v3.6.10 Python source-freshness protections remain intact.
- v3.6.9 installer runtime shutdown protections remain intact.
- v3.6.8 image-browsing performance and gallery-quality work remains intact.

For normal installed updates, use About & Updates inside NewzDeck or run the
newest NewzDeck Setup.exe over the existing installation. User settings,
provider configuration, queue state, Automation data, and history are stored
outside the application directory and are preserved.
