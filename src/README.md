# NewzDeck Source Tree

This directory is NewzDeck's public source-first application tree.

For v3.5.33:

- `app/` contains the Python backend, SAB adapter, media Automation engine, browser UI, and application manifests shipped in the Portable/Setup package.
- `windows/NewzDeckLauncher.go` builds `NewzDeck.exe`.
- `windows/NewzDeckService.go` builds `NewzDeckService.exe`.
- `windows/NewzDeckTray.go` builds `NewzDeckTray.exe`.
- `windows/NewzDeckPicker.go` builds `NewzDeckPicker.exe`.
- `windows/NewzDeckThumb.go` builds `NewzDeckThumb.exe`.
- `windows/NewzDeckYenc.go` builds `NewzDeckYenc.exe`.
- `assets/` contains NewzDeck-owned build artwork.

The legacy `NewzDeckBootstrap.exe` and `NewzDeckCore.exe` compatibility binaries are retired in v3.5.33 and are not shipped.

The canonical source-to-Portable build is `../release/windows/build-portable.py`. See `../docs/SOURCE_RELEASES.md` and `../docs/RELEASE_COMPLIANCE.md` for the source-complete/release gate.
