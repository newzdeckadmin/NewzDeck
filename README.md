# NewzDeck

NewzDeck is a Windows Usenet newsreader, downloader, and personal media automation application.

**Current production release:** v3.5.33
**Source status:** Source-complete Windows release

**Project website:** https://www.newzdeck.com
**Windows releases:** https://github.com/newzdeckadmin/NewzDeck/releases

## License

NewzDeck source code published in this repository is licensed under the **GNU General Public License v3.0 only (GPL-3.0-only)** unless a file or third-party notice says otherwise. See [LICENSE](LICENSE).

Third-party software, services, data, logos, and other assets retain their own licenses and terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Source publication status

v3.5.32 remains the documented transition release: its Python/JavaScript application source and desktop launcher source are public, but several legacy NewzDeck-owned helper executables in that historical binary package were carried forward from the earlier binary-first development period.

The **v3.5.33 release closes that gap**. Every NewzDeck-owned executable shipped by the v3.5.33 Windows Portable/Setup package is built from public source in this repository. The old `NewzDeckBootstrap.exe` and `NewzDeckCore.exe` compatibility binaries are retired and are not part of v3.5.33.

See [docs/SOURCE_RELEASES.md](docs/SOURCE_RELEASES.md) for the release-by-release source map.

## Source tree

- `src/app/` — backend, SAB adapter, media automation engine, browser UI, and application manifests.
- `src/windows/NewzDeckLauncher.go` — desktop launcher and first-run private CPython provisioning.
- `src/windows/NewzDeckService.go` — Windows Service wrapper/maintenance helper.
- `src/windows/NewzDeckTray.go` — notification-area companion.
- `src/windows/NewzDeckPicker.go` — native Windows folder chooser/taskbar helper.
- `src/windows/NewzDeckThumb.go` — native thumbnail helper.
- `src/windows/NewzDeckYenc.go` — native yEnc decoder helper.
- `src/assets/` — NewzDeck-owned build artwork.
- `release/windows/build-portable.py` — deterministic public-source-to-Portable build.
- `release/windows/build-release.ps1` and `NewzDeck.iss` — conventional Windows installer/checksum build.
- `.github/workflows/windows-release.yml` — GitHub Actions source-build, draft-validation, and exact-asset publication pipeline.
- `source-releases/` — per-release source status/manifests.
- `licenses/` — preserved third-party license texts/notices used by distributed build outputs.

## Reproducible Windows release model

Starting with v3.5.33, GitHub Actions builds the Portable ZIP directly from the tagged public source rather than accepting an externally prepared Portable ZIP as the primary build input.

The canonical Windows build uses:

- Python 3.12.10 for source validation/packaging;
- Go 1.23.2, `GOOS=windows`, `GOARCH=amd64`, `CGO_ENABLED=0` for every NewzDeck-owned EXE;
- Inno Setup 7.1.0 x64, downloaded from the official upstream release and verified by SHA-256 plus Authenticode before installer compilation.

The validation run stages **the exact built Portable ZIP, Setup EXE, and SHA-256 file on a draft GitHub Release**. The publish run does not rebuild them; it verifies and publishes those exact tested draft assets, while also requiring the draft to remain pinned to the source commit that produced them.

The final published v3.5.33 Windows Portable ZIP has SHA-256:

`a2e7ec5a79904f40e5fb0b864ee420c002b591e01aa64b840b58b026eed90935`

The final r5 acceptance Portable used during pre-publication validation had SHA-256:

`6b96d0cd8ea92a29e5178d33eea1208de0309c70cf0b3e6e04d40ebf65cc2e39`

The r5 hash is retained as historical acceptance provenance. The published hash above is the integrity value for the v3.5.33 Portable asset currently distributed from GitHub.

See [docs/RELEASE_COMPLIANCE.md](docs/RELEASE_COMPLIANCE.md).

## Third-party architecture

NewzDeck can provision or interoperate with independent third-party components including CPython, SABnzbd, UnRAR, par2cmdline-turbo, and optionally 7-Zip. These components are not relicensed as NewzDeck. The v3.5.33 Portable/Setup package does not embed CPython, SABnzbd, UnRAR, or par2cmdline-turbo; NewzDeck obtains them separately from their upstream publishers when needed.

NewzDeck's Go-built Windows executables statically contain portions of the Go runtime and standard library, which are BSD-licensed. The required Go license notice is distributed with the binary package.

## Security and credentials

Do not commit provider usernames/passwords, Newznab API keys, TMDB credentials, SAB API credentials, installation credentials, or user data. Runtime configuration belongs under NewzDeck's per-user data directory and is intentionally outside this repository.

## Project status

NewzDeck is under active development. v3.5.33 is the first source-complete Windows production release and completes the transition from the earlier binary-first development model. The source-built GitHub Actions validation/publish pipeline established for v3.5.33 is the release model for subsequent Windows releases.
