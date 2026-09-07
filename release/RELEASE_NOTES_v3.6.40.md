# NewzDeck v3.6.40 — Runtime Storage Cleanup & Hygiene

v3.6.40 is a focused maintenance release based on inspection of a long-lived NewzDeck installation whose private SAB runtime directory had accumulated many historical `admin-vN` generations and other superseded recovery/provisioning artifacts.

## What accumulated

Older NewzDeck releases intentionally created a fresh private SAB admin generation when isolating a damaged or conflicting SAB identity. Those generations were preserved because their credentials were useful for identifying and quarantining stale private SAB processes. After the identity/recovery architecture was hardened, the old directories remained on disk even after their localhost listeners were long gone.

A production installation could therefore contain `admin`, `admin-v2`, `admin-v3`, and many later generations even though only one generation was authoritative.

The same runtime directory could also retain the downloaded SAB provisioning ZIP, old v3.5 engine-state repair artifacts, and abandoned extraction/download staging from interrupted provisioning attempts. Startup logs were append-only and could grow indefinitely.

## Fail-closed historical admin cleanup

v3.6.40 removes obsolete private SAB admin generations only after the authoritative engine is healthy.

For every non-authoritative `admin` / `admin-vN` directory, NewzDeck reads the SAB config identities stored in that generation and verifies their saved localhost ports before deletion.

- The authoritative admin directory is never eligible for cleanup.
- If any historical port is still occupied, that generation is preserved.
- Historical stale-engine quarantine runs before cleanup, so a live old NewzDeck SAB can still be authenticated and paused/shut down safely using its historical credentials.
- A non-empty generation whose identity cannot be read is preserved rather than guessed away.
- Only a generation whose recorded listeners are proven free is deleted.

This keeps the v3.6.20+ split-brain/stale-engine protections while preventing dead generations from accumulating forever.

## Canonical `admin` normalization

When the authoritative SAB process is offline and NewzDeck owns the launch lock, an active `admin-vN` generation can now be normalized back to the canonical:

`%LOCALAPPDATA%\NewzDeck\sab-engine\admin`

The move occurs only when the authoritative saved port is not live and the old canonical `admin` generation has itself been proven safe to remove. `engine.json` is updated atomically to the new config path before SAB starts.

A currently running SAB process is never moved underneath itself. If the engine survives an app update and is still live, cleanup can still reduce the directory to one active generation; canonical renaming waits for a later clean offline start.

## Provisioning and legacy artifact cleanup

Once the embedded SAB executable is present and healthy, v3.6.40 removes runtime files that no longer provide recovery value:

- the retained `SABnzbd-5.1.1-win64-bin.zip` provisioning archive;
- `last-engine-state-repair.txt` from the retired v3.5 repair path;
- `engine-state-backup-v3.5.*` artifacts;
- abandoned SAB extraction directories older than one hour;
- abandoned provisioning `.download` files older than one hour.

New first-time provisioning also deletes the verified SAB ZIP immediately after a successful extraction.

## Bounded startup logs

The following diagnostic logs are now bounded to the current file plus two rotated backups:

- `sab-engine\sab-startup.log`
- `data\backend-startup.log`

Each rotates at approximately 2 MB. Log rotation is hygiene-only: a Windows sharing lock or rotation failure is ignored and can never block startup or downloads.

## What cleanup never touches

v3.6.40 does **not** delete or prune:

- `incoming`;
- `incomplete`;
- the active `cache` directory;
- `newzdeck-jobs.json`;
- `engine.json`;
- `engine-identities.json`;
- `browser-name-recovery.json`;
- current lock files;
- active/recoverable SAB queue data;
- media files or Smart Import destinations.

## Preserved behavior

- v3.6.39 Automation startup-reservation refinement is unchanged.
- v3.6.38 crash-recovered import reconciliation, sole paused-job repair, and authoritative pre-Grab queue admission remain unchanged.
- Persistent SAB transport and stale-engine quarantine remain authoritative.
- Manual Search/Grab, Newznab matching/scoring/blacklisting, Smart Import, no-downgrade protection, and Downloads continuity are unchanged.
- v3.6.37 operation feedback, v3.6.36 Automation action wiring, and v3.6.35 Manual Import progress remain intact.
