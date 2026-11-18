# NewzDeck v3.7.34 — Windows CI Recovery & Path-Identity Regression Correction

## Release purpose

v3.7.33 successfully created an immutable annotated source tag and trigger-only main commit, but Windows workflow [44407238050](https://github.com/newzdeckadmin/NewzDeck/actions/runs/44407238050) stopped at `validate-v3733-flat-output.py`, before any Windows installers were built. No v3.7.33 GitHub Release assets were published. Preserve that tag and its history without moving/reusing it.

## Correction

The SAB finalization regression checked `slot['storage'] == str(root)` even though the SAB adapter legitimately resolves the directory path. On Windows, a junction or short-name alias can refer to the same directory using different strings. The regression now uses `Path(slot['storage']).samefile(root)` to verify the actual output directory, plus a separate assertion that the durable state-saving steps occurred. No production finalizer logic was changed for this issue.

## Preserved behavior

- **Extract into a subfolder checked:** existing download/extraction folder behavior remains unchanged.
- **Unchecked + Organization One folder:** verified completed non-Automation NZB files are finalized into the download root, preserving temporary staging and crash-safe no-clobber recovery.
- Distinct manual TV episode/season-pack Grabs retain separate asynchronous identities with same-target deduplication.
- Smart Import, queue/history integrity, SABnzbd 5.1.3, SABCTools 9.6.3, provider settings, existing downloads, library and history remain protected.
- Metadata Server v0.3.3 and Diagnostic Collector v1.0.31 are unchanged.

## Release engineering

Target version 3.7.34 uses the same three-part tag/source/trigger Windows workflow. The guarded publisher pins the actual v3.7.33 annotated tag/source and failed trigger-only main, validates genuine canonical-LF conversion under both Git for Windows line-ending configurations, runs the v3.7.34-only full version gate and inherited targeted regressions, then permits publication only after separate owner approval.

A local Python test pass is not a successful Windows installer build. Run the canonical GitHub Windows job and independently confirm both installer/Portable artifacts and checksums.
