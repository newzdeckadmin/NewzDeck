# NewzDeck v3.7.0 — Production Milestone & Repository Hygiene

NewzDeck v3.7.0 promotes the proven v3.6.99 application to the 3.7 production milestone.

This release is intentionally conservative: the installed application's feature set and runtime behavior are preserved from v3.6.99 while the public repository, release workflow, and source/build documentation are cleaned up so 3.7 starts from one clear production baseline.

## Production milestone

- **Backup & Restore remains intact:** v3.6.99 Configuration Backup, password-encrypted Complete Backup, transactional restore, pre-restore safety snapshots, legacy compatibility, and cross-PC path safety are unchanged.
- **Automation sorting remains intact:** v3.6.96 A/An/The-aware TV and Movie library sorting is unchanged and displayed titles are never renamed.
- **Themes remain intact:** all twelve themes and the Light/Arctic/Sandstone readability corrections are unchanged.
- **Runtime behavior remains intact:** Newsgroup Browser, Downloads, Smart Import, Automation search/grab/import behavior, private SABnzbd 5.1.2, Metadata Server v0.3.3, and Diagnostic Collector v1.0.31 are unchanged.
- **Defender-clean native/update architecture remains intact:** folder-only Picker, accepted yEnc build profile, checksum-verified Setup updater, launcher-owned browser close, and installer-owned runtime restoration are unchanged.

## Repository hygiene

- **Single authoritative production workflow:** the obsolete duplicate `.github/workflows/windows-release.yml` manual workflow is removed. `.github/workflows/publish-release-trigger.yml` is the only production Windows publication workflow and continues to run the complete protected regression/build/smoke-test gate.
- **Current Windows build documentation:** `release/windows/README.md` now documents the trigger/source topology, pinned toolchain, protected yEnc build, and canonical production release process instead of directing contributors to the retired manual workflow.
- **Current source-tree documentation:** `src/README.md` is version-independent, no longer describes the current tree as “For v3.5.33,” and no longer links to the nonexistent `docs/RELEASE_COMPLIANCE.md`.
- **Version-neutral third-party notices:** `THIRD_PARTY_NOTICES.md` keeps the same current component versions and license references while removing stale v3.6.93-specific wording.
- **Historical provenance retained:** historical release notes, `.release-trigger` records, regression guards, `source-releases/`, licensing records, and source-release history remain in the repository because they are active provenance or release-safety records rather than redundant files.

## Release gate

The v3.7.0 regression guard verifies that the installed-app behavior remains on the v3.6.99 baseline except for required version/cache identity, that styles/themes and protected native/update sources are unchanged, that the obsolete duplicate workflow is absent, that source/build/licensing documentation has been cleaned up, and that the canonical workflow runs the full historical chain plus the v3.7.0 guard.
