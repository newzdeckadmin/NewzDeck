# License Scope

Unless a file or third-party notice states otherwise, original NewzDeck source code in this repository is licensed under **GNU GPL v3.0 only (GPL-3.0-only)**.

The root `LICENSE` file contains the complete license text.

## Exclusions

The NewzDeck GPL license does **not** relicense:

- third-party software downloaded or invoked by NewzDeck;
- third-party trademarks, logos, artwork, metadata, or API-provided content;
- operating-system components;
- material that carries its own license notice.

See `THIRD_PARTY_NOTICES.md` and `licenses/`.

## Release history

### v3.5.32 — licensing/source transition

The v3.5.32 public Windows binaries predate the complete public source tree. The source published for that historical release is complete for the Python/JavaScript application and v3.5.32 outer launcher, but not for every legacy helper executable carried into the v3.5.32 binary package. The project therefore does not rewrite history by describing v3.5.32 as a complete corresponding-source binary distribution.

### v3.5.33 — source-complete build foundation

The v3.5.33 source tree contains the buildable source for every NewzDeck-owned Windows executable shipped by v3.5.33. `NewzDeckBootstrap.exe` and `NewzDeckCore.exe` are retired rather than carried forward. The public build pipeline compiles all six current NewzDeck-owned Windows executables from this source tree and packages the Python/JavaScript source with the binary distribution.

Third-party components continue to retain their own licenses and source/distribution obligations as documented in `THIRD_PARTY_NOTICES.md`.
