# NewzDeck v3.6.57 — Import Hold Semantics & Downloads Count Integrity

v3.6.57 is a focused follow-up to the first real v3.6.56 duplicate-content acceptance run. v3.6.56 correctly prevented bad media from entering the library, but that new protected state exposed counting, classification, and retry-policy gaps. This release fixes those gaps without changing SABnzbd transfer, repair, extraction, or queue behavior.

## Changes

- **Presentation counts match the actual tabs.** Durable history now maintains presentation Completed/Failed/Cancelled counts separately from raw SAB transfer Completed/Failed/Cancelled counts. A transfer that completed successfully but whose Smart Import is held therefore appears in Failed exactly once, and the Failed badge matches the Failed page total.
- **Raw transfer truth remains available.** Diagnostics expose both presentation terminal counts and authoritative SAB transfer terminal counts.
- **Explicit import-integrity failure class.** Duplicate-content holds persist `failure_class=import_integrity_hold`, the preserved reason, and the conflicting fingerprint.
- **Exact release blacklist after integrity hold.** A release proven byte-identical to another episode is added to the existing per-target failed-release blacklist.
- **Next candidate after the first conflict.** One duplicate-content failure does not stop Automation; unattended targets immediately become eligible to search for the next qualifying candidate.
- **Repeated-conflict Integrity Hold.** If two distinct release identities produce the same conflicting fingerprint for one target, unattended Automation pauses that target for manual review.
- **Hold visibility and recovery.** Automation Health exposes active target Integrity Holds with fingerprint/distinct-release evidence. A later verified successful import clears the active target hold while retaining historical evidence.
- **Clearer Smart Import event text.** Integrity-held imports now log `Smart Import held for review` instead of the misleading `Smart Import finished` warning.

## Validation

The v3.6.57 regression guard seeds durable history with SAB-completed/import-held rows and requires presentation counts to equal the Completed/Failed indexes while raw transfer counts remain unchanged. It also verifies exact-release blacklisting, first-conflict next-candidate behavior, repeated-fingerprint target pause, successful-import hold clearing, explicit failure classification, and preservation of the v3.6.56/v3.6.55 protections.

## Preserved behavior

Private SABnzbd 5.1.2 remains authoritative for NNTP transfer, verification, PAR2 repair, extraction and retry. v3.6.56 pre-import duplicate detection, recovered-warning handling, bounded raw-overlap telemetry and diagnostics caching remain intact. v3.6.55 no-op terminal-history synchronization/index efficiency, the v3.6.53 NZB identity gate, Smart Import ownership, Library Integrity, and installer/runtime handoff also remain unchanged.
