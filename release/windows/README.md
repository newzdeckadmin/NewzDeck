# Building NewzDeck for Windows

> **Just want to use NewzDeck?** You do not need anything in this folder. Download the latest Windows Installer or Portable ZIP from the [Releases page](https://github.com/newzdeckadmin/NewzDeck/releases/latest).

This directory contains the Windows packaging tools used to build the same type of artifacts distributed in official NewzDeck releases.

## Official build model

A Windows build starts from the public source tree and produces:

- `NewzDeck_vX.Y.Z_Portable.zip`
- `NewzDeck_vX.Y.Z_Setup.exe`
- `NewzDeck_vX.Y.Z_SHA256.txt`

The Portable build compiles all six NewzDeck-owned Windows executables from the Go source under `src/windows/` and packages the application source/static files from `src/app/`.

The installer is built from that exact Portable payload.

## Toolchain

The canonical Windows build uses:

- Python 3.12.10
- Go 1.23.2
- Windows x64 (`GOOS=windows`, `GOARCH=amd64`, `CGO_ENABLED=0`)
- Inno Setup 7.1.0 x64

The GitHub Actions workflow verifies the Inno Setup installer download by SHA-256 and Authenticode before using it.

## GitHub Actions

Use **Actions → Build Windows release artifacts → Run workflow** and enter the version from `src/app/version.txt`.

The workflow:

1. validates the public application source;
2. builds all six NewzDeck Windows executables from source;
3. builds and validates the Portable ZIP;
4. compiles the Setup EXE;
5. verifies the release checksums;
6. performs a clean-install and installed-upgrade smoke test, including the tray-lock/service-repair upgrade path;
7. uploads the three completed files as a GitHub Actions artifact.

The build workflow does **not** publish or replace a GitHub Release automatically. This keeps release publication separate from the build and acceptance test.

## Installer behavior

The normal installer:

- installs per-user under `%LOCALAPPDATA%\Programs\NewzDeck`;
- preserves persistent data under `%LOCALAPPDATA%\NewzDeck`;
- upgrades over an existing installation;
- closes the NewzDeck tray companion before replacing locked files;
- repairs an existing NewzDeck background service when necessary;
- keeps the same NewzDeck application icon for the installed app and shortcuts;
- does not add Defender exclusions;
- remains intentionally unsigned.

## Source and licenses

NewzDeck-owned source is GPL-3.0-only unless a file says otherwise. Third-party software retains its own license.

See the repository root `LICENSE`, `THIRD_PARTY_NOTICES.md`, and `licenses/` directory.
