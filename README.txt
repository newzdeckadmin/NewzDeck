NewzDeck v3.6.44
Library Integrity Audit Route Hotfix

Production hotfix based on v3.6.43.

Highlights:
- Fixes the Library Integrity Review HTTP 404 by exposing the read-only integrity audit through GET.
- Keeps Open Folder and Mark Missing actions POST-only.
- Preserves the v3.6.43 non-destructive review workflow and all TV identity/diagnostics improvements unchanged.
- Adds a release-blocking API-route regression guard so the read-only audit cannot silently move back to POST.

NewzDeck is free and open-source software licensed under GPL-3.0-only.
