# NewzDeck v3.6.11 - SAB Ownership Continuity & Managed Update Handoff

NewzDeck v3.6.11 is a focused download-lifecycle and in-app update reliability
release built on v3.6.10.

## SAB ownership and completion continuity

- **Active jobs no longer disappear during SAB queue reshaping.** SAB can
  temporarily expose aggregate transfer speed/remaining data while omitting the
  individual foreground queue slot. NewzDeck now bridges that package from its
  durable ownership record instead of showing `0 active`.
- **Transient omissions cannot create removal tombstones.** Removal tombstones
  are reserved for explicit user Remove/Cancel actions. A missing SAB slot is
  never interpreted as user intent.
- **Automation ownership survives queue-to-history gaps.** Smart Import jobs are
  retained long enough to reconcile the completed SAB history record and enter
  Post-processing/Completed normally.
- **Legacy automatic-prune recovery.** Recent reasonless tombstones created by
  older NewzDeck builds can be reconciled when SAB history proves the same job
  completed after that tombstone. Genuine explicit user removals remain
  suppressed.
- **Completion remains actionable.** Reconciled Automation jobs retain their
  original Automation context so rename/move/cleanup can proceed through Smart
  Import.

## Managed in-app update handoff

- **The actual desktop window closes before Setup.** NewzDeck's UI is hosted in
  an Edge/Chrome app-mode window, so terminating `NewzDeck.exe` is not enough.
  The native coordinator closes the real NewzDeck window.
- **Coordinator survives file replacement.** A short-lived copy of
  `NewzDeckPicker.exe` runs from the version-independent update staging
  directory while Setup replaces the installed application files.
- **Tray lifecycle is managed.** The existing tray is closed before Setup and
  restored afterward when it was previously active/configured.
- **Background service is restored.** Setup still performs the authoritative
  pre-overlay service stop/repair. After Setup exits, the coordinator starts the
  updated service again when a service was installed before the update.
- **NewzDeck reopens automatically.** After a successful Setup, the coordinator
  launches the updated tray and then the updated `NewzDeck.exe`.
- **Both update entry points use the same lifecycle.** Verified online Update
  Center installations and manually selected Setup packages share the managed
  handoff.

## Preserved

- v3.6.10 Python Source Freshness & Runtime Refresh, including source-byte module
  loading and stale adjacent bytecode cleanup.
- v3.6.9 installed-upgrade native-helper/service shutdown protections.
- v3.6.8 Image Browsing Performance & Gallery Quality, including WIC-first
  persistent thumbnail workers, multipart acceleration, RAM caches, tiny-image
  suppression, deep-page-jump isolation, and rendering hot-path optimizations.
- Private SAB high-throughput downloads, Automation, Smart Import,
  Discover/TMDB, provider behavior, taskbar identity, and Metadata Server v0.3.3
  compatibility.

## Upgrade notes

You may install v3.6.11 directly over v3.6.10. Existing NewzDeck user data,
provider settings, download queue state, Automation configuration/history, and
media libraries are stored outside the application directory and remain
preserved.

For the most representative update test, use **About & Updates -> Install
Update** from an installed v3.6.10 build. The expected lifecycle is:

`close app -> close tray -> Setup/service handoff -> restore service -> restore tray -> reopen app`.
