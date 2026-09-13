NewzDeck v3.6.99 - Final UX & Backup/Restore

NewzDeck is a free and open-source Windows Usenet newsreader, downloader, and personal media automation application.

v3.6.99 is the final pre-v3.7 UX and consistency release. It adds portable Settings and Automation backup/restore while preserving the proven v3.6.96 application behavior outside that feature.

Backup & Restore
----------------
Settings > Backup & Restore provides two backup types:

- Configuration Backup: one-click portable backup of Settings and Automation configuration without passwords or API keys.
- Complete Backup: includes provider passwords, Newznab API keys, and a configured user TMDB key inside a password-encrypted .newzdeck-backup file.

Complete Backup encryption is performed in the local NewzDeck browser UI with AES-256-GCM and PBKDF2-SHA-256 (600,000 iterations). The backup password is never sent to the NewzDeck backend.

Restore validates the backup before applying it, writes a local pre-restore safety snapshot, uses Automation locks while configuration is replaced, and rolls back configuration if restore fails. Active downloads, SAB runtime/queue state, Automation runtime ownership, caches, thumbnails, logs, diagnostics, and metadata caches are not included in portable backups.

Configuration-only restores preserve matching credentials already present on the destination PC. Complete restores re-protect imported credentials for the destination Windows installation. Unavailable Download or NZB Watch paths from another PC do not overwrite working local paths.

Preserved behavior
------------------
- v3.6.96 article-aware TV/Movie sorting remains unchanged: leading A, An, or The is ignored only for alphabetical placement.
- All twelve themes and the v3.6.95 Light/Arctic/Sandstone readability fixes remain unchanged.
- Newsgroup Browser, Downloads, Smart Import, Automation search/grab/import behavior, SABnzbd 5.1.2, Metadata Server v0.3.3, Diagnostic Collector v1.0.31, and the Defender-clean native/update architecture are unchanged.

License: GNU GPLv3.
