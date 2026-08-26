# NewzDeck Windows release process

This directory contains the release-only automation for the conventional unsigned NewzDeck Windows installer. It does not build or change NewzDeck runtime code, the Metadata Server, or the GitHub Pages website.

## Why the workflow starts from a draft release

The public repository currently does not contain the compiled NewzDeck application payload. To avoid committing large generated binaries or inventing a new runtime build system, the GitHub Actions workflow takes the already-tested Portable ZIP as its trusted input.

For each release, the maintainer uploads that tested Portable ZIP to a **draft GitHub Release**. GitHub Actions verifies its SHA-256, extracts and validates it, builds the installer from that exact payload, generates checksums, and can then publish the draft.

End users never run `BUILD_INSTALLER.bat`, install Inno Setup, or compile anything.

## Preserved installer behavior

The version-driven `NewzDeck.iss` is based directly on the installer that was successfully tested with NewzDeck v3.5.31.

It preserves:

- Stable Inno product identity: `{A84C814C-704C-4C7D-A20B-BA5DD83F9429}`
- Per-user install under `%LOCALAPPDATA%\Programs\NewzDeck`
- Persistent data under `%LOCALAPPDATA%\NewzDeck`
- Native x64 Inno Setup 7 installer
- Windows 10 minimum
- Overlay upgrades without purging generated/private runtime files
- Existing `NewzDeckService` stop/repair behavior during upgrades
- No automatic service enablement on a fresh install
- Existing `NewzDeckTray` autostart migration to the new installed version
- Safe service removal and tray-autostart cleanup during uninstall
- Uninstall cancellation if Windows cannot remove an existing registered service
- Start Menu shortcut and optional Desktop shortcut
- The real NewzDeck icon
- Installer foreground/stay-on-top behavior
- No automatic post-install NewzDeck launch; the user starts NewzDeck normally after Setup fully exits, avoiding the same-version reinstall startup race found during v3.5.31 validation
- No deletion of `%LOCALAPPDATA%\NewzDeck`
- No Defender exclusions, PowerShell security exclusions, signing, or custom SFX launcher

There is no `NewzDeck.Integration.exe`; the proven installer uses `NewzDeckService.exe` plus Inno `[Code]` for service/tray integration.

## Publish a release

1. Produce and test the NewzDeck Portable ZIP.
2. Calculate its SHA-256.
3. In GitHub, create a **draft release** with tag `vX.Y.Z`.
4. Attach the tested portable file using the exact name:

   `NewzDeck_vX.Y.Z_Portable.zip`

5. Leave the release as a draft.
6. Open **Actions → Build Windows release → Run workflow**.
7. Enter:
   - `version`: `X.Y.Z`
   - `portable_sha256`: the SHA-256 of the tested Portable ZIP
   - `publish`: leave **false** for a validation-only run, or select **true** to publish after a successful build
8. GitHub Actions downloads the draft asset, verifies it, builds with the official Inno Setup 7.1.0 x64 compiler, and produces:

   - `NewzDeck_vX.Y.Z_Setup.exe`
   - `NewzDeck_vX.Y.Z_Portable.zip`
   - `NewzDeck_vX.Y.Z_SHA256.txt`

Every run also stores the three outputs as a temporary GitHub Actions artifact for validation. With `publish=true`, the installer and checksum file are attached to the draft release and the release is published. The original tested Portable ZIP remains the public portable asset.

## Required portable payload

The portable ZIP must contain the normal tested NewzDeck payload at its root, including at least:

- `version.txt`
- `NewzDeck.exe`
- `NewzDeck.ico`
- `NewzDeckBootstrap.exe`
- `NewzDeckCore.exe`
- `NewzDeckService.exe`
- `NewzDeckTray.exe`
- `NewzDeckPicker.exe`
- `NewzDeckThumb.exe`
- `NewzDeckYenc.exe`
- `server.py`
- `sab_engine.py`
- `automation_engine.py`
- `static/index.html`
- `static/app.js`
- `static/styles.css`

The payload version must exactly match the requested release version.

## Inno Setup toolchain

The workflow downloads the official immutable Inno Setup **7.1.0 x64** release from `jrsoftware/issrc`, verifies the published SHA-256 before running it, and requires a valid Authenticode signature on the Inno installer itself.

The workflow uses Node.js 24-native `actions/checkout@v6` and `actions/upload-artifact@v6` to avoid the GitHub Actions Node.js 20 deprecation warning.

NewzDeck's own installer remains intentionally unsigned.

## Website safety

This release infrastructure does not modify `CNAME` or `index.html`. GitHub Pages remains independent from the Windows release workflow.
