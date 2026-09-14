# Building NewzDeck for Windows

> **Just want to use NewzDeck?** Download the latest Windows Installer or Portable ZIP from the [Releases page](https://github.com/newzdeckadmin/NewzDeck/releases/latest).

This directory contains the Windows packaging, smoke-test, and regression-gate source used by the official NewzDeck release pipeline.

## Authoritative production release model

NewzDeck has one authoritative production Windows publication path: `.github/workflows/publish-release-trigger.yml`.

A reviewed release first creates an immutable production-source commit and annotated `vX.Y.Z` tag. A separate trigger-only commit then adds `.release-trigger/X.Y.Z`. That trigger commit starts the canonical workflow, which verifies that its parent is the declared source commit before any release artifact is published.

The former manually-dispatched duplicate `windows-release.yml` workflow was retired in v3.7.0 to prevent two build/release implementations from drifting apart.

## Produced artifacts

The canonical workflow produces:

- `NewzDeck_vX.Y.Z_Portable.zip`
- `NewzDeck_vX.Y.Z_Setup.exe`
- `NewzDeck_vX.Y.Z_SHA256.txt`

The Portable build compiles all five NewzDeck-owned Windows executables from the Go source under `src/windows/` and packages the application source/static files from `src/app/`. The installer is built from that validated Portable payload.

## Canonical toolchain

The production workflow pins:

- Python 3.12.10
- Go 1.23.2
- Windows x64 (`GOOS=windows`, `GOARCH=amd64`, `CGO_ENABLED=0`)
- Inno Setup 7.1.0 x64

The workflow verifies the Inno Setup installer download by SHA-256 and Authenticode before using it. SABCTools 9.6.3 is built from the pinned upstream commit for CPython 3.12.10, validated for yEnc/CRC behavior, and vendored into the release payload; the retired standalone NewzDeckYenc.exe is not built or shipped.

## Release validation

Before publication, the production workflow:

1. proves the trigger/source topology and version identities;
2. runs the complete carried-forward regression chain plus the current release guard;
3. compiles the Python, JavaScript, and protected Go source;
4. builds and validates the Portable ZIP and its source manifest;
5. builds the Setup EXE from that exact payload;
6. verifies release checksums;
7. performs clean-install and installed-upgrade smoke tests, including service/tray restoration and locked native-helper replacement;
8. publishes the GitHub Release only after all gates pass.

For local/source work, `build-portable.py` remains the canonical source-to-Portable builder. Local builds are useful for development but are not a substitute for the pinned production release gate.

## Installer behavior

The normal installer:

- installs per-user under `%LOCALAPPDATA%\Programs\NewzDeck`;
- preserves persistent data under `%LOCALAPPDATA%\NewzDeck`;
- upgrades over an existing installation;
- closes the NewzDeck tray companion and protected native helpers before replacing locked files;
- repairs/restores an existing NewzDeck background service when necessary;
- keeps the NewzDeck application icon for the installed app and shortcuts;
- does not add Defender exclusions;
- remains intentionally unsigned.

## Source and licenses

NewzDeck-owned source is GPL-3.0-only unless a file says otherwise. Third-party software retains its own license.

See the repository root `LICENSE`, `THIRD_PARTY_NOTICES.md`, and `licenses/` directory.
