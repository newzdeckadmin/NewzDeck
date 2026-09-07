NewzDeck v3.6.40
Runtime Storage Cleanup & Hygiene

Focused maintenance release for long-lived NewzDeck installations.

WHAT'S NEW IN v3.6.40

- Safely removes obsolete private SAB admin/admin-vN generations after proving they are non-authoritative and their saved localhost listeners are no longer live.
- Preserves any historical generation whose port is occupied or whose identity cannot be safely proven dead.
- Normalizes an offline active admin-vN generation back to the canonical sab-engine\admin folder when it is safe to do so.
- Deletes the retained SAB provisioning ZIP after successful provisioning.
- Removes retired v3.5 engine-state repair artifacts and abandoned provisioning staging files.
- Bounds sab-startup.log and backend-startup.log to the current file plus two rotated backups.
- Exposes cleanup counters in download-engine health telemetry.

The cleanup never targets incoming, incomplete, active cache, newzdeck-jobs.json, engine.json, engine-identities.json, active lock files, or media/library data.

v3.6.39 Automation startup reservation refinement and the complete v3.6.38 crash-recovery/queue-admission stack are preserved unchanged.
