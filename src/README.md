# NewzDeck Source Tree

This directory is NewzDeck's public source-first application tree.

- `app/` contains the Python backend, SAB adapter, media Automation engine, browser UI, and application manifests shipped in the Portable/Setup package.
- `windows/NewzDeckLauncher.go` builds `NewzDeck.exe`.
- `windows/NewzDeckService.go` builds `NewzDeckService.exe`.
- `windows/NewzDeckTray.go` builds `NewzDeckTray.exe`.
- `windows/NewzDeckPicker.go` builds `NewzDeckPicker.exe`.
- `windows/NewzDeckThumb.go` builds `NewzDeckThumb.exe`.
- `windows/NewzDeckYenc.go` builds `NewzDeckYenc.exe`.
- `assets/` contains NewzDeck-owned build artwork.

The retired `NewzDeckBootstrap.exe` and `NewzDeckCore.exe` compatibility binaries are not part of the current product.

The canonical source-to-Portable builder is `../release/windows/build-portable.py`. The authoritative production Windows release pipeline is `../.github/workflows/publish-release-trigger.yml`, which validates the public source, builds the release artifacts, runs the protected upgrade/runtime gates, and publishes the GitHub Release after a dedicated `.release-trigger/<version>` commit.

See `../docs/SOURCE_RELEASES.md` for source-publication history and release provenance, and `../release/windows/README.md` for Windows build details.
