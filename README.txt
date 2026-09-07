NewzDeck v3.6.42
TV Release Identity & Reliability Hardening

Production correctness and reliability release based on the completed v3.6.41 Diagnostic Collector review.

WHAT'S NEW IN v3.6.42

- TV release identity is now anchored to the complete series prefix before the season/episode marker. Unrelated shows can no longer satisfy a target merely because the target title appears later as an episode title or phrase.
- The strict persisted title/country-edition identity is enforced across release matching, final Grab validation, Smart Import, and library scanning. Real diagnostic regressions involving Love Island, FROM, Sugar, and S.W.A.T. are protected by production tests.
- TV library scans prefer the proven series folder and refuse to learn a folder from a stale cross-title episode record.
- The read-only Library Integrity Audit now reports strict identity mismatches as Needs Review. It never deletes, moves, renames, or automatically repairs media.
- Expired cross-process Automation Grab reservation files are safely pruned while live reservations keep their full duplicate-Grab protection window.
- Automation can keep a configurable percentage of each media/staging drive free in addition to the existing GB minimum; unattended grabs/imports are blocked below the reserve and Setup surfaces low-root status.
- Windows process-memory diagnostics now use typed 64-bit APIs and report explicit telemetry errors instead of silently showing 0 bytes.
- Generic SAB engine warnings are separated from NNTP provider errors and disk faults, preventing unrelated SAB warnings from appearing as provider failures.
- Launcher startup-log version identity is now dynamic from version.txt, and the production workflow permanently guards both that behavior and strict TV identity matching.

v3.6.41 Downloads snapshot responsiveness, serialized private-SAB transport, authoritative queue/recovery safeguards, Smart Import no-downgrade protections, and installer/runtime handoff behavior remain preserved.
