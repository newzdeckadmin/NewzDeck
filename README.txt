NewzDeck v3.7.0 - Production Milestone & Repository Hygiene

NewzDeck is a free and open-source Windows Usenet newsreader, downloader, and personal media automation application.

v3.7.0 promotes the proven v3.6.99 application to the 3.7 production milestone. The application feature set and runtime behavior are intentionally preserved while the public repository, build documentation, and release workflow are cleaned up for the new milestone.

Production milestone
--------------------
- The complete v3.6.99 Settings and Automation Backup & Restore system is preserved.
- v3.6.96 article-aware TV/Movie sorting remains unchanged: leading A, An, or The is ignored only for alphabetical placement.
- All twelve themes and the v3.6.95 Light/Arctic/Sandstone readability fixes remain unchanged.
- Newsgroup Browser, Downloads, Smart Import, Automation search/grab/import behavior, SABnzbd 5.1.2, Metadata Server v0.3.3, Diagnostic Collector v1.0.31, and the Defender-clean native/update architecture are unchanged.

Repository hygiene
------------------
- The obsolete duplicate manual Windows release workflow is removed; the guarded publish-release-trigger workflow is the single authoritative production release path.
- Source/build documentation is updated to the current topology and no longer points at retired v3.5.33-era guidance or a missing RELEASE_COMPLIANCE.md file.
- Third-party notices are version-neutral while retaining the current pinned component/tool versions and license references.

License: GNU GPLv3.
