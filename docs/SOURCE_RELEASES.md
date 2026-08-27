# Source Releases

This document records NewzDeck's transition from binary-first development to a source-first Windows release model and defines what "source-complete" means for NewzDeck.

## v3.5.32 — transition source map

| Shipped component | Public source status | Repository path |
| --- | --- | --- |
| `server.py` | Complete | `src/app/server.py` historical v3.5.32 snapshot |
| `sab_engine.py` | Complete | `src/app/sab_engine.py` historical v3.5.32 snapshot |
| `automation_engine.py` | Complete | `src/app/automation_engine.py` historical v3.5.32 snapshot |
| browser UI | Complete | `src/app/static/` historical v3.5.32 snapshot |
| `NewzDeck.exe` | Complete for v3.5.32 | historical `src/windows/NewzDeckLauncher.go` |
| `NewzDeckBootstrap.exe` | Legacy source gap | Not reconstructed for the historical binary |
| `NewzDeckCore.exe` | Legacy source gap | Not reconstructed for the historical binary |
| `NewzDeckService.exe` | Legacy source gap | Not reconstructed for the historical binary |
| `NewzDeckTray.exe` | Legacy source gap | Not reconstructed for the historical binary |
| `NewzDeckPicker.exe` | Legacy source gap | Not reconstructed for the historical binary |
| `NewzDeckThumb.exe` | Legacy source gap | Not reconstructed for the historical binary |
| `NewzDeckYenc.exe` | Legacy source gap | Not reconstructed for the historical binary |

Those helpers were carried forward from the pre-source-publication baseline. v3.5.32 remains explicitly documented as a **transition release**, not retroactively described as source-complete.

## v3.5.33 — first source-complete Windows release

v3.5.33 removes the legacy Bootstrap/Core compatibility layer and ships six NewzDeck-owned Windows executables, all built directly from public Go source:

| Shipped component | Public source | Build path |
| --- | --- | --- |
| `NewzDeck.exe` | `src/windows/NewzDeckLauncher.go` | Go 1.23.2 Windows/amd64 |
| `NewzDeckService.exe` | `src/windows/NewzDeckService.go` | Go 1.23.2 Windows/amd64 |
| `NewzDeckTray.exe` | `src/windows/NewzDeckTray.go` | Go 1.23.2 Windows/amd64 |
| `NewzDeckPicker.exe` | `src/windows/NewzDeckPicker.go` | Go 1.23.2 Windows/amd64 |
| `NewzDeckThumb.exe` | `src/windows/NewzDeckThumb.go` | Go 1.23.2 Windows/amd64 |
| `NewzDeckYenc.exe` | `src/windows/NewzDeckYenc.go` | Go 1.23.2 Windows/amd64 |
| Python backend/SAB/Automation | `src/app/*.py` | Packaged as source |
| browser UI | `src/app/static/` | Packaged as source/static assets |

The canonical build is `release/windows/build-portable.py`. It validates the application source, compiles each Windows executable with `GOOS=windows`, `GOARCH=amd64`, `CGO_ENABLED=0`, generates `SOURCE_MANIFEST.json`, includes the GPL and third-party notices, and writes a deterministic Portable ZIP with fixed archive timestamps and ordering.

`release/windows/build-release.ps1` then uses that exact source-built Portable payload to compile the conventional Inno Setup package.

## Source-complete release rule

A Windows release may be labeled source-complete only when all of the following are true:

1. Every NewzDeck-owned executable in the Portable ZIP maps to public source in the tagged repository.
2. Build scripts and canonical toolchain versions are public and documented.
3. A clean build from the tag does not depend on an unpublished prior NewzDeck binary.
4. The Portable ZIP/installer includes the NewzDeck GPL license and required third-party binary notices.
5. The exact source tag/archive is public alongside the binaries.
6. No secrets, credentials, user data, or private API keys are present in the published tree.
7. The Windows acceptance build is tested before the same exact draft assets are published.

## Exact-asset release staging

Starting with v3.5.33, the GitHub Actions validation run builds from source and uploads all three Windows artifacts to a **draft** GitHub Release. The release is pinned to the exact source commit that produced them. The publish run verifies the draft checksums, Portable source manifest, version, retired-binary exclusions, accepted Portable hash when supplied, and source-commit pin before changing the draft to public. It does not rebuild the assets during publication.

v3.5.33 completed this transition and is the first production Windows release under the source-complete model. v3.5.32 remains documented historically as the transition release and is not retroactively relabeled.

## v3.5.34 — Reliability & Release Hardening

v3.5.34 is the first normal production follow-on to the v3.5.33 source-complete
transition. It keeps the six-source-built-Windows-binary model and changes the
application layer only: updater compatibility, suspend/resume lifecycle
hardening, Downloads snapshot ordering, Completed-history migration/sorting,
TMDB attribution, localhost request hardening, Watch Folder fairness, and
production-package cleanup.

The final v3.5.34 Windows assets are rebuilt from the public `v3.5.34` tag by
the same deterministic GitHub Actions pipeline established in v3.5.33.
