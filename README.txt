NewzDeck v3.6.56
Smart Import Duplicate Protection & Diagnostics Refinement

New in v3.6.56:
- Smart Import stops before commit when incoming TV media is byte-identical to a different episode of the same title; the downloaded output is preserved for Needs Review.
- Incoming season-pack episodes are also checked against one another for identical bytes before commit.
- SAB warnings tied to releases that later completed successfully are retained as resolved historical evidence instead of remaining current engine warnings.
- Raw SAB Active-slot overlap is separated from real visible-card correction and uses bounded examples instead of long UUID signatures.
- /api/diagnostics and /api/diagnostics/report share a coherent 1.5-second snapshot cache to avoid duplicate expensive aggregation.
- Preserves v3.6.55 terminal-history efficiency, v3.6.54 compaction, v3.6.53 identity/Smart Import safeguards, and private SABnzbd 5.1.2 authority.
