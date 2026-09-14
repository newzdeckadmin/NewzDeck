# NewzDeck v3.7.3 - Managed In-App Update Handoff Hotfix

v3.7.3 restores the seamless About & Updates installation lifecycle while preserving the v3.7.2 SABCTools/download architecture and Defender-compatible helper design.

## Fixed

- **One-click managed updates are restored.** About & Updates launches the already SHA-256-verified Setup package using Inno Setup's `/SILENT` managed update path instead of opening the normal interactive installer wizard.
- **NewzDeck closes before file overlay.** During the managed in-app path, Setup asks the installed `NewzDeck.exe --close-app-windows` maintenance mode to close the browser-hosted NewzDeck UI before installation starts.
- **Tray and service lifecycle remains Setup-owned.** Setup captures the existing tray/service state, closes and waits for the tray process, stops and waits for the Windows service, overlays the new files, repairs/restarts the service, and restores the tray state.
- **Silent managed updates reopen NewzDeck.** The installer distinguishes About & Updates `/SILENT /update` from CI's `/VERYSILENT /update` smoke path, allowing the managed update to relaunch NewzDeck without causing CI smoke installs to launch the desktop application.
- **No copied update coordinator returns.** The Defender-sensitive v3.6.91 `NewzDeckUpdateHandoff-*.exe` architecture remains retired. The verified Setup executable itself owns the update transaction.
- **Publisher Pages monitoring is corrected.** The guarded publisher watches the Pages deployment for the final trigger commit, so a source-commit Pages run cancelled as superseded cannot falsely mark an otherwise successful release as failed.

## Preserved

- In-process SABCTools 9.6.3 built from upstream commit `54d7663b9e8f527b5ab196d43f0d5c561a87c1ac`.
- Private SABnzbd 5.1.2, Direct Unpack, PAR2/repair, article cache, async disk, queue behavior, Automation, Smart Import, Newsgroup Browser, Backup & Restore, and all twelve themes.
- The retired standalone `NewzDeckYenc.exe` remains absent from new payloads.
- Existing settings, providers, queues, libraries, history, and user data remain under the version-independent NewzDeck user-data directory.

Metadata Server remains v0.3.3 and Diagnostic Collector remains v1.0.31.
