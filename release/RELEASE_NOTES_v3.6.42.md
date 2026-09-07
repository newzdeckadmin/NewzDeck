# NewzDeck v3.6.42 — TV Release Identity & Reliability Hardening

NewzDeck v3.6.42 is a production correctness and reliability release based on a completed v3.6.41 Diagnostic Collector review. v3.6.41 successfully kept Downloads and diagnostics responsive under real snapshot contention; the newer capture also exposed a separate Automation identity flaw and several smaller long-running-installation issues.

## Strict TV series identity

TV identity no longer means “the target title occurs somewhere in the release string.” NewzDeck now parses the complete normalized series prefix before the first season/episode marker and requires that prefix to match a persisted, explicitly permitted title/country-edition identity.

This blocks real failures observed in diagnostics, including unrelated releases such as `The.Morning.Show.S03E05.Love.Island...`, `The.Bradshaw.Bunch.S02E01.Love.Island...`, and episode-title text such as `Sugar...Home.Away.from.Home` being mistaken for Love Island or FROM.

Confirmed country aliases remain supported only when backed by the stored series identity. For example, the UK Love Island item can accept its permitted UK/GB forms while conflicting USA/Romania/spinoff identities fail closed.

The same strict identity check is used by search eligibility, final release validation, Smart Import, and library scanning so a candidate cannot pass a loose stage and fail a stricter stage later.

## Safer TV library reconciliation

TV library scans now prefer the established or expected series directory instead of recursively searching the entire multi-show root whenever NewzDeck can prove the series directory.

A stale episode record is no longer allowed to teach NewzDeck the wrong series folder: the candidate folder itself must match the persisted title/library-title identity. This lets a later scan recover from the type of FROM → Sugar stale mapping found in the diagnostic capture instead of reinforcing it.

## Read-only Needs Review integrity audit

The existing library-integrity audit now adds strict TV identity review. For imported files with retained release provenance, the audit validates that provenance against the current strict series identity; otherwise it uses the library filename as a conservative fallback.

Identity mismatches, country-edition mismatches, and cross-title duplicate fingerprints are surfaced as **Needs Review** evidence. The audit remains read-only and never deletes, moves, renames, or automatically repairs existing media.

## Bounded Automation Grab reservation cleanup

Cross-process Grab reservation files still prevent two NewzDeck runtimes from submitting the same target at the same time. v3.6.42 now removes only reservations whose expiry has passed. Malformed reservation files receive an additional age grace before removal.

Cleanup runs at startup and periodically with a bounded directory pass, and exposes counters in target-integrity telemetry. Active reservations are never removed early.

## Media-drive free-space reserve

Automation now supports a percentage free-space reserve in addition to the existing absolute GB minimum. NewzDeck uses the larger reserve for each actual destination/staging drive.

The default percentage is 5%, can be set to Off/1%/3%/5%/10% in Automation Setup, and unattended or manual grabs/imports fail before submission when the selected media or staging drive would fall below its configured reserve. Automation Setup also reports when a configured media root is already below reserve.

## Windows memory diagnostics

Backend working-set diagnostics now use explicitly typed Win64 process-memory APIs. This prevents 64-bit process handles from being truncated by implicit ctypes signatures. If memory telemetry cannot be read, diagnostics return an explicit error instead of silently reporting zero bytes.

## SAB warning classification

SAB warnings are now split into provider/network warnings, generic engine warnings, and disk faults. Generic warnings such as NZB import warnings no longer become `provider_summary` and therefore no longer masquerade as a Usenet provider outage.

Disk-full/disk-error conditions continue to drive the dedicated engine-fault path.

## Dynamic launcher log identity

`launcher-handoff.log` no longer contains a manually bumped `startup-vX.Y.Z` string. The launcher reads `version.txt` and writes that runtime version into the log dynamically.

The production release workflow now rejects a hardcoded startup-version marker and runs a persistent TV identity regression suite using the real diagnostic failure cases.

## Preserved behavior

- v3.6.41 bounded Downloads snapshot/read contention behavior remains intact.
- NewzDeck → SAB control traffic remains serialized and does not reintroduce overlapping localhost SAB requests.
- Authoritative queue ownership, terminal reconciliation, crash recovery, and Pause recovery safeguards remain unchanged.
- Smart Import no-downgrade and transaction safety remain intact.
- v3.6.40 runtime-storage cleanup, v3.6.39 startup-reservation refinement, and v3.6.38 crash-recovery/queue-admission protections remain intact.
- Source-freshness protections and installer service/tray upgrade handoff remain intact.
- The library integrity audit performs no media mutation.

## Validation

The production package validates exact v3.6.41 GitHub baseline SHAs before applying any change. Python compilation, JavaScript syntax, strict TV identity regression cases, version markers, LF/no-BOM hygiene, staged-path allowlisting, `git diff --cached --check`, source-parent identity, remote source SHA, and the separate release-trigger SHA are all checked before/after publication.

The canonical GitHub release workflow performs the final deterministic Portable build, Inno Setup build, installed-upgrade smoke test, checksum verification, tag creation, and GitHub Release publication from the exact validated source commit.
