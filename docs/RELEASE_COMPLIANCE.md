# Release Compliance Checklist

Use this checklist for every source-complete production NewzDeck Windows release beginning with v3.5.33.

## Source

- [ ] Release version in `src/app/version.txt` matches the intended tag.
- [ ] Python/JavaScript source matches the release candidate tested on Windows.
- [ ] Every NewzDeck-owned Windows executable has corresponding public source.
- [ ] Every NewzDeck-owned EXE is rebuilt from the tagged source; no opaque previous-release helper is copied forward.
- [ ] Canonical build commands/toolchain versions are documented and pinned.
- [ ] Secret/credential scan passes.
- [ ] `SOURCE_MANIFEST.json` maps every shipped NewzDeck-owned EXE to source and hashes.

## Licensing

- [ ] Root source tree contains `LICENSE` (GPL-3.0-only).
- [ ] Binary package contains `LICENSE.txt`.
- [ ] Binary package contains current `THIRD_PARTY_NOTICES.txt`.
- [ ] Go BSD license is included with Go-built binaries.
- [ ] Inno Setup notice/license is preserved in repository distribution documentation.
- [ ] Third-party downloaded tools are identified by project/version/license/upstream source.
- [ ] Third-party trademarks/API data are not described as GPL-covered NewzDeck content.

## Source-built validation run

- [ ] Run **Build Windows release** with `publish=false`.
- [ ] GitHub Actions checks out the public source candidate.
- [ ] Python 3.12.10 source validation passes.
- [ ] Go 1.23.2 builds all NewzDeck Windows helpers for Windows/amd64 with CGO disabled.
- [ ] Source-built Portable ZIP integrity and source manifest validation pass.
- [ ] If an already accepted Portable hash exists, `expected_portable_sha256` matches exactly.
- [ ] Verified Inno Setup 7.1.0 x64 builds Setup.exe.
- [ ] Setup/Portable checksum file verifies.
- [ ] Workflow stages the exact three artifacts on a draft release pinned to `github.sha`.
- [ ] Actions validation artifact is retained for independent download/testing.

## Windows acceptance

- [ ] Install/upgrade Setup.exe on a real Windows system.
- [ ] Persistent `%LOCALAPPDATA%\NewzDeck` state is preserved.
- [ ] Background service remains stopped when it was stopped before upgrade.
- [ ] Desktop startup is fast and duplicate launches are suppressed.
- [ ] Download/queue/post-processing lifecycle works.
- [ ] Smart Import renames and moves Automation media correctly.
- [ ] A cutoff-satisfying import leaves Wanted and does not trigger duplicate grabs.
- [ ] Interactive Search Grab handles temporary control-channel resets without raw WinError toasts or duplicate queue submissions.
- [ ] Folder picker/taskbar/tray helpers work as expected.
- [ ] No runaway `engine.json.tmp-*` / `engine-identities.json.tmp-*` accumulation occurs.

## Publication

- [ ] Do not modify `main` between the successful validation build and publication.
- [ ] Run **Build Windows release** again with the same version, accepted hash, and `publish=true`.
- [ ] Publish job verifies the draft release is still pinned to the current exact source commit.
- [ ] Publish job downloads and validates the already-tested draft artifacts instead of rebuilding them.
- [ ] Public release contains exactly Setup EXE, Portable ZIP, and SHA-256 file.
- [ ] Source tag/archive is public for the exact source commit.
- [ ] Release notes identify GPLv3/source-complete status and unsigned Windows distribution.

## Historical v3.5.32 note

v3.5.32 predates this complete-source gate and remains explicitly documented as the licensing/source transition release. Its history is not rewritten to claim source completeness for legacy helper binaries whose historical build source is unavailable.
