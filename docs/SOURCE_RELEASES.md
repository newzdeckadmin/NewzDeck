# NewzDeck source and release history

NewzDeck is free and open-source software. Current Windows releases are built from the public source in this repository.

## Current release: v3.6.40

**v3.6.40 is the current stable production release.**

The `v3.6.40` tag identifies the public source used by the canonical Windows release workflow. Published installer, Portable, and SHA-256 values are recorded in the GitHub Release and checksum asset.
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

- **v3.6.40 - Runtime Storage Cleanup & Hygiene.** Safely prunes proven-dead historical SAB admin generations, normalizes an offline active generation back to canonical admin, deletes redundant provisioning/legacy repair artifacts, and bounds startup logs without touching incomplete downloads, current queue state, or the v3.6.39/v3.6.38 Automation recovery protections.

- **v3.6.39 - Automation Startup Reservation Refinement.** Limits unproven pending-* handoff reservations to a 120-second startup grace, preserves durable v3.6.38 recovered-job protection, removes the static initial max-grab allowance, and lets the same running cycle use capacity that becomes available while retaining the authoritative pre-Grab occupancy recheck.

- **v3.6.38 - Crash Recovery & Automation Queue Reconciliation.** Prevents post-restart SAB queue/history reconstruction from being mistaken for free Continuous Automation capacity, reconciles false recovered Import Failed cards only from exact authoritative library proof, recovers the narrow sole unintended paused-job state, and shortens only the expected service-before-tray startup retry.

- **v3.6.37 - Operation Progress & Activity Feedback.** Adds audited browser-side busy/activity states for noticeable operations, fixes item-level Scan files feedback, preserves existing real/loading progress surfaces, and repairs/guards visible static version identity without changing backend operation semantics.

- **v3.6.36 - Automation Action Wiring Recovery.** Restores the shared browser-side Automation action helpers accidentally removed in v3.6.35, including Wanted/episode/season-pack manual release search plus Save, Refresh metadata, Open folder, Remove, and Scan library; preserves v3.6.35 Manual Import live progress and adds release-blocking UI wiring regression checks.

- **v3.6.35 - Manual Import Live Progress.** Adds real Smart Import transaction progress to v3.6.34 Manual Media Import, including phase/current-file status, byte-based cross-volume copy advancement, modal job locking, and 100% only after authoritative library/Wanted reconciliation, while preserving the existing import safety and no-downgrade path.

- **v3.6.34 - Manual Media Import & Wanted Reconciliation.** Adds explicit TV season/episode import from an external folder, non-destructive import preview, transactional Smart Import rename/move with final no-downgrade revalidation, and immediate Wanted reconciliation when imported media satisfies the monitored quality cutoff.

- **v3.6.33 - TV Edition Search Alias Compatibility.** Adds safe confirmed country-suffix aliases for USA/US, Australia/AU/AUS, United Kingdom/UK/GB, Canada/CA/CAN, and New Zealand/NZ/NZL to Newznab search and local TV release identity validation; merges/deduplicates alias results; keeps conflicting/fuzzy editions rejected; and preserves v3.6.32 Automation integrity plus the accepted SAB/download-control stack.

- **v3.6.32 - Automation Target Integrity & Downgrade Protection.** Revalidates unattended targets immediately before NZB submission, blocks any unproven Smart Import downgrade, protects live import state from stale long-running library-scan merges, and adds direct target-integrity diagnostics while preserving the accepted SAB transport stack.

- **v3.6.31 - Historical SAB Probe Quieting.** Skips closed/free historical SAB localhost ports before HTTP identity probing, retains full version+historical-key proof for occupied ports, adds historical-sweep telemetry, and preserves the accepted current-SAB transport and Downloads continuity paths unchanged.

