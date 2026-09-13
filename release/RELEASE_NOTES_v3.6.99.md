# NewzDeck v3.6.99 — Final UX & Backup/Restore

NewzDeck v3.6.99 is the final pre-v3.7 product-polish release built on the proven v3.6.96 production baseline. Its substantive addition is a portable Settings and Automation backup/restore workflow designed for recovery and moving NewzDeck to another Windows PC without copying transient runtime state.

## Backup & Restore

- **Configuration Backup:** one-click portable backup of NewzDeck settings, provider definitions, bookmarks/browser state, saved searches, Automation TV/Movie library, monitoring, root folders, quality profiles, indexer definitions, and Automation configuration. Passwords and API keys are omitted.
- **Complete Backup:** includes provider passwords, indexer API keys, and a configured user TMDB key inside a password-encrypted `.newzdeck-backup` file.
- **Client-side encryption:** Complete Backup uses AES-256-GCM with PBKDF2-SHA-256 and 600,000 iterations. The backup password is used only in the NewzDeck browser UI and is never posted to the backend.
- **Validated restore:** encrypted backups are authenticated/decrypted before restore; the backend validates backup schema and required sections before changing configuration.
- **Transactional safety:** NewzDeck automatically writes a local pre-restore snapshot, pauses Automation mutation with existing locks, and rolls configuration back if restore fails.
- **Cross-PC path safety:** an unavailable backed-up Download or NZB Watch Folder does not replace the working path on the destination PC. Automation media-root paths are retained so disconnected drives can later return online.
- **Secret handling:** Configuration Backup preserves matching credentials already present on the restore PC; Complete Backup re-protects imported credentials with Windows DPAPI. NewzDeck metadata-service installation identity is never exported or imported.
- **Runtime state excluded:** active downloads, SAB queue/runtime ownership, download payloads, caches, thumbnails, logs, diagnostics, Automation runtime locks/reservations, and metadata caches are not part of a portable backup.
- **Legacy restore:** earlier `NewzDeckConfigBackup` JSON files remain accepted as configuration-only restores.

## Final UX consistency

- Backup & Restore is now a first-class Settings category instead of being buried in Advanced.
- Backup types clearly explain what is and is not included.
- Restore presents backup type/content before confirmation and reports cross-PC path warnings after completion.
- Existing application styling and all twelve themes remain unchanged.

## Preserved production baseline

- v3.6.96 article-aware A/An/The sorting for Automation TV and Movie libraries is unchanged.
- All v3.6.95 light-theme readability fixes and all twelve themes are unchanged.
- Newsgroup Browser, Downloads, Smart Import, Automation searching/grabbing/import behavior, private SABnzbd 5.1.2, Metadata Server v0.3.3, and Diagnostic Collector v1.0.31 are unchanged.
- The Defender-clean folder-only Picker, accepted yEnc helper, direct checksum-verified Setup updater, and installer-owned runtime restoration architecture are unchanged.

## Release gate

The v3.6.99 regression guard verifies secret-free configuration export, client-side authenticated encryption markers, transactional restore/rollback, legacy-backup compatibility, runtime-state exclusions, v3.6.96 sorting preservation, immutable theme payloads, and the protected Defender-sensitive native/update architecture.
