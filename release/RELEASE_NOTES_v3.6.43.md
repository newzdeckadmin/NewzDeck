# NewzDeck v3.6.43 — TV Identity Compatibility & Library Integrity Review

NewzDeck v3.6.43 is a focused follow-up to v3.6.42 based on a completed production diagnostic capture. v3.6.42 successfully stopped new cross-series TV imports, but the audit exposed historical bad assignments and a small set of legitimate release-name variants that the new strict matcher rejected.

## TV identity compatibility without fuzzy matching

- The complete TV series identity is still anchored before the first Sxx/Eyy/season marker.
- One or two year-only tokens are now permitted only **after an already-exact allowed series prefix**. This supports observed names such as `Reacher.2026.S04E06`, `Beast.Games.2026.S02E08`, `From.2023.S02E10`, and `Dark.Matter.2024.2024.S01E04`.
- A bounded full-token stylization fold supports names such as `PLUR1BUS` for `Pluribus`. It is never used as a substring search.
- Arbitrary intervening words remain rejected, so `Love.Island.The.Debrief`, `Love.Island.Romania`, `The.Morning.Show...Love.Island`, Bradshaw/Larva collisions, conflicting country editions, and FROM episode-title collisions remain blocked.

## Library Integrity — Needs Review

Automation Setup now includes an on-demand **Library Integrity / Needs Review** workflow. It shows retained release provenance, current library path, identity/edition reasons, and cross-title duplicate-fingerprint evidence.

Review actions are intentionally conservative:

- **Open folder** opens the current associated file's folder.
- **Mark Missing (keep file)** clears only NewzDeck's library association. The physical media file is not deleted, moved, renamed, or overwritten.
- The exact reviewed path/fingerprint is remembered so a periodic library scan cannot immediately reattach the same known-bad file. If the physical file is genuinely replaced with a different fingerprint, normal reconciliation can accept the replacement.

No audit finding is automatically repaired or deleted. The user explicitly chooses each state change.

## Smaller, faster diagnostics

`/api/diagnostics` no longer duplicates the entire Downloads presentation history that is already available from `/api/downloads`. It retains authoritative counts, SAB/Downloads telemetry, durable statistics, engine state, and a bounded compact sample of active/recent collections. This substantially reduces diagnostic JSON size and response serialization work on long-lived installations.

## Client-disconnect logging cleanup

Localhost JSON response delivery now quietly absorbs only proven browser/client disconnect errors such as BrokenPipe/connection reset/WinError 10053/10054. A browser reload or cancelled fetch therefore no longer gets mislabeled as an Automation sidebar or summary calculation failure. Genuine application exceptions continue to surface normally.

## Regression protection

The production TV identity validation suite now includes the diagnostic-proven year-decoration and PLUR1BUS compatibility cases plus the existing cross-series rejection cases. Python compilation, JavaScript syntax, source-freshness, installer, tray, and release-trigger protections remain mandatory in the canonical GitHub workflow.

## Preserved behavior

- v3.6.42 strict series ownership, storage reserve, expired Grab reservation cleanup, Win64 memory diagnostics, SAB warning classification, and dynamic launcher log identity remain intact.
- v3.6.41 fail-soft Downloads snapshots remain intact.
- The v3.6.20+ serialized private-SAB transport remains intact.
- Automation target integrity, no-downgrade Smart Import, Manual Import, Newznab search, Discover, installer/service/tray handoff, and user-data locations are unchanged except where described above.
