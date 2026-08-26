# NewzDeck

NewzDeck is a Windows Usenet newsreader, downloader, and personal media automation application.

**Current production release:** v3.5.32  
**Project website:** https://www.newzdeck.com  
**Windows releases:** https://github.com/newzdeckadmin/NewzDeck/releases

## License

NewzDeck source code published in this repository is licensed under the **GNU General Public License v3.0 only (GPL-3.0-only)** unless a file or third-party notice says otherwise. See [LICENSE](LICENSE).

Third-party software, services, data, logos, and other assets retain their own licenses and terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Source publication status

NewzDeck is transitioning from binary-first development to a source-first, reproducible release model.

The repository now contains the complete Python/JavaScript application source shipped in v3.5.32 and the exact Go source for the v3.5.32 outer desktop launcher. However, several legacy NewzDeck-owned helper executables carried forward unchanged into v3.5.32 were built before a complete public source tree was established. Their reconstructable source is not yet present here.

For that reason, **v3.5.32 should be treated as the transition release, not as a complete corresponding-source GPL binary release**. Future production releases will not be described as source-complete until every NewzDeck-owned executable in the Windows package maps to published source and a documented build path.

See [docs/SOURCE_RELEASES.md](docs/SOURCE_RELEASES.md) for the exact v3.5.32 source map and the rules for future releases.

## What is in the source tree

- `src/app/` — NewzDeck backend, SAB adapter, media automation engine, and browser UI.
- `src/windows/NewzDeckLauncher.go` — exact v3.5.32 fast desktop launcher source.
- `src/assets/` — NewzDeck-owned application artwork used by the Windows build.
- `release/windows/` — GitHub/Inno Setup Windows release automation already maintained in this repository.
- `source-releases/` — per-release source-status manifests.
- `licenses/` — license texts/notices for third-party components that are incorporated into build outputs or are useful to preserve with the project.

## Third-party architecture

NewzDeck can provision or interoperate with independent third-party components, including CPython, SABnzbd, UnRAR, par2cmdline-turbo, and optionally 7-Zip. These components are not relicensed as NewzDeck. The v3.5.32 release downloads CPython, SABnzbd, UnRAR, and par2cmdline-turbo separately on the user's machine rather than embedding them in the NewzDeck Portable ZIP.

NewzDeck's Go-built Windows executables statically contain portions of the Go runtime and standard library, which are BSD-licensed. The required Go license notice is included under `licenses/` and should be carried into future binary packages.

## Building and releases

The current public GitHub Actions workflow builds the Windows installer from a tested Portable ZIP. That workflow is intentionally a distribution pipeline, not yet a full source-to-binary build pipeline.

The source-first release target is documented in [docs/RELEASE_COMPLIANCE.md](docs/RELEASE_COMPLIANCE.md). A future release is considered source-complete only when its tagged source can rebuild every NewzDeck-owned executable and the shipped source/license notices match the binary package.

## Security and credentials

Do not commit provider usernames/passwords, Newznab API keys, TMDB credentials, SAB API credentials, installation credentials, or user data. Runtime configuration belongs under NewzDeck's per-user data directory and is intentionally outside this repository.

## Project status

NewzDeck is under active development. Bug reports and source contributions are welcome as the public source tree is completed and stabilized.