- **v3.6.30 - SAB Identity Probe Stabilization.** Replaces redundant routine `mode=version` heartbeats with authoritative API-key `auth` liveness checks, makes unchanged provider/configuration sync passes return before any SAB heartbeat, adds identity-probe telemetry, and preserves the accepted v3.6.29 persistent transport plus v3.6.28 Downloads continuity unchanged.

- **v3.6.29 - Persistent SAB Control Transport.** Replaces explicit per-request localhost SAB connection teardown with a serialized persistent HTTP/1.1 control connection, safely recreates the socket after genuine control faults/listener changes, adds per-mode transport telemetry, and preserves the v3.6.28 Downloads visibility bridge unchanged.

- **v3.6.28 - Downloads Continuity & SAB Recovery Hardening.** Keeps durably owned non-terminal downloads visible through transient SAB Queue/History slot omissions, requires consecutive fresh Queue+History absence before stale ownership can expire, adds visibility-gap diagnostics, reduces redundant localhost control reads, and stops temporary tray/session launch failures from allocating unnecessary SAB admin generations.

- **v3.6.27 - Runtime Adapter Identity Repair.** Repairs the built-in SAB adapter runtime identity so it matches the UI/backend version, centralizes adapter version output in one constant, and hardens production publishing checks so stale runtime adapter identities cannot ship again.

- **v3.6.26 - Verified Remove & Bulk Failed Cleanup.** Removes the false reconnect gate from verified Remove, verifies individual jobs directly against targeted SAB Queue/History state with bounded retries, makes Remove all failed truly bulk at the SAB control plane, and preserves active-transfer safety plus all accepted v3.6.25 backlog/Smart Import safeguards.

- **v3.6.25 - Automation Backlog & Smart Import Reliability.** Makes exhausted Smart Import retries truly terminal until explicit Retry Import, requires job-owned/fail-closed SAB output resolution, prevents TV franchise/edition cross-matches, throttles high-frequency import-state persistence, reduces redundant SAB control traffic, adds startup-recovery cooldown and stable stale-ownership reconciliation, exposes a read-only library integrity audit, and adds a one-click Remove all failed action to the Failed downloads view.

- **v3.6.24 - Durable Download Statistics.** Replaces the incomplete session/legacy statistics bridge with restart-safe SAB lifetime accounting: persistent SAB byte totals are additive to the pre-SAB baseline, completed jobs are counted once across service/desktop runtimes, retained History/Archive timing is backfilled, Average Speed is weighted over timed bytes, Peak Speed is durable, and captured lifetime statistics survive History clearing.

- **v3.6.23 - Accent-Insensitive Automation Search.** Folds Latin accents/diacritics and common non-decomposing Latin characters for Newznab queries and safe local title identity checks while preserving canonical TMDB/library names; this improves compatibility when release names omit diacritics without weakening token-based false-positive protection.

- **v3.6.22 - All Posts Binary Resolution & Recovery.** Makes complete reconstructed multipart binaries actionable before friendly-name resolution, automatically drains bounded filename work, distinguishes opaque/missing/unavailable/retryable outcomes, backs off on transient provider failures, keeps long package reconstruction polling alive, flattens direct loose-binary downloads into the configured Download Folder, and adds conservative PAR2/archival obfuscated-name recovery.

- **v3.6.21 - Newsgroups Image Browsing & Related Media.** Moves Group Related Media into a dedicated side pane, flattens direct loose-image downloads into the configured Download Folder, adds measured Continuous-gallery DOM windowing and incremental media-set indexing, bounds broken-set/image recovery work, and hardens Related Media cover scheduling with stable set ownership, reserved capacity, cache-first activation, and visible queue promotion.

- **v3.6.20 - Authoritative SAB & Fresh-State Reconciliation.** Enforces one authoritative private SAB identity, quarantines historical engines, serializes NewzDeck-to-SAB control traffic, bounds stale Queue/History fallback, prevents stale state from driving Pause/Resume or destructive reconciliation, and preserves the verified Automation-to-Smart-Import end-to-end path.

