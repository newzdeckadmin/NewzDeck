# NewzDeck v3.6.9 - In-App Update Runtime Handoff

NewzDeck v3.6.9 is a focused Windows upgrade-path hotfix built on v3.6.8. It fixes an in-app Update Center failure where Setup could detect `NewzDeckPicker.exe` using files that needed to be updated but could not automatically close the process.

## Upgrade reliability

- **Retires the legacy long-lived taskbar helper launch** - since v3.6.5, `NewzDeck.exe` owns the Windows taskbar identity. The backend no longer launches `NewzDeckPicker.exe --taskbar-fix` as a process that remains alive with the UI.
- **Explicit native-helper shutdown** - after the tray and background service are stopped, Setup explicitly terminates stale `NewzDeckPicker.exe`, persistent `NewzDeckThumb.exe`, and `NewzDeckYenc.exe` helper processes before file replacement begins.
- **Update Center defense in depth** - future verified installer launches also request Inno Setup close/force-close behavior.
- **Regression-tested installed upgrade** - both Windows build workflows now deliberately start the real long-lived Picker taskbar-fix mode before an upgrade and fail if Setup cannot close the process and replace the locked executable.

## Preserved

- v3.6.8 Image Browsing Performance & Gallery Quality is unchanged, including persistent WIC-first thumbnails, multipart acceleration, RAM caches, tiny-image suppression, and browser rendering hot-path optimizations.
- v3.6.7 browsing responsiveness, v3.6.6 adaptive preview scaling, v3.6.5 taskbar identity, v3.6.4 package reconstruction, private SAB downloads, Smart Import, Automation, Discover/TMDB, and Metadata Server v0.3.3 compatibility remain preserved.

## Upgrade notes

You may install v3.6.9 directly over an existing NewzDeck installation. The v3.6.9 installer is specifically designed to close the stale v3.6.8/v3.6.7 Picker helper that could block earlier in-app upgrades.

NewzDeck remains intentionally unsigned. Verify downloads with `NewzDeck_v3.6.9_SHA256.txt` if desired.
