NewzDeck v3.5.34 — Reliability & Release Hardening

NewzDeck v3.5.34 is a focused reliability release built on the proven v3.5.33
source-complete baseline. It does not change the SAB download data path.

Key changes
-----------
- Repairs the built-in verified online updater for NewzDeck's real GitHub release
  naming: NewzDeck_vX.Y.Z_Setup.exe plus NewzDeck_vX.Y.Z_SHA256.txt.
- Enables the official GitHub latest-release feed by default while preserving the
  NEWZDECK_UPDATE_FEED_URL override.
- Makes the desktop heartbeat lifecycle safe across Windows sleep/resume and
  browser timer throttling.
- Makes Downloads polling order-safe so an older late response cannot overwrite a
  newer SAB snapshot, and bounds each status request with a UI timeout.
- Orders Downloads > Completed by actual completion time, newest first.
- Migrates existing SAB history by backfilling real completion timestamps; older
  entries without that value retain SAB's newest-first history order.
- Repairs the About & Updates TMDB attribution logo and text wrapping.
- Adds localhost browser-origin protection for mutating API requests plus
  anti-framing/resource hardening headers.
- Keeps raw unexpected backend exceptions in Diagnostics while returning a stable
  user-facing HTTP 500 message.
- Rotates Watch Folder scanning fairly when more than 100 NZBs are present so a
  stuck early filename cannot starve later files.
- Removes acceptance-only production-package artifacts. start.bat launches
  NewzDeck.exe so the supported launcher/runtime path is always used.

Compatibility
-------------
- Download Engine v2 / private SABnzbd behavior is unchanged.
- Automation and Smart Import behavior from the accepted v3.5.33 r5 baseline is
  preserved.
- Metadata Server v0.3.3 remains the matching server baseline.
- Existing user state under %LOCALAPPDATA%\NewzDeck is preserved.

License
-------
NewzDeck-owned source is licensed under GNU GPL v3.0 only. Third-party
components retain their own licenses. See LICENSE.txt and THIRD_PARTY_NOTICES.txt.
