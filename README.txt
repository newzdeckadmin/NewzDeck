NewzDeck v3.6.14
Automation Save Reliability & Responsiveness

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application.

WHAT'S NEW IN v3.6.14

- Automation JSON state reads and writes are serialized per file so Windows no
  longer races a media-library.json reader against the final atomic replacement.
- Short-lived Windows access/sharing violations during atomic JSON replacement
  receive bounded retries instead of immediately surfacing WinError 5.
- Changing a show's monitoring type now confirms Saved as soon as the authoritative
  media update has actually been persisted.
- Wanted, Calendar, health, counts, and other broader Automation state refresh in
  the background after the persisted Save instead of delaying the notification.
- Season and episode monitoring toggles likewise no longer block on a full summary
  rebuild.

v3.6.13 download continuity, verified Remove/Cancel, hidden-transfer recovery,
Wanted policy clarity, and fallback-only season packs remain preserved, along with
the v3.6.12 installer-owned update lifecycle and prior source-freshness protections.
