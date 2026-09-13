# NewzDeck v3.6.93 - Defender Handoff Release Gate Recovery

NewzDeck v3.6.93 is a release-pipeline recovery roll-forward built on the reviewed v3.6.92 source state. The v3.6.92 source/tag was published immutably, but its canonical GitHub Actions run stopped at the installed-upgrade smoke test before GitHub Release assets were published.

## Fixed

- Repairs the installed-upgrade smoke test so it no longer invokes `NewzDeckPicker.exe --taskbar-fix`, a mode intentionally removed when v3.6.92 reduced Picker to folder selection only.
- The smoke test now replaces the clean-install Picker with a purpose-built inert legacy-lock stand-in, starts that process, and proves Setup terminates/replaces a locked `NewzDeckPicker.exe` during upgrade.
- Adds a v3.6.93 regression guard that rejects any return of the retired Picker taskbar/update modes and requires the corrected legacy-lock smoke strategy.

## Preserved

- v3.6.92 application behavior is unchanged apart from version identity.
- `NewzDeckPicker.exe` remains folder-picker-only and keeps normal Go metadata (`-H windowsgui`).
- About & Updates launches the checksum-verified Setup directly; no `NewzDeckUpdateHandoff-*.exe` copy is created.
- Setup continues to own service/tray shutdown and restore, while `NewzDeck.exe --close-app-windows` handles the bounded browser-window close after overlay.
- Automation, Wanted, Smart Import, Discover, Newsgroup Browser, downloads, SABnzbd 5.1.2, Metadata Server v0.3.3, Diagnostic Collector v1.0.31, and the Defender-accepted yEnc pipeline are unchanged.

## Release history note

`v3.6.92` remains an immutable source tag with a failed canonical release run and no GitHub Release assets. v3.6.93 is the clean roll-forward rather than moving or rewriting that tag.
