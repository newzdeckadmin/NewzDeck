# NewzDeck v3.5.34 — Reliability & Release Hardening

v3.5.34 is a focused reliability release built on the source-complete v3.5.33
baseline. It preserves the proven SAB transfer and Automation/Smart Import data
paths while hardening edge cases discovered during a post-release audit.

## Highlights

- **Verified updater repaired:** NewzDeck now uses the official GitHub
  latest-release feed by default and recognizes the canonical versioned
  `Setup.exe` and SHA-256 assets.
- **Sleep/resume safety:** desktop heartbeat handling tolerates Windows suspend,
  resume, and browser timer throttling without incorrectly shutting down a live
  desktop backend.
- **Downloads snapshot ordering:** late polling responses can no longer overwrite
  newer state.
- **Completed history fixed:** Downloads → Completed is ordered by actual
  completion time, newest first. Existing SAB history is migrated by backfilling
  its real completion timestamps.
- **TMDB attribution repaired:** the bundled TMDB logo renders correctly and the
  required attribution text wraps cleanly.
- **Localhost hardening:** cross-site browser POSTs are rejected and unexpected
  backend exceptions no longer expose raw OS/socket details to the UI.
- **Watch Folder fairness:** large Watch Folders rotate beyond the first 100 NZBs
  instead of allowing early stuck files to starve later entries.
- **Production package cleanup:** acceptance-only files are excluded and
  `start.bat` routes through `NewzDeck.exe`.

## Compatibility

- SABnzbd transfer/post-processing behavior is unchanged.
- Automation and Smart Import behavior from the accepted v3.5.33 baseline is
  preserved.
- Metadata Server **v0.3.3** remains the matching server baseline.
- Existing user data under `%LOCALAPPDATA%\NewzDeck` is preserved.

## Source and integrity

All NewzDeck-owned Windows executables are rebuilt from the public GPLv3 source
tag by GitHub Actions. The release contains the Setup EXE, Portable ZIP, and a
SHA-256 checksum file.

NewzDeck is intentionally unsigned. Windows SmartScreen may display an
**Unknown Publisher** warning.
