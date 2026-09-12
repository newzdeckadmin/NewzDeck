NewzDeck v3.6.83 - Quality Profile UI & Update Version Coherency

This release is a targeted UI and update-status correctness pass built on the published v3.6.82 release.

Highlights:
- The Quality Profile editor now uses a dedicated, polished dialog layout with consistent spacing, aligned controls, uniform field heights, a scrollable body, and a stable action footer.
- About & Updates no longer contains the stale hard-coded v3.6.62 label; the installed version is read dynamically.
- Update checks distinguish installed, runtime, and UI versions so a version mismatch is shown clearly instead of presenting the already-installed release as an upgrade.
- The backend compares the GitHub release feed against the installed version.txt value and rejects update-feed cache entries created by a different installed version.
- The UI independently verifies version ordering so the same release can never be offered as an update even if a stale backend/feed result reports otherwise.
- All v3.6.81 Automation Intelligence & Quality Profiles behavior remains intact.
- The v3.6.82 canonical source -> tag -> trigger release pipeline remains intact.
- Newsgroup Browser performance architecture, SABnzbd 5.1.2, Metadata Server v0.3.3, Diagnostic Collector v1.0.31 and the Defender-clean yEnc pipeline are unchanged.

See release/RELEASE_NOTES_v3.6.83.md for details.
