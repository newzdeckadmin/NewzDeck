# NewzDeck source and release history

NewzDeck is free and open-source software. Current Windows releases are built from the public source in this repository.

This page exists for people who want to understand how the public source relates to released Windows binaries. You do not need this information to install or use NewzDeck.

## Current release: v3.6.15

**v3.6.15 is the current stable production release.**

The `v3.6.15` tag identifies the public source used by the canonical Windows release workflow. Published installer, Portable, and SHA-256 values are recorded in the GitHub Release and checksum asset.

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

## Recent production releases

- **v3.6.15 — Wanted State Reconciliation & Responsive Automation.** Makes live Downloads authoritative for Wanted queue state, adds honest QUEUEING handoff state and per-target cycle progress, decouples metadata/library maintenance from release searching, bounds automatic NZB retrieval, and prevents stale long-cycle runtime snapshots from overwriting newer failure/maintenance state.
- **v3.6.14 — Automation Save Reliability & Responsiveness.** Serializes Automation JSON reads/writes per file, adds bounded Windows sharing/access retry around atomic replacement, and returns truthful Save feedback immediately after persistence while the larger Automation summary refreshes asynchronously.
- **v3.6.13 — Download Continuity & Automation Clarity.** Adds bounded SAB Active-card continuity, verified Remove/Cancel with hidden-transfer reconciliation, Wanted policy visibility, and fallback-only season packs with member-target reservation.
- **v3.6.12 — Installer-Owned Runtime Restore.** Makes Setup authoritative for closing the browser-hosted UI after overlay, repairing and starting the service, restoring the tray, and reopening NewzDeck after `/update`; production CI exercises the update restore path.
- **v3.6.11 — SAB Ownership Continuity & Managed Update Handoff.** Preserves live SAB job ownership across transient slot omissions and restores queue-to-history Smart Import completion continuity.
- **v3.6.10 — Python Source Freshness & Runtime Refresh.** Forces NewzDeck-owned Python modules to load from current source bytes and removes stale adjacent bytecode during startup/upgrades.
- **v3.6.9 — In-App Update Runtime Handoff.** Fixes Update Center upgrades blocked by the legacy long-lived Picker taskbar helper and adds native-helper lock regression coverage.
- **v3.6.8 — Image Browsing Performance & Gallery Quality.** Promotes the accepted image-browsing performance and gallery-quality work.

## Earlier source-complete milestones

### v3.5.52

v3.5.52 consolidated the accepted v3.5.36-v3.5.52 reliability cycle: tray/session resilience, Live Downloads, Smart Import finalization and one-time media organization, Discover responsiveness, durable Grab queueing, Windows Session 0 private-SAB launch correction, live post-processing progress, provider-state compatibility, and authoritative background-service handoff.

### v3.5.36 through v3.5.51

These versions were acceptance/development builds produced while the v3.5.52 cumulative release was being validated. Their accepted fixes were consolidated into v3.5.52.

### v3.5.35

v3.5.35 was the previous stable production release before the v3.5.52 cumulative cycle. Its source commit was:

`d5435cb46ce778f6edea37bbd0b3758718bd1111`

Published SHA-256 values:

- Setup EXE: `c9daa17ab2bbf429e77e2009239979ed5156715cf62284c4db5025e0e83490eb`
- Portable ZIP: `cec30158f559a17c6a2bb6b0116e2842c96d5bcbb214f51076f4e8234314bd3a`
- SHA-256 file: `6b7161e518a9995515ac8288f4db08da02771d68c26fa20a1763a08028563185`

### v3.5.34

v3.5.34 was an unreleased development candidate. Its accepted work was carried into v3.5.35.

### v3.5.33

v3.5.33 was the first NewzDeck Windows release in which every NewzDeck-owned executable shipped in the release had corresponding public source in the repository. It established the source-complete Windows build model used by current releases.

### v3.5.32 and earlier

v3.5.32 marks the transition from NewzDeck's earlier binary-first development period to the current public-source build model. Some legacy helper binaries in that historical package did not have complete corresponding build source published; the repository keeps that distinction documented.

## Build toolchain

Current official Windows builds use:

- Python 3.12.10 for source validation and packaging
- Go 1.23.2 for NewzDeck-owned Windows executables
- Inno Setup 7.1.0 x64 for the Windows installer

Official release downloads are available from:

https://github.com/newzdeckadmin/NewzDeck/releases/latest
