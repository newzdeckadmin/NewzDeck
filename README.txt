NewzDeck v3.6.12
Installer-Owned Runtime Restore

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

v3.6.12 fixes the installed Update Center lifecycle after real-machine testing
of v3.6.11. The previous release could install the new files and correctly stop
the tray/service, yet leave the Chromium-hosted NewzDeck window open and fail
to restore the service/tray afterward.

The update authority now belongs to Setup itself:
- Existing tray and service state are captured before upgrade.
- Setup closes the browser-hosted NewzDeck window from the signed-in Setup session.
- Setup stops the existing tray and service before replacing files.
- After the new files are installed, Setup runs the new helper again as a safety
  net before restoring the runtime.
- Setup repairs AND starts the previously installed background service.
- Setup restores the tray when it was previously running/configured.
- At successful Setup completion, NewzDeck is relaunched automatically for
  /update installs.
- The external coordinator no longer performs a second post-Setup UAC/service
  start pass.

v3.6.11 SAB ownership/completion continuity, v3.6.10 source freshness, and all
accepted v3.6.8 browsing performance work remain preserved.
