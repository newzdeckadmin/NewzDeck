# NewzDeck v3.7.4 - Release Hygiene & Publisher Reliability Maintenance

v3.7.4 is a narrow maintenance release built on the proven v3.7.3 runtime. It cleans up stale release-facing version text and corrects the guarded publisher checks that falsely reported failures after otherwise successful v3.7.3 publication.

## Fixed

- **Runtime-facing version fallbacks are coherent.** The browser shell cache-buster/sidebar fallback, Automation engine default-version fallback, and tray helper's no-argument version fallback now identify v3.7.4 instead of retaining v3.7.0 text.
- **SABCTools decoder wording is version-neutral.** Current yEnc adapter/server documentation no longer describes the active SABCTools 9.6.3 integration as specifically belonging to v3.7.1.
- **Publisher Pages monitoring follows the content/source commit.** The guarded publisher now watches GitHub Pages for the actual source/content commit instead of incorrectly requiring a Pages deployment on the later trigger-only commit.
- **Superseded Pages runs are tolerated correctly.** An older cancelled Pages run no longer marks publication failed when a newer run for the same source commit succeeds.
- **Release topology verification uses the immutable annotated tag.** Final publication verification peels `refs/tags/v3.7.4` to the source commit rather than treating GitHub Release `target_commitish` (which may legitimately be `main`) as the immutable source identity.
- **Publisher diagnostics are current.** Stale v3.7.2/v3.7.3 publisher labels and failure messages are replaced with v3.7.4/current-release wording.

## Preserved

- The v3.7.3 managed About & Updates lifecycle and verified Setup handoff remain unchanged.
- In-process SABCTools 9.6.3 remains pinned to upstream commit `54d7663b9e8f527b5ab196d43f0d5c561a87c1ac`.
- Private SABnzbd 5.1.2, Direct Unpack, PAR2/repair, article cache, async disk, queue behavior, Automation, Smart Import, Newsgroup Browser, Backup & Restore, and all twelve themes are unchanged.
- The retired standalone `NewzDeckYenc.exe` remains absent from new payloads.
- Existing settings, providers, queues, libraries, history, backups, and user data remain under the version-independent NewzDeck user-data directory.

Metadata Server remains v0.3.3 and Diagnostic Collector remains v1.0.31.
