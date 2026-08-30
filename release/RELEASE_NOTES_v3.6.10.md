# NewzDeck v3.6.10 - Python Source Freshness & Runtime Refresh

NewzDeck v3.6.10 is a focused runtime-freshness hotfix built on v3.6.9. It fixes an upgrade case where the UI/backend could be current while the built-in SAB adapter still reported an older NewzDeck version because a deterministic timestamp-based Python bytecode cache survived the in-place update.

## Runtime freshness

- **Source-byte module loading** - `sab_engine.py` and `automation_engine.py` are now read and compiled from the installed source bytes on every backend start instead of being executed through timestamp-based adjacent `.pyc` validation.
- **App bytecode cache purge** - the backend removes the application-level `__pycache__` before loading NewzDeck-owned sibling modules and disables adjacent bytecode writes for the app source runtime.
- **Installer cleanup** - installed upgrades delete `{app}\__pycache__` before the new application files are used.
- **Release guards** - both Windows workflows require the source-byte loader and bytecode cleanup markers before a release can build.
- **Deterministic packaging preserved** - reproducible/fixed archive timestamps remain intact without allowing those timestamps to select stale NewzDeck code.

## Preserved

- v3.6.9 In-App Update Runtime Handoff, including stale Picker/native-helper shutdown and its installed-upgrade regression coverage.
- v3.6.8 Image Browsing Performance & Gallery Quality, including WIC-first persistent thumbnails, multipart acceleration, RAM caches, tiny-image suppression, and rendering hot-path optimizations.
- Private SAB downloads, Smart Import, Automation, Discover/TMDB, provider behavior, and Metadata Server v0.3.3 compatibility.

## Upgrade notes

You may install v3.6.10 directly over v3.6.9. The installer removes stale NewzDeck application bytecode, and the new backend always loads the SAB/Automation adapter from the current source. Queue and user state remain preserved.
