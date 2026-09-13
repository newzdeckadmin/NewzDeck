# NewzDeck v3.6.92 - Defender Handoff Reduction & Picker Simplification

NewzDeck v3.6.92 is a narrowly scoped Windows updater/Defender false-positive reduction release built on v3.6.91.

## Why this release exists

Microsoft Defender accepted the v3.6.91 Portable ZIP and Setup download, but still detected `NewzDeckPicker.exe` as `Trojan:Win32/Wacatac.B!ml` when Setup installed or the older in-app updater copied/renamed Picker into `%LOCALAPPDATA%\NewzDeck\updates\NewzDeckUpdateHandoff-*.exe` and executed it. v3.6.92 removes that architecture instead of making another linker-flag-only change.

## Changed

- **About & Updates launches Setup directly.** NewzDeck still downloads the GitHub Release Setup asset and verifies its published SHA-256 first, but it no longer copies `NewzDeckPicker.exe` to a random temporary executable name or executes that copy.
- **Picker is folder-picker-only.** `NewzDeckPicker.exe` now contains only the native Windows folder chooser and its result-file plumbing. Update handoff, browser-window control, process launching, taskbar compatibility, elevation, and Setup coordination have been removed from Picker source.
- **Browser-window close moved to `NewzDeck.exe`.** The launcher already owns Chromium app-window discovery for NewzDeck taskbar identity. It now exposes one bounded internal `--close-app-windows` maintenance mode for Setup.
- **Setup never launches Picker during upgrade.** Setup stops the tray/service/helpers, overlays the new files, invokes the new launcher to close any remaining NewzDeck Chromium app window, restores service/tray state, and relaunches NewzDeck.
- **Picker keeps normal Go metadata.** The `-H windowsgui` Picker profile remains so the helper retains a normal Go build ID and symbol table.

## Upgrade note for v3.6.91 and older affected builds

If Microsoft Defender blocks the existing in-app updater before v3.6.92 is installed, download and run `NewzDeck_v3.6.92_Setup.exe` manually for this one upgrade. The v3.6.92 installer does not execute the old or new Picker during upgrade. Future in-app updates from v3.6.92 use the direct verified-Setup path.

## Preserved

- SABnzbd 5.1.2 download behavior.
- Metadata Server v0.3.3.
- Diagnostic Collector v1.0.31.
- Automation, Wanted, Smart Import, quality profiles, Discover, Newsgroup Browser, download/post-processing behavior, and the accepted yEnc helper pipeline.
- Existing user settings, provider credentials, libraries, caches, queues, and download statistics.

This release reduces the behavior that triggered Defender, but it does not claim Microsoft has already reclassified the new binary. The finished v3.6.92 `NewzDeckPicker.exe` should still be tested with current Microsoft Defender after publication.
