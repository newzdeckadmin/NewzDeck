# NewzDeck v3.6.44 — Library Integrity Audit Route Hotfix

NewzDeck v3.6.44 is a narrowly scoped production hotfix for the Library Integrity Review introduced in v3.6.43.

## Fixed: Library Integrity Review HTTP 404

The v3.6.43 browser correctly requested the read-only Library Integrity audit with:

`GET /api/automation/library/integrity-audit`

but the backend route was accidentally placed in the POST handler. As a result, **Automation → Setup → Library Integrity → Run integrity review** opened the review modal and then returned HTTP 404.

v3.6.44 registers the audit endpoint in the GET handler, matching the UI and the read-only nature of the operation.

## API safety preserved

- `GET /api/automation/library/integrity-audit` is read-only and returns the current audit.
- `POST /api/automation/library/integrity/open-folder` remains an explicit action endpoint.
- `POST /api/automation/library/integrity/mark-missing` remains an explicit state-change endpoint.
- **Mark Missing (keep file)** still never deletes, moves, renames, or overwrites the physical media file.

## Regression protection

The production regression validator now verifies that the integrity-audit route exists in the GET handler and does not exist in the POST handler. The existing 30 TV identity cases, non-destructive Mark Missing test, diagnostics compaction test, and client-disconnect classifier remain mandatory.

## Preserved behavior

All v3.6.43 TV identity compatibility, strict cross-series safeguards, reviewed-file fingerprint exclusions, diagnostics compaction, localhost client-disconnect handling, Automation behavior, SAB transport, Downloads continuity, installer/service/tray handoff, and user-data locations are otherwise unchanged.
