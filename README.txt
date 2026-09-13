NewzDeck v3.6.88 - Smart Import Wanted Reconciliation Fix

This release fixes Automation state after a successful quality upgrade import.
A freshly imported Dolby Vision/HDR release now becomes the authoritative
post-import state immediately, while pre-v3.6.88 records with uncertain dynamic-
range provenance can still accept a corrective same-tier replacement.

Preserved:
- v3.6.87 same-tier dynamic-range correction behavior
- v3.6.86 Automation/Interactive Search cache snapshot performance
- SABnzbd 5.1.2 integration and Smart Import transaction safety
- Metadata Server v0.3.3
- Diagnostic Collector v1.0.31
- Frozen Newsgroup Browser architecture and tuning

See release/RELEASE_NOTES_v3.6.88.md for details.
