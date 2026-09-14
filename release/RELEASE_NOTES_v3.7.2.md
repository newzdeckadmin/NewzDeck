# NewzDeck v3.7.2 - Runtime Identity & Release Metadata Hotfix

v3.7.2 is a focused hotfix for the v3.7.1 native-decoder release. It preserves the proven SABCTools 9.6.3 decoder architecture and corrects release/runtime identity that was inconsistent in v3.7.1.

## Fixed

- **Download-engine version coherence:** `server.py`, `sab_engine.py`, `app.js`, `version.txt`, and `build-manifest.json` now all identify the same v3.7.2 runtime. This removes the false `background runtime is from a different version` warning caused by v3.7.1 shipping `ADAPTER_VERSION = "3.7.0"` in the otherwise-v3.7.1 payload.
- **Direct source identity:** the public `server.py` and `app.js` now contain the actual shipped runtime source instead of retaining v3.7.0 blobs and transforming them only during packaging. The current builder no longer invokes the v3.7.1 runtime transformer.
- **Release surfaces:** the GitHub README, website fallback release labels, update notes, Windows build documentation, and source/release history now advance with the current release.
- **Pages publication path:** the guarded publisher uses ordinary single-ref `main` pushes again, so GitHub's managed `pages build and deployment` workflow receives the same branch-push signal used by prior releases.
- **SABCTools notices:** bundled SABCTools 9.6.3 is documented explicitly as GPL-2.0-or-later and the GPL-2.0 license text is carried in `licenses/SABCTOOLS-LICENSE.md`.

## Preserved

- In-process SABCTools 9.6.3 built from upstream commit `54d7663b9e8f527b5ab196d43f0d5c561a87c1ac` for NewzDeck's CPython 3.12.10 runtime.
- The split NNTP fetch/decode pipeline and bulk-Python emergency yEnc fallback.
- Private SABnzbd 5.1.2, Direct Unpack, PAR2/repair, article cache, async disk pipeline, queue behavior, Background Service, tray companion, Automation, Smart Import, Newsgroup Browser, Backup & Restore, and all twelve themes.
- Removal of `NewzDeckYenc.exe` from new payloads plus upgrade cleanup of stale copies from older installations.

Metadata Server remains v0.3.3 and Diagnostic Collector remains v1.0.31; neither component changes in this hotfix.