- **v3.6.19 - Non-Disruptive SAB Runtime & Single-Foreground Downloads.** Debounces private-SAB control-plane recovery, prevents transient health misses from forcing provider/config rewrites, suppresses configuration retry storms, normalizes one-package queue mode to one foreground Active package, and preserves monotonic live progress.

- **v3.6.18 - Idle-Aware Engine Pause Recovery.** Makes private-SAB Pause recovery workload-aware so an empty engine may idle as Paused without cycling Resume/recovery, while preserving v3.6.17 canonical Downloads-state and Smart Import recovery invariants.

- **v3.6.17 - Downloads State Integrity & Smart Import Recovery.** Unifies Downloads around one canonical visible-job state model, prevents contradictory SAB aggregate Remaining values, guarantees every live SAB Queue slot has a visible card, separates user Pause intent from engine pause state, and reclaims Smart Imports orphaned by dead runtimes.

- **v3.6.16 Ã¢â‚¬â€ Verified Download Control & Active Continuity.** Hardens Failed/Completed verified Remove/Cancel, preserves specific control errors, invalidates stale pre-mutation snapshots, and bridges short unexpected SAB global Pause samples when NewzDeck knows the user did not pause the queue.
- **v3.6.15 Ã¢â‚¬â€ Wanted State Reconciliation & Responsive Automation.** Makes live Downloads authoritative for Wanted queue state, adds honest QUEUEING handoff state and per-target cycle progress, decouples metadata/library maintenance from release searching, bounds automatic NZB retrieval, and prevents stale long-cycle runtime snapshots from overwriting newer state.
- **v3.6.14 Ã¢â‚¬â€ Automation Save Reliability & Responsiveness.** Serializes Automation JSON reads/writes per file, adds bounded Windows sharing/access retry around atomic replacement, and returns truthful Save feedback immediately after persistence while the larger Automation summary refreshes asynchronously.
- **v3.6.13 Ã¢â‚¬â€ Download Continuity & Automation Clarity.** Adds bounded SAB Active-card continuity, verified Remove/Cancel with hidden-transfer reconciliation, Wanted policy visibility, and fallback-only season packs with member-target reservation.
- **v3.6.12 Ã¢â‚¬â€ Installer-Owned Runtime Restore.** Makes Setup authoritative for closing the browser-hosted UI after overlay, repairing and starting the service, restoring the tray, and reopening NewzDeck after `/update`.
- **v3.6.11 Ã¢â‚¬â€ SAB Ownership Continuity & Managed Update Handoff.** Preserves live SAB job ownership across transient slot omissions and restores queue-to-history Smart Import completion continuity.
- **v3.6.10 Ã¢â‚¬â€ Python Source Freshness & Runtime Refresh.** Forces NewzDeck-owned Python modules to load from current source bytes and removes stale adjacent bytecode during startup/upgrades.
- **v3.6.9 Ã¢â‚¬â€ In-App Update Runtime Handoff.** Fixes Update Center upgrades blocked by the legacy long-lived Picker taskbar helper and adds native-helper lock regression coverage.
- **v3.6.8 Ã¢â‚¬â€ Image Browsing Performance & Gallery Quality.** Promotes the accepted image-browsing performance and gallery-quality work.

## Earlier source-complete milestones

### v3.5.52
v3.5.52 consolidated the accepted v3.5.36-v3.5.52 reliability cycle.

### v3.5.35
v3.5.35 was the previous stable production release before the v3.5.52 cumulative cycle.

### v3.5.33
v3.5.33 established the source-complete Windows build model used by current releases.

## Build toolchain

Current official Windows builds use:
- Python 3.12.10 for source validation and packaging
- Go 1.23.2 for NewzDeck-owned Windows executables
- Inno Setup 7.1.0 x64 for the Windows installer

Official release downloads are available from:
https://github.com/newzdeckadmin/NewzDeck/releases/latest
