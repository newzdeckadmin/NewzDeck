# NewzDeck v3.7.28 — Windows Release Validation Recovery

## Why this release is necessary

The v3.7.27 source tag was created and the trigger committed to main, but Windows workflow run 42519884334 failed in the source validation step. The correct v3.7.27 regression gate passed; an obsolete v3.7.26 full release gate then asserted that `src/app/version.txt` was `3.7.26`. Since that file correctly contained `3.7.27`, the CI run stopped before building the installer. GitHub Pages succeeded; no v3.7.27 Windows release assets were published.

v3.7.28 is a **non-destructive, versioned recovery**. The existing annotated v3.7.27 tag and commit are left immutable. No force push, tag movement or unverified manual release is performed.

## Changes

- Remove execution of `release/windows/validate-v3726-regressions.py` (version-specific 3.7.26 identity assertion) from the current CI workflow. It remains in historical source history.
- Replace `release/windows/validate-v3727-regressions.py` execution with `release/windows/validate-v3728-regressions.py`, which verifies the current v3.7.28 identity and preserved v3.7.27 functionality.
- Continue running the targeted v3.7.26 search engine and early-filter regressions, v3.7.27 download pulse/backend tests, JavaScript simulations, v3.7.25 Image Sets ON/OFF, yEnc, filename, preview and download safety regressions.
- Update v3.7.28 runtime version strings, website, Windows tray, build manifest and documented release identity.

## Unchanged

No functional modifications to NNTP scanner, SABnzbd engine, downloads queue processing, Image Sets, Diagnostics, saved data, existing history, or settings. All v3.7.27 improvements are retained.

## Release safety

The guarded publisher requires the exact currently failed v3.7.27 source tag `b41715ae99880413e92c3bbf141cb1a31b03a10f`, main trigger commit `78a2e903174d2e3288518ebde4a78fbfbe10bcf6`, and latest successful GitHub release v3.7.26. Publication uses an independent v3.7.28 source commit, annotated v3.7.28 tag and one-file trigger commit. It refuses if any of these baseline requirements change.

Windows installer, Portable ZIP, smoke testing, GitHub Pages and release assets are performed by the canonical GitHub Actions Windows workflow after the guarded publisher is run, not by this ZIP.
