NewzDeck v3.6.10
In-App Update Runtime Handoff
Getting Started

NewzDeck is a free and open-source Windows Usenet newsreader, downloader,
and personal media automation application. v3.6.10 is a focused upgrade-path
hotfix built on the accepted v3.6.8 image-browsing release.

WHAT'S NEW IN v3.6.10

- The verified in-app Update Center no longer leaves the legacy long-lived
  NewzDeckPicker.exe taskbar helper blocking Setup file replacement.
- Setup explicitly shuts down stale Picker, persistent thumbnail, and native
  yEnc helper processes after the tray/background-service handoff.
- Future in-app installer launches request Inno close/force-close handling as
  defense in depth.
- The Windows release pipeline now reproduces the real Picker file lock during
  an installed-upgrade smoke test, preventing this regression from publishing.
- v3.6.8 image browsing performance, tiny-image suppression, WIC thumbnail
  acceleration, cache behavior, and gallery rendering remain unchanged.

WHAT YOU NEED

- Windows 10 or Windows 11, 64-bit
- Your own Usenet provider account

NewzDeck remains intentionally unsigned. Verify downloads with
NewzDeck_v3.6.10_SHA256.txt if desired.
