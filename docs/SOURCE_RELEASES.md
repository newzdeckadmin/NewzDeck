# Source Releases

NewzDeck is moving to a source-first release model. This document defines what "source-complete" means for a NewzDeck Windows release.

## v3.5.32 source map

The v3.5.32 Portable/Setup payload contains NewzDeck-owned application code and helper executables.

| Shipped component | Public source status | Repository path |
| --- | --- | --- |
| `server.py` | Complete | `src/app/server.py` |
| `sab_engine.py` | Complete | `src/app/sab_engine.py` |
| `automation_engine.py` | Complete | `src/app/automation_engine.py` |
| `static/index.html` | Complete | `src/app/static/index.html` |
| `static/app.js` | Complete | `src/app/static/app.js` |
| `static/styles.css` | Complete | `src/app/static/styles.css` |
| `NewzDeck.exe` | Complete for v3.5.32 | `src/windows/NewzDeckLauncher.go` |
| `NewzDeckBootstrap.exe` | Legacy source gap | Not yet published/reconstructed |
| `NewzDeckCore.exe` | Legacy source gap | Not yet published/reconstructed |
| `NewzDeckService.exe` | Legacy source gap | Not yet published/reconstructed |
| `NewzDeckTray.exe` | Legacy source gap | Not yet published/reconstructed |
| `NewzDeckPicker.exe` | Legacy source gap | Not yet published/reconstructed |
| `NewzDeckThumb.exe` | Legacy source gap | Not yet published/reconstructed |
| `NewzDeckYenc.exe` | Legacy source gap | Not yet published/reconstructed |

The helper binaries above were carried forward byte-for-byte from the pre-source-publication v3.5.31 baseline when v3.5.32 was built. The v3.5.32 source snapshot must therefore be described as **partial corresponding source** rather than a complete rebuildable source release.

## Rule for future releases

A future Windows release may be labeled source-complete only when all of the following are true:

1. Every NewzDeck-owned executable in the Portable ZIP maps to a source file/directory in the tagged repository.
2. Build scripts/tool versions are documented and available.
3. A clean build from the tag can produce functionally equivalent binaries without relying on an unpublished prior NewzDeck binary.
4. The Portable ZIP/installer contains the NewzDeck GPL license and required third-party binary notices.
5. A source archive or Git tag for the exact release is publicly available alongside the binaries.
6. No secrets, credentials, user data, or private API keys are present in the published tree.

## Why the transition is explicit

Publishing a license file is not enough by itself to make a binary distribution source-complete. The project is documenting the gap rather than pretending legacy helper binaries have source that is not actually available in the repository.
