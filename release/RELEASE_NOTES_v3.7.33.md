# NewzDeck v3.7.33 — Completed Download Folder Control & Manual Grab Identity

**Source-development package; not yet a published release or Windows CI build.**

## Corrected: Extract into a subfolder

For **new NZB jobs** when **Downloads → Organization = One folder**:

- **Checked**: exactly the existing behavior. SABnzbd and NewzDeck can use normal per-job folders; extraction keeps its current subfolder layout.
- **Unchecked**: download, verify, repair and unpack inside the existing per-job working folder, and **only after successful completion** place finished files directly into the configured Download Folder, including nested archive members.
- Existing queued and completed jobs are **not** reorganized when the setting changes.
- Automatic TV/movie Smart Import continues moving verified media into its configured Root Folder, following existing cleanup and integrity protections; do not flatten library structure.
- Loose Newsgroups image/video downloads retain their previously established output handling.

The safe finalizer uses a durably recorded job-relative filename plan and atomic, collision-safe hard links. It never overwrites a file already in the Download Folder. A new final name such as `video (2).mkv` is chosen when necessary. Partial operations resume from the persistent plan without making duplicate outputs. If the output directory is untrusted, a lock prevents finalization, a symlink is encountered, or the filesystem does not support safe no-clobber linking, NewzDeck **preserves the staging files instead of deleting or blindly copying them**. In such cases see Diagnostics. No existing user files are migrated or removed by the update.

## Corrected: asynchronous manual TV Grab identity

The temporary in-memory Grab coalescer now separates TV episodes and season packs for unmonitored manual titles, matching the existing durable Automation target identity. Same-target replay/duplicate prevention and request-ID safety remain intact.

## Preserved

SABnzbd 5.1.3 and SABCTools 9.6.3, pending SAB handoffs, Auto PAR2 repair, Direct Unpack, Smart Import, failed-release identity, download history, native Windows service and tray, existing installer identity and settings, metadata server 0.3.3 and diagnostic collector 1.0.31.

## Verification boundary

Local offline Python and Node.js regression checks are not equivalent to a Windows installer build. New Windows CI, upgrade smoke tests and live NTFS/SAB NZB checks are required before publication. The publisher must not be run or pushed without separate authorization.
