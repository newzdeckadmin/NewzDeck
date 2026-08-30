# NewzDeck source and release history

NewzDeck is free and open-source software. Current Windows releases are built from the public source in this repository.

This page exists for people who want to understand how the public source relates to released Windows binaries. You do not need this information to install or use NewzDeck.

## Current release: v3.5.52

**v3.5.52 is the current stable production release.**

The `v3.5.52` tag identifies the exact public source commit used by the canonical Windows release workflow. Published installer, Portable, and SHA-256 values are recorded in the GitHub Release and checksum asset.

All six NewzDeck-owned Windows executables are built from public Go source:

| Windows file | Public source |
| --- | --- |
| `NewzDeck.exe` | `src/windows/NewzDeckLauncher.go` |
| `NewzDeckService.exe` | `src/windows/NewzDeckService.go` |
| `NewzDeckTray.exe` | `src/windows/NewzDeckTray.go` |
| `NewzDeckPicker.exe` | `src/windows/NewzDeckPicker.go` |
| `NewzDeckThumb.exe` | `src/windows/NewzDeckThumb.go` |
| `NewzDeckYenc.exe` | `src/windows/NewzDeckYenc.go` |

The Python backend, Automation engine, SAB adapter, and browser interface are also published in `src/app/`.

v3.5.52 incorporates the accepted v3.5.36–v3.5.52 reliability cycle: tray/session resilience, Live Downloads, Smart Import finalization and one-time media organization, Discover responsiveness, durable Grab queueing, the Windows Session 0 private-SAB launch correction, live post-processing progress, provider-state compatibility, and authoritative background-service handoff.

## v3.5.36 through v3.5.51

These versions were acceptance/development builds produced while the v3.5.52 cumulative release was being validated. They were not promoted as the next stable public production release. Their accepted fixes are consolidated into v3.5.52.

## v3.5.35

v3.5.35 was the previous stable production release. Its source commit was:

`d5435cb46ce778f6edea37bbd0b3758718bd1111`

Published SHA-256 values:

- Setup EXE: `c9daa17ab2bbf429e77e2009239979ed5156715cf62284c4db5025e0e83490eb`
- Portable ZIP: `cec30158f559a17c6a2bb6b0116e2842c96d5bcbb214f51076f4e8234314bd3a`
- SHA-256 file: `6b7161e518a9995515ac8288f4db08da02771d68c26fa20a1763a08028563185`

## v3.5.34

v3.5.34 was an **unreleased development candidate**. It contained reliability work that passed application acceptance testing, but its Windows installer did not pass final release acceptance. Its accepted work was carried into v3.5.35.

## v3.5.33

v3.5.33 was the first NewzDeck Windows release in which every NewzDeck-owned executable shipped in the release had corresponding public source in the repository. It established the source-complete Windows build model used by current releases.

## v3.5.32 and earlier

v3.5.32 marks the transition from NewzDeck's earlier binary-first development period to the current public-source build model.

Some legacy helper binaries in that historical package did not have complete corresponding build source published. The repository keeps that distinction documented rather than retroactively describing older packages as source-complete.

## Build toolchain

Current official Windows builds use:

- Python 3.12.10 for source validation and packaging
- Go 1.23.2 for NewzDeck-owned Windows executables
- Inno Setup 7.1.0 x64 for the Windows installer

Official release downloads are available from:

https://github.com/newzdeckadmin/NewzDeck/releases/latest

- **v3.6.8** - Image Browsing Performance & Gallery Quality. Production source promotes the accepted r1-r6 image-browsing performance work and is rebuilt/published by the repository Windows release workflow.

- **v3.6.9** - In-App Update Runtime Handoff. Fixes verified Update Center upgrades blocked by the legacy long-lived Picker taskbar helper and adds native-helper lock regression coverage to the Windows release pipeline.
