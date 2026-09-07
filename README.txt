NewzDeck v3.6.43
TV Identity Compatibility & Library Integrity Review

Production release based on v3.6.42.

Highlights:
- Preserves exact pre-Sxx/Eyy TV identity anchoring while accepting bounded year-only release decorations.
- Adds safe full-token stylization compatibility such as PLUR1BUS without substring matching.
- Adds an on-demand Library Integrity Needs Review UI with Open Folder and explicit Mark Missing actions.
- Mark Missing never deletes media and excludes only the exact reviewed old fingerprint from immediate scan re-attachment.
- Shrinks /api/diagnostics by removing duplicated full Downloads history while keeping counts, telemetry, statistics, engine state, and bounded current/recent collection evidence.
- Treats proven browser/client disconnects during localhost JSON delivery as transport completion events rather than Automation calculation failures.

NewzDeck is free and open-source software licensed under GPL-3.0-only.
